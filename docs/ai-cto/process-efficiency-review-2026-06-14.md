# Process-efficiency review — user↔AI workflow (2026-06-14)

*A scheduled-routine audit of how we spend tokens and human attention across the
A777ance repos. Findings are grounded in this repo's own artifacts plus current
Anthropic API behaviour (verified 2026-06-14) and 2026 best-practice sources.*

**TL;DR — the three biggest wins, in order:**

1. **Cut the session-start context tax.** Our seven `CLAUDE.md` files total ~58 KB
   (~14.6 K tokens). When a session touches multiple repos, all of them load
   *before the first instruction is read*. Trim + split → est. 40–60% off the fixed
   per-session cost.
2. **Collapse the NARF/ZORT daily-review cadence.** Two full agent sessions every
   day, each re-reading 4–6 state files and committing a "session update," is the
   single largest *recurring* spend. Move to event-triggered + weekly, and have the
   routine stay silent on no-change days. Est. 50–70% fewer review-session tokens.
3. **Route by task, not by reflex.** We already run a local+cloud LLM router
   (stage 10). Push the cheap, high-volume work (triage, link-checking, log
   summaries, draft passes) to the local model or Haiku, and reserve Opus for
   reasoning. Industry data shows 60–80% cost reduction from smart routing alone.

---

## 1. What costs us tokens today (observed, not theoretical)

| Source | Measured | Why it's a cost |
| ------ | -------- | --------------- |
| `CLAUDE.md` × 7 | ~58 KB ≈ **14.6 K tokens** | `localDNS` (2,728 words) and `DESIGN` (2,608 words) alone are ~9.5 K tokens. Cross-repo sessions load all of them up front, every time. |
| Session-start reading list | DESIGN §5 → 4 CTO files; §6 → **6** CFO files + MARKETING context | Each role re-reads the same portfolio/decisions/metrics/runway/budget every session. |
| Review-file accumulation | **19** CFO reviews + **10** CTO reviews (and counting) | `2026-06-04` alone has 10 ZORT reviews. These get re-read by future sessions. |
| Dual daily agents | NARF + ZORT each commit a "session update" **every day** | 2 long sessions/day × (big CLAUDE.md + reading list + write-back). |

The pattern: **a large, fixed prologue is paid on every run, and two runs happen
daily whether or not anything changed.** That's the lever.

---

## 2. Recommendations

### A. Shrink and tier the context that loads every session

- **Keep `CLAUDE.md` lean — it's billed before you type a word.** Move the
  reference-grade material (full stage maps, deploy-path tables, the long
  known-issues lists) into the existing `README.md`/`network-context.md` and have
  `CLAUDE.md` *point* to them. A 5 K-token `CLAUDE.md` costs 5 K tokens on every
  turn; a 2 K one costs 2 K. Target: each `CLAUDE.md` under ~1,500 tokens, detail
  one hop away.
- **Don't make a session read six state files to start.** Replace the §5/§6
  "read these 6 files" ritual with **one** rolled-up `portfolio.md` snapshot
  (current status + open items + pointers). Read the deep files only when a task
  actually touches them. This is the "minimum necessary context" principle —
  every token you don't carry is one you never pay for, wait on, or cache.
- **Cap and roll the review logs.** 29 dated review files is a growing re-read
  surface. Keep the last ~7 days live; archive older ones into a single
  `reviews/ARCHIVE-<month>.md` (or just rely on git history). Newest-first per
  house style, but bounded.

### B. Fix the cadence, not just the size

- **Two daily full-session reviews is the costliest recurring item.** Move NARF
  (CTO) and ZORT (CFO) to **event-triggered + a single weekly digest**: run on a
  real change (a PR merged, a metric crossed, a decision logged), otherwise skip.
- **On no-change days, the routine should send nothing and write nothing.** A
  scheduled run that finds "same as yesterday" and still commits a session-update
  spends tokens *and* human attention for zero signal. (This very review will
  notify only because it found something; a quiet day should be quiet.)
- **One combined CTO+CFO pass** where the agendas overlap, instead of two
  independent sessions each re-loading the same portfolio.

### C. Use the cost levers the API already gives us

Grounded in current Anthropic API behaviour (2026-06-14):

- **Prompt caching** — cache reads cost ~**0.1×** input price; writes 1.25× (5-min)
  / 2× (1-hour). For a stable prologue (the CLAUDE.md + portfolio prefix that
  repeats across our runs) this is up to **~90%** off the repeated portion. *Caveat
  that bites us:* caching is a **prefix match** — any byte change invalidates the
  rest. So keep the stable prologue **frozen and first**; never interpolate the
  date/run-id/"today is…" into the top of `CLAUDE.md`. The Opus minimum cacheable
  prefix is 4,096 tokens, so the prologue has to clear that bar to cache at all.
- **Batch API** — **50% off** for anything not latency-sensitive: the nightly
  stats roll-ups, bulk statement drafting, multi-household passes. These are the
  textbook batch workload.
- **Context editing / compaction / the memory tool** — for the long agent runs,
  let stale tool results clear and let cross-session state live in a memory file
  instead of re-reading the whole portfolio each time.
- **`/compact` proactively** in long interactive sessions — it rewrites history
  into a shorter, cacheable prefix, making the rest of the session cheaper.

### D. Route work to the cheapest model that can do it (we're half-built here)

We already have the hard part: a LiteLLM router on the t630 with a local
reasoning model (`deepseek-r1:1.5b`) and a cloud-GPU fallback. Extend the same
idea to *which Claude tier* handles a task:

| Task class | Send to | Rationale |
| ---------- | ------- | --------- |
| Link-check, lint, log/diff summary, status triage, classification | **Local model** or **Haiku 4.5** ($1/$5 per MTok) | High volume, low sensitivity, no deep reasoning. |
| Draft passes, routine doc edits, first-cut copy | **Sonnet 4.6** ($3/$15) | Good quality at 40% of Opus output price. |
| Architecture/finance decisions, cross-repo reasoning, the gold-standard Statement logic | **Opus 4.8** ($5/$25) | Reserve the top tier for where it earns its rate. |

Current model IDs/pricing (per MTok in/out): Opus 4.8 `claude-opus-4-8`
$5/$25 · Sonnet 4.6 `claude-sonnet-4-6` $3/$15 · Haiku 4.5 `claude-haiku-4-5`
$1/$5. In Claude Code, the `opusplan` alias does a version of this automatically
(Opus for planning, Sonnet for code-gen). Published 2026 case studies put smart
routing at **60–80%** savings with negligible quality loss because the hard 10%
still goes to the strong model.

### E. Structural: subagents for the fan-out reads

Our cross-repo audits ("read all 7 repos, reconcile") are exactly what subagents
are for — push the wide search into a separate context window and keep only the
*conclusion* in the main session, instead of dragging seven repos' worth of file
dumps through the expensive main loop. (This routine used that pattern.)

---

## 3. About the prompt that launched this routine

The triggering prompt was effective at *intent* but expensive by construction,
and the same fixes apply to how we brief these routines generally:

- **"ANYTHING that could help… search the web… check the news"** is unbounded.
  Open scope invites broad, costly exploration. Give the routine a **scope + a
  stop condition + an output target** (e.g. "audit token spend in the AI-CTO/CFO
  loop; produce one ranked list of ≤5 fixes; write to `docs/ai-cto/`"). That alone
  would cut a run like this by a large margin.
- **State the deliverable and where it lands.** "Let me know" in a routine nobody
  is watching means the finding can die in an unread transcript. The durable
  outputs are a committed file (this one) and a push notification.
- **Front-load the facts, don't make the agent re-derive them.** Pointing the
  routine straight at the artifacts to measure (the CLAUDE.md sizes, the review
  cadence) is cheaper than "find inefficiencies anywhere."
- **One well-specified turn beats a vague one elaborated over many turns** — it's
  both cheaper and produces better output on current models.

A tighter re-statement of the same request:

> *"Weekly: measure token cost of the NARF/ZORT loop (CLAUDE.md + session-start
> reads + review files). Rank the top 5 reductions with est. savings. Write to
> `docs/ai-cto/process-efficiency-review-<date>.md`. Notify only if a new,
> actionable item appears since last week."*

---

## 4. Suggested order of operations

1. Trim the two largest `CLAUDE.md` (localDNS, DESIGN) to pointers — fastest,
   biggest fixed-cost win, zero behaviour change.
2. Replace the §5/§6 multi-file reading ritual with a single `portfolio.md`
   snapshot + on-demand deep reads.
3. Switch NARF/ZORT to event-triggered + weekly, silent on no-change days.
4. Turn on prompt caching for the stable prologue; move nightly roll-ups to the
   Batch API.
5. Extend the existing router to tier Claude calls (Haiku/local → Sonnet → Opus).

Items 1–3 need no new infrastructure and capture most of the savings. 4–5 build
on tools we already run.

---

*Keep this current — the model lineup, pricing, and caching/batch economics shift
fast; re-verify against the live Anthropic docs each time this routine runs.*

### Sources
- [Anthropic — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code — How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching)
- [Claude Code token optimization guide (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 tips for Claude Code token saving (2026)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid cloud-local LLM architecture (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid cloud-local AI workflow cost optimization (2026)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LLM request routing: GPT-4 vs Claude vs local (2026)](https://www.buildmvpfast.com/blog/llm-request-routing-gpt4-claude-local-models-2026)
- [Best practices for Claude Code subagents](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
