# Process efficiency review — human ⇄ AI workflow

**Author:** NARF (AI CTO) · **Date:** 2026-06-22 · **Status:** recommendations, not yet adopted

A review of how we *spend tokens and attention* working with Claude across the A777ance
repos — where the process is wasteful, and the concrete moves that recover the most for the
least effort. Findings are ordered by payoff (biggest win first). Most of these are config
or habit changes, not code.

The headline: **we already own the expensive piece of the hybrid story** — a LiteLLM router
on the t630 (`localDNS` stage 10) with a local reasoning ladder. The opportunity is to *use*
it, not build it.

---

## TL;DR — the five moves, by payoff

| # | Move | Effort | Est. saving | Where |
| - | ---- | ------ | ----------- | ----- |
| 1 | **De-duplicate `CLAUDE.md`; scope sessions to one repo** | 1 hr | 30–50% of per-turn overhead | all repos |
| 2 | **Right-size the model: Sonnet/Haiku default, Opus on demand** | habit | 40–80% on routine turns | all repos |
| 3 | **Route mechanical work to the local LLM we already run** | 1 day | 60–70% of "simple" tasks → ~$0 | `localDNS` stage 10 |
| 4 | **Lean on prompt caching + the 1-hour cache tier** | config | 30–90% of input cost | API jobs |
| 5 | **Batch the non-interactive jobs (statements, stats, link-checks)** | 0.5 day | 50% on those jobs | stages 06/08/11 |

---

## 1. The `CLAUDE.md` tax (biggest, cheapest win)

Every turn re-sends the whole `CLAUDE.md` for the active repo. Ours are large
(DESIGN's is **295 lines, ~3,500 tokens**) and the **House style** block is copy-pasted
**verbatim into all six repos**. A 3,500-token memory file costs 3,500 tokens *on every
single turn* — a long session pays it hundreds of times.

Worse: a broad, cross-repo prompt (like the one that triggered this review) can pull *all
six* CLAUDE.md files into context at once — ~15k+ tokens of standing instructions before a
word of work.

**Do:**
- Cut each `CLAUDE.md` to stable essentials: how to build/test, the hard invariants, the
  pointers to deeper docs. Move the rest into the README/`docs/` it already links to.
- Pull the identical **House style** block into one canonical file
  (`DESIGN/docs/house-style.md`) and have each repo's `CLAUDE.md` link to it instead of
  inlining it. One edit, six repos, ~15 fewer lines × 6 on every turn.
- **Scope a session to one repo.** Don't open a session against all seven at once unless
  the task is genuinely cross-cutting. Multi-repo scope multiplies the standing-context tax.
- Run `/context` periodically to see where tokens actually go (system prompt, tools,
  memory, history).

## 2. Right-size the model

This routine runs on **Opus 4.8 (1M context)** — the most expensive default we could pick
($5/$25 per M tok). Most turns don't need it.

- **Default to Sonnet** for day-to-day edits and Q&A; reach for **Opus only** for deep
  architecture, tricky refactors, or ambiguous reasoning.
- **Scheduled/mechanical routines** (link-checks, log triage, status sweeps, *this* review's
  data-gathering) should run on **Haiku** or the local model — not Opus.
- Opus 4.8 **Fast mode is now ~3× cheaper** than on 4.7 ($10/$50 for 2.5×-speed frontier),
  and 4.8 adds **effort controls** and more efficient tool-calling (fewer steps per task).
  Turn effort *down* for routine work.
- The **1M context window is on by default** — convenient, but a full window is a full bill.
  Big context is a tool for specific jobs, not a resting state. Keep tasks small; start fresh
  sessions instead of letting one balloon.

## 3. Use the hybrid router we already built

We don't need to *build* a local/cloud split — `localDNS` stage 10 already has it: **LiteLLM
gateway + Ollama-style local models + a rented cloud GPU + Claude cloud**, with a reasoning
ladder (`local-reason` → `cloud-gpu-reason` → `cloud-overflow`). Industry consensus for 2026:
**60–70% of agent requests are simple** (classification, extraction, summarization, intent,
formatting) and run fine on a local open-source model at ~$0/inference. Smart routing cuts
total inference cost 60–80% with minimal quality loss.

**Do:**
- Route to the **local model** for: doc-link triage, log/Handled-For-You summarization, draft
  copy, classification/tagging of leads, "is this comment actionable?" — the cheap 60–70%.
- Reserve **Claude** for code reasoning, architecture, and anything customer-facing where
  quality is the product.
- **Fix TD-14 first.** The router's privacy fallback is open: a `sensitive`-tagged task can
  fail over from `local-reason` to `cloud-overflow` (Claude cloud) because `allow_cloud=False`
  isn't enforced at the LiteLLM failover layer. Give `local-reason` a **local-only fallback
  (fail closed)** before pushing more traffic through it — otherwise routing *more* work
  locally widens a privacy hole.

## 4. Prompt caching — and mind the 5-minute TTL

Prompt caching cuts input cost **60–90%** on repetitive workloads. Two things to get right:
- **Stable content first, volatile last.** Put the unchanging system prompt / CLAUDE.md /
  schema up front so the expensive prefix is byte-identical and cache-reusable; keep the
  small changing bit at the end.
- **The default cache TTL dropped to 5 minutes in early 2026**, which quietly raised effective
  costs 30–60% for slow/interactive workloads — the cache expires between turns if you pause
  to think. For long working sessions, use the **1-hour cache tier**; for batch runs, structure
  so reads land inside the window.
- Instrument the cache-read vs. cache-creation token counts the API returns; a high
  read:create ratio means it's working.

## 5. Batch the non-interactive jobs (50% off)

The **Batch API gives ~50%** off for anything that doesn't need an answer *right now*. Good
fits in our pipeline:
- Monthly **statement generation** (stage 06) and the nightly **stats collection** (`localDNS`
  collect tools) — already scheduled, already non-interactive.
- Bulk **doc-link checks** (`tools/check-docs.py` is mechanical — local model or batch, never
  Opus).
- Any **bulk roster/CRM enrichment** (stage 08).

---

## On the prompt that triggered this review

The triggering prompt was, frankly, a **kitchen-sink prompt** — and a good teaching example
of the anti-pattern, especially ironic for a *token-reduction* request:

> "Locate inefficiencies… Anything you could possibly think of… ANYTHING that could help.
> Search the web… Look for best practices… Keep UP TO DATE… Check the news."

What makes it expensive:
- **No scope** — "anything" + "ANYTHING" invites unbounded fan-out (web + news + all repos).
- **No deliverable spec** — no format, length, or destination, so the agent guesses.
- **No budget** — no token/time ceiling and no "good enough" bar, so it over-researches.
- **Vague freshness** — "check the news / day by day" implies re-running expensive searches
  with no cadence defined.

**A tighter version of the same ask:**

> "Review our human⇄AI workflow for token waste. Deliverable: a ranked list of the top 5 fixes
> with effort and estimated savings, written to `docs/ai-cto/process-efficiency-review.md`.
> Ground it in our actual stack (LiteLLM router, the CLAUDE.md files). Do **up to 4** web
> searches for 2026 best practices; cite them. Run on Haiku/Sonnet, not Opus. Stop at the
> ranked list — don't implement. Budget ~15 min."

That version is scoped, has a format and a home, caps the research, picks a cheap model, and
defines "done." Same outcome, a fraction of the spend.

**General prompting habits that save tokens:**
- State the **deliverable and its destination** up front (file path, length, format).
- Give a **budget and a stop condition** ("top 5", "≤ 4 searches", "don't implement").
- **Pick the model deliberately** in the request — don't let a mechanical task ride Opus.
- **Scope to the repo(s) that matter**; don't invoke all seven for a one-repo question.
- Prefer **one well-specified prompt** over an open-ended one you'll re-steer five times
  (each re-steer re-sends the whole growing context).

---

## Suggested next actions

1. **TD-14** — fix the router's fail-closed privacy fallback (P1, blocks move #3).
2. Add a tech-debt item to **de-duplicate House style** into `docs/house-style.md` and trim
   the CLAUDE.md files (move #1).
3. Set a team habit: **scheduled routines default to Haiku/local**, Opus is opt-in (move #2).
4. Audit the statement/stats jobs for **Batch API** eligibility (move #5).

---

## Sources (2026)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude Prompt Caching in 2026: the 5-minute TTL change — DEV](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Best practices for Claude Code — Docs](https://code.claude.com/docs/en/best-practices)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid LLM Routing: Ollama + Claude API Without Quality Degradation — DEV](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8)
- [Claude Opus 4.8 release: effort controls, cheaper fast mode — The New Stack](https://thenewstack.io/claude-opus-48-release/)
