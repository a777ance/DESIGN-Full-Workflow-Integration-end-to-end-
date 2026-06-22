# AI process efficiency — token & workflow audit

**Author:** NARF (AI CTO) · **Date:** 2026-06-22 · **Status:** advisory

Audit of how we spend Claude tokens and how the human↔AI loop is run, with the cheapest
wins first. Grounding facts: Anthropic API line is **~$5–15/mo** against a **<$30/mo** burn
target ([`ai-cfo/budget.md`](../ai-cfo/budget.md)); we already run a hybrid LiteLLM router
(local Ollama tiers on the t630 + Claude cloud overflow,
[`localDNS/10-ai-orchestration/config.yaml`]). So the lever is **not** "build a router" —
that's done — it's **tuning what we already have** and not paying frontier prices for
routine work.

Model prices used below (per 1M tokens, in/out): Opus 4.8 **$5 / $25**, Sonnet 4.6
**$3 / $15**, Haiku 4.5 **$1 / $5**. Cache read ≈ **0.1×** input; cache write ≈ 1.25×
(5-min) / 2× (1-hour). Batch API = **50% off** input *and* output, and **stacks** with
caching.

---

## The five wins, ranked by effort-to-payoff

### 1. Stop paying Opus prices for routine prose (router retune) — biggest, easiest win
`config.yaml` points **three** cloud tiers at Opus 4.8 — `cloud-overflow`, `cloud-explore`,
`cloud-vision` — and only `cloud-code` at Sonnet. Most of what overflows from the local
tiers is *not* frontier-reasoning: statement copy, FAQ answers, "Handled For You" log
phrasing, summarization, classification. Those run fine on **Haiku 4.5** (1/5th the input
cost of Opus, 1/5th output) or **Sonnet** (3/5ths).

- Add a `cloud-overflow-cheap` tier on `anthropic/claude-haiku-4-5` and make it the default
  failover for `local-fast`/`local-smart` (today they spill straight to Opus).
- Reserve Opus 4.8 for `cloud-explore` and genuinely hard reasoning only.
- Net: the overflow path — the one that actually bills — drops ~80% on input where it
  lands on Haiku instead of Opus, with no quality loss on dull tasks. **The network is
  meant to be dull; the model serving it can be too.**

### 2. Statement generation (Stage 06) → Batch API + prompt caching
The monthly statement job is the textbook batch-and-cache workload: many households, **not**
latency-sensitive, and every render shares a large **stable prefix** (template + system
instructions + honesty rules) with only a small **variable suffix** (one home's data file).

- **Prompt-cache the prefix:** put the template/instructions first with a `cache_control`
  breakpoint, per-home data last. Repeated renders read the prefix at ~0.1× → up to 90% off
  the shared portion.
- **Run the month's homes through the Batch API:** 50% off in *and* out, stacks with the
  cache. Most batches finish within the hour — fine for a monthly job.
- Together these take the "~a penny a home" claim and make it hold at scale instead of
  drifting up. (Stacking caching + batch is the single highest-leverage change once we have
  more than a handful of households.)

### 3. Trim the CLAUDE.md files (they're re-read every session)
`localDNS/CLAUDE.md` and this repo's `CLAUDE.md` are large, and **every** Claude Code
session (every NARF/ZORT run, every routine like this one) loads them into context. Claude
Code prompt-caches them, so the cost is ~0.1× — but a cache *read* is not free, and the
bytes still occupy the working window on every turn, crowding out room to think.

- Keep CLAUDE.md to the briefing + pointers; push the long reference tables (deploy-path
  maps, exhaustive known-issues) into README/INSTALL-NOTES and link them. The session reads
  the link only when it needs it.
- This also helps quality: a leaner system context is a sharper one.

### 4. Tighten the session-start ritual
NARF reads 4 files at start (`portfolio`, `roadmap`, `tech-debt`, `decisions`) and ZORT
reads 6. That's the right discipline, but it's ~10 file reads before any work begins on a
dual-hat session. Consider one condensed `state.md` per hat that the end-of-session update
maintains, with the detailed logs linked for when they're actually needed. Same continuity,
fewer tokens per warm-up.

### 5. Effort & one-shot discipline (free)
- **Don't default to `xhigh`/`max` effort** for doc edits and routine ops — `high` or
  `medium` is the sweet spot. Opus 4.8 rewards *the full task spec up front in one turn*
  over many interactive turns, so a well-specified single prompt beats a drawn-out
  back-and-forth on both cost and quality.
- **Scheduled routines (like this run) are the efficient pattern** for recurring watch work
  (news, CI, PR babysitting) — no human round-trips, runs while you're away. Keep using
  them; that's already right.
- **`count_tokens`** before a large send instead of eyeballing it; never estimate with a
  non-Claude tokenizer (off by 15–20%+).

---

## What we're already doing right (don't "fix" these)
- **Local-first routing** — Ollama `local-fast`/`local-smart`/`local-reason` carry the
  default load on the t630; cloud is overflow, not primary. This is the 10× lever, and it's
  in place.
- **Local embeddings** — `local-embed` (nomic) keeps RAG indexing inside the walls; no
  per-token cloud embedding bill, and no private lookups leaving.
- **Privacy gate** — sensitive tasks pinned local before planning. (One open hole tracked
  separately: see TD-14 — `local-reason`'s failover can reach cloud.)

---

## On the prompt that requested this audit
Asked to flag it if inefficient — it was, mildly, and the fix generalizes.

**Strengths:** clear intent, explicit permission to search the web / use other AI, and the
"keep up to date" framing pointed me at current sources rather than stale memory.

**Inefficiency:** "Locate inefficiencies… Anything you could possibly think of… ANYTHING
that could help" has no scope, no budget anchor, no target metric, and no deliverable
format — which maximizes *my own* exploration cost (the irony of an open-ended prompt asking
how to spend fewer tokens). A tighter version would have cut this run's cost by more than
half:

> "Audit our Claude spend. We run NARF/ZORT via Claude Code + a LiteLLM router; budget is
> <$30/mo. Give the top 3 token-reduction wins ranked by $ saved, write them to
> `docs/ai-cto/`, and skip generic LLM advice we already follow."

The pattern: **goal + constraint + deliverable + "skip what I already know."** That last
clause is the cheapest token-saver of all — it stops the agent re-deriving things you've
settled.

---

## Sources
- [Anthropic — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [Claude API cost optimization: caching, batching, 60% token reduction](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
