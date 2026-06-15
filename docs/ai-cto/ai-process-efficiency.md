# AI Process Efficiency — How we work *with* the AI

**Owner:** NARF (AI CTO) · **First written:** 2026-06-15 · Newest notes at the top per house style.

This is the meta-layer: not what the AI builds, but **how the human↔AI loop itself runs** —
where tokens (and therefore dollars and rate-limit budget) leak, where prompting can be tighter,
and where our own homelab can carry work the Claude API is overpaying for. Findings are ranked by
impact, and tied to the specific way A777ance works (seven repos, big `CLAUDE.md` briefings, the
NARF/ZORT session-start reading protocol, the t630 LiteLLM reasoning ladder, scheduled routines).

> **Grounding (verified 2026-06-15 via the `claude-api` skill, not memory):** current model prices —
> Opus 4.8 `$5 / $25` per Mtok, Sonnet 4.6 `$3 / $15`, Haiku 4.5 `$1 / $5`, Fable 5 `$10 / $50`.
> Prompt-cache reads ≈ **0.1×** input price; cache writes ≈ 1.25× (5-min) / 2× (1-hour).
> Batch API = **50% off** for non-urgent work. These are the numbers the levers below trade against.

---

## TL;DR — the five highest-leverage moves

1. **Cut the fixed per-session context.** Every Claude Code session on a repo silently ingests that
   repo's `CLAUDE.md` *plus*, for this repo, the NARF protocol's "read these 10 files at session
   start" (4 ai-cto + 6 ai-cfo docs). That's a large, repeated input bill on **every** task,
   including trivial ones. Trim + make most of it **load-on-demand** (skill/`@import`), not
   always-on. Biggest single lever we control.
2. **Route by task, not by habit.** We already run the exact hybrid stack the 2026 cost guides
   recommend (LiteLLM gateway + local Ollama ladder + Claude cloud on the t630). The lever isn't
   *build* it — it's *use* it: send linting, link-checking, log triage, commit-message drafting,
   classification, and first-pass summarization to **local / Haiku**, reserve **Opus/Fable** for
   genuinely hard reasoning. Industry split: ~60–70% of requests don't need a frontier model.
3. **Lean on prompt caching for the big briefings.** A stable `CLAUDE.md` prefix read at ~0.1× is
   nearly free; the win is keeping it *byte-stable* (no timestamps/IDs up front) so the cache
   actually hits.
4. **Batch the un-urgent.** Scheduled/overnight routines (like the one that produced this doc),
   bulk statement QA, doc-integrity sweeps → **Batch API, 50% off**. Nothing a human is waiting on
   should pay interactive rates.
5. **Write tighter prompts.** Scope + success criteria + stop conditions. Open-ended "look at
   everything" prompts (see the critique of *this task's* prompt below) maximize tokens and minimize
   precision.

---

## Critique of the prompt that launched this task (as requested)

The originating prompt was, paraphrased: *"Find inefficiencies in our process between user and AI.
Token use, prompting, other AI, hybrid local+Claude, anything. Search the web. Keep up to date.
Check the news. Also critique this prompt."*

**What it did well:** named the domain, explicitly invited web research and a self-critique, and gave
permission to range widely. For an exploratory ask that's fine.

**Where it costs us:**

- **No scope or success criterion.** "ANYTHING that could help" forces a maximal sweep — the model
  reads broadly and writes long, because nothing tells it when to stop. Token cost scales with
  ambiguity.
- **No constraints surfaced.** It doesn't say "we already run LiteLLM + a reasoning ladder" — so a
  cold reader could waste a section recommending we *build* the thing we already have. (I knew from
  the repo context; a fresh agent wouldn't.)
- **Mixed altitudes in one ask** — strategy ("leverage other AI"), tactics ("better prompting"), and
  ops ("check the news") bundled together, which produces a sprawling answer rather than a decision.
- **"Keep UP TO DATE… day by day"** is a *standing* need, not a one-shot — it belongs in a scheduled
  routine with a tight remit, not a paragraph in a prompt.

**A tighter rewrite** (same intent, ~⅓ the output, sharper):

> *"Audit our Claude usage for cost. Context: we run LiteLLM + an Ollama reasoning ladder on the
> t630 and use Claude Code across 7 repos with large CLAUDE.md briefings. Give me the top 5
> token-reduction levers ranked by $ impact, each with the concrete change and a rough estimate.
> Note anything our local stack should be handling instead of Claude. Flag if my framing misses
> something. One page max."*

Rule of thumb for us: **state the context the AI can't infer, name the deliverable shape, and set a
stop condition.** That alone trims long answers.

---

## The levers, ranked, tailored to A777ance

### 1. Shrink the always-on context (biggest controllable bill)
- **Symptom.** Seven `CLAUDE.md` files, several very large (the `localDNS` one is a full system
  reference). Each is loaded into *every* session on that repo. This repo's NARF/ZORT protocol then
  instructs reading **10 more files** at session start. A one-line fix request pays the same context
  toll as a major refactor.
- **Fixes.**
  - Keep `CLAUDE.md` to the *durable, every-task* essentials; move stage-deep detail to files the
    model reads **only when the task touches that stage** (the Skills / progressive-disclosure
    pattern — a short description in context, full file on demand).
  - Make the "read these 10 docs" protocol **conditional**: read the portfolio hub always; read the
    ai-cfo set only for finance work, the spoke context only for the repo in play.
  - Add/curate `.claudeignore` (or equivalent) so search/agent steps don't slurp generated output,
    samples, and vendored files. Reported context reductions from ignore-discipline alone are large.
- **Why it pays:** this input is *repeated on every invocation*. A 30% trim compounds across every
  session and every routine, forever.

### 2. Use the hybrid stack we already built (route by task)
- We are ahead here: `10-ai-orchestration/` on the t630 is LiteLLM + an Ollama reasoning ladder
  (`local-reason` on CPU for light work, `cloud-gpu-reason` for heavy, `cloud-overflow` to Claude).
  The 2026 guides describe this exact architecture as the #1 cost lever — *model routing*.
- **Apply it to AI-assisted work, not just app inference:**
  - **Local / Haiku-class:** lint, format, link-check (`tools/check-docs.py`), log triage, commit
    messages, "summarize this diff", classify/label, first-pass extraction.
  - **Sonnet:** most routine coding and editing.
  - **Opus 4.8 / Fable 5:** architecture, multi-repo reasoning, the hard debugging, security review.
- **Privacy caveat is already logged as TD-14:** the `local-reason` fallback chain can fail *open*
  to `cloud-overflow`. Routing more sensitive work locally only counts as a privacy win once that
  fails **closed**. Fixing TD-14 is a prerequisite for leaning on local routing for anything
  customer-data-adjacent.

### 3. Prompt caching for the briefings
- Cache reads are ~0.1× input price. The big `CLAUDE.md`/protocol prefix is the ideal cache target —
  but only if the **prefix is byte-stable**. Audit for silent cache-busters at the top of any
  assembled prompt: `datetime.now()`, run IDs, unsorted JSON, per-session interpolated values. Keep
  volatile content *after* the stable block. (For our own LiteLLM-fronted calls, verify
  `cache_read_input_tokens > 0` across repeated calls; if it's zero, something up front is changing.)

### 4. Batch everything no human is waiting on
- Batch API = 50% off, completes within the hour. Candidates: this nightly process-audit routine,
  monthly statement spot-checks, doc-integrity sweeps across repos, any bulk classification. If a
  person isn't blocked on the answer, it shouldn't pay interactive rates.

### 5. Tighter prompting + the right tools
- **Subagents** for fan-out / large-search tasks so verbose intermediate results stay out of the
  main context window (Explore-style, often on a cheaper model).
- **Tool-definition tax:** every connected MCP server loads its tool schemas into context (reports
  cite up to ~18k tokens/turn for heavy MCP setups). Audit which servers are actually needed per
  task; harnesses that defer tool schemas until searched (as this one does) avoid the standing cost.
- **Effort levels:** set low effort for mechanical work (format/lint), reserve high/xhigh for
  reasoning — cuts thinking tokens with no quality loss on routine tasks.
- **Compact sooner / scope tighter:** drive sessions to one clear task; compact before the auto
  threshold rather than letting a session balloon.

---

## Keeping up to date (the standing need, done right)
"Check the news day by day" is a routine, not a prompt. Suggested shape: a **low-frequency, tightly
scoped** scheduled routine (weekly, Batch-priced) that checks only (a) Anthropic model/price changes,
(b) Claude Code changelog items affecting cost/context, (c) anything that changes the local-vs-cloud
math — and **notifies only on a real delta**, silent otherwise. A daily "all quiet" ping is noise.
Pin model/price facts via the `claude-api` skill rather than from memory; they move.

---

## Concrete next actions (smallest first)
1. **Fix TD-14** (fail-closed local fallback) — unblocks privacy-safe local routing. *P1, already tracked.*
2. **Token-budget the briefings:** measure each `CLAUDE.md` + the session-start doc set with
   `count_tokens`; set a target and trim/defer to hit it.
3. **Make the NARF/ZORT session-start reads conditional** on the task domain.
4. **Write a routing cheat-sheet** for `10-ai-orchestration/`: task type → tier (local/Haiku/Sonnet/Opus).
5. **Move the un-urgent routines to Batch.**
6. **Adopt the prompt template** (context the AI can't infer + deliverable shape + stop condition).

---

## Sources (2026-06-15)
- Claude Code token optimization: [buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization) ·
  [Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/) ·
  [Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency) ·
  [agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- Hybrid local+cloud routing: [SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
  [MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) ·
  [Morph](https://www.morphllm.com/llm-cost-optimization) ·
  [Cleveroad](https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/)
- Claude Code features (subagents/skills/context): [MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/) ·
  [claudefa.st changelog](https://claudefa.st/blog/guide/changelog)
- Pricing/caching/batch facts: bundled `claude-api` skill (cached 2026-06-04).
