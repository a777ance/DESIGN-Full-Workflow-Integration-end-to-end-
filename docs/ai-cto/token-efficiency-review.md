# Token & Process Efficiency Review

**Date:** 2026-06-19 · **Author:** NARF (AI CTO) · **Scope:** the human↔AI working loop across all A777ance repos

This is a standing review of how we spend tokens working with Claude, and where the process
itself wastes time and money. Newest findings lead (house style). Re-run quarterly or when
pricing/features shift — see "How to keep this current" at the bottom.

---

## TL;DR — the five biggest levers, ranked

| # | Lever | Est. saving | Effort |
| - | ----- | ----------- | ------ |
| 1 | **Make the session-start reading ritual lazy, not mandatory** | ~15–19k tokens *per DESIGN session* | Low (edit CLAUDE.md) |
| 2 | **Trim the CLAUDE.md files** (DESIGN 4.5k, localDNS 5.1k tokens — loaded every turn) | ~30–40% of baseline | Low–Med |
| 3 | **Route routine work to Haiku / the local box; reserve Opus for hard reasoning** | 5–20× on routine calls | Med (already half-built) |
| 4 | **Scope prompts tightly + name the files** (this prompt is the anti-pattern — see below) | Big variance reducer | Free |
| 5 | **Cache the best-practices research; don't re-web-search every routine run** | Most of this routine's cost | Low |

---

## 1. The session-start ritual is the single biggest hidden cost

`DESIGN/CLAUDE.md` instructs Claude to read, *at the start of every session*:

- **NARF (CTO):** `portfolio.md` (2.3k) + `roadmap.md` (0.6k) + `tech-debt.md` (0.7k) + `decisions.md` (2.1k) = **~5.5k tokens**
- **ZORT (CFO):** `portfolio.md` (2.3k) + `decisions.md` (1.1k) + `metrics.md` (**4.0k**) + `runway.md` (0.6k) + `budget.md` (0.7k) + `MARKETING/.../context.md` = **~8.7k tokens**
- Plus `CLAUDE.md` itself (**~4.5k**).

**A DESIGN session that obeys the briefing literally burns ~18–19k input tokens before a single
useful instruction is read** — whether the task is a one-line typo fix or a quarter-end financial
model. Most sessions don't need the CFO metrics log or the full decisions history.

**Fix (recommended):** change the ritual from *"read these at session start"* to *"read these
**when the task touches** CTO/CFO state."* Concretely, in `CLAUDE.md` §5/§6, replace the
imperative read-list with: *"For portfolio/roadmap/financial tasks, read the relevant file(s)
below; otherwise skip."* This makes the cost proportional to the task. Claude Code already
caches `CLAUDE.md` between turns, but these *referenced* files are re-read on demand each session
and are not part of that automatic cache.

**Secondary fix:** `docs/ai-cfo/metrics.md` is 16 KB (~4k tokens). Split the long KPI *actuals
log* (time-series, append-only) out of the *definitions/targets* so a session can load the small
definitions file without dragging the whole history.

## 2. Trim the CLAUDE.md files — they are the per-turn baseline

A CLAUDE.md is re-sent on **every turn of every session** for that repo. Current sizes:

| Repo | CLAUDE.md tokens |
| ---- | ---------------- |
| localDNS | ~5,118 |
| DESIGN | ~4,496 |
| MARKETING | ~2,665 |
| customers | ~1,033 |
| claude-code-homelab | ~724 |
| azure-lab | ~573 |

Two concrete cuts:

- **The "House style: ordering & typography" block (~250 words) is byte-identical in all 7
  CLAUDE.md files.** That's fine for single-repo work, but when several repos are in scope (as in
  cross-repo sessions) it's loaded *N times*. Keep the rule short in each CLAUDE.md (a 2-line
  summary + a pointer to one canonical `docs/house-style.md`), and put the full prose in that one
  file. Saves the duplication on multi-repo turns.
- **localDNS/CLAUDE.md mixes reference tables that rarely change every turn** (the full deploy-path
  table, the nftables deploy checklist). Those are lookup material — move the long tables to
  `README.md`/`INSTALL-NOTES.md` (already the "full guide") and keep CLAUDE.md to the briefing +
  pointers. Target: under ~3k tokens each.

Rule of thumb from current guidance: a 5k-token CLAUDE.md is a 5k tax paid before Claude reads any
code, on every turn.

## 3. Hybrid local + Claude — we're half-way there; finish the routing

We already run a LiteLLM router on the t630 with a reasoning ladder (`local-reason` on the t630
CPU, `cloud-gpu-reason` on a rented GPU, `cloud-overflow` to Claude). The 2026 best practice is to
push **the 60–70% of work that is classify/extract/format/summarize** to the local model (or
Haiku) and reserve Opus/Fable-5 for the ~10% that needs frontier reasoning.

Specific to our workflows:
- **Roster/CRM field extraction, statement-data validation, log summarization, link-checking,
  commit-message drafting** → local model or **Haiku 4.5** (~$1/$5 per 1M vs Opus ~$5/$25). 5–25×
  cheaper, quality is fine for these.
- **Use Claude Code subagents with `model:` pinned in YAML** (`.claude/agents/*.yaml`): code-review
  on Sonnet, lint/format/search on Haiku, only architecture/financial reasoning on Opus. Subagents
  run inside the parent session and report back compactly — the most token-efficient agent type,
  and they keep large file dumps out of the main context.
- **Privacy note that doubles as a cost note:** TD-14 (the `sensitive`→`cloud-overflow` failover
  gap) should fail *closed* to a local-only chain. Fixing it both protects private lookups and
  keeps sensitive work off the metered API.

## 4. Prompting — and yes, *this* prompt is an example

Tightly-scoped prompts that name the files cost less and vary less. Broad, open-ended prompts
force expensive exploration. The prompt that triggered this review —

> *"Locate inefficiencies in our PROCESS… Is there a better way… Perhaps also better prompting…
> Anything you could possibly think of… Leveraging other AI… ANYTHING that could help. Search the
> web… Keep UP TO DATE… Check the news."*

— is itself the anti-pattern, in three ways:

1. **Unbounded scope** ("ANYTHING", "anything you could possibly think of") → the agent must
   guess where to look and tends to over-search and over-read. A bounded version costs a fraction.
2. **No output contract** → no target file, length, or format, so the agent has to invent one.
3. **Mixed asks in one shot** (audit + web research + news + self-critique) → each pulls context
   in a different direction.

A cheaper, sharper rewrite:

> *"Review token efficiency of our Claude workflow. Focus on (a) the DESIGN session-start reading
> ritual and (b) CLAUDE.md sizes. Give me a ranked list of fixes with token estimates, written to
> `docs/ai-cto/token-efficiency-review.md`. One web search for current Claude pricing is enough —
> don't sweep the news unless something changed since 2026-06."*

Same outcome, scoped exploration, a named deliverable, and a cap on web search.

General prompting rules worth standardizing for the guild:
- **Name the files.** "Refactor the booking-form handler in `03-funnels.../...`" beats "improve the funnel."
- **State the deliverable** (file path + format + rough length) up front.
- **Cap the research** ("one search", "skip the news") so a routine doesn't sweep the web every run.
- **Use `/compact` / `/recap`** to control session length; compact earlier than the default (~70%).
- **One ask per turn.** Split audit-and-implement into two prompts.

## 5. This routine is itself inefficient — make it incremental

This task runs on a schedule with nobody watching. Doing a full multi-query web sweep + repo audit
**every run** is wasteful: best practices don't change daily, and our repo sizes change slowly.

**Fix:** treat this doc as the cache. On each scheduled run, do the cheap thing first —
*one* search for "Claude API / Claude Code pricing or major feature changes since `<date of this
file>`." Only if something material changed do the deeper audit and update this file. Otherwise
exit quietly without notifying (the routine's job is to be eyes when something changes, not to
report "all quiet"). Consider a less-frequent schedule (monthly) for the deep pass.

---

## How to keep this current (the cheap loop)

1. One web search: Claude pricing / Claude Code feature changes since the date at the top of this file.
2. If nothing material → stop, no notification.
3. If something changed → update the relevant section + the TL;DR table, bump the date, notify once.

## Current pricing snapshot (2026-06, verify before relying)

| Model | Input /1M | Output /1M | Use for |
| ----- | --------- | ---------- | ------- |
| Haiku 4.5 | ~$1 | ~$5 | classify / extract / format / lint / search |
| Sonnet 4.6 | ~$3 | ~$15 | code review, routine edits |
| Opus 4.x | ~$5 | ~$25 | architecture, financial reasoning, this review |

Prompt caching reads cost ~10% of normal input; structure prompts static-first, dynamic-last, and
keep timestamps/user-specific text out of the cached prefix. Billing notes to watch: Agent SDK /
headless `claude -p` moved to a separate credit pool (June 15), and Fable 5 moved from included
plans to usage credits (June 22) — confirm against the dashboard.

## Sources

- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Code Token Optimization (2026) — BuildToLaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude API Cost Optimization: Caching, Batching, 60% Reduction — DEV](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Agents in 2026: Subagents, Teams, Costs — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Claude Code Pricing (2026) — MorphLLM](https://www.morphllm.com/claude-code-pricing)
