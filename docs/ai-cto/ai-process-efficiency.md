# AI Process Efficiency — user↔AI cost & workflow review

A review of how we spend tokens and AI effort across the guild's repos, and where the
process between a human operator and the AI (Claude API, the local LLM router, the
scheduled NARF/ZORT runs) can be made cheaper or more reliable. Findings are ranked by
leverage, newest analysis at the top per house style.

**Authoritative-facts note:** model pricing, prompt-caching, Batch API, and context-editing
behavior below are taken from the Claude API reference (as of 2026-06), not from open-web
summaries — several public "2026 cost-cutting" posts are out of date (one widely-cited
piece claims Anthropic has no Batch API; it has had a GA 50%-discount one for over a year).

---

## Verdict

The architecture is already good. We run a LiteLLM gateway with a reasoning ladder
(`local-reason` on the t630 → `cloud-gpu-reason` on a rented GPU → `cloud-overflow` to
Claude), an Odin/LangGraph supervisor, and the budget already prices the Haiku-vs-Opus
split (`~$0.01/run Haiku; $0.10–0.50/run Opus`). We are not the team that needs to be told
"use a smaller model." The waste is in **two specific places**: the *cadence and scope* of
open-ended recurring AI runs, and a **known-open routing bug (TD-14)** that makes the hybrid
setup unsafe to lean on. Everything else is incremental tuning.

---

## 2026-06-19 — review findings

### F-1 (highest leverage) — This kind of routine is the inefficiency

The run that produced this document was triggered by a broad, open-ended prompt
("locate inefficiencies… anything that could help… keep up to date, check the news day by
day"). Run on a schedule, that prompt is expensive in exactly the way it's asking to avoid:

- **No delta.** Each run re-derives the same standing advice and re-searches the same
  topics. "Day by day" web monitoring of LLM best practices produces a near-identical
  answer most days — the signal-to-token ratio collapses after the first run.
- **Two cadences fused into one.** "Analyse our process" is a **one-time** task. "Tell me
  when something materially changes" is a **recurring** task that should be a *narrow delta
  check*, not a fresh open-ended research sweep.
- **Opus-tier model on an open mandate.** An unbounded "think of anything" prompt invites
  maximum exploration (and maximum output tokens) every run, on the most expensive tier,
  for a session nobody is watching live.

**Fix — split it:**

1. Keep *this* deep analysis as a **one-off** (this document is its output). Don't schedule it.
2. If we want ongoing awareness, run a **cheap, narrow weekly delta** instead of a daily
   open sweep: pin it to 2–3 named sources (Anthropic release notes, the model/pricing page,
   one routing/gateway changelog), and make it *notify-only-on-change*. That job is a
   Haiku-tier or `local-reason` task, not Opus.
3. Give every scheduled routine an explicit **stop/notify threshold** so it stays silent when
   nothing changed. A routine that pings on every run trains us to ignore it.

**Suggested rewrite of the recurring prompt:**

> "Check the Anthropic model/pricing page, Anthropic release notes, and the LiteLLM
> changelog for changes since the date in `docs/ai-cto/ai-process-efficiency.md`. If a
> change affects our model choice, pricing, caching, Batch API, or routing, summarise it in
> two sentences and update the dated section. If nothing material changed, do nothing and
> send no notification."

That is bounded, dated, delta-only, and cheap.

### F-2 — The hybrid setup has an open privacy hole (TD-14) — fix before leaning on it

The user explicitly asked about "running a hybrid, local LLM and Claude API." We already do
— but **TD-14** (P1, open since 2026-06-07) means a `sensitive`-tagged task routed to
`local-reason` can fail over to `cloud-overflow` (Claude cloud) when the local model is down,
because the dispatcher's `allow_cloud=False` isn't enforced at the LiteLLM failover layer.
Until that's fixed, the hybrid split gives a cost benefit but **not** the privacy guarantee
that is the whole point of keeping sensitive lookups local. Fix: give `local-reason` a
**local-only fallback chain** (fail closed) in `10-ai-orchestration/config.yaml`. This is the
single most important hybrid-routing change and it's already on the books — it just needs to
land.

### F-3 — Token levers, grounded in our stack (in priority order)

1. **Keep the CLAUDE.md prefix cache-stable.** Claude Code web sessions load every in-scope
   repo's `CLAUDE.md` as a fixed prefix on every turn; prompt caching makes that nearly free
   *within* a session (cache reads ≈ 0.1× input price) **only if the prefix is byte-stable**.
   Never interpolate `today's date`, a session id, or anything per-run into a `CLAUDE.md` or
   system prompt — one changed byte invalidates the whole cached prefix. Our `CLAUDE.md`
   files are large; that's fine for caching, but it means the *first* turn of every session
   pays full price for all of them. Two cheap wins: (a) scope each session to the repos it
   actually needs rather than loading all seven, and (b) keep the house-style/boilerplate
   blocks identical across repos so they cache as one prefix.

2. **Tier the model to the task — we already price this, now enforce it.** Field extraction
   for the CRM (08), lead classification (02→03), "Handled For You" log tidying, and routing
   decisions are **Haiku 4.5** ($1/$5) or `local-reason` work, not Opus ($5/$25). Reserve
   Opus/Claude Code for genuine multi-file reasoning (this kind of cross-repo review, stage-11
   automation design). Use the `effort` parameter: `low` for the cheap subtasks, `high` only
   where correctness matters.

3. **Batch the statement run.** The statement generator is described as "≈ a penny a home"
   and runs monthly across the whole book — a textbook **Batch API** fit: 50% off all tokens,
   async, completes well within its 24h window. Any non-interactive bulk generation (monthly
   statements, backfilling sidecar copy, bulk classification) should go through Batches, not
   live calls. This roughly halves the per-statement model cost at scale.

4. **Context editing / compaction for long agent runs.** When a Claude Code or Managed-Agent
   run goes long (stage-11 automation work, big doc passes), enable context editing
   (`clear_tool_uses`) so stale tool output is pruned rather than re-sent every turn. This is
   the lever that keeps long autonomous runs from ballooning input tokens.

### F-4 — Route the *right* class of work local vs. cloud

The reasoning ladder exists; the discipline is matching work to rung:

| Work | Rung | Why |
| ---- | ---- | --- |
| CRM field extraction, lead/label classification, log cleanup, the weekly delta check (F-1) | `local-reason` / Haiku | High volume, low sensitivity, cheap; keep it off Opus |
| Sensitive household data, anything personal | `local-reason`, **fail-closed** | Privacy is the point — blocked by F-2/TD-14 until the fallback is fixed |
| Heavy multi-step reasoning, cross-repo design, code review | `cloud-gpu-reason` or Claude (Opus/Sonnet) | Worth the spend; rare |
| Monthly statement generation (bulk) | Claude **Batch API** | 50% off, async, not latency-sensitive |

---

## What actually changes day-to-day (so we don't over-monitor)

Most days: nothing that affects us. The things worth a *weekly* glance, not a daily one:
new model tiers or price changes on the Anthropic pricing page; LiteLLM/gateway routing
features; Batch/caching/context-editing changes. Pin the delta check to those and stay
silent otherwise (see F-1).

---

## Sources

Open-web context (treat as secondary to the Claude API reference):

- [Cutting LLM Inference Costs in 2026 — caching, batching, routing (GMI Cloud)](https://www.gmicloud.ai/en/blog/llm-inference-cost-optimization-caching-batching-routing)
- [LLM Cost Optimization: 5 levers (Morph)](https://www.morphllm.com/llm-cost-optimization)
- [Hybrid Cloud-Local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Model Routing in 2026 (Digital Applied)](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Token optimization 2026 (Obvious Works)](https://www.obviousworks.ch/en/token-optimization-saves-up-to-80-percent-llm-costs/)
