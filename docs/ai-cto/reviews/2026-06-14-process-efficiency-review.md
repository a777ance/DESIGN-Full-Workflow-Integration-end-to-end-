# Process Efficiency Review — User ↔ AI workflow

**Date:** 2026-06-14
**Scope:** How we work with Claude (and other AI) across the A777ance repos — where tokens
and effort leak, and what to change. Grounded in the actual repo state, with current
(June 2026) best practices from the web.

> **TL;DR.** The single biggest leak is the **daily NARF + ZORT ritual**: two full LLM
> review passes *every day* (`docs/ai-cto/reviews/` and `docs/ai-cfo/reviews/` each have an
> entry for every day since 2026-06-04), each re-ingesting the whole hub + the large
> `CLAUDE.md` files, then writing a session-update commit — on a pre-revenue business whose
> blockers barely move week to week. Fix that one thing and most of the spend goes away. The
> rest is: trim the always-loaded context, mechanize what isn't really an LLM job, run the
> unattended/scheduled work on the **Batch API (-50%)** or the **local tier you already
> built but never deployed (Odin/LiteLLM)**, and triage-before-escalate.

---

## 1. The findings, ranked by payoff

### 🔴 #1 — The daily two-agent review ritual is the main token sink

Evidence in this repo:
- `docs/ai-cto/reviews/` — a review file **every day**, 2026-06-04 → 2026-06-14 (~4–8 KB each).
- `docs/ai-cfo/reviews/` — same cadence, ~6–11 KB each.
- 31 `NARF/ZORT session update` commits in history.
- `2026-06-12` CFO review is **335 bytes** — i.e. "nothing changed." That run still paid the
  full cost of reading the hub before discovering there was nothing to say.

Each run re-reads the hub (`portfolio.md` 141 lines + `decisions.md` 131 + `roadmap.md` +
`tech-debt.md` for CTO; **six** files for CFO) plus the `CLAUDE.md` of every co-located repo,
then appends a dated review and rewrites `portfolio.md`. Two agents, overlapping context,
once a day, on a business with **0 paying customers** that is **blocked on one thing**
(t630 SSH access — see `portfolio.md` Active Blockers). Most days the honest output is "same
blocker."

There is also a **compounding** cost: every session-end update *grows* `portfolio.md` and the
reviews dir, which the *next* session must read. The ritual makes its own input bigger.

**What to do:**
1. **Trigger on change, not on the clock.** Run NARF/ZORT only when something material
   actually changed (a commit landed in a spoke repo, a decision was made, t630 access
   happened). A scheduled job should first run a cheap **triage** ("did anything change that
   warrants a CTO/CFO pass?") and **exit silently if not** — no full read, no churn commit.
   The 335-byte file is the proof case.
2. **One pass, not two.** NARF and ZORT read mostly the same hub. Merge into a single
   session that produces both the tech and finance delta, or have one read the hub and hand a
   summary to the other (subagent), instead of two independent full reads.
3. **Cap and archive the working memory.** Keep `portfolio.md` to a short *current-state*
   header; move history to an append-only `archive/` that is **not** read at session start.
   Same for the `reviews/` dirs — they are a log, not session input.
4. **Stop the reflex "session update" commit when nothing changed.** A commit that restates
   yesterday is negative value: it costs tokens to write and tokens to read tomorrow.

### 🟠 #2 — The always-loaded context (`CLAUDE.md`) is heavy and duplicated

`CLAUDE.md` loads *before every task*, so its weight is paid on every single interaction.

- Combined `CLAUDE.md` across the repos: **~1,040 lines / ~8,000 words** (≈ 11–12k tokens).
  `localDNS` 326 lines, DESIGN 295, MARKETING 214 — much of it narrative duplicated from each
  repo's own `README.md`.
- The ~30-line **"House style: ordering & typography"** block is copy-pasted **verbatim into
  all six** `CLAUDE.md` files. When repos are checked out side-by-side (as here), a session can
  load several at once.

**What to do:**
- Treat `CLAUDE.md` as a *rules + pointers* file, not a second README. Move the funnel
  diagram, money-flow prose, and philosophy essays into `README.md` (read on demand); keep
  `CLAUDE.md` to the invariants and "where to look." Best-practice guidance is explicit that
  `CLAUDE.md` should be lean because it is pre-loaded every time.
- De-duplicate House Style: keep the full version in one `STYLE.md`, reduce the `CLAUDE.md`
  copies to a 3-line summary + a link. Within a repo you can `@import` it; across repos accept
  a short pointer. This is deterministic policy anyway — see #3.

### 🟠 #3 — A lot of this is **not an LLM job** — mechanize it for zero tokens

Several recurring asks are deterministic and should be enforced by code/hooks, not by asking
Claude (or re-reading the rule) each time:
- **House-style ordering** (newest-first, alphabetical Z→A), **Gill Sans font** enforcement,
  reverse-chronological checks → a linter / pre-commit hook.
- **Broken links / anchors** → `tools/check-docs.py` already exists and is in CI. Good. Extend
  the same pattern to the other deterministic rules.
- **`roster.json` / stats JSON** → schema validation, not a model read.
- **Vale** already exists in `Chronikomicon` (`.vale/styles/...`). Generalize that prose linter
  to the other repos so style is caught by tooling, freeing the model for judgment work.

Every rule you move into a hook is a rule you no longer pay to re-explain or re-check.

### 🟡 #4 — Run the unattended work on the cheap paths you already have

This very routine ran on **Opus 4.8** (the most expensive model) to do mostly research +
summarization — work a smaller model does well. For scheduled/unattended jobs:

- **Batch API = 50% off** input *and* output, all models, for anything async (Anthropic). The
  daily digests, metrics roll-ups, link checks, and "scan the news" routines are not
  interactive — they are textbook batch jobs. ([Anthropic pricing](https://www.finout.io/blog/anthropic-api-pricing))
- **Model-match the task.** Scheduled scans/triage on **Haiku/Sonnet**; escalate to **Opus**
  only when a finding needs deep judgment. Don't run a recurring "check the news" loop on Opus.
- **Use the local tier you built but never deployed.** `localDNS/10-ai-orchestration` (Odin /
  LiteLLM, the deepseek-r1:1.5b "cool" local tier → cloud-GPU reason → cloud-overflow ladder)
  is *reference code, not deployed* (per `portfolio.md`). That is exactly the hybrid router the
  2026 literature says cuts 60–80% of LLM cost by keeping the 60–70% of simple tasks
  (classification, extraction, formatting, triage) local and sending only the ~10% that needs
  frontier reasoning to Claude. **Deploying it is itself a top cost lever**, not just a homelab
  toy. ([hybrid architecture](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
  [LiteLLM routing](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/))

### 🟡 #5 — Prompt caching: real, but watch the March-2026 regression

The hub docs + `CLAUDE.md` are a stable prefix — ideal for **prompt caching** (cached input is
~10% of the price). Two current caveats:
- Around **2026-03-06 Anthropic dropped Claude Code's effective cache TTL from 1h to 5m**
  (widely reported regression). So sessions spaced hours apart re-pay the full prefix.
  ([XDA](https://www.xda-developers.com/anthropic-quietly-nerfed-claude-code-hour-cache-token-budget/),
  [issue #46829](https://github.com/anthropics/claude-code/issues/46829))
- **Implication:** batch the day's CTO+CFO work into **one** session window so the prefix stays
  warm, instead of two separate runs hours apart. For the scheduled routines, call the API
  directly with an **explicit 1-hour cache** where it's supported (Bedrock/Vertex/API beta).

### 🟢 #6 — Subagents / context isolation, used sparingly

When a task genuinely spans many files (cross-repo reconcile, the kind of sweep this review
did), use **subagents** so the verbose file reads stay in the subagent's context and only a
summary returns to the main thread. Caveat from current guidance: subagents add startup
overhead — don't wrap a one-line git op in one. Rule of thumb: subagent when it would
otherwise pull >3–4 large files into the main context.

---

## 2. The prompt that launched this review — was it efficient?

**Honestly, no — and the user asked to be told.** The prompt was, paraphrased: *"Find any
inefficiency anywhere, reduce tokens, better prompting, other AI, hybrid local LLM, search the
web, check the news, keep up to date day by day — ANYTHING."*

Why that's costly:
- **Unbounded scope.** "ANYTHING that could help" + "search the web" + "check the news"
  maximizes exploration with no stop condition — the most expensive shape of request, and the
  hardest output to act on.
- **No deliverable spec.** No target (token budget? which repo? format? where to write it?), so
  the model has to guess, and guesses wide.
- **A recurring need expressed as a one-shot.** "Keep up to date, this changes day by day" is a
  *cadence*, not a single answer — but phrased as one prompt it re-does the broad scan from
  scratch each time.
- **Wrong tier for the job.** A broad news-scan + summarize is Haiku/Sonnet + Batch work; it ran
  on Opus interactively.

**A tighter version (drop-in):**

> *"Weekly, on Sonnet via the Batch API: list what changed in Claude Code / Anthropic
> pricing & cost features since the last run (caching, batch, model prices, context tools).
> For each change, one line: does it change our setup? If nothing material changed, reply
> 'no change' and stop. Write findings to `docs/ai-cto/reviews/`. Budget: one web pass,
> ≤300 words out."*

That keeps the *intent* (stay current, find savings) while bounding cost, fixing the tier,
making it recurring, and giving it a stop condition. Set it up as a scheduled routine / `/loop`,
not a fresh broad prompt each time.

**General prompting hygiene that applies here:** front-load the constraints; name the
deliverable and where it goes; give a budget and a stop condition; scope to one repo/question
per run; prefer "tell me the delta" over "review everything."

---

## 3. Do-this-week checklist

- [ ] **Gate the daily ritual on change.** Cheap triage first; exit silently + no commit when
      nothing material changed. (Biggest single saving.)
- [ ] **Merge NARF + ZORT** into one hub read per run (or hub→summary→handoff), not two.
- [ ] **Archive hub history** out of session-start reads; cap `portfolio.md` to a short header.
- [ ] **Slim `CLAUDE.md`**: move narrative to README; reduce House Style to a pointer + `STYLE.md`.
- [ ] **Move the scheduled/unattended jobs to Batch API + Haiku/Sonnet**; reserve Opus for
      judgment calls.
- [ ] **Deploy Odin/LiteLLM** and route triage/lint/classification to the local tier.
- [ ] **Mechanize deterministic rules** (ordering, font, schema) via hooks/linters; extend Vale
      beyond Chronikomicon.
- [ ] **Rewrite recurring prompts** with scope + budget + stop condition; run them as routines.

---

## Sources (June 2026)

- [Claude Code best practices — context management](https://muhammadusmangm.github.io/claude-code-best-practices/guides/context-management/)
- [Claude Code advanced best practices 2026 — hooks, subagents, context (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/)
- [7 ways to reduce Claude Code token usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [Anthropic API pricing 2026 — caching, batch, optimization (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM smart routing — cut API costs (Markaicode)](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Run local models with Claude Code to cut costs (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Prompt cache TTL 1h→5m regression (XDA)](https://www.xda-developers.com/anthropic-quietly-nerfed-claude-code-hour-cache-token-budget/) · [claude-code issue #46829](https://github.com/anthropics/claude-code/issues/46829)
