# Process efficiency review — user ↔ AI (2026-06-15)

A review of how we work with the AI: where tokens and effort leak, what 2026 best
practice says, and what to actually change. Commissioned as a scheduled routine
("locate inefficiencies in our PROCESS… reduce token use… better prompting…
hybrid local LLM + Claude API… keep up to date").

> **Read the scale first.** Our current AI spend is **~$11–27/mo** against a
> **<$30/mo** target (`docs/ai-cfo/budget.md`). So the honest headline is *not*
> "we can save thousands." At our volume the dollar savings are cents. The reason
> to do this now is that **the habits we set at 1 customer are the habits we run at
> 50** — the Statement generator is designed to cost "about a penny a home," and the
> per-session context tax below is the part that *doesn't* stay a penny as we scale.
> Per the honesty rule, no inflated savings numbers appear in this doc.

---

## TL;DR — the five that matter

1. **Our CLAUDE.md files are large and load on every turn.** localDNS ~5,100 tok,
   DESIGN ~4,500 tok. 2026 guidance is to keep CLAUDE.md lean (the cited benchmark
   trims to ~300 tok of "only what Claude can't infer from the code"). We don't need
   to go that far, but we're carrying 10–15× that.
2. **The NARF/ZORT session-start reading lists are an unmetered tax.** DESIGN tells
   the AI to read **4 docs at start for NARF + 6 for ZORT** before any work. That's
   thousands of tokens spent every session whether or not the task touches them.
3. **We already built the hybrid router and aren't safely using it.** The LiteLLM
   reasoning ladder exists (`localDNS/10-ai-orchestration`), but **TD-14** means a
   "sensitive" task can fail over to cloud — so we can't trust it for the bulk-cheap
   work it was built for. Fix TD-14, then route summarize/extract/classify locally.
4. **We're not using the two biggest free levers: prompt caching (–90% on cached
   reads) and the Batch API (–50%).** The monthly statement run is a *textbook*
   batch job — non-interactive, scheduled, bulk. It should never pay interactive rates.
5. **Scheduled routines (like this one) burn tokens every run whether or not there's
   signal.** They earn their keep only if they notify on signal and stay silent
   otherwise. Audit which routines actually fire useful notifications.

---

## 1. Inefficiencies found in *our* setup (measured)

| # | Finding | Measured | Cost shape |
| - | ------- | -------- | ---------- |
| A | CLAUDE.md loaded every turn | localDNS ~5.1k, DESIGN ~4.5k, MARKETING ~2.7k tok | Per-turn, per-session |
| B | Session-start reading lists | NARF 4 docs + ZORT 6 docs (DESIGN) | Per-session, often unused |
| C | House-style block duplicated verbatim ×6 repos | ~302 tok/copy | **Maintenance** cost (one session loads one copy) — edit-in-6-places risk |
| D | Two personas (NARF/ZORT) | Each pulls its own doc set | Doubles session-start reads if both invoked |
| E | Unattended routines | this run + any `/loop` jobs | Per-run, regardless of signal |
| F | Hybrid router unusable for bulk | TD-14 privacy fallback gap | Forces cloud for work that should be local |

**Note on (C):** the duplication is a *maintenance* problem, not a per-session token
problem — a session in one repo only loads that repo's CLAUDE.md. But it means the
"Adopted 2026-06-05" house-style rules must be hand-synced across 6 files, which is
exactly the kind of copy-paste seam our own philosophy ("one source of truth") warns
against.

---

## 2. What 2026 best practice says — and our move for each

### Prompt caching (–90% on cached input)
Cache reads price at ~10% of base input. The rule: **stable prefix cached, volatile
content last.** Avoid timestamps in system prompts (they invalidate the cache at
midnight) and non-deterministic JSON key ordering in tool defs. There was a March 2026
Anthropic caching bug that inflated tokens 10–20×, so *measure*, don't assume.
- **Our move:** when the statement generator or any NARF/ZORT job calls the API
  directly, put the big stable context (CLAUDE.md, schema, templates) in a cached
  prefix and the per-home data last. Free win, zero quality cost.

### Batch API (–50%, all models)
Non-interactive, asynchronous workloads get half off. Opus 4.8 via batch ≈ $2.50/$12.50
per MTok.
- **Our move:** the **monthly statement build (Stage 06)** is the ideal batch job —
  scheduled, bulk, no human waiting. Run it through the Batch API, not interactively.

### Skills & subagents (–25–40%, context isolation)
Skills load only when invoked (vs. monolithic prompts); subagents run in their own
context window so verbose file/log output never lands in the main thread's bill.
- **Our move:** we already use Skills — good. For research-heavy routines like *this*
  one, do the web-search/file-sweep fan-out in **subagents** so only the conclusion
  returns to the main context. (This run did some of that via parallel search; next
  iteration should delegate the sweep to an `Explore`/`general-purpose` subagent.)

### Hybrid local + cloud routing (–60–80% on routed bulk)
The documented pattern is exactly ours: LiteLLM gateway + local (Ollama/deepseek) +
Claude cloud tier, routed by **data sensitivity, task complexity, availability.**
Send high-stakes / tool-calling / customer-facing work to Claude; send
summarize / extract / classify / draft-cleanup to the local model.
- **Our move:** **Fix TD-14 first** (give `local-reason` a local-only fallback so a
  sensitive task fails *closed*, never to cloud). Only then can we trust the router to
  carry bulk work locally on the t630, which is free electricity we already pay for.

### Model & mode selection
Opus 4.8 holds $5/$25; **Fast Mode dropped 3× to $10/$50.** Haiku remains the cheap
tier for mechanical work.
- **Our move:** don't default everything to Opus. Mechanical doc edits, link-checking,
  roster formatting → Haiku or local. Reserve Opus for design/architecture/ambiguous
  judgment. Use Fast Mode when latency matters and the task is frontier-hard.

### Context hygiene (Claude Code)
`.claudeignore`, `/compact` instead of long-running sessions, point at specific files
not whole repos, trim CLAUDE.md. Cited cases report 85–92% context reduction with no
quality regression.
- **Our move:** see §3.

---

## 3. Recommendations, prioritized

**P1 — do now (free, compounding)**
1. **Fix TD-14** — it's the gate on everything hybrid. Until sensitive fails closed,
   we can't route bulk to local safely.
2. **Move the monthly statement run to the Batch API** (Stage 06 / 11). Half price,
   zero downside for a scheduled job.
3. **Trim CLAUDE.md.** Target ≤ ~1,500 tok each. Push the long "why" prose into the
   already-existing `*-context.md` / README files (which load only when needed) and
   leave CLAUDE.md as the dense map + invariants. Keep the parts Claude *can't* infer.

**P2 — soon**
4. **Make session-start reading lazy.** Replace "read these 6 docs at start" with
   "read X *when the task touches* finance/architecture." Or collapse the portfolio
   hub into one short index the AI reads, fetching detail on demand.
5. **Single-source the house-style block.** Put it once (e.g. in
   `claude-code-homelab/templates/` or a shared snippet) and reference it; stop
   hand-syncing 6 copies.
6. **Enable prompt caching** on any direct API job (statement generator, NARF/ZORT
   batch runs): stable prefix cached, per-home data last, no timestamps in the prefix.

**P3 — hygiene**
7. **Audit scheduled routines** for signal-to-noise: a routine that never notifies, or
   notifies on noise, is pure burn. Keep the ones that catch real conditions.
8. **Right-size the model per task** (Haiku/local for mechanical, Opus for judgment).
9. Adopt `.claudeignore` + `/compact` discipline in interactive sessions.

---

## 4. Was *this* prompt efficient? (you asked)

Honestly — it's a good *intent*, loosely *aimed*. What cost extra effort:

- **Unbounded scope.** "ANYTHING that could help… search the web… check the news" is
  open-ended, so the agent has to guess where to stop. A scheduled routine with no
  budget tends to over-research. Better: *"Find the top 3 token-efficiency wins for our
  setup; web-check only if it changes the ranking; ≤1 page."*
- **No success criterion or output target.** "Locate inefficiencies" doesn't say
  *deliverable, length, or where to put it.* Naming the artifact ("write to
  `docs/ai-cto/…`, ≤1 page, P1/P2/P3") removes a whole round of guessing.
- **Two questions in one** (analyze the process *and* critique the prompt). Fine, but
  state them as a numbered list so neither gets dropped.
- **Stale-by-design contradiction.** "Keep UP TO DATE, this changes day by day" inside
  a *standing* routine means every run re-does the web sweep. Cheaper: cache the
  best-practice findings in a doc (this one), and have the routine only re-check the
  delta ("what changed since 2026-06-15?").

A tighter version: *"Monthly: re-check this doc's recommendations against current
Anthropic pricing + Claude Code release notes. If a recommendation changed or a new
lever appeared, update the doc and notify me with the diff. Otherwise stay silent.
≤1 page, cite sources."*

That turns an open-ended essay request into a cheap delta-check — which is the same
"stable prefix, volatile content last" discipline, applied to the *prompt* instead of
the cache.

---

## Sources (2026)

- [Prompt Caching for Claude — cut API bill 60% (AI Magicx)](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Claude Cost Optimization: Batch (50% off) & Prompt Caching (90% off)](https://pecollective.com/tools/claude-pricing-guide/)
- [Anthropic API Pricing 2026 — caching, batch, optimization (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude Opus 4.8 Pricing 2026 (Finout)](https://www.finout.io/blog/claude-opus-4.8-pricing-2026-everything-you-need-to-know)
- [Claude Code Token Optimization — the $1,600 bill (Build to Launch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to Reduce Claude Code Token Usage: Skills (Agensi)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Skills and Subagents Reduce Prompt Bloat (newline)](https://www.newline.co/@Dipen/claude-skills-and-subagents-reduce-prompt-bloat--f2920804)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Claude API Cost Optimization for Enterprises 2026 (Cleveroad)](https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/)
