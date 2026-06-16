# NARF — process & token-efficiency review — 2026-06-16

**Question asked:** find inefficiencies in *our process* — the loop between the human and the
AI. Where can we cut token use? Better prompting? Hybrid local-LLM + Claude API? Anything.
Keep it current.

**Scope note:** this is a meta-review of *how we use AI*, not of the portfolio's content. It
was produced by a scheduled, unattended routine running on **Opus 4.8 (1M ctx)** — which is
itself one of the findings (see §4).

---

## TL;DR — the five moves, ranked by leverage

| # | Move | Effort | Payoff |
| - | ---- | ------ | ------ |
| 1 | **Turn on prompt caching** for the standing context (system prompt + CLAUDE.md + repo rules) | Low | ~90% off the input that repeats every turn — the single biggest win |
| 2 | **Cut CLAUDE.md bloat & de-duplicate the shared house-style block** | Low–Med | This run loaded ~all 7 repos' CLAUDE.md every turn; the house-style block is copy-pasted verbatim 7× |
| 3 | **Match the model to the job** — scheduled/monitoring routines on Haiku 4.5 or Sonnet 4.6, not Opus 4.8 | Low | Opus is ~the most expensive tier; most routine work doesn't need it |
| 4 | **Route Claude Code itself through the LiteLLM gateway** so the local tier + privacy gate we already built actually serve our day-to-day | Med | We have the hybrid; our coding sessions bypass it |
| 5 | **Batch the non-interactive work** (50% off) + scope prompts tighter | Low | Scheduled jobs are textbook Batch-API candidates |

Combining caching + model-matching + batching is documented at **60–95% cost reduction** with
no measurable quality loss. We are currently getting close to none of it on the Claude-Code /
API side.

---

## 1. The biggest leak is *standing context*, and we can see it in this very run

Claude Code re-sends the system prompt and all in-scope `CLAUDE.md` files **on every turn of
every session.** In this run the model received the **full CLAUDE.md of all seven repos** as
standing context — easily 15k–20k tokens before a single word of work. Two problems:

- **It repeats every turn, uncached.** Without prompt caching, we pay full input price for the
  same ~18k tokens on turn 1, turn 2, turn 20. With caching, the repeated prefix drops to ~10%
  of input cost (cache reads are 0.1× base; a 5-min write is 1.25×, 1-hour 2×). Rule of thumb:
  3+ reads inside the 5-min TTL, or 5+ inside the 1-hour TTL, and you're ahead. A long agent
  session clears that bar on the first few turns.
- **The shared "House style: ordering & typography" block is duplicated verbatim in all seven
  CLAUDE.md files.** Every session that touches more than one repo pays for that block N times.

**Actions**

- Verify caching is on: in Claude Code run `/doctor` / check `ENABLE_PROMPT_CACHING` (and the
  1-hour variant `ENABLE_PROMPT_CACHING_1H` for long sessions). On the API / LiteLLM path,
  add `cache_control` breakpoints to the stable prefix (system + tools + CLAUDE.md). LiteLLM
  supports Anthropic cache breakpoints — our `cloud-overflow`/`cloud-*` tiers currently set
  **none**, so we get zero cache benefit on the gateway path today.
- **Trim every CLAUDE.md to a lean core and link out.** The detail belongs in README /
  context.md (which only load when actually read), not in the always-resident brief. Target:
  the resident brief small enough to read in 20 seconds.
- **Factor the house-style block into one file** (e.g. `localDNS`-published or a shared
  `HOUSE-STYLE.md`) and have each CLAUDE.md *link* to it instead of inlining it. One source of
  truth — which is our own stated principle — applied to our own instructions.
- Use the diagnostics: `/context` to see what's actually loaded, `/clear` between unrelated
  tasks, `/recap` (Apr 2026) to resume without replaying the whole transcript.

## 2. Prompting: scope the delta, not the universe

The 2026 consensus for coding agents: **write the spec once, store repo rules once, package
repeated workflows once, let memory hold durable preferences — and spend the live prompt only
on the *delta*** (the specific step needed now). Open-ended prompts are the expensive kind: a
20-turn ramble can carry 5–10k tokens of context where 500–1k would do.

Concrete habits:

- Lead with keywords; ask for **extraction over generation** and structured output.
- Cap tool output (long test/CI logs drain tokens fast).
- Prefer several small scoped requests over one broad one — documented to cut a session to
  ~33% of an open-ended one.
- For data we feed the model (roster.json, stats JSON), **TOON format saves 30–60% vs JSON**
  with comparable comprehension. Relevant to stage 06/08 if we ever pass roster/stats inline.

## 3. We already have the hybrid — the gap is that we don't *use* it for our own work

Credit where due: `10-ai-orchestration` is genuinely good. LiteLLM gateway, local Ollama tiers
(`local-fast` qwen2.5:3b, `local-smart` 7b), a reasoning ladder that keeps heavy DeepSeek-R1
off the CPU, local embeddings for RAG, a deterministic privacy gate that pins sensitive tasks
local, and graceful local→cloud fallback. That is exactly the architecture the 2026 write-ups
recommend (60–88% savings on the simple-task majority; ~60–70% of requests are simple enough
for a local model).

**The gaps:**

- **Our actual Claude Code / API work doesn't flow through that gateway.** This routine went
  straight to Opus. The local tier and privacy gate protect the *Open WebUI / supervisor*
  path, not our coding sessions. Wherever feasible, point Claude-Code-style work at
  `ai.home.lan:4040` so cheap/sensitive turns can land local first.
- **No cache breakpoints on the cloud tiers** (see §1) — easy add to `config.yaml` callers.
- **RouteLLM note:** if we ever reach for a learned router, RouteLLM is effectively frozen
  (last real update Aug 2024; LMSYS moved on). Treat it as a stable tool, not an evolving one.
  Our deterministic gate + LiteLLM fallbacks are the better bet and we already have them.

## 4. This routine is over-modelled and could be batched

It ran on **Opus 4.8** — the top, most expensive tier — to do scheduled research + monitoring.
That's a mismatch:

- **Model-match:** routine monitoring/triage → Haiku 4.5; structured build/code → Sonnet 4.6;
  reserve Opus/Fable for the genuinely hard reasoning. Our own `config.yaml` already encodes
  this instinct (`cloud-code` = Sonnet) — extend it to the routines.
- **Batch API is 50% off** for non-real-time work. A scheduled, nobody-watching routine is the
  canonical batch candidate. Caching (90%) + batch (50%) stack to ~95% on suitable pipelines.
- Practical reference point from the field: one team went $2,400 → $680/mo (−72%) on caching +
  budgets + model-switching alone.

## 5. The prompt that triggered this run — honest critique

It asked, verbatim, for *"ANYTHING that could help"* and to *"Check the news."* That is the
**single most token-expensive prompt shape** there is: unbounded scope on the top model with no
stop condition, so the agent fans out maximally. It's a fine *kickoff* prompt for a one-time
audit (this one), but as a recurring routine it would re-pay full freight every run.

Better shape for the recurring version:

- **Pin the model:** run the routine on Haiku/Sonnet, escalate to Opus only on a flagged
  finding.
- **Bound it:** "Check these 3 sources for changes since last run; report only deltas." A diff
  against the prior review is far cheaper than re-deriving the field each time.
- **Make it incremental:** keep a small `process-efficiency/` state file; each run appends only
  what changed. (Newest-first, per house style.)
- **Separate research from action:** one cheap scheduled "scan & flag," then a human-triggered
  deep dive only when the scan surfaces something. Don't pay for a deep web sweep daily.

---

## Watch-list (this changes fast — re-check monthly, cheaply)

- Claude Code added **nested sub-agents**, smarter model/region handling, plugin search (Jun
  2026). Parallel specialist sub-agents on a shared filesystem can cut wall-clock and let each
  sub-agent carry a *smaller* context than one monolithic session.
- **Claude Platform on AWS** is GA (full feature set incl. caching, batch, Skills, MCP) — only
  relevant if we ever move billing to AWS.
- Prompt-compression (LLMLingua-2, 2–5× typical, up to 20×) is mature but **overkill for us
  right now** — caching + trimming CLAUDE.md gets the same money with none of the complexity.
  Park it until we have a high-volume RAG path that justifies it.

## Sources (2026)

- [Anthropic API pricing 2026 — caching, batch, optimization (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API cache pricing — 90% input savings (TokenMix)](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [Claude API cost optimization: caching, batching, 60% reduction (dev.to)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Claude Code token optimization — the $1,600 bill (buildtolaunch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 tips for Claude Code token saving (Analytics Vidhya)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [How to reduce Claude Code token usage — 8 methods (Agensi)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM model routing with Ollama + LiteLLM (Medium/Hannecke)](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
- [Token efficiency in AI coding agents (Medium/Sathyanarayana)](https://medium.com/@nprasads/token-efficiency-in-ai-coding-agents-12d4e3b00f00)
- [TOON vs JSON + LLMLingua-2 token savings (dev.to)](https://dev.to/sreeni5018/two-efficient-technologies-to-reduce-ai-token-costs-toon-and-microsofts-llmlingua-2-294e)
- [Anthropic updates — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic)
- [Anthropic launches Claude Platform on AWS (InfoQ)](https://www.infoq.com/news/2026/05/anthropic-claude-aws/)
