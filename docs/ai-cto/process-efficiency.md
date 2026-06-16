# Human ↔ AI process efficiency — token & cost review

*First pass 2026-06-16 (NARF). Living doc; newest findings at the top per house style. This
is about how we **work with** the AI — not the product. Pair with `runway.md`/`budget.md`
(ZORT) for the dollar side.*

The headline: our biggest recurring waste isn't the model we pick, it's **how much fixed
context we re-send every turn** and **routing judgment-free work to a frontier model**. Both
are fixable this week with no new tooling — we already own the hybrid stack (LiteLLM reasoning
ladder on the t630). Everything below is ordered by payback.

Verified against current public guidance (Claude Code best-practices docs; Anthropic pricing
June 2026) — links at the bottom. Prices: Opus 4.8 $5/$25 per MTok, Sonnet 4.6 $3/$15, Haiku
4.5 $1/$5; cached input reads ~0.1×, cache writes ~1.25× (5m) / ~2× (1h); Batch API −50%.

---

## P1 — Stop re-sending fixed context every turn (biggest, cheapest win)

**The problem, measured here.** Our seven `CLAUDE.md` files total ~1,040 lines (~10K tokens),
and they load at the **start of every session**. On top of that, `DESIGN/CLAUDE.md` tells NARF
to read 4 docs at session start and ZORT to read 6 more — before any actual work begins. A
"quick question" can spend 20–30K tokens just hydrating. That cost recurs on every session,
forever, and it's the single largest lever we control.

**Fixes (in order):**

1. **Prune the CLAUDE.md files.** The bar (straight from Anthropic's own guidance): for each
   line ask *"would removing this make the AI make a mistake?"* If not, cut it. A bloated
   CLAUDE.md doesn't just cost tokens — past a point the model **ignores** instructions buried
   in the noise. `localDNS/CLAUDE.md` (326 lines, with the full deploy-path and verification
   tables) and `DESIGN/CLAUDE.md` (295) are the prime candidates. Move the reference tables
   (deploy paths, verification commands, the nftables checklist) into the files they describe
   and **link** to them; keep CLAUDE.md to the rules and the map.
2. **Convert "read these N files at session start" into on-demand skills.** The NARF (4-file)
   and ZORT (6-file) session-start rituals should be **Skills**, not standing instructions.
   A skill's one-line description sits in context; the full file loads only when the task
   actually touches CTO/CFO state. Today every localDNS deploy session also pays for the CFO
   reading list.
3. **Lean on prompt caching.** The CLAUDE.md + tool definitions form a stable prefix — exactly
   what prompt caching is for (cached reads ≈ 0.1× vs full price). On the API side set
   `ENABLE_PROMPT_CACHING_1H` for long sessions. Caveat: caching is a **prefix match** — if a
   CLAUDE.md interpolates anything per-session (a date, a status line), everything after it
   stops caching. Keep them byte-stable.

**Expected effect:** 40–70% fewer input tokens on a typical session, and better instruction
adherence as a bonus.

---

## P2 — Route judgment-free work off the frontier model (we already have the pipe)

We built the LiteLLM reasoning ladder precisely for this (`localDNS/10-ai-orchestration`), but
it's aimed at *reasoning depth*. Add a **task-type** split:

| Work | Send to | Why |
| ---- | ------- | --- |
| Classification, extraction, summarization, label/format, roster lookups, "is this paid?" | **local model** (deepseek-r1:1.5b / a local Haiku-class) via the router | Local models clear the quality bar here; cloud spend on these is pure waste. Industry hybrid setups cut 60–80% on exactly this traffic. |
| Drafting copy, statement prose, routine edits, codebase Q&A | **Sonnet 4.6** ($3/$15) | 40% cheaper than Opus, ample for non-judgment work |
| Architecture, multi-file changes, the hard agentic loops, anything customer-facing-and-irreversible | **Opus 4.8** | Reserve the premium model for where it pays |

**In Claude Code specifically:** default to Sonnet; use the `opusplan` alias (plan in Opus,
execute in Sonnet) for big changes instead of running Opus end-to-end. Don't downgrade silently
on anything that touches a kept document or real customer money — that's a judgment call, keep
it on Opus.

**Privacy guardrail (already a known bug):** TD-14 — a `sensitive`-tagged task can fail over
from `local-reason` to `cloud-overflow` (Claude cloud) if the local model is down. **Do not
expand local→cloud routing until TD-14 is fixed** (local-only fallback, fail closed). A cost
optimization that leaks private lookups is not a win.

---

## P3 — Batch the bulk, non-interactive jobs (−50%, no latency cost to us)

The Batch API is half price and we have natural batch workloads where nobody's waiting:

- **Monthly statement generation** across all households (stage 06) — the canonical batch job.
- **Doc-integrity / copy-variant / classification sweeps** — anything we'd loop over many rows.

Pair batching with prompt caching (shared system prefix across all rows) and the two discounts
stack toward ~90% off input on those runs. Keep interactive/agentic work on the live API.

---

## P4 — Session hygiene (cheap habits, real savings)

- **`/clear` between unrelated tasks.** A long "kitchen-sink" session re-reads its whole
  history every turn and degrades quality. One task, one context.
- **`/compact <focus>`** when a long single task fills up; **`/recap`** to resume without
  replaying the whole thread.
- **Subagents / the Explore agent for codebase research.** They read many files in a *separate*
  context and report back a summary — the file dumps never touch the main window. Use them for
  "how does X work across the repo" instead of reading 30 files inline.
- **Cap tool output** (e.g. max ~8K) and filter logs before the model sees them — grep the
  error lines, don't paste the whole log.
- **Two corrections rule:** if you've corrected the AI twice on the same thing, `/clear` and
  rewrite the prompt with what you learned. A clean start beats a polluted context.
- **Verification as a gate, not a vibe.** We already have `tools/check-docs.py` (and CI runs
  it). Tell the AI to run it before claiming done; a Stop hook makes it deterministic.

---

## P5 — Prompt better (specific beats sprawling)

Scope the ask: *"refactor the login function in auth.ts"* not *"refactor the auth module."*
Smaller scope = less context pulled = fewer tokens and tighter output. Point at files with `@`,
paste the actual error, name what "done" looks like. For big features, have the AI **interview
you** into a SPEC.md first, then execute it in a fresh session — far cheaper than discovering
the requirements mid-build across a bloated context.

---

## On the prompt that triggered this review

The triggering prompt was deliberately open-ended — *"ANYTHING that could help… anything you
could possibly think of."* That phrasing is the most expensive shape of request: it licenses
unbounded exploration, so the model fans out across the whole codebase and the open web before
it can converge. It cost more tokens than the answer needed.

The same ask, scoped, would have been cheaper and sharper, e.g.:

> "Audit our human↔AI workflow for token waste. Focus on: (1) recurring per-session context
> cost, (2) model/task routing given our LiteLLM ladder, (3) batch/caching opportunities.
> Give the top 5 fixes ranked by payback, each with a concrete action. Check current Anthropic
> pricing and Claude Code best-practice docs."

That keeps the "search the web / stay current" intent (which *was* worth doing — it surfaced
the 1h-cache flag, `opusplan`, `/recap`, and current prices) while bounding the fan-out.
General rule: ask for **a ranked short list with actions**, not an exhaustive survey, and name
the dimensions you care about. Save the open-ended version for when you genuinely want to be
surprised — it's a feature, just an expensive one.

---

## Sources (verified June 2026)

- Claude Code best practices — https://code.claude.com/docs/en/best-practices
- Reduce token usage — https://code.claude.com/docs/en/costs
- Anthropic pricing / caching / batch — https://www.finout.io/blog/anthropic-api-pricing
- Hybrid local+cloud routing economics — https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
