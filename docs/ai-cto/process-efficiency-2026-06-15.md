# Process efficiency review — human ↔ AI workflow (2026-06-15)

A standing-watch review of how we work *with* Claude across the A777ance repos:
where tokens (and time) leak, what to change, and what to leave alone. Grounded in
current Claude Code / API behavior as of June 2026 and in our own setup. Sources at
the bottom.

**The one-line answer:** the biggest, cheapest win is *session hygiene* + *trimming
the always-loaded context* (CLAUDE.md and the "read these files at session start"
instructions). The second is *routing the cheap, bulk work to the t630's local LLM
router we already run* — the infrastructure is already standing. The third is leaning
on caching and batching we're probably already getting for free but should verify.

---

## A. What's actually costing us

### 1. The always-loaded context is heavier than it needs to be

Every Claude Code session loads that repo's `CLAUDE.md` *before the first word is
typed* — it's fixed overhead on every turn (mitigated by prompt caching, but the
first turn and every re-warm after a 5-minute idle pays it fresh). Current sizes:

| Repo | CLAUDE.md words | ≈ tokens |
| ---- | --------------- | -------- |
| localDNS | 2,728 | ~3,800 |
| DESIGN (this repo) | 2,608 | ~3,700 |
| MARKETING | 1,445 | ~2,000 |
| customers | 562 | ~800 |
| claude-code-homelab | 371 | ~520 |
| Azure-lab | 316 | ~440 |

Not catastrophic. But the *real* sink is the **session-start reading instructions**.
This repo's `CLAUDE.md` tells the agent to read, at session start: `portfolio.md`,
`roadmap.md`, `tech-debt.md`, `decisions.md` (NARF) **and** five ZORT files
(`portfolio.md`, `decisions.md`, `metrics.md`, `runway.md`, `budget.md`) **plus**
`MARKETING/docs/ai-cfo/context.md`. That's 10+ documents pulled into context on every
session — most of it uncached, most of it irrelevant to any single task.

**Fixes (in order of payoff):**
- **Make session-start reading conditional, not mandatory.** Change "At session start,
  read 1–4" to "When the task touches CTO state, read X; when it touches money, read
  the ZORT files." A doc-link change, costs nothing, saves thousands of tokens per
  session.
- **Split the giant CLAUDE.md into a thin always-loaded core + on-demand detail.**
  Claude Code reads `CLAUDE.md` always; everything else only when referenced. Keep the
  briefing to the rules + the map; push the long tables behind a link. (We already do
  this with README/network-context — extend the discipline to CLAUDE.md itself.)
- **Keep the prefix byte-stable.** Prompt caching is a *prefix match* — any change near
  the top of CLAUDE.md invalidates the cache for everything after it. Put the most
  volatile content (status lines, dates) at the *end*, never interpolate today's date
  into the header.

### 2. Session hygiene — the habits that quietly burn tokens

Token cost grows with conversation length: every turn re-sends the whole history.
The cheapest savings are behavioral, not technical:
- `/clear` when switching to unrelated work (stale context rides along otherwise).
- `/compact` (and the newer micro-compact) to summarize a long session instead of
  replaying it; `/recap` to resume without replaying.
- `/usage` (new in 2026) breaks down which component is eating tokens — run it when a
  session feels expensive.
- **Scope prompts tightly.** "Refactor the login function in `auth.ts`" pulls far less
  context than "refactor the auth module." Smaller scope = fewer tokens *and* better
  output.
- Don't take long breaks mid-session — a >5-min gap goes cold and re-warms the cache
  from scratch.

### 3. This prompt (the one that launched this review) — yes, it's inefficient

The triggering instruction was broad and open-ended ("ANYTHING that could help…
search the web… check the news"). That's fine for a scheduled scan like this one, but
as a *recurring* pattern it maximizes tokens: an unbounded research agent fans out
across many searches and pulls large pages into context. Tighter framings for next
time:
- **Name the lever.** "Audit CLAUDE.md sizes and session-start reads; propose cuts" is
  one cheap focused run instead of an open web crawl.
- **Cadence the web research.** Best-practice/news scanning genuinely does change
  week to week — but run *that* part monthly, not every invocation, and have it write
  findings to a doc (like this one) so we don't re-research from zero.
- **Separate "scan our setup" (cheap, local, frequent) from "scan the field" (web,
  monthly).** Two routines, two budgets.

---

## B. Hybrid local + Claude — we already own the hard part

We run a LiteLLM router (stage 10, `~/llm-router`) on the t630 with a reasoning ladder
(`local-reason` = deepseek-r1:1.5b on CPU; `cloud-gpu-reason` for heavy work) and Open
WebUI. That's exactly the gateway the industry now recommends for cost routing. The
move is to *use it as a router*, not just a chat UI:

- **Route the cheap, high-volume, low-stakes work to local models:** doc-link checking
  (`tools/check-docs.py` is already deterministic — no LLM needed there), first-draft
  summarization, classification/triage of leads or issues, "is this commit message
  sane," bulk reformatting. Industry rule of thumb: 60–70% of LLM calls are simple
  enough for local; hybrid setups report **60–80% cost reduction** with little quality
  loss.
- **Keep Claude for what it's best at:** the Statements' honesty checks, anything
  customer-facing, architecture decisions, code that has to be right the first time,
  long-horizon agentic work.
- **The decision axes are sensitivity, complexity, availability.** Sensitivity matters
  for us specifically: the `customers` repo holds real PII. Anything touching real
  household data is a candidate for *local-only* processing on the t630 — it never
  leaves the box. That's a privacy win, not just a cost one, and it lines up with the
  network-side "don't leak personal lookups" invariant we already hold in localDNS.
- **One caveat from our own CLAUDE.md:** don't run heavy reasoning models on the t630
  CPU (deepseek-r1:7b+ cooks the box). The ladder already encodes this — route heavy
  reasoning to Claude or the rented GPU, light bulk work to local.

This is a config-and-discipline change, not new infrastructure. The router is up.

---

## C. Caching & batching — verify we're getting the free money

Claude Code uses prompt caching automatically, but it's worth confirming we benefit:
- **Cache reads cost ~10% of input price; writes cost 1.25× (5-min) or 2× (1-hr).**
  Break-even is ~2 reads. For repeated work over the same big context (a CLAUDE.md, a
  Statement template, a schema), this is the single biggest API-side lever — up to 90%
  off the repeated portion.
- **Batch API = 50% off** for anything not latency-sensitive: monthly Statement
  generation across all households, bulk classification, overnight report runs. Stage
  06/08 batch jobs are the obvious fit.
- **If we ever build our own tooling on the API** (vs. Claude Code), the model split
  matters: Opus 4.8 ($5/$25 per Mtok) for hard work, Sonnet 4.6 ($3/$15) for
  high-volume production, Haiku 4.5 ($1/$5) for simple/fast. Don't default everything
  to the top tier.

---

## D. Current Claude model & price reference (June 2026)

| Model | ID | Input $/Mtok | Output $/Mtok | Note |
| ----- | -- | ------------ | ------------- | ---- |
| Fable 5 | `claude-fable-5` | $10 | $50 | Most capable; for the hardest long-horizon work only |
| Opus 4.8 | `claude-opus-4-8` | $5 | $25 | Default for hard/agentic work (current Claude Code default) |
| Sonnet 4.6 | `claude-sonnet-4-6` | $3 | $15 | Best speed/intelligence balance; high-volume production |
| Haiku 4.5 | `claude-haiku-4-5` | $1 | $5 | Fast, cheap; classification/simple tasks |

Prompt caching: read ~0.1×, write 1.25× (5-min TTL) / 2× (1-hr). Batch API: 50% off.
Newer API features worth knowing for any custom tooling: server-side **memory tool**
(curated facts persist across sessions, replacing replayed history) and **compaction**.

---

## E. Recommended next actions (cheapest first)

1. **Edit the session-start reading rules** in this repo's CLAUDE.md (§5 NARF / §6
   ZORT) from "always read N files" to "read when the task calls for it." ~10 min, big
   per-session saving. *(No tooling.)*
2. **Trim each CLAUDE.md to a thin core**; push long tables behind links. Re-run
   `tools/check-docs.py` after.
3. **Adopt session hygiene as a habit:** `/clear` between unrelated tasks, `/compact`
   on long ones, scope prompts to a file not a module.
4. **Turn the LiteLLM router into an actual router:** point bulk/low-stakes/PII work at
   local models; keep Claude for honesty-critical and customer-facing work.
5. **Move Statement generation and any bulk classification onto the Batch API** (50%).
6. **Split this routine** into a frequent cheap "scan our setup" run and a monthly
   "scan the field" web run that appends to this doc.

## F. What to leave alone

- Don't build local LLM into anything customer-facing yet — quality bar on the
  Statements is the product. Honesty rule wins over cost.
- Don't over-engineer a routing layer; the LiteLLM config already does it.
- Don't chase model-price micro-optimizations while the real money is in context size
  and session hygiene.

---

*Sources:* Anthropic Claude Code cost docs; prompt-caching guidance (MindStudio,
build-to-launch); hybrid local/cloud architecture guides (SitePoint, buildmvpfast,
MindStudio "run local models with Claude Code"); LiteLLM gateway comparisons; 2026
token-optimization playbooks (programstrategyhq, getmaxim, tokenoptimize); Claude Code
June 2026 changelogs (jangwook.net, MarkTechPost, releasebot). Pricing/model IDs
confirmed against the in-repo Claude API reference, 2026-06.
