# NARF — special review — 2026-06-22 — process & token efficiency

CEO asked the open question directly: *find the inefficiencies in our PROCESS — between the user and
the AI. Is there a better way to cut token use? Better prompting? Leverage other AI? Run a hybrid
local LLM + Claude API? Keep it current, check the news. And critique the prompt that asked this.*

This is a CTO/CFO-shared review: token spend is a cost line (ZORT), the routing is architecture (NARF).
Best-practice claims below are dated **2026-06-22** and sourced at the bottom — this space moves weekly,
so treat the dated facts as perishable.

**Headline:** the biggest wins are not "shorter prompts." They are (1) prompt caching, which we are not
using and which is a 90% discount on repeated context, (2) the Batch API for anything not interactive
(50% off, stackable with caching), and (3) closing the one gap that makes our *existing* hybrid
local/cloud routing trustworthy (TD-14). The prompt that asked this is itself a good worked example of
the main inefficiency — it is unscoped, so it spends a frontier model's full effort on "anything you can
think of." More on that at the end.

---

## 0. What we already have (don't rebuild it)

We are further along than the question implies. `localDNS/10-ai-orchestration/` already runs the hybrid:
LiteLLM gateway (port 4040) → Ollama local models on the t630 → Claude API as the cloud tier, with a
reasoning ladder (`local-reason` cool, `cloud-gpu-reason` heavy, `cloud-overflow` = Claude). The Odin/
LangGraph supervisor adds a deterministic privacy gate. **The architecture the news articles describe as
the 2026 best practice is the one we already built.** So this review is about *using it well*, not
standing it up.

---

## 1. Token reduction — ranked by payoff, tied to our stack

**1. Prompt caching — the single biggest miss. ~90% off repeated input.**
Claude cache reads cost **0.1×** base input; writes cost 1.25× (5-min) or 2× (1-hour). Break-even is one
re-read on the 5-min cache. Every session here re-sends the same large stable prefix — the per-repo
`CLAUDE.md` files, the house-style block, the schema, the AI-CTO/CFO context docs. That is thousands of
identical tokens at full price on every turn. Mark the stable prefix (`tools` → `system` → frozen
context) with `cache_control: {type: "ephemeral"}` and put volatile content (the actual question, the
date) *after* the last breakpoint. Watch out: any byte change in the prefix invalidates everything after
it — so a `Current date: 2026-06-22T...` line in a system prompt silently kills the cache every request.
Min cacheable prefix is 4096 tokens on Opus 4.8, 2048 on Sonnet 4.6 — our CLAUDE.md files clear that
easily. *Effort: config-level on the LiteLLM/router side; no t630 trip.*

**2. Batch API — 50% off, stackable with caching, for everything non-interactive.**
The monthly Statement run (Stage 06), bulk roster operations (Stage 08), any "generate N things
overnight" job: these are not latency-sensitive. The Batch API processes async (most < 1h, max 24h) at
**50% off input and output**, and the discount **stacks** with prompt caching. A statement-generation
pass over a book of homes is the textbook batch workload. *Effort: code change at the generation/job
layer.*

**3. Model ladder discipline — match the model to the task, don't default to the ceiling.**
Per-1M pricing: Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5. Industry split is ~60–70% simple
/ 20–30% moderate / ~10% frontier-grade. We already have the ladder in `config.yaml`; the discipline is
sending classification/extraction/short-summarize work to **local Ollama or Haiku**, routine drafting to
**Sonnet**, and reserving **Opus** for genuine reasoning. The `effort` parameter (`low`→`max`) is the
other dial: lower effort = fewer tool calls, less preamble, fewer tokens. Default to `high`, drop to
`medium`/`low` for scoped work, reserve `xhigh`/`max` for hard problems.

**4. Context engineering > prompt shortening.** The 2026 consensus: token cost is driven by *bloated
context, idle tool schemas, and stale history* — not prose length. Concretely for us: keep each
`CLAUDE.md` lean (the guidance benchmark is trimming agent context files toward ~500 tokens of
load-bearing content), load data dynamically by reference (file paths, not pasted file bodies), and
filter tool output before it re-enters context. Benchmarks cite 77–91% cost reduction from this class of
change alone.

**5. Memory + compaction for long/repeat sessions.** For agents that work across sessions, server-side
memory replaces tens of thousands of replayed-history tokens with a compact memory load — cited as the
single highest-impact optimization for multi-session agents. For one long session, server-side
compaction summarizes earlier context automatically as it approaches the window. Relevant if/when we run
standing agents over the roster rather than one-shot prompts.

---

## 2. Process inefficiencies — between the user and the AI

- **Unscoped, open-ended asks burn frontier effort.** "Anything you could possibly think of" forces a
  max-effort model to enumerate exhaustively. Scoped asks ("review TD-14 and propose the fix") get a
  cheaper, faster, better answer. This is the dominant user-side cost lever, and it's free.
- **Re-establishing context every session is the recurring tax.** Six repos, each with a long CLAUDE.md
  and AI-CTO/CFO state docs that get re-read at session start. Prompt caching (above) is the technical
  fix; the process fix is a tight "session-start" digest rather than re-reading everything.
- **Wrong tier for the job.** Routing a 3-line classification to Opus is pure waste when local Ollama or
  Haiku clears it. The ladder exists — the habit needs to match it.
- **No measurement loop.** We can't optimize what we don't see. `response.usage` already reports
  `cache_read_input_tokens` / `cache_creation_input_tokens` / `input_tokens`; LiteLLM logs per-model
  spend. Nobody is reading either. Recommend a weekly ZORT line: tokens + $ by model, cache-hit rate.
  If `cache_read_input_tokens` is 0 across repeated runs, a silent cache invalidator is live.

---

## 3. Leverage other AI / hybrid — current state and the one fix

The hybrid is built. The thing standing between us and trusting it is **TD-14** (already P1 in
tech-debt): `local-reason` has a cloud fallback chain, so a `sensitive`-tagged prompt can fail *open* to
Claude cloud if the local box is down — the opposite of what the config comments claim. Until that fails
*closed* (local-only fallback), the privacy guarantee is asserted but not enforced, and "leverage local
AI for sensitive work" is not actually true. **Fixing TD-14 is the prerequisite to honestly claiming the
hybrid saves both money and privacy.** One-line edit, no t630 trip.

Beyond that: route by data sensitivity *and* complexity (we have both axes), use local for the 60–70%
simple slice, and keep Claude for reasoning and final-quality work. That is the documented 2026 pattern
(LiteLLM gateway + Ollama + Claude tier) and matches our `config.yaml` intent.

---

## 4. The prompt that asked this — critique (CEO requested)

It is warm and clear about *intent*, but inefficient by its own standard:

- **Unscoped.** "ANYTHING that could help… Anything you could possibly think of" has no boundary, so a
  frontier model spends maximum effort fanning out. A scoped version gets a better answer for a fraction
  of the tokens.
- **Stacked sub-questions in one breath** (token use + prompting + other AI + hybrid + news + self-
  critique). Each is answerable; together they invite a sprawling response. Fine for a kickoff like
  this; for routine work, one question per turn is cheaper and sharper.
- **"Search the web… keep UP TO DATE… check the news"** is the right instinct and worth keeping — this
  space does move weekly. But pair it with a scope so the search is targeted, not open.

**Tighter rewrite, same intent:**
> "Audit our AI token spend. Cover: (1) prompt caching on our CLAUDE.md prefixes, (2) Batch API for the
> Statement run, (3) model-ladder discipline across the LiteLLM router. For each, give the expected %
> saving and the effort to implement. Check for any 2026 best practice we're missing. One paragraph each."

That version is scoped, ordered, bounded in output, and still invites the news check — and it would cost
a fraction of what the original did to answer well.

---

## Top 3 actionable now

1. **Turn on prompt caching for the stable prefix** (CLAUDE.md + house-style + context docs) at the
   router/API layer, and move the date/volatile content after the breakpoint. ~90% off repeated input.
   No box access. **Do this first.**
2. **Move the monthly Statement run and any bulk roster job onto the Batch API.** 50% off, stacks with
   caching. Code change at the generation layer.
3. **Close TD-14 (fail closed) so the hybrid's privacy claim is real** — already the standing P1 one-line
   fix; it's also what makes "leverage local AI" honest.

And one process habit, free: **scope the ask, pick the tier, read the usage numbers.**

---

## Sources (2026-06-22)

- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Cost Optimization 2026: Batch API (50% Off) and Prompt Caching (90% Off)](https://pecollective.com/tools/claude-pricing-guide/)
- [Claude API Cost Optimization: Caching, Batching, and 60% Token Reduction in Production (DEV)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM: Cut API Costs by 60% with Smart Routing — Markaicode](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [LLM Token Optimization Strategies: The Complete Guide for 2026 — Token Optimize](https://www.tokenoptimize.dev/guides/llm-token-optimization-strategies)
- [Context Engineering vs Prompt Engineering for AI Agents — Firecrawl](https://www.firecrawl.dev/blog/context-engineering)
