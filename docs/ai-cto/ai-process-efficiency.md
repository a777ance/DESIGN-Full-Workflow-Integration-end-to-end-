# AI process efficiency — user ↔ AI, token spend, hybrid routing

How we work *with* the AI across the seven repos: where tokens leak, how to spend
fewer for the same output, where a local model beats the Claude API, and how to
prompt better. Living doc — the model/pricing landscape moves weekly, so treat the
"As of" date as a freshness stamp and re-check before acting on the pricing rows.

**As of 2026-06-14.** Owner: NARF (CTO) with ZORT (CFO) on the cost rows.

> Per house style this file reads newest-first: the most recent review sits at the
> top of [§7](#7-review-log), older audits below it.

---

## Contents

- [0. The one-paragraph answer](#0-the-one-paragraph-answer)
- [1. Where the tokens actually go (measured)](#1-where-the-tokens-actually-go-measured)
- [2. Prioritised levers (impact × effort)](#2-prioritised-levers-impact--effort)
- [3. Hybrid: local LLM + Claude API](#3-hybrid-local-llm--claude-api)
- [4. Better prompting (incl. a critique of the request that spawned this doc)](#4-better-prompting)
- [5. Current best practices & news (June 2026)](#5-current-best-practices--news-june-2026)
- [6. Quick-win checklist](#6-quick-win-checklist)
- [7. Review log](#7-review-log)

---

## 0. The one-paragraph answer

The biggest inefficiency in our process is **not** how we phrase prompts — it's that
**every Claude Code session in the DESIGN repo pays ~13K tokens of fixed "startup
tax" before any real work begins**, and our scheduled routines run that tax on the
full Opus model on a schedule, unattended. The fixes, in order of payoff: (1) shrink
and tier the CLAUDE.md + mandated-read load so the standing context is small; (2) let
**prompt caching** carry the stable parts at ~10% of input cost; (3) run cheap,
mechanical routines on **Haiku or the local t630 model** instead of Opus; (4) batch
the non-urgent work at **50% off**. Prompting style is a real but second-order lever.
Net: a realistic 50–80% cut in spend on routine AI work with no loss of quality on the
work that matters.

---

## 1. Where the tokens actually go (measured)

Measured on this repo, 2026-06-14:

| What loads at session start (DESIGN repo) | Words | ≈ Tokens |
| ----------------------------------------- | ----- | -------- |
| `CLAUDE.md` (auto-loaded every session)   | 2,608 | ~3,500   |
| 9 files NARF + ZORT **instruct** Claude to read at start (`portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md` ×2, `metrics.md`, `runway.md`, `budget.md` …) | 7,360 | ~9,800 |
| **Standing context before any task** | **~9,968** | **~13,300** |

That ~13.3K rides in the context **every turn** of the session (CLAUDE.md persists; the
read files persist once read). On a 30-turn session that's ~400K token-turns of fixed
overhead. The other repos are lighter (`localDNS` 2,728 words, `MARKETING` 1,445, the
rest <600), but `localDNS`'s CLAUDE.md is also large and its deploy-path table is read
constantly.

Two structural amplifiers make it worse:
- **Cross-repo read chains.** Every repo's CLAUDE.md points at the DESIGN portfolio
  hub, so a session that "reads the AI-CTO state" pulls DESIGN files into a `localDNS`
  or `customers` session too.
- **Unattended schedules pay it repeatedly.** This very routine is a scheduled run on
  `claude-opus-4-8`. Each fire re-pays startup tax at Opus rates ($5 in / $25 out per
  MTok) whether or not it finds anything to report.

This is good news: the dominant cost is **standing context**, which is the most
cacheable, tierable, and model-downgradable kind of cost there is.

---

## 2. Prioritised levers (impact × effort)

Ranked. Do them top-down.

### A. Tier the CLAUDE.md + mandated reads — **highest impact, low effort**
The rule "read these 9 files at session start" is convenient but expensive. Replace
*mandatory* reads with *conditional* ones:
- Keep CLAUDE.md a **lookup table, not a brain dump** — stable rules only (house
  style, repo map, the invariants). Move the prose ("the *why*") to files Claude reads
  *only when the task needs them*. The community benchmark figure is a 5K-token
  CLAUDE.md costing 5K tokens *every turn* regardless of task — so trimming it is pure
  win. ([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage), [Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency))
- Change the NARF/ZORT preamble from *"At session start, read portfolio.md, roadmap.md,
  tech-debt.md, decisions.md, …"* to *"At session start read **portfolio.md** only;
  read the others **when the task touches roadmap / debt / a past decision / a financial
  figure.**"* That alone drops standing context from ~13.3K to ~5K on a typical run.
- Consider a `/skill`-style on-demand loader: a one-line description in context, full
  file pulled only on demand (Anthropic's Skills / progressive-disclosure pattern).

### B. Turn on prompt caching for the stable prefix — **high impact, low effort**
The CLAUDE.md + portfolio files are byte-stable across a session and across runs within
the 5-min/1-h window. Cached reads cost **~10% of input** and writes **~1.25×**, so
break-even is the *second* request. For our scheduled routines that re-read the same
hub files every fire, this is close to free money.
- **Keep the prefix byte-identical.** The #1 silent cache-killer is a timestamp or
  "today's date" interpolated near the top of context — which our `currentDate` system
  context does. Keep volatile values (dates, run IDs) *after* the stable block, never
  inside it.
- Verify with `usage.cache_read_input_tokens`; if it's 0 across repeated runs, a silent
  invalidator is in the prefix. (See `claude-api` skill → prompt-caching.)
- Stacking caching (≈90% off repeat input) is the single highest-leverage knob for any
  workload that reuses big context — which describes every one of our repos. ([Finout](https://www.finout.io/blog/anthropic-api-pricing), [hidekazu-konishi](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html))

### C. Right-size the model per job — **high impact, low effort**
We default everything to Opus 4.8. Most of our *routine* AI work is mechanical and does
not need a frontier model:
- **Doc-integrity / link checks** (`tools/check-docs.py` gating), changelog tidying,
  "did anything change?" status sweeps, roster field validation → **Haiku 4.5**
  ($1/$5 per MTok — 5× cheaper in, 5× cheaper out than Opus) or the **local t630 model**
  (≈ free). 
- **Statement composition, schema reasoning, sales copy, architecture decisions** →
  keep on Opus 4.8 / Sonnet 4.6.
- Model routing is described industry-wide as "the single biggest cost lever," with the
  rule of thumb *route ~70% of queries to the cheapest adequate model* for 60–80%
  savings. ([buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026), [zenvanriel](https://zenvanriel.com/ai-engineer-blog/llm-api-cost-comparison-2026/))

### D. Batch the non-urgent work — **medium impact, low effort**
Anything that doesn't need an answer *now* — monthly statement pre-renders, bulk
classification of leads, doc audits across all repos — goes through the **Message
Batches API at 50% off**, results within 24h. Batch + caching stack. ([Finout](https://www.finout.io/blog/anthropic-api-pricing))

### E. Scope work smaller — **medium impact, zero cost**
"Refactor the login function in `auth.ts`" beats "refactor the auth module": less
context pulled, fewer tokens, fewer wrong turns. Long chat threads are a hidden drain —
every turn re-reads the whole thread. Start fresh sessions for unrelated tasks;
`/compact` or summarize long ones. ([Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/), [MindStudio](https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage))

### F. Make routines self-silencing — **medium impact, low effort**
A scheduled run that finds nothing should cost as little as possible and say nothing.
Gate the expensive Opus reasoning behind a cheap first pass (Haiku/local: "has anything
changed since last run?") and only escalate to Opus when the cheap pass says yes.

---

## 3. Hybrid: local LLM + Claude API

We are **already half-built for this** — the t630 runs LiteLLM (stage 10) with a
reasoning ladder: `local-reason` (deepseek-r1:1.5b, t630 CPU), `cloud-gpu-reason`
(full R1 on a rented GPU), `cloud-overflow`. The gap is that this ladder serves the
*homelab LLM router*, not our *dev / business* AI workflow. Extend the same idea:

**The routing decision has three axes** (the 2026 consensus): *data sensitivity*,
*task complexity*, *availability*. ([SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/), [dev.to](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b))

| Task | Route to | Why |
| ---- | -------- | --- |
| Real customer PII in `customers/` (roster, sidecars) | **Local (t630)** | Privacy rule — keep real names/figures off third-party APIs where a local model suffices |
| Link/anchor checks, lint, "what changed" sweeps, commit-message drafts | **Local or Haiku** | Mechanical, short-context, error-tolerant |
| Statement composition, schema design, sales/brand copy, ADR reasoning | **Claude (Opus/Sonnet)** | Quality-sensitive, customer-facing, the product |
| Long-context (>~3K tokens), strict output format, multi-step reasoning | **Claude** | Exactly where open models degrade — don't route these local ([SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)) |

**Concrete next step:** add a `business`/`dev` model group to `10-ai-orchestration/config.yaml`
that mirrors the reasoning ladder, and point internal tooling (doc checks, the glue in
stage 11) at the local tier first, Claude as fallback. The honesty/privacy rules in the
`customers` repo make local-first the *correct* default there, not just the cheap one.

**Caveat (don't over-rotate):** the t630 is a 16GB Carrizo thin client; heavy
chain-of-thought models cook it (already a known issue). Keep local to small, fast,
short-context jobs; let Claude own anything that earns or touches a customer.

---

## 4. Better prompting

General, high-yield habits (these reduce *re-work* tokens, which dwarf prompt length):
- **State the goal and constraints up front, in one well-specified turn.** Opus 4.8 is
  autonomous and does best with the full task spec given once, rather than dragged out
  over many clarifying turns. Ambiguous, progressively-revealed prompts burn the most
  tokens.
- **Give the *reason*, not just the request** ("I'm building X for Y; they need Z; so:
  …"). It lets the model connect the task to the right context instead of guessing.
- **Drop aggressive instruction language.** "CRITICAL: you MUST…" over-triggers on
  current models and produces longer, hedgier output. Plain imperatives work better.
- **Ask for the deliverable, not a survey of options** — unless you want options.

### Critique of the prompt that spawned this doc
The request was, paraphrased: *"Locate inefficiencies in our PROCESS… reduce token use…
better prompting… leverage other AI… hybrid local + Claude… ANYTHING that could help…
search the web… keep UP TO DATE… check the news… also tell me if THIS prompt is
inefficient."* Honest assessment:
- **Strengths:** clear domain, explicitly invites web/current sources, asks for a
  self-critique (good instinct), names the candidate solution space (hybrid, prompting,
  token use).
- **Inefficiencies:**
  1. **Unbounded scope** ("ANYTHING that could help") invites a sprawling, expensive
     answer. A scoped version ("top 5 levers ranked by $ saved, with the one quick win
     I should do this week") gets a tighter, cheaper, more actionable result.
  2. **No success criterion / budget.** "Reduce token use" — by how much, measured how?
     Give a target ("halve our monthly Claude spend without slowing statement
     production") so the answer can prioritise.
  3. **Mixed altitudes** in one prompt: strategy ("hybrid architecture") + tactics
     ("better prompting") + ops ("check the news"). Splitting these into separate,
     cheaper runs (some on Haiku) would cost less than one big Opus pass.
  4. **"Keep UP TO DATE… day by day"** in a one-shot prompt is a mismatch — freshness is
     a *recurring routine*, not a single answer. (This doc + a scheduled monthly re-check
     is the right shape; see §7.)
- **Tighter rewrite:** *"You're our AI-cost reviewer. In ≤1 page: the 5 highest-$ levers
  to cut our Claude spend across the 7 repos, ranked, each with effort and the first
  action. Use current (2026) sources for any pricing claim. Flag the single quick win
  for this week."*

---

## 5. Current best practices & news (June 2026)

Pricing/feature facts confirmed against the bundled `claude-api` skill (cached
2026-06-04) and corroborated by current web sources:

- **Model line & rates (per MTok in/out):** Fable 5 $10/$50 · **Opus 4.8 $5/$25** ·
  Sonnet 4.6 $3/$15 · **Haiku 4.5 $1/$5**. Opus/Sonnet now carry a **1M-token context
  window at standard pricing** (no long-context premium). ([aipricing.guru](https://www.aipricing.guru/anthropic-pricing/), [Calcis](https://www.calcis.dev/pricing/anthropic))
- **Prompt caching:** ~90% off cached reads (Opus cached read $0.50 vs $5.00). Highest-
  leverage knob for repeated-context workloads. ([Finout](https://www.finout.io/blog/anthropic-api-pricing), [AI Cost Check](https://aicostcheck.com/blog/ai-prompt-caching-cost-savings))
- **Batch API:** flat 50% off, ≤24h. Stacks with caching. ([Finout](https://www.finout.io/blog/anthropic-api-pricing))
- **Adaptive thinking + `effort`:** on Opus 4.6+/Sonnet 4.6 the old fixed
  `budget_tokens` is gone; use `thinking:{type:"adaptive"}` and dial `effort`
  (`low`→`max`). For routine routine-runs, **lower `effort`** is a direct token saver —
  reserve `high`/`xhigh` for coding/agentic and quality-sensitive work.
- **Hybrid is mainstream:** the reference 2026 stack is exactly ours — **LiteLLM gateway
  + Ollama local + Claude cloud tier**, routed by sensitivity/complexity/availability,
  with quoted 60–80% cost cuts. ([SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/), [MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs))
- **Claude Code specifically:** the repeated 2026 advice is (1) lean CLAUDE.md, (2)
  short-scoped tasks, (3) fresh/compacted sessions, (4) skills for on-demand context —
  all of which map directly to §2 above. ([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage), [Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency), [agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage))

---

## 6. Quick-win checklist

This week, in order:

- [ ] **Trim the NARF/ZORT preamble** from "read 9 files" to "read `portfolio.md`;
      read the rest on demand." (≈ −8K standing tokens/session, DESIGN repo.)
- [ ] **Move the `currentDate` / volatile values out of the cacheable prefix** so prompt
      caching actually hits; confirm via `cache_read_input_tokens`.
- [ ] **Downgrade mechanical scheduled routines** (doc checks, status sweeps) to Haiku
      or the t630 local tier; keep Opus for statements/decisions.
- [ ] **Gate this routine itself**: cheap "did anything change?" pass first, escalate to
      Opus only on a hit.
- [ ] **Batch** the monthly statement pre-renders and any cross-repo audits (50% off).
- [ ] **Add a `dev`/`business` group to `10-ai-orchestration/config.yaml`** mirroring the
      reasoning ladder; route `customers/` PII work local-first per the privacy rule.

---

## 7. Review log

### 2026-06-14 — initial audit (NARF, scheduled routine)
First pass. Headline: ~13.3K-token startup tax per DESIGN-repo session is the dominant
inefficiency, not prompt phrasing. Standing context is cacheable/tierable/downgradable,
so the upside is large (est. 50–80% on routine spend). Six quick wins logged in §6.
**Open follow-ups:** (a) instrument actual monthly Claude spend by repo so we can
measure these levers instead of estimating; (b) revisit pricing rows monthly — the
landscape moves weekly.
