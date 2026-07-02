# NARF — AI process-efficiency review — 2026-07-02

**Question from the CEO:** where are the inefficiencies in *our process — between the human and
the AI* — and how do we cut token spend, prompt better, lean on other/local AI, and stay current?

This is a **meta** review: not the portfolio, but the way we *work with* Claude and the local
stack. Everything below is dated mid-2026 and will drift — see [§10 Keeping current](#10-keeping-current-this-page-goes-stale-fast).
Web sources are listed in [§11](#11-sources).

---

## 0. TL;DR — ranked by return on effort

| # | Move | Effort | Payoff | Where |
| - | ---- | ------ | ------ | ----- |
| 1 | **Fix the cloud-overflow tier: Opus → Haiku/Sonnet.** We fail over to the *most expensive* model. | 1 line | Overflow calls ~5–10× cheaper | `localDNS/10-ai-orchestration/config.yaml` |
| 2 | **Trim & de-duplicate the CLAUDE.md files.** They're resident in context every turn. | ~1 hr | 30–50% off the fixed per-turn tax | all repos |
| 3 | **Prompt-cache our own Claude API paths** (statement build, LangGraph supervisor). Claude Code already caches; our scripts likely don't. | ~1 hr | 60–90% off input tokens on repeated calls | `customers` Makefile, `langgraph-router/` |
| 4 | **Route by task, not just by failure.** Today cloud is failover-only; add a cheap complexity/sensitivity gate so the *right* work goes local vs. cloud. | ~½ day | Better quality-per-dollar; also closes TD-14 | `langgraph-router/` |
| 5 | **Adopt the 2026 context tools** — `/clear` discipline, `/compact` with custom instructions, subagents for exploration, and the memory tool. | habit | 30–84% fewer tokens on long sessions | Claude Code workflow |
| 6 | **Scope this routine's context.** A recurring routine that loads all 7 repos pays that load every run. | config | Linear savings per run | scheduled routines |

The prompt that triggered this review is itself an example of the #1 prompting inefficiency — see
[§9](#9-critique-of-the-prompt-that-asked-for-this).

---

## 1. The fixed per-turn tax: CLAUDE.md bloat (biggest silent cost)

Every Claude Code turn re-sends the repo's `CLAUDE.md` — it's resident context, not a one-time
read. Current sizes:

| Repo | Words | ≈ Tokens (resident **every turn**) |
| ---- | ----- | ---- |
| localDNS | 2,728 | ~3,600 |
| DESIGN (this repo) | 2,608 | ~3,500 |
| MARKETING | 1,445 | ~1,900 |
| claude-code-homelab | 371 | ~500 |
| customers | 562 | ~750 |
| azure-lab | 316 | ~420 |

In a **single-repo** session that's a 3–4k-token tax on *every* message. In a **multi-repo**
routine (like the one that generated this file), all of them load — ~10k tokens before we do any
work, and the identical **~350-word "House style" block is duplicated in all six** files.

**Fixes, cheapest first:**
- **De-duplicate house style.** Keep the canonical block in *one* place (this repo's CLAUDE.md or
  a `docs/house-style.md`) and have the other repos carry a two-line pointer, not the whole block.
  Claude follows a linked file when it needs the detail. Saves ~300 words × 5 repos of pure
  repetition.
- **Push detail down to README, keep CLAUDE.md as an index.** CLAUDE.md should be the map
  ("what/where/the 3 rules"), not the territory. The long deploy-path table and the full
  known-issues list in `localDNS/CLAUDE.md` belong in README/INSTALL-NOTES; CLAUDE.md links to
  them. Target: **< 1,200 words** for the big two.
- Anthropic's own guidance (Sept 2026, "Effective context engineering") is *right-altitude* system
  prompts — the smallest set of high-signal tokens, not exhaustive rules. Our CLAUDE.md files have
  drifted long.

## 2. Model selection — we fail over to the most expensive brain

`config.yaml` sets **every** cloud tier and the overflow target to `anthropic/claude-opus-4-8`
(the top of the price sheet). Overflow should be the *cheap* safety net, not Opus:

```yaml
# cloud-overflow — the failover net. Make it cheap; escalate deliberately, not by accident.
- model_name: cloud-overflow
  litellm_params:
    model: anthropic/claude-haiku-4-5      # was: claude-opus-4-8
    api_key: os.environ/ANTHROPIC_API_KEY
```

Current Anthropic pricing (mid-2026, per million tokens): **Opus 4.8 $5 / $25**; Sonnet and Haiku
tiers are materially cheaper, and **Haiku-first, escalate-on-failure** is the consensus 2026 habit
(run structure/logic through Haiku, promote to Sonnet for daily work, reserve Opus for genuinely
hard reasoning). Keep a named `cloud-opus` tier for the hard cases; don't make Opus the *default*
landing spot for a timed-out local call.

Two more current facts worth banking:
- **Opus 4.8 fast mode is now 3× cheaper** than on 4.7 ($10/$50 vs $30/$150). If we use fast mode
  for latency-sensitive interactive work, it's newly affordable.
- **Sonnet 5 is the Claude Code default now**, with a native **1M-token context** and promo pricing
  through Aug 31, 2026. Good default; just don't let a 1M window tempt us into dumping whole repos
  in — a big window is a *capacity*, not a *budget*.

## 3. Prompt caching — Claude Code gets it free; our own scripts probably don't

Prompt caching is the single highest-leverage API lever in 2026: a cache **read** costs ~10% of
normal input price, so any stable prefix reused within the TTL (5-min default, 1-hr option) saves
**60–90% on input tokens**.

- **Claude Code already does this automatically** for system prompts and repeated context — one
  reason `/clear`-ing and *not* thrashing the early context matters (see §5).
- **Our own Claude API calls likely don't set cache breakpoints.** Two candidates:
  - `customers` statement build (`make statement` → `localDNS/.../compose.py`, `generate_client.py`)
    — if these call Claude with a large stable template/system prefix per household, mark the prefix
    `cache_control` and the per-home data goes after it. Monthly batch of N homes → N−1 cache reads.
  - the LangGraph supervisor (`langgraph-router/`) — tool schemas (3–8k tokens on MCP-style agents)
    are the textbook thing to cache.
- **Anti-patterns to avoid** (they silently break the cache): a timestamp or `{household.name}` in
  the cached prefix invalidates it every call. Keep dynamic content *after* the cache breakpoint;
  truncate any clock to the day.
- Also consider **batch processing** for the monthly statement run — ~50% off, and statements are
  not latency-sensitive.

## 4. Routing: fail-over is not the same as route-by-task

Our router is deliberately **local-first, cloud-as-failover** — great for privacy and floor cost.
But "failover-only" means a task only reaches Claude when the *local model breaks*, not when the
*task actually needs* a frontier brain. So customer-facing copy (a Statement's "Handled For You"
log, an ADR, marketing voice) gets qwen2.5 quality by default, while trivial mechanical prompts
that a 3B could nail sometimes still hit cloud on a timeout.

2026 best practice is a **routing layer on three axes: sensitivity, complexity, availability.**
Route ~70% of volume local (industry reports 60–80% cost cut) and send the *quality-critical or
hard* slice to Claude on purpose:
- **Sensitivity gate first, fail *closed*.** This is exactly **TD-14**, still open: `local-reason`
  falls over to `cloud-overflow`, so a *sensitive* task leaks to Claude the moment the local model
  is down. Fixing routing and fixing TD-14 are the same edit — give sensitive chains a
  **local-only** fallback.
- **Complexity gate second.** A tiny local classifier (qwen2.5:3b) can score "hard/customer-facing?"
  in one cheap local call and set the tier — a "small model as router" pattern. Tools exist off the
  shelf now (vLLM Semantic Router; Portkey went Apache-2.0 in March 2026) if we'd rather not build
  it in LangGraph.
- **Semantic cache** in front of the router: match repeat questions by *meaning* and return the
  stored answer — kills spend on the "how do I deploy X again?" class of repeats.

## 5. Context-management features we're leaving on the table

Anthropic shipped real token savers in 2026; adopt the habits:
- **`/clear` between unrelated tasks.** Stale context is re-billed on every subsequent message.
  This is the cheapest habit and the most skipped.
- **`/compact` with custom instructions** when a session must continue ("keep the file paths and
  the decision, drop the exploration").
- **Subagents for exploration.** A subagent can burn tens of thousands of tokens spelunking and
  return a 1–2k-token distilled summary to the main thread — the main context stays lean. Use the
  `Explore`/`general-purpose` agents for "find where X lives" instead of reading files into the
  main window.
- **The memory tool + context editing** (public beta on the Developer Platform): context editing
  auto-clears stale tool results; in Anthropic's own 100-turn eval it **cut tokens 84%** and, paired
  with the memory tool, improved task performance **+39%**. Relevant to the LangGraph supervisor
  and any long-running routine.
- **A code index beats grep-flooding.** Retrieval over an embedded index (we already run
  `local-embed`/nomic-embed-text for Huginn's RAG) lets the agent pull the ~right files instead of
  dumping directory listings into context. Expand that index to cover the repos, not just
  statements.

## 6. Routines & loops — pay the context tax once, not every tick

This very review is a scheduled routine that loaded **all seven repos'** CLAUDE.md before starting.
For any *recurring* routine:
- **Scope it to the one repo it needs.** A daily "check the PR" loop shouldn't load the whole
  portfolio.
- **Right-size the cadence.** A 5-minute poll pays the cold-context cost 12×/hour; most of our
  checks change on the order of hours. Prefer event-driven (webhook wakeups) over tight polling.
- **Pick the model to the job.** A status-check routine can run on Haiku; it doesn't need Opus.

## 7. Lean on the local stack for the cheap 80%

We own a capable local tier — use it as a *pre-processor* so Claude only sees what needs a frontier
brain:
- **Triage/classify/route** with qwen2.5:3b (local, cool, free) before deciding whether to spend a
  cloud token.
- **First-pass summarize** long logs/transcripts locally, send Claude the summary.
- **Embeddings/RAG** for retrieval (already have `local-embed`) — index the repos.
- Keep the **honesty invariant**: sensitive data never crosses the Bifröst — which is why the
  sensitivity gate (TD-14) must fail closed before we lean harder on local↔cloud handoff.

## 8. What we're already doing right (don't regress these)

- Local-first router with a cloud failover path — the correct default posture.
- A deterministic **privacy gate** in the supervisor design (just not yet enforced at the failover
  layer — TD-14).
- Local embeddings for RAG (index stays inside the walls).
- A disciplined review cadence and an honest "built / scaffold / not-deployed" status log.

## 9. Critique of the prompt that asked for this

The triggering prompt was, paraphrased: *"Locate inefficiencies in our process… reduce token use…
better prompting… leverage other AI… hybrid local+Claude… ANYTHING that could help… search the
web… keep UP TO DATE… check the news."*

**What it did well:** clear intent, gave permission to search, flagged that the field moves fast,
and asked me to self-critique. Good instincts.

**Where it's inefficient — and this is the irony, it's the #1 prompting anti-pattern:**
- **Unbounded scope.** "ANYTHING that could help" has no stop condition, so the model explores
  maximally and spends maximally. For a *recurring* routine, unbounded scope = unbounded spend
  **every run**.
- **No output contract.** No length, format, or destination specified, so the model guesses (I chose
  a committed review doc + a notification).
- **Many questions in one breath.** Token use, prompting, other AI, hybrid routing, news — five
  investigations bundled; each wants a different search.
- **No budget or "done" definition.**

**A tighter version** (drop-in for the next run of this routine):

> Review our AI-usage efficiency. **Output:** update `docs/ai-cto/reviews/` with a dated file, ≤1,200
> words, top 5 findings ranked by ROI, each with the exact file/line to change. **Scope:** token cost,
> model/routing choices, prompt caching, and one "what changed since last review" web-check (cite
> sources). **Skip** anything already logged as resolved. Notify only if a finding is P1 or costs us
> money today.

That version is *cheaper every time it runs*, produces a comparable artifact, and has a clear
finish line. General rule for our prompts: **state the output shape, bound the scope, name the
budget, and define done.** Vague-and-broad is the most expensive way to ask.

## 10. Keeping current (this page goes stale fast)

Model prices, context features, and routing tools are changing monthly in 2026. Rather than a
human re-reading blogs, make *this review* the recurring job:
- Re-run this review ~monthly (the tightened prompt in §9), with one web-check: "what changed in
  Claude pricing / context tooling since `<last review date>`."
- Watch specifically: Anthropic release notes (pricing, context editing/memory GA), Claude Code
  defaults (model + context window), and the local-routing tools (vLLM Semantic Router, Portkey,
  LiteLLM releases).
- Bank each check as a dated delta at the top of this file (house style: newest first).

## 11. Sources

Current as of 2026-07-02 (my training cutoff is Jan 2026; the below are live web results):

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Cookbook — Context engineering: memory, compaction, tool clearing](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Claude Platform Docs — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Platform Docs — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Code Docs — Manage costs effectively](https://code.claude.com/docs/en/costs)
- [Anthropic — Introducing Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8)
- [VentureBeat — Claude Opus 4.8: 3× cheaper fast mode](https://venturebeat.com/technology/anthropics-claude-opus-4-8-is-here-with-3x-cheaper-fast-mode-and-near-mythos-level-alignment)
- [DigitalApplied — LLM model routing 2026: cost-quality optimization](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [SitePoint — Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [vLLM Semantic Router](https://vllm-semantic-router.com/)
- [systemprompt.io — Reduce Claude Code costs 60% with four habits](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Milvus — Cut Claude Code token usage with a code index](https://milvus.io/blog/claude-context-reduce-claude-code-token-usage.md)

---

*Filed by NARF (AI CTO). This is advisory — no config was changed by this review. The #1 and #3
items are one-line/one-hour edits with real dollar impact; #4 also closes the still-open TD-14
privacy gap.*
