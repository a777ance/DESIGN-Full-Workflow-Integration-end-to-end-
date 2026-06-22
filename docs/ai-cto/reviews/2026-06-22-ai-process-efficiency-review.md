# AI process efficiency review — user ↔ AI workflow, token spend, hybrid routing

**Date:** 2026-06-22 · **Scope:** the *process* between the operator and the AI across the
seven A777ance repos — not the product. Asks answered: where we waste tokens, better
prompting, leveraging other/local AI, hybrid local+Claude, and a critique of the request
that triggered this review. Grounded in the live `localDNS/10-ai-orchestration/` router
and `ORCHESTRATION-BLUEPRINT.md`. Web-checked against current (Jun 2026) practice — sources
at the foot.

## TL;DR — ranked levers (impact × ease)

| # | Lever | Est. saving | Effort | Where |
| - | ----- | ----------- | ------ | ----- |
| 1 | **Prompt caching on the cloud tiers + trim CLAUDE.md prefixes** | 40–80% on repeated input | Low | LiteLLM callers, all CLAUDE.md |
| 2 | **Right-size the routing table (Haiku/local for the 60–70% simple work; Opus only for the ~10% that needs it)** | 50–90% per downshifted call | Low–med | `config.yaml`, dispatcher |
| 3 | **Batch API (50% off) for all non-interactive bulk work** | 50% on those jobs | Low | statements (06), CRM/lead classify (08), nightly jobs |
| 4 | **Context discipline in Claude Code sessions: manual compact at ~50%, subagents, `/clear` between tasks** | 55–65% per long session | Low | every Claude Code session |
| 5 | **Tighter prompts + per-run deliverable spec** (incl. this routine's prompt) | 20–40% on exploratory runs | Low | how we ask |
| 6 | **`effort` + adaptive thinking instead of always-full reasoning** | 10–40% on reasoning calls | Med | LiteLLM passthrough / Claude Code |

The architecture is already good: a deterministic gateway (LiteLLM) + capability routing +
"route, don't shard" + local-first privacy gate is exactly the 2026 consensus pattern for
cutting cost without quality loss. The wins below are tuning, not redesign.

---

## 1. Prompt caching is the single biggest lever — and we're probably leaving it on the table

Caching computed prefixes bills the static part at ~10% of input price; reported real-world
savings are **41–80%**, and one team went from a 7% to 84% cache-hit rate just by moving the
*volatile* content out of the system prompt to the end of the message. The rule is mechanical:
**stable bytes first, volatile bytes last; any byte change in the prefix invalidates everything
after it.**

Two concrete actions for us:

- **Cloud tiers via LiteLLM don't cache automatically.** Anthropic prompt caching only fires
  when the caller marks a `cache_control` breakpoint. Our `dispatcher.py` / Odin supervisor
  should put the breakpoint on the last block of the *stable* prefix (rule context, system
  prompt, repo facts), with the per-request question after it. Verify with
  `usage.cache_read_input_tokens` — if it's zero across repeated calls, a silent invalidator
  (a `datetime.now()`, an unsorted JSON dump, a varying tool list) is in the prefix.
- **The CLAUDE.md files are large and are read on every Claude Code session.** They sit in the
  cached prefix, so caching softens the cost — but they're still re-read and they crowd the
  window. Trim each CLAUDE.md to the essential briefing and push detail into the linked files
  Claude opens on demand (README, network-context, blueprints). This repo's CLAUDE.md and
  localDNS's are the two heaviest; they're the best trim candidates. Keep the founder's
  standing instructions and the invariants; move the long tables/rationale behind links.

## 2. Right-size the routing table

The blueprint already says this; the live `config.yaml` doesn't fully reflect it yet:

- `cloud-overflow` is pinned to **`claude-opus-4-8`** ($5/$25). That means *every* local-tier
  failover lands on the most expensive model. For the `local-fast` spill specifically, a
  cheaper overflow (`claude-haiku-4-5`, $1/$5, or `claude-sonnet-4-6`, $3/$15) is the right
  catch — a snappy 3B-class query that spilled to cloud does not need Opus.
- Task distribution in production LLM apps is ~60–70% simple (classify / extract / format),
  ~20–30% moderate, ~10% genuinely needs frontier reasoning. Our dispatcher rule table should
  mirror that: simple → `local-*` or Haiku, moderate → Sonnet 4.6, hard → Opus 4.8. `cloud-code`
  is already correctly Sonnet 4.6 — good. `cloud-vision` is Opus; Sonnet 4.6 also has vision and
  is half the price for routine screenshot reads — reserve Opus-vision for dense/degraded images.
- Keep the deterministic, no-LLM-in-the-routing-decision rule (ADR stands — it's free,
  debuggable, and keeps the privacy gate hard). The right-sizing is just editing the rule
  table's targets, not adding a model to the decision.

## 3. Batch API — 50% off for everything that isn't interactive

Anything not waiting on a human can go through Message Batches at **half price**, same models,
full feature support (caching, tools, vision), usually back within the hour:

- **Statement generation (stage 06)** — the monthly run at "a penny a home" is the textbook
  batch workload. Halve it.
- **Lead / CRM classification and enrichment (stage 08)**, demand-gen copy variants (02),
  any nightly summarization — all batchable.
- Keep interactive chat (Open WebUI) and the live dispatcher on the synchronous path.

## 4. Context discipline in Claude Code sessions

The biggest controllable spend in day-to-day Claude Code use is context compounding:

- **Compact manually at ~40–60% context**, not at the auto-trigger (~93%). A directed early
  compact is smaller, cheaper, and keeps the cache warm.
- **Use subagents for heavy context** (the Explore pattern / Odin's host already embodies this):
  fan the large reads out to a fresh-context subagent, keep the main session for direction and
  review. Reported 55–65% token reduction on long tasks.
- **`/clear` between unrelated tasks** so a finished task's transcript doesn't ride along.
- These are exactly what this very routine should do: load only the skills a run needs (this
  session pulled a very large API skill into context — fine here, wasteful if it happened every
  run).

## 5. Better prompting — including the prompt that triggered this review

The request that launched this run is a good example of an *expensive* prompt shape:
open-ended ("ANYTHING that could help"), two distinct asks bundled (optimize the process **and**
critique the prompt), an unbounded research instruction ("keep UP TO DATE… check the news"),
and no deliverable spec. That invites maximal exploration and maximal tokens. It worked, but it
would be cheaper and sharper as:

- **One ask per run.** Split "optimize our process" and "critique my prompt" into separate runs.
- **State the deliverable and a budget.** e.g. *"Return the top 5 token-saving levers as a ranked
  table with impact/effort; ≤1 page; cite sources."* A format cap is the simplest token control.
- **Front-load the context.** Name the repos, the router, and the workloads in the prompt so the
  AI doesn't spend a research budget rediscovering its own setup (this run spent several tool
  calls re-deriving the stack from the repos).
- **Scope the research.** "Search the web if helpful / keep up to date" is unbounded. Better:
  *"Check [these 2–3 sources] for changes since 2026-06-22; flag only material deltas."*
- **For the recurring "keep up to date" intent**, this is precisely what a tight scheduled
  routine is for: a narrow prompt, a fixed source list, and **notify only on change** — not an
  open standing instruction to stay current.

General prompting hygiene that saves retries: ask for **structured output** when you'll parse
the result (guarantees valid shape, no re-asks), and prefer `effort: low/medium` for routine work.

## 6. Model landscape is current — adopt the new cost knobs

Our IDs are right (`claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`; Opus 4.8 is the
current Opus, Sonnet 4.6 the speed/intelligence pick, Haiku 4.5 the cheap tier). What's worth
adopting:

- **Adaptive thinking + the `effort` parameter** replaced fixed `budget_tokens` (which now
  400s on 4.7/4.8). `effort: low|medium|high` is the cost dial — `medium` is the usual sweet
  spot; reserve `high`/`max` for the hardest. Pass it through LiteLLM where the backend supports it.
- **Server-side compaction / context editing** exist now for long agent runs if Odin ever holds
  a long session.
- **RAG is already right** — `local-embed` (nomic-embed-text) + `rag.py` keeps the repo embedded
  locally so we retrieve chunks instead of stuffing whole docs into context. Keep leaning on it.

---

## What NOT to change

- The deterministic, local-first privacy gate. It's correct and it's the moat-aligned choice.
- "Route, don't shard." Whole models behind one front door; heal on node loss.
- Pushing heavy reasoning off the laptop/t630 CPU to the rented GPU. Thermal + cost both right.

## Suggested next actions (small, independent)

1. Add `cache_control` breakpoints in `dispatcher.py` / supervisor calls; verify cache reads.
2. Edit `config.yaml`: cheaper overflow for `local-fast`; consider Sonnet-vision for routine images.
3. Move stage-06 statement generation and stage-08 bulk classification onto the Batch API.
4. Trim `CLAUDE.md` prefixes (this repo + localDNS first); detail behind links.
5. Adopt a prompt template for routines: one ask, a deliverable spec, a scoped source list,
   "notify only on change."

---

## Sources (Jun 2026)

- [Prompt Caching in 2026: Cut LLM Costs, Keep Quality — digitalapplied](https://www.digitalapplied.com/blog/prompt-caching-2026-cut-llm-costs-engineering-guide)
- [Token optimization 2026: saving up to 80% LLM costs — Obvious Works](https://www.obviousworks.ch/en/token-optimization-saves-up-to-80-percent-llm-costs/)
- [Don't Break the Cache: Prompt Caching for Long-Horizon Agentic Tasks (arXiv 2601.06007)](https://arxiv.org/abs/2601.06007)
- [AI Agent Token Cost Optimization — Fastio](https://fast.io/resources/ai-agent-token-cost-optimization/)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid LLM Routing: Ollama + Claude API Without Quality Degradation — DEV](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [LLM Gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Reduce Claude Code Costs 60% — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- Anthropic API facts (model IDs/pricing, prompt caching, Batch API 50%, adaptive thinking/`effort`) per the bundled `claude-api` reference, cached 2026-06-04.
