# Process-Efficiency Review — User ↔ AI Workflow

**Date:** 2026-07-02 · **Author:** NARF (AI CTO) · **Type:** advisory / no-code

Requested question: *where are the inefficiencies in how we work with the AI, how do we
reduce token use, is there better prompting, can we lean harder on a hybrid local-LLM +
Claude API setup, and what's the current best practice?* This is the write-up. Nothing in
here changes a config; every recommendation is a decision for a human to accept first. It
is ordered by leverage — the top three items are where the money actually is.

---

## TL;DR (the three that matter)

1. **Prompt caching is the single biggest lever, and it's free.** Cached input tokens bill
   at ~0.1× (a 90% discount); the only cost is a 1.25× write on the first request. Our
   `CLAUDE.md` files are large (localDNS ≈ 5.1K tokens, DESIGN ≈ 4.5K) and get re-read every
   session. Keeping the stable prefix *byte-identical* across a session is what makes the
   cache hit — one interpolated timestamp or a reordered list breaks it.
2. **Match the model to the job.** We default everything to Opus. Opus 4.8 is right for the
   hard agentic coding; **Haiku 4.5** ($1/$5 per M vs Opus $5/$25 — 5× cheaper) is right for
   subagents, mechanical edits, doc-link checks, and the daily review sweep's cheap stages.
   **Sonnet 5** is the coding sweet spot when Opus is overkill.
3. **The hybrid router we already built serves the homelab assistant, not our coding.** The
   LiteLLM stack (local Ollama default → Claude overflow) is the right design *for
   chat/RAG*. But Claude Code talks straight to the Anthropic API and should — a 3B/7B CPU
   model can't do agentic coding. Don't try to route dev work through Ollama; do lean on the
   router for the RAG/assistant traffic it's built for.

---

## A. Prompt caching — do this first

The cost model (verified against current Anthropic pricing, 2026-07):

| token class | price vs base input |
| ----------- | ------------------- |
| cache write (5-min TTL) | 1.25× |
| cache write (1-hour TTL) | 2.0× |
| cache **read** | **0.10×** |
| uncached input | 1.0× |

Break-even is **two requests** on the 5-min TTL. Real-world agents hit 80–95% cache-read
rates on static content and routinely cut spend 60–90%.

**What breaks the cache silently** (the thing to actually watch):

- A `datetime.now()`, UUID, or per-request ID interpolated *early* in the prompt → every
  request is unique, zero cache hits.
- Non-deterministic JSON (`json.dumps` without `sort_keys`), a varying tool set, or a
  reordered list in the prefix.
- Editing the system prompt mid-session, or switching models mid-session (caches are
  model-scoped).

**For us specifically:**

- Keep `CLAUDE.md` lean and *stable*. It's the biggest fixed prefix we carry. Treat it like
  a lookup table, not a brain dump — the current DESIGN file (18 KB) has a lot of narrative
  that's genuinely useful to a *new reader* but is re-tokenized every session. Consider
  splitting the "why" prose into `workflow-context.md` (already exists) and keeping
  `CLAUDE.md` to the operational rules. Every KB trimmed is tokens saved on every run.
- If we build anything on the Claude API directly (statement generator, ZORT/NARF batch
  jobs), put `cache_control` on the tool definitions and the frozen system prompt. 40 tools
  cached ≈ $1K/month saved at 1K calls/day per the public benchmarks.
- Verify it's working: `usage.cache_read_input_tokens` should be non-zero on repeated runs.
  If it's zero, a silent invalidator is at work.

Sources: [Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) ·
[Prompt caching deep dive (Agentbrisk, 2026)](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/) ·
[$720→$72 case study](https://labeveryday.medium.com/prompt-caching-is-a-must-how-i-went-from-spending-720-to-72-monthly-on-api-costs-3086f3635d63)

---

## B. Model tiering — stop defaulting to Opus

Current model economics (per 1M tokens, in/out):

| model | in / out | use it for |
| ----- | -------- | ---------- |
| Opus 4.8 | $5 / $25 | hard agentic coding, the main loop, long-horizon work |
| Sonnet 5 | $3 / $15 | most coding, structured build — near-Opus quality, cheaper/faster |
| Haiku 4.5 | $1 / $5 | subagents, mechanical edits, formatting, doc-link checks, cheap review stages |

**Concrete moves:**

- In Claude Code, subagents inherit the parent model by default. File sorting, searches,
  and routine edits don't need Opus — point them at Haiku. The `Explore`/search agents in
  our workflow are prime candidates.
- Our **daily review sweep** (the `docs/ai-cto/reviews/` cadence — one per day plus the
  "codex full-tilt" runs) is a recurring, structured, high-volume job. Run the *finding*
  and *mechanical* stages on Haiku/Sonnet and reserve Opus for the adversarial-verify /
  synthesis stage. That's the classic "cheap fan-out, expensive judge" split.
- One live nit: `localDNS/10-ai-orchestration/config.yaml` still points the `cloud-code`
  capability tier at `claude-sonnet-4-6`. `claude-sonnet-5` is the current sweet-spot
  Sonnet (introductory pricing through 2026-08-31). Small swap, whenever localDNS is next
  touched — not urgent, and not changed here since this is advisory.

---

## C. Context hygiene (where tokens leak in agentic sessions)

The 2026 consensus: cost comes from *bloated context*, not long prompts. "Context rot" —
accumulated history, redundant tool output, noise — is the real bill.

- **Compact early, not late.** Compacting while the session is still healthy produces a
  better summary and keeps signal. Waiting until the context warning means you compact
  noise.
- **Use subagents for read-heavy work.** Anything that needs reading >3–4 large files is a
  subagent candidate — the verbose output stays in the subagent's window and only the
  summary returns. But don't spawn a subagent for a one-line `grep`; the startup overhead
  isn't worth it for trivial work.
- **Batch API for non-interactive jobs.** Anything that isn't latency-sensitive (the
  overnight reviews, bulk statement rendering, ZORT reconciliation) runs at **50% off** on
  the Batches API. This stacks with caching.

Sources: [7 ways to reduce Claude Code tokens (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) ·
[Manage costs — Claude Code docs](https://code.claude.com/docs/en/costs) ·
[23 token-saving tips (Analytics Vidhya, 2026)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)

---

## D. Hybrid local + Claude — we already built the right thing

`10-ai-orchestration/` is a textbook hybrid gateway: LiteLLM front door, local Ollama tiers
as the privacy-preserving default, Claude as failover/overflow, a LangGraph supervisor with
a deterministic privacy gate, and a graceful fallback ladder (light-local → rented-GPU →
cloud). The 2026 literature says this architecture cuts 60–80% of LLM cost for
*general assistant/RAG traffic* by keeping the ~70% of simple requests local. Good.

Two clarifications so we don't over-apply it:

- **This is for the homelab assistant/RAG, not for Claude Code.** Local 3B/7B CPU models on
  the t630 can't do agentic multi-file coding — that's Opus/Sonnet's job, direct to the API.
  Keep the split: router for chat/RAG/classification; Claude Code direct for dev.
- **The privacy gate is the real win, not the cost.** Sensitive lookups never leave the
  walls. That's worth more than the token savings and is the reason to keep pushing local
  as the default for anything touching customer data (which the `customers` repo mandates
  anyway).

Where the router can save *real* Claude spend: route the cheap, non-sensitive, high-volume
tasks (summaries, tag extraction, first-draft classification for the CRM/demand-gen stages)
to `local-fast`/`local-smart` before they ever hit `cloud-overflow`. That's exactly the
60–70%-simple-requests bucket the hybrid guides target.

Sources: [Hybrid cloud-local LLM architecture (Sitepoint, 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
[Hybrid AI cost optimization (BuildMVPfast, 2026)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026) ·
[What is LiteLLM (2026)](https://a2a-mcp.org/blog/what-is-litellm)

---

## E. On the *prompt that requested this* (the meta-ask)

The requesting prompt was, honestly, well-shaped for an open-ended research task — it gave
direction ("token use, prompting, hybrid local/Claude, keep up to date, check news") and
license to range. That's better than a vague "make the AI cheaper." Two refinements would
make future versions of it cheaper *and* sharper:

- **"ANYTHING that could help" is expensive.** An unbounded scope makes the model survey
  broadly rather than dig deep. If the goal is action, name the constraint: *"the 3 changes
  that would cut the most token spend this month, with rough $ impact."* Narrower prompts
  produce more decisive answers and burn fewer tokens getting there.
- **Give it the numbers to reason over.** The single highest-value thing we could hand a
  future review is a real usage/cost export (Anthropic Console → usage, or the router's
  cost logs). Right now this review reasons from public benchmarks and our configs; with
  actual spend-by-model data it could rank fixes by dollars, not by heuristic.
- **This is a good routine to keep, run monthly, and diff.** The field moves fast (model
  lineup, pricing, caching behavior all shifted in 2026). A standing monthly "efficiency &
  news" routine that re-checks pricing and compares to last month's numbers is the right
  cadence — more often than that is noise.

---

## Recommended next actions (ranked)

1. Trim `CLAUDE.md` files toward lookup-table density; push narrative into `*-context.md`. (caching + every-session savings)
2. Point Claude Code subagents / search agents at Haiku 4.5. (5× cheaper on the biggest-volume work)
3. Move the daily review sweep's find/mechanical stages off Opus; keep Opus for verify/synthesis; run it via the Batch API. (50% + tiering)
4. Route non-sensitive, high-volume CRM/demand-gen text tasks through the local LiteLLM tiers before cloud. (uses infra we already own)
5. Pull a real cost-by-model export before the next review so fixes can be ranked in dollars.
6. Housekeeping: bump `cloud-code` in the router config from `sonnet-4-6` → `sonnet-5`.

*No files were changed by this review. Model IDs and pricing verified current as of
2026-07-02.*
