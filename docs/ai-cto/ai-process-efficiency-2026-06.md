# AI Process Efficiency Review — 2026-06-22

How we (founder ↔ Claude) spend tokens, where it leaks, and what to change. Scoped to the
A777ance workflow: cross-repo Claude Code sessions, scheduled/headless routines, and the
LiteLLM hybrid router already on the t630. Web-sourced best practices are dated — recheck
quarterly; this field moves weekly. Sources at the bottom.

---

## TL;DR — the five levers, biggest first

| # | Lever | Est. saving | Effort | Where |
| - | ----- | ----------- | ------ | ----- |
| 1 | **Trim the CLAUDE.md files** — ~11K tokens re-sent *every turn* | 60–90% of per-turn fixed cost | Half a day | all repos |
| 2 | **Right-size the model** — stop running Opus on monitoring routines | 5× on routed work (Opus→Sonnet), more to Haiku | minutes/session | all sessions |
| 3 | **Session hygiene** — scope tasks, `/clear`, `/recap`, batch | 30–70% per session | habit | all sessions |
| 4 | **Use the hybrid router we already built** for routine automation | up to 10× on the offloaded slice | already deployed | localDNS router |
| 5 | **Prompt caching + Batch API** for any API-side jobs | 50–90% on repeated/async work | low | statement/CFO jobs |

---

## 1. The biggest leak: CLAUDE.md weight (fix this first)

Every turn of a Claude Code session re-sends the system prompt, the tool schemas, **and every
loaded `CLAUDE.md`** as input. A 5,000-token instruction file costs 5,000 tokens on turn 1 *and*
on turn 200. In a 30-turn session, 1,000 wasted tokens up front becomes 30,000 tokens of waste,
paid at the input rate every re-send.

Our numbers (word count → rough token count ≈ ×1.35):

| File | Words | ≈ tokens |
| ---- | ----- | -------- |
| `localDNS/CLAUDE.md` | 2,728 | ~3,680 |
| `DESIGN-…/CLAUDE.md` | 2,608 | ~3,520 |
| `MARKETING/CLAUDE.md` | 1,445 | ~1,950 |
| `customers/CLAUDE.md` | 562 | ~760 |
| `claude-code-homelab/CLAUDE.md` | 371 | ~500 |
| `Azure-lab/CLAUDE.md` | 316 | ~430 |
| **Total** | **8,030** | **~10,800** |

A cross-repo session (like the scheduled routines) loads several — or all — of these at once.
That's ~11K tokens of fixed overhead **before a single word of the actual task**, re-sent on
every turn.

A published benchmark stripped a 3,847-token CLAUDE.md to 312 tokens — only what Claude
*cannot infer from the code itself* — for a **91.9% reduction with no quality regression.**

**What to cut here, concretely:**

- The **House style block is duplicated verbatim in all 6 files** (~300 tokens each, ~1,800
  total, re-sent every turn). Put it in **one** file and reference it, or move it to a
  `STYLE.md` that's loaded only when a doc is actually being written — not on every coding turn.
- Long prose rationale ("the *why*") belongs in `README.md` / `network-context.md` /
  `workflow-context.md`, which Claude reads **on demand**. CLAUDE.md should be the *index and
  the invariants*, not the narrative. Our CLAUDE.md files currently re-tell the business model
  three times across DESIGN/MARKETING/localDNS.
- Keep in CLAUDE.md only what Claude can't derive by reading the repo: hard invariants (e.g.
  "never add sensitive domains to the forward-path"), the deploy-path table, the
  push-to-`main`/branch rule, and pointers to the deeper docs.

Target: get each CLAUDE.md under ~800 tokens. That alone likely saves more than every other
lever combined, because it's a tax on *every turn of every session forever*.

> ⚠️ House-style caveat: the reverse-chronological / Z→A / reversed-walkthrough conventions are
> themselves a token and error cost — they're surprising, so they get re-explained in every file
> and invite mistakes. Worth a founder decision on whether the stylistic payoff is worth the
> recurring overhead. (Not changing it here — flagging it.)

## 2. Right-size the model

Opus costs ~5× Sonnet per token; Sonnet is the speed/intelligence sweet spot; Haiku handles
routine edits at a fraction of the cost. Guidance: **start every session on Sonnet, escalate to
Opus only for deep analysis or gnarly multi-file refactors.**

This very routine is running on **Opus 4.8** to do web research + summarize — work Sonnet (or a
local model, §4) does at a fraction of the cost. **Action:** set scheduled/monitoring routines to
Sonnet or Haiku by default; reserve Opus for the hard interactive sessions. Model routing is
cited as a 40–70% lever on its own.

## 3. Session hygiene (the per-session habits)

- **Scope precisely.** "Refactor the login function in `auth.ts`" beats "refactor the auth
  module." Smaller scope = less context pulled in = fewer tokens and tighter output.
- **`/clear` between unrelated tasks** instead of letting one mega-session accumulate. Long
  threads are the biggest hidden drain — every new message re-reads the whole history.
- **`/recap`** (new Apr 2026) summarizes where you left off without replaying the conversation —
  use it to resume instead of scrolling/re-reading.
- **Batch related work** into one session (all five statement tweaks together), not five
  sessions that each re-load context.
- **`.claudeignore` / `.gitignore` discipline** keeps generated data, `stats/`, rendered HTML,
  and `node_modules`-type noise out of Claude's view (one source measured 85% context reduction
  from ignore-file discipline alone).

## 4. We already built the hybrid — now route work to it

`localDNS/10-ai-orchestration/` is ahead of the curve: a LiteLLM front door with local Ollama
tiers (`local-fast` qwen2.5:3b, `local-smart` qwen2.5:7b, `local-reason`), a rented-GPU tier for
heavy reasoning, and **Claude only as `cloud-overflow`**. Industry reports put hybrid savings at
**60–83%** by running the routine 70–80% of prompts locally and reserving the cloud for the hard
20–30%.

The gap is **usage, not capability** — our scheduled routines run on Claude (Opus, headless)
instead of through this router. Candidates to move local (the t630 is CPU-only and slow, so favor
*non-interactive, nightly, latency-tolerant* jobs):

- Doc-link checking, lint-style passes, "did anything change" diffs.
- First-draft summaries and classification (then a cheap Claude pass only if needed).
- Embeddings for any RAG (already local via `local-embed` / nomic-embed-text).

**Blocker to fix first:** **TD-14** — a `sensitive`-tagged task can fail over from `local-reason`
to `cloud-overflow` (Claude cloud) because the LiteLLM fallback isn't fenced by `allow_cloud`.
Fix the privacy gate (fail closed to a local-only chain) before pushing more traffic through the
router, or we risk leaking private lookups to the cloud.

## 5. Prompt caching + Batch API (for API-side jobs)

For anything hitting the Claude API directly (CFO/statement automation, not interactive Claude
Code, which already caches automatically):

- **Prompt caching:** cached input reads cost **10% of normal** (90% off); writes cost 1.25×.
  Default TTL 5 min, 1-hr option. Rule: **stable content first** (system prompt, tools, durable
  examples), volatile/user content last — and don't edit the cached prefix often, since any edit
  invalidates the whole cached block. High-ROI once a system prompt is >2K tokens and you make
  more than a few hundred calls/day.
- **Batch API:** async jobs that can wait up to 24h are **50% cheaper across all models.** The
  monthly statement run and any bulk classification are perfect fits.

## 6. The billing signal worth designing for (not a current alarm)

Anthropic announced (May 14) that Agent SDK / headless `claude -p` / Claude Code GitHub Actions /
scheduled programmatic use would leave the subscription pool on **June 15, 2026** for a separate
metered credit pool ($20 Pro / $100 Max 5× / $200 Max 20×, no rollover). **Anthropic *paused*
this on June 15 — it is not live, interactive use is untouched.** But the direction is clear:
programmatic/automated Claude usage is the thing they want metered separately. Designing our
scheduled routines to be lean (§1–4) and to lean on the local router (§4) is exactly the
resilience hedge if/when this returns. Recheck status before assuming the subscription subsidy
for automation is permanent.

## 7. Other current techniques worth a look

- **Subagents / fan-out** — each subagent runs in its **own** context window and reports back
  only its conclusion, so intermediate file-dumps never bloat the main thread. June 2026 added
  nested subagents and "dynamic workflows" (a lead agent fans out many subagents). Good for
  research-style and multi-file review tasks. (This routine used parallel web searches in one
  turn for the same reason.)
- **Skills for terse output** — community "caveman"-style skills that strip pleasantries/filler
  reportedly cut output tokens ~65%. A lighter version: a house instruction to skip preamble and
  postamble on routine runs.

---

## Critique of the prompt that triggered this review

The request was effective at *intent* but expensive by design. It said, in effect, "find
inefficiencies… anything you could possibly think of… ANYTHING that could help… search the web…
check the news." That's three problems for token efficiency:

1. **Unbounded scope** ("anything", "ANYTHING") invites a sprawling, maximal answer — the
   opposite of the efficiency being asked for.
2. **No output contract** — no length, format, or destination, so the model has to guess (and
   tends to over-produce).
3. **Open-ended web research** — "search the web… check the news" with no stopping rule can fan
   out indefinitely.

A leaner version that gets the same result for fewer tokens:

> *"Review our Claude usage for token waste. Cover: (1) CLAUDE.md / context size, (2) model
> choice, (3) session habits, (4) using our local LiteLLM router, (5) caching/batch. Do up to ~6
> web searches for 2026 best practices, prioritizing anything that changed this quarter. Output:
> a ranked table of fixes (saving / effort) + a one-paragraph note on each, committed to
> `docs/ai-cto/`. Skip anything we already do well unless it's underused."*

That version names the buckets (so I don't rediscover them), caps the research, fixes the output
shape and destination, and tells me what to skip — typically a large reduction in both my
thinking tokens and the response length, for a more useful answer.

---

## Recommended next actions (ranked)

1. **Trim all 6 CLAUDE.md files to ≤~800 tokens**; de-duplicate the House-style block into one
   place. (§1 — biggest, recurring win.)
2. **Default scheduled/monitoring routines to Sonnet or Haiku**, not Opus. (§2.)
3. **Fix TD-14** (privacy fail-closed), then **route nightly/batch automation through the local
   router**. (§4.)
4. Adopt **`/clear` + `/recap` + tight scoping** as standing session habits. (§3.)
5. For API-side statement/CFO jobs, turn on **prompt caching** and use the **Batch API**. (§5.)
6. Re-check the **June-15 billing** status quarterly; keep automation lean as the hedge. (§6.)

## Sources (2026; recheck — fast-moving)

- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Anthropic Prompt Caching in 2026 — finout.io](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching in 2026: Anthropic vs OpenAI vs Azure — technspire](https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins)
- [Hybrid Cloud-Local AI Workflows — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Local AI Models with Claude Code to Cut Costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Steering Claude Code: skills, hooks, subagents — claude.com](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Claude Credit Overhaul 2026: Anthropic Pauses the June 15 Change — digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Your Claude Code Automations Are About to Get a Bill — Medium/Fukuda](https://medium.com/@fukuda.aritomo/your-claude-code-automations-are-about-to-get-a-bill-6a77cf5338f9)
