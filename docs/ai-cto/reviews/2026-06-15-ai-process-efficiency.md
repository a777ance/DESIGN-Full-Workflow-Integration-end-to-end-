# AI Process Efficiency Review — 2026-06-15

A look at the **process between the human and the AI** across the A777ance repos:
where tokens (and money) leak, where prompting can be tighter, and where the existing
local-LLM stack should be doing more of the work. Findings are prioritized; the dollar
figures use current Anthropic pricing (verified 2026-06-15, sources at the bottom).

Author: NARF (AI CTO), scheduled routine. Newest-first per house style.

---

## TL;DR — the five things worth acting on

1. **[TIME-SENSITIVE] Anthropic's June 15 billing change hits scheduled routines.** As of
   today, `claude-p` / Agent SDK runs (which is what Claude Code on the web and these
   scheduled routines use) meter against a **separate credit pool at full API rates with
   no rollover** ($20 Pro / $100 Max-5x / $200 Max-20x). Broad "analyze everything"
   routines on Opus now burn that pool fast. **Audit and scope your routines this week.**
2. **The session-start ritual is the biggest recurring token sink.** Every session loads a
   large CLAUDE.md *and* is told to read 4 (NARF) + 6 (ZORT) more docs. Make that
   conditional, not unconditional.
3. **You already own a hybrid stack — use it.** The LiteLLM router + local DeepSeek on the
   t630 + cloud-GPU tier is built. Route the cheap 60–70% of work (classification,
   extraction, log/triage summaries, first drafts) locally; reserve Claude for the hard
   ~10%. Industry reports put this at **60–90% cost reduction**. But fix **TD-14 first**
   (the privacy fail-open) before leaning on it.
4. **Prompt caching + Batch API are free money for any programmatic Claude calls.** Cache
   reads cost ~10% of input price; the Batch API is 50% off. Neither is wired in.
5. **This very prompt is inefficient** — see the last section for why and a rewrite.

---

## 0. How the money actually flows today

| Surface | What it costs | Notes |
| --- | --- | --- |
| Claude Code on web (interactive) | Opus 4.8 @ $5 in / $25 out per 1M tok | Within a session, CLAUDE.md + system prompt are prompt-cached automatically (~10% on reads) |
| **Scheduled routines (this run)** | **Same Opus rates, now on a separate no-rollover credit pool** | June 15 change — see Finding 1 |
| localDNS LLM router (LiteLLM) | local = electricity only; `cloud-overflow` = Claude API | The hybrid lever already exists (stage 10) |

Current Anthropic pricing, per 1M tokens: **Opus 4.8 $5/$25 · Sonnet 4.6 $3/$15 ·
Haiku 4.5 $1/$5.** Prompt-cache reads ≈ $0.50/1M on Opus (10% of input); cache writes
1.25× (5-min TTL) or 2× (1-hr TTL). Batch API: 50% off everything.

---

## 1. [P1, TIME-SENSITIVE] June 15 billing change — scoped routines, not broad ones

**What changed (today):** Anthropic moved Claude Agent SDK / `claude-p` onto a separate
metered credit, billed at full API rates with no rollover. Headless/scheduled runs — like
this routine — draw down that pool. Before, agentic runs leaned on the subscription window;
now overflow is metered cash.

**Why it bites us:** an open-ended routine ("analyze ANYTHING that could help, search the
web, check the news") on Opus 4.8 at high effort is a multi-dollar run *every time it
fires*. A daily cadence of those is real money against a finite pool.

**Actions**
- Inventory every scheduled routine / loop. For each, ask: does this need Opus, or would
  Sonnet/Haiku do? Does it need to run daily, or weekly? Does it need the web at all?
- Make routines **scoped and idempotent**: "check X for condition Y, notify only if Z"
  beats "review everything." A tight routine is cheaper *and* gives a better notification.
- Keep a cost line in `docs/ai-cfo/budget.md` for the metered credit so ZORT sees the burn.

## 2. [P1] The session-start ritual is the dominant recurring cost

**Measured today** (`wc` across repos):

| File | Bytes | ≈ tokens |
| --- | --- | --- |
| localDNS/CLAUDE.md | 20.5 KB | ~5,100 |
| DESIGN/CLAUDE.md | 18.0 KB | ~4,500 |
| MARKETING/CLAUDE.md | 10.7 KB | ~2,700 |
| customers / homelab / azure stubs | ~9 KB | ~2,200 |

That's the *floor*. On top of it, DESIGN's CLAUDE.md instructs **NARF to read 4 docs and
ZORT to read 6 docs at the start of every session** (portfolio, roadmap, tech-debt,
decisions, metrics, runway, budget, …). A routine touch-up to one stage README can pull
~30–40 KB of context before any work happens — paid on every session and every routine.

This is not "delete your CLAUDE.md." These files are genuinely good and the voice/house-style
rules earn their keep. The waste is **unconditional eager-loading**.

**Actions**
- Convert the session-start "read these 10 files" block into a **conditional**: read the
  hub docs *only when the task is cross-repo planning or a session-end status update*. A
  one-line README fix in stage 06 does not need the CFO runway analysis in context.
- Move rarely-needed detail out of CLAUDE.md into the linked READMEs (they're already
  referenced) so it loads on demand, not always.
- Consider a **skill** for the house-style/voice rules (loads its description always, full
  body only when writing customer-facing copy) instead of carrying the full ruleset inline.
- Run `client.messages.count_tokens` on each CLAUDE.md to track the real number over time —
  don't eyeball it.

## 3. [P2] Run the hybrid stack you already built

The localDNS LLM router (LiteLLM, stage 10) already has a reasoning ladder: `local-reason`
(DeepSeek-R1:1.5b on the t630, cool/cheap), `cloud-gpu-reason` (rented GPU on demand), and
`cloud-overflow` (Claude). The architecture is done — it's just under-used.

Typical workloads split ~60–70% simple (classify, extract, reformat, summarize), ~20–30%
moderate, ~10% needing a frontier model. Routing the cheap majority to the local tier and
reserving Claude for the hard slice is the single biggest structural saving — reports
converge on **60–90% lower cost at the same quality ceiling**.

**Candidates to route locally:** log/health triage summaries (Uptime Kuma, packet-loss
monitor), first-draft marketing copy, classification/tagging of CRM rows, "Handled For You"
log normalization. **Keep on Claude:** statement-honesty review, anything cross-repo,
contract/compliance reasoning, code review.

**Blocker — do this first:** **TD-14**. A `sensitive`-tagged task can currently fail *open*
to `cloud-overflow` (Claude cloud) if the local model is down, because `allow_cloud=False`
isn't enforced at the LiteLLM failover layer. Until `local-reason` has a **local-only**
fallback (fail closed), do not push more sensitive traffic through the router. Fixing TD-14
is the prerequisite for trusting the hybrid path with real customer data.

## 4. [P2] Prompt caching + Batch API for programmatic Claude calls

For any non-interactive Claude calls (anything going through `cloud-overflow`, or a future
batch job):
- **Structure prompts stable-first:** frozen instructions/context first, the volatile
  question last, one `cache_control` breakpoint at the boundary. Cache reads are ~10% of
  input price. Keep `datetime.now()`, UUIDs, and unsorted JSON out of the cached prefix —
  they silently invalidate the cache.
- **Use the Batch API for anything not latency-sensitive** (overnight bulk classification,
  monthly report generation): **50% off**, completes within ~1 hour usually.
- Combined with local routing, a bulk pipeline can run **80–90% cheaper than naive calls**.

## 5. [P2] Model selection inside Claude Code

Opus 4.8 is the right default for hard reasoning, but not for everything. For routine edits,
doc fixes, and mechanical refactors, Sonnet 4.6 ($3/$15) is ~40% the cost and plenty capable;
Haiku 4.5 ($1/$5) handles classification/lookup. The choice is the operator's to make per
task — just make it deliberately rather than running Opus on a typo fix.

## 6. [P3] Workflow hygiene (cheap habits, real savings)

- **`/clear` between unrelated tasks.** Long threads re-send the whole history every turn —
  the single most common hidden drain. Start fresh when the topic changes.
- **Scope prompts.** "Fix the broken link in stage 06's README" beats "review the repo."
- **Use subagents / Explore for search.** They run in an isolated context and return only
  the conclusion, so the search dump never lands in your main window. (Costs more tokens
  total per multi-agent run, so use for genuine fan-out, not single-file lookups.)
- **Plan mode for big changes** — agree the plan before the model spends tokens executing
  the wrong thing.

---

## On the prompt that triggered this review

Asked directly: **yes, the triggering prompt is inefficient**, and it's a good worked
example of the cost of an unscoped ask.

> *"Locate inefficiencies in our PROCESS … Is there a better way … Perhaps also better
> prompting … Anything you could possibly think of. Leveraging other AI … Search the web …
> Keep UP TO DATE … Check the news. … If THIS prompt is inefficient then also let me know."*

What makes it expensive:
- **Unbounded scope** ("ANYTHING that could help") forces broad, open-ended exploration on
  Opus at high effort — the model has no signal for when it has done enough, so it does the
  most.
- **Many parallel sub-asks** (token use, prompting, hybrid LLM, web best-practices, news,
  critique-the-prompt) in one turn — each pulls its own searches and context.
- **No output target or budget** — "let me know" doesn't say where, how long, or how deep.

A tighter version gets ~80% of the value for a fraction of the cost:

> *"Once a week, review our AI usage for cost. Output a short prioritized list (≤1 page) to
> `docs/ai-cto/reviews/`. Cover: (1) any Anthropic pricing/billing news in the last 7 days,
> (2) our top 3 token sinks, (3) one concrete change to try. Use Sonnet unless reasoning
> demands Opus. Notify only if you find a change worth >$X/mo or a billing change."*

That version is scoped, has an output location, names a cadence, sets a model, and gives a
notification threshold — cheaper to run and easier to act on.

---

## Sources (verified 2026-06-15)
- Anthropic API pricing & June 15 billing change — finout.io, codersera.com, releasebot.io
- Prompt caching economics — platform.claude.com/docs (prompt-caching), claude-api skill
- Hybrid local/cloud routing savings — sitepoint.com, buildmvpfast.com, localaimaster.com
- Claude Code token-reduction practices — firecrawl.dev, kdnuggets.com, mindstudio.ai
- Subagent context isolation / token multiplier — tembo.io, smartscope.blog

Pricing changes fast — re-verify before acting on any dollar figure more than a few weeks old.
