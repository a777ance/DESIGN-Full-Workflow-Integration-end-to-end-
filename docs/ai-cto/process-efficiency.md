# Process efficiency — user ↔ AI token & workflow review

*Reviewed 2026-06-19 by NARF (AI CTO). Standing item — re-run quarterly or when Anthropic
ships pricing/feature changes. This is a living analysis; newest findings go at the top per
house style.*

## TL;DR

The single biggest waste in our process is **how much a session reads before it does any
work**. A DESIGN session that fires both the NARF and ZORT session-start rituals loads
**~19,000 tokens of context before the first useful action** — and most of it is irrelevant
to any one task (a doc edit does not need the CFO metrics log). The fix is cheap and has three
layers: (1) make that fixed preamble *near-free* with prompt caching, (2) stop reading docs the
task doesn't need, and (3) push cheap/bulk work to the local LLM rig we already own. Combined,
a realistic **40–70% cut in per-session token spend** with no loss of capability.

---

## 1. The numbers (measured today, this repo)

| What loads | Chars | ≈ Tokens | When |
| ---------- | ----: | -------: | ---- |
| `CLAUDE.md` | 17,987 | ~4,500 | every session **and re-sent every turn** |
| NARF reads (portfolio + roadmap + tech-debt + decisions) | 22,183 | ~5,550 | every CTO session start |
| ZORT reads (portfolio + decisions + metrics + runway + budget) | 34,949 | ~8,740 | every CFO session start |
| **Fixed preamble before task work** | **~75,000** | **~18,800** | every dual-hat session |

For scale, `localDNS/CLAUDE.md` is **20,472 chars (~5,100 tok)** and `metrics.md` alone is
**16,081 chars (~4,000 tok)**. None of this is "the work" — it's table-setting that repeats
every run.

---

## 2. The levers, in priority order

### Lever 1 — Prompt caching: make the preamble ~free (do this first)
Cache writes cost 1.25× input; **cache reads cost 0.1× — a 90% discount on repeated input**.
Our CLAUDE.md + session-start docs are the textbook case: large, stable, re-sent every turn.
Claude Code applies caching automatically, but it only helps if the prefix is *stable within a
session* — so: keep the long stable docs at the **front** of context, don't interleave edits
into them mid-session, and prefer one longer session over many cold starts (each cold start pays
the 1.25× write again). Practical effect: the ~19k-token preamble drops from ~19k tok/turn to
~1.9k tok/turn after the first turn. **This is the highest-ROI change and requires zero repo
edits.**

### Lever 2 — Lazy session-start reads (stop reading what the task won't use)
Today both CLAUDE.md files command an unconditional "at session start, read these 4–6 files."
That's ~14k tokens of CTO+CFO docs loaded even for a one-line doc fix. Change the instruction to
**conditional/lazy loading**: read the index/portfolio only, then pull a specific doc *when the
task touches it*. Concretely, replace "read all of these" with "skim `portfolio.md` for state;
read the others only if the task is about roadmap/tech-debt/finance." Subagents (Lever 5) make
this even cleaner. Estimated saving: 8–12k tokens on the majority of sessions that aren't
finance work.

### Lever 3 — Right-size the model and effort to the task
Opus is ~5× Sonnet per token; Opus 4.8 is $5/$25 per MTok, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5.
Most of our routine work — doc edits, link fixes, roster entries, `check-docs.py` runs, commit
messages — is Sonnet/Haiku work. Reserve Opus (and `/effort xhigh`) for genuine architecture and
ambiguous reasoning. Default routine sessions to Sonnet; escalate deliberately. Note Opus 4.8
defaults to *high* effort — drop effort for mechanical tasks.

### Lever 4 — Use the local rig we already paid for (hybrid routing)
We run a LiteLLM router on the t630 with a reasoning ladder (`local-reason` deepseek-r1:1.5b on
CPU, `cloud-gpu-reason`, `cloud-overflow`). Industry pattern: ~60–70% of LLM requests are simple
(classify/extract/format/draft) and can run **locally at $0 marginal cost**; reserve the Claude
API for the ~10% that needs frontier reasoning. Hybrid setups report **60–80% cost cuts**.
Candidate local-only jobs for us: roster field validation, statement-data sanity checks,
first-draft "Handled For You" copy, log triage, doc-link pre-checks, classification/tagging.
**Caveat — TD-14 is a hard blocker for anything sensitive:** `local-reason` currently fails over
to `cloud-overflow` (Claude cloud), so a `sensitive`-tagged prompt can leak. Fix the fail-closed
gap before routing any real customer data locally.

### Lever 5 — Subagents for heavy/verbose reads
A subagent runs in its own context window and returns only a summary — the verbose intermediate
(reading 5 finance docs, scanning logs, sweeping files) stays out of the main session's running
cost. Use one for "go read the CFO docs and tell me X" instead of inlining all of metrics.md.
Caveat: multi-agent *teams* burn ~7× tokens (each teammate is a full instance) — use a single
delegated subagent for context isolation, not a swarm, unless the parallelism genuinely pays.

### Lever 6 — De-duplicate the house-style block
The identical ~350-token "House style" block is copy-pasted into **all 7 CLAUDE.md files**. It's
loaded whenever its repo is active and is a maintenance hazard (change it once, it drifts 6
ways). Move the canonical copy to one file (e.g. a shared `HOUSE-STYLE.md` in DESIGN) and have
each CLAUDE.md link to it in one line. Small token win; real consistency win.

### Lever 7 — Trim CLAUDE.md to a true "briefing"
CLAUDE.md is meant to be the short briefing but DESIGN's is ~4,500 tok and re-sent every turn.
Push the funnel diagram, full stage map, and verification walkthrough into README (already
linked) and keep CLAUDE.md to: what the repo is, the rules, where to look. Target <2,000 tok.
Caching softens this, but a leaner prefix also speeds the first turn and every cold start.

---

## 3. Best practices captured (June 2026)

- **Prompt caching**: 90% off repeated input (reads 0.1×, writes 1.25×). Stack with **batch
  processing (50% off)** for any non-interactive bulk job (e.g. generating many statements).
- **Context is the cost, not prompt length** — you pay for every earlier message, file read,
  and tool output re-sent each turn. `/clear` between unrelated tasks; don't let one session
  accrete. Claude Code now hints when to clear.
- **Plan-before-code** (exact file paths up front) measurably cuts rework tokens.
- **`.claudeignore` / scoped tools** keep junk out of context (reported ~85% context cut from
  ignore discipline alone) — relevant as repos grow.
- **News check**: The June 15 2026 billing change (moving Agent SDK / `claude -p` / 3rd-party
  usage to a separate credit) was **cancelled** — those surfaces still draw from the normal
  subscription. Opus 4.8 is the new default (May 28 2026); Fast Mode dropped to $10/$50.
  Auto mode now runs on Bedrock/Vertex/Foundry. No action needed from us beyond awareness.

---

## 4. The prompt itself was inefficient — here's the fix

The triggering request ("Locate inefficiencies… ANYTHING that could help… anything you could
possibly think of… search the web… check the news") is **unscoped and open-ended**, which is the
most expensive shape of prompt: no success criteria, no boundary, no output format, no budget —
so the model fans out maximally and burns tokens exploring. It's friendly and clear in *intent*,
but it optimizes for breadth over cost, which is ironic given the goal.

A leaner version that gets the same answer for far fewer tokens:

> *"Review our Claude-Code-on-the-web process for token waste. Focus on the three biggest levers
> only. For each: the problem, a concrete fix, and a rough % saving. Skip anything speculative.
> Output a short bullet list, then one recommended next action. Web-search only if a 2026 pricing
> or feature fact is load-bearing."*

Prompting habits that save us tokens going forward:
- **Scope and cap**: "top 3," "short list," "skip speculative" — bound the fan-out.
- **Name the output format** up front (bullets, table, one file) so the model doesn't draft long
  prose you'll trim.
- **Gate the web**: "search only if a fact is load-bearing" stops reflexive searching.
- **One task per session**, then `/clear` — don't chain unrelated asks in a long thread.
- **Say the model/effort you want** for the job ("this is mechanical, use Sonnet, low effort").

---

## 5. Recommended next actions (quick wins → bigger bets)

1. **Now, zero-risk**: rely on prompt caching — keep long docs at the front, favor longer
   sessions over cold starts. (Lever 1)
2. **One edit**: change both CLAUDE.md session-start rituals from "read all" to "skim portfolio,
   read the rest on demand." (Lever 2)
3. **Habit**: default routine sessions to Sonnet/Haiku; reserve Opus + high effort for
   architecture. (Lever 3)
4. **Unblock then route**: fix TD-14 (fail-closed local fallback), then move classify/extract/
   draft jobs to the local rig. (Lever 4) — tracked as **TD-15**.
5. **Cleanup**: hoist the house-style block to one shared file; trim DESIGN CLAUDE.md toward
   <2,000 tok. (Levers 6–7)

---

## Sources

- [Anthropic prompt caching — docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API pricing 2026 (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API cache pricing — 90% input savings (TokenMix)](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [What's new — Claude Code docs](https://code.claude.com/docs/en/whats-new)
- [7 practical ways to reduce Claude Code token usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 ways to cut token consumption in Claude Code (Firecrawl)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Claude Code subagents — 2026 guide (Tembo)](https://www.tembo.io/blog/claude-code-subagents)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM model routing 2026 — cost/quality (DigitalApplied)](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Anthropic June 15 2026 billing change paused (DigitalApplied)](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
