# AI process efficiency — token & cost review

**Date:** 2026-06-26 · **Author:** NARF (AI CTO) · **Trigger:** founder routine —
"locate inefficiencies in our PROCESS (user ↔ AI); reduce token use; better prompting;
hybrid local + Claude; keep up to date."

This is a review of *how we work with the AI*, not the product. It ranks the levers by
return-on-effort for **our actual setup** (Claude Code on the web across 7 repos, a
LiteLLM reasoning-ladder already running on the t630, doc-heavy CTO/CFO workflows, and
scheduled routines like the one that produced this file). Sources at the bottom; the
field moves weekly, so re-check before acting on any single number.

---

## TL;DR — the five biggest levers, ranked

| # | Lever | Effort | Est. saving | Owner |
| - | ----- | ------ | ----------- | ----- |
| 1 | **Stop running routine doc work on Opus.** Default sessions to Sonnet; escalate to Opus only for architecture/hard code. | trivial (per-repo `model` setting) | Opus is **5× Sonnet, ~25× Haiku** per token — most of our work is log/doc/link edits | NARF |
| 2 | **Route Claude Code through the LiteLLM ladder we already built.** Mechanical ops (reads, greps, commit msgs, log appends) → local DeepSeek/Ollama; reasoning → Opus. | medium (wire CC Router / LiteLLM complexity-router) | Reported **50–99% CC cost cut**; 60–80% on hybrid workflows | NARF |
| 3 | **De-bloat the 7 CLAUDE.md files.** They load before every task and re-load on every compaction. The house-style block is duplicated verbatim in all 7. | low | "lean CLAUDE.md + ignore discipline" reports up to **85% context reduction** | NARF |
| 4 | **Batch API for the monthly statement run.** Bulk, async, penny-a-home, scheduled — the textbook case. | low (if any LLM step is in compose/generate) | **50% off**, stacks with caching → ~10% of baseline | ZORT/NARF |
| 5 | **Tighten prompts: scope + format + output location.** Our default prompt style is "shotgun" (see §6). | trivial (habit) | "right info, not most info" — avoids re-exploration + runaway output | founder |

---

## 1. Model selection — we are overpaying per token by default

This routine ran on **Opus 4.8 (1M context)**. Opus is ~5× Sonnet and ~25× Haiku per
token. The bulk of what we ask inside these repos — updating decision/metrics logs,
appending Handled-For-You entries, fixing links, drafting copy, rendering statements — is
Sonnet or even Haiku work. Opus earns its price only on genuine reasoning: architecture
calls, multi-file refactors, the gnarly debugging.

**Action:** set a per-repo default of Sonnet, escalate to Opus deliberately. The
"start on the cheap model, upgrade only when stuck" rule is the single most-cited
cost practice for 2026.

## 2. We built the hybrid infra and aren't pointing Claude Code at it

`localDNS` stage 10 already runs LiteLLM with a reasoning ladder (`local-reason` =
deepseek-r1:1.5b on the t630, `cloud-gpu-reason` on a rented GPU, `cloud-overflow`). The
missing piece is using it for **Claude Code itself**, not just Open WebUI chat.

- **Claude Code Router / LiteLLM complexity-router** sits between CC and the providers and
  classifies each request (rule-based, sub-ms, zero extra API calls) → cheap/local for
  mechanical ops, Opus for reasoning. Community reports: 50–99% CC spend reduction.
- **Privacy guardrail (hard):** this interacts with **TD-14** — `local-reason` currently
  has a cloud fallback, so a `sensitive`/customer-data task can fail *open* to Claude
  cloud. Do not route anything touching `customers/` real data until TD-14 is fixed to
  fail **closed** (local-only fallback chain). Fix TD-14 first, then route.

## 3. CLAUDE.md is a per-turn tax

Every CLAUDE.md loads before Claude reads the task, and re-loads on compaction. Ours are
large, and the **House-style ordering & typography** block (the same 4 bullets) is pasted
verbatim into all 7 repos. The guidance for 2026: keep CLAUDE.md a **lookup table**, not a
brain dump — move rationale to README/context files the model reads on demand.

**Actions:**
- Factor the shared house-style into one canonical short file; replace the duplicated block
  in each repo with a one-line pointer. (Caveat: CC only auto-loads the repo-root CLAUDE.md,
  so the canonical text still has to live somewhere loadable — keep it *short*.)
- Trim each CLAUDE.md to the lookup essentials; push deep "why" into the existing
  `*-context.md` / README files (already our pattern — lean on it harder).
- A `.claudeignore` for generated/rendered output (e.g. rendered statement HTML, data
  dumps) keeps them out of context.

## 4. Prompt caching & the 5-minute TTL

Anthropic dropped the prompt-cache TTL from 60 → 5 min in early 2026; spaced-out work now
re-pays the cache write (effective +30–60% for some). For us:
- **Scheduled routines that loop** (this one, PR babysitting) should consider the **1-hour
  cache** so the stable prefix (system + CLAUDE.md) survives the gap between ticks.
- **Interactive sessions:** keep the stable stuff at the front of context and batch your
  turns inside the 5-min window rather than trickling one message every 20 minutes.

## 5. Batch API for the statement run

`make statement` is bulk, asynchronous, scheduled monthly, ~a penny a home — exactly what
the **Batch API** (50% off input+output, stackable with caching ≈ 10% of baseline) is for.
Today the compose/generate tools are largely deterministic Python, so confirm whether any
step actually calls an LLM; if/when one does (e.g. drafting per-home Handled-For-You copy at
scale), run it as a batch job, not synchronous calls.

## 6. Prompting — our default style is the expensive anti-pattern

The routine prompt that produced this file is a good teaching example. It asked for
"**ANYTHING** that could help… **anything you could possibly think of**," with no scope, no
output format, no budget, and several stacked sub-questions. That maximises both exploration
*and* output length — the opposite of token-efficient. It worked because the model is
capable, but it cost more than it needed to.

**What good prompts give the model (2026 consensus): the right info, not the most info.**
- **Scope it.** "Refactor the login function in `auth.ts`" beats "refactor auth."
- **Name the output format + location.** "Return a markdown table; write it to
  `docs/ai-cto/x.md`" beats "let me know."
- **Set a budget/depth.** "Top 5 levers, one paragraph each" caps runaway output.
- **One ask per turn**, `/clear` between unrelated tasks (stale context is re-read every turn).

**Tightened rewrite of this routine's own prompt:**

> Monthly: review how we use the AI across the 7 repos for token/cost waste. Output the
> **top 5 levers** ranked by ROI as a markdown table + one paragraph each, written to
> `docs/ai-cto/ai-process-efficiency.md`, newest run at top. Cover model choice, the
> LiteLLM routing we already run, CLAUDE.md size, caching, and prompting. Web-check any
> figure that's > 1 month old. Notify only if a lever could save > 20%.

That version is scoped, formatted, located, budgeted, and self-limiting on notifications —
and would have cost a fraction of the open-ended one.

## 7. Smaller wins worth a habit

- **Subagents/personas cost 200–500% (up to ~7×) more tokens.** Our Odin pattern (3 orders
  of 5 + Loki = 16 agents) and the NARF/ZORT split are great for genuinely parallel or
  repeatable locked-config work — not for everything. Planner on Opus, workers on Haiku.
- **Compaction / context-editing** (Anthropic beta, 2026) auto-summarises long sessions —
  good for long routines so context doesn't grow unbounded.
- **Terse-output skills** ("caveman"-style, no filler) report ~65% output-token savings for
  chatty tasks; useful for high-volume mechanical runs, not for customer-facing copy.
- **Cheaper third-party reasoning** (DeepSeek V3.2 ≈ 50× cheaper than Opus) is already in
  our ladder — lean on it for the non-sensitive heavy-but-not-frontier jobs.

---

## Proposed tech-debt items (for the founder to confirm before adding to `tech-debt.md`)

- **CLAUDE.md de-bloat + de-dup** the house-style block across all 7 repos (P2, all repos).
- **Wire Claude Code through LiteLLM/CC-Router** for mechanical-op offload — **blocked on
  TD-14** (privacy fail-closed) for anything touching real customer data (P2, localDNS/all).
- **Per-repo default model = Sonnet**, escalate to Opus deliberately (P3, all repos).

## Sources (2026, re-verify — moves weekly)

- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — firecrawl.dev](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [5 Claude Code Skills That Cut Token Costs up to 70% — MindStudio](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Prompt Caching in 2026: the 5-Minute TTL Change — dev.to](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Claude Batch API in Practice: 50% + caching — claudeapi.com](https://claudeapi.com/en/blog/dev-guides/claude-batch-api-cost-optimization/)
- [Run Local AI Models with Claude Code to Cut Costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Router Guide 2026 — getaiperks.com](https://www.getaiperks.com/en/ai/claude-code-router-guide)
- [LiteLLM Auto Routing / Complexity Router — docs.litellm.ai](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Why Claude Code Subagents Burn So Many Tokens — youcanbuildthings.com](https://youcanbuildthings.com/articles/claude-code-subagents-token-usage/)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Steering Claude Code: skills, hooks, subagents — claude.com (2026-06-18)](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Context Engineering: reducing token usage isn't shorter prompts — tokenoptimize.dev](https://www.tokenoptimize.dev/guides/context-engineering-reduce-token-usage)
