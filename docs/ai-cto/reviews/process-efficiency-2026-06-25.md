# Process efficiency review — user ↔ AI, token & cost

**Date:** 2026-06-25 · **By:** NARF (AI CTO), scheduled routine · **Scope:** how we work *with*
the AI across the A777ance repos — token waste, prompting, hybrid local/cloud routing, and the
recurring-routine design itself.

This is advisory. Findings are ordered by impact, not by date. Sources at the bottom.

---

## TL;DR — the five moves that matter

1. **Trim every `CLAUDE.md`.** They total ~8,000 words (~10–11K tokens) and *all of them* load
   at session start, before any work. Industry guidance is <500 tokens / <200 lines each; ours
   run 5–7× that. This is a constant tax on every turn of every session.
2. **Actually use Odin (local tier) for bulk text.** We *built* the LiteLLM+Ollama hybrid but
   left cloud as "failover only." 60–70% of real tasks (classify, extract, format, draft) are
   cheap-model work — route those local-first and reserve Claude for hard reasoning +
   customer-facing prose.
3. **Turn on prompt caching for the cloud tier.** Cache reads cost 10% of input. Our repeated
   jobs (statement runs share a big static template/system prompt) are the textbook case —
   60–90% input savings.
4. **Batch the monthly statement run.** It's not interactive → Messages Batch API is 50% off and
   stacks with caching.
5. **News that hits *this* routine:** since **2026-06-15**, `claude -p` / Agent SDK (i.e.
   scheduled/headless runs like this one) bill from a **separate dollar credit at API rates**, no
   longer the subscription. Scheduled routines now have a real dollar meter — which makes #1
   financially concrete, and means open-ended "find anything" routines should be narrowed.

---

## 1. The `CLAUDE.md` baseline tax  — biggest, most concrete win

Measured today:

| Repo | `CLAUDE.md` words |
| ---- | ----------------- |
| localDNS | 2,728 |
| DESIGN (this repo) | 2,608 |
| MARKETING | 1,445 |
| customers | 562 |
| claude-code-homelab | 371 |
| Azure-lab | 316 |
| **total** | **~8,030 words ≈ 10–11K tokens** |

When a session opens with several repos in scope, **all** their `CLAUDE.md`s are injected as a
fixed prefix — paid on every turn, before a single file is read. Two specific wastes:

- **Duplication.** The "House style: ordering & typography" block is copy-pasted verbatim into
  all 7 files (~150 words each ≈ ~1,000 words of pure repetition loaded every session). Put it
  **once** in a shared `CONVENTIONS.md` and have each `CLAUDE.md` link to it.
- **Reference material masquerading as briefing.** localDNS's full deploy-path table, the DESIGN
  stage map, the known-issues tables — these are *lookup* docs, not "read before you act" rules.
  They belong in `README.md` / `network-context.md`, fetched on demand.

**Recommendation:** cut each `CLAUDE.md` to a lean core (<500 tokens): what the repo is, the 3–5
hard rules (push-to-main, honesty rule, no secrets), and pointers to where the detail lives. Move
everything else down a level. Target: ~3K tokens total across all repos, down from ~10K.
(Caching softens the in-session cost, but cold sessions — and every scheduled run — pay it fresh.)

→ logged as **TD-15**.

## 2. Use the hybrid we already built (Odin / LiteLLM)

`10-ai-orchestration/` already has the right architecture: one OpenAI-compatible front door,
local `qwen2.5:3b/7b` as default, Claude as overflow, a deterministic privacy gate in the
dispatcher. The gap is that the *real workflow* doesn't route through it — cloud is treated as
"failover only," so in practice the expensive brain does cheap work.

Published task-mix data: ~60–70% simple (classification, extraction, formatting), ~20–30%
moderate, ~10% needs a frontier model. Map that onto us:

- **Local-first (qwen on the t630):** lead/intent classification, roster field extraction,
  "Handled For You" first drafts, statement-prep text munging, commit-message/changelog drafts,
  doc-lint triage. Non-sensitive, high-volume, quality-tolerant.
- **Claude (cloud):** customer-facing prose that must read well, hard reasoning/architecture, code
  diffs, anything needing the 1M context. Keep the dispatcher's privacy gate as the guardrail.

Concrete: point cheap subagents / scripts at `ai.home.lan:4040` instead of the API. Reported
hybrid savings are 60–80%. (Caveat from the docs: the CPU 7B is slow — use it for "submit and
wait" batch work, not interactive chat. And **fix TD-14 first** — the `local-reason` →
`cloud-overflow` fallback can leak a `sensitive` task; fail it closed before routing real data.)

## 3. Prompt caching on the cloud tier

Our `cloud-overflow`/`cloud-*` tiers go to `claude-opus-4-8` via LiteLLM with **no caching
configured**. Anthropic caching is aggressive: cache write = 1.25× input (5-min TTL), cache read
= **0.10× input**. It pays off after the first reuse. Best fits here:

- Statement generation: one large static system prompt + template, reused across many households
  → cache the static prefix, vary only the per-home data.
- Any agent loop with a stable instruction block.

Rules that bite: keep static content first, dynamic last; **no timestamps in the cached prefix**
(truncate to the day or move them to the user turn) or you invalidate the cache every call.

## 4. Batch the monthly run

Stage 06 statements are produced on a schedule, not interactively — the **Messages Batch API**
(50% off, async) is built for exactly this, and it stacks with #3. One nightly/monthly batch job
beats N interactive calls.

## 5. NEWS — the 2026-06-15 Agent SDK billing change (affects this routine directly)

As of 2026-06-15, **`claude -p` and the Agent SDK no longer draw from the Claude plan's usage
limits** — they bill from a separate, dollar-denominated Agent SDK monthly credit at standard API
rates. Interactive terminal Claude Code, claude.ai chat, and Cowork are unchanged.

Implication for us: **every scheduled routine is now a metered API spend, not "free" subscription
quota.** So:
- The fat `CLAUDE.md` baseline (#1) is now real dollars per run → do #1.
- Open-ended "find anything you can" routines re-plough the same ground each run and burn the
  credit. Narrow recurring routines to *deltas* (see #7).
- Track the new credit line in ZORT's budget (`docs/ai-cfo/budget.md`) — it's a new recurring cost.

## 6. Model tiering & session hygiene (cheap habits, real savings)

- **Right-size the model.** Don't run Opus for mechanical edits; `opusplan` plans on Opus then
  implements on Sonnet. Most edits are Sonnet/Haiku work. Reported 40–70% on focused tasks.
- **One repo per session when you can.** A multi-repo session pays every repo's `CLAUDE.md`
  baseline; scope down to shed it.
- **`/clear` between unrelated tasks, `/compact` before long sessions, point at specific files**
  rather than "the whole project." Stale context is re-billed every turn.
- **Subagents for heavy *read-only* research** (like this review) keep the main context lean — but
  they add overhead, so don't spawn one for a `git status`.

## 7. Critique of the prompt that launched this routine

The prompt was, verbatim, a kitchen sink: *"Anything you could possibly think of … ANYTHING that
could help."* That maximizes breadth and output length — it's the most expensive shape a prompt
can take, and as a **recurring** routine it re-derives the same findings every run against the new
metered credit. It worked once (this doc), but it's the wrong standing instruction.

**Make it two prompts:**

- *One-off audit* (this one — done): keep the breadth.
- *Recurring watch* (narrow, cheap): something like —
  > "Check the Anthropic changelog, model list, and pricing page. Compare against
  > `docs/ai-cto/reviews/process-efficiency-2026-06-25.md`. Notify **only** if something changed
  > that affects our token cost, model choice, or the Agent SDK billing. Otherwise stay silent.
  > Budget: keep it short."

That gives scope, a comparison baseline, an explicit silence condition, and a budget — the four
things the original lacked. It turns a daily broad essay into a cheap diff.

---

## Sources

- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Code — Manage costs](https://code.claude.com/docs/en/costs)
- [Anthropic June 15 2026: Claude Code / Agent SDK billing change](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [Hybrid Cloud-Local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude API cost optimization: caching, batching, 60% reduction](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [23 tips for Claude Code token saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [LLM gateways & model routing — cut AI costs 2026](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
