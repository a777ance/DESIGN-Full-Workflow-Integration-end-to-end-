# Process efficiency review — user ↔ AI (Claude) workflow

**Date:** 2026-06-28 · **Author:** NARF (AI CTO) · **Status:** recommendations, not yet ratified

Brief: find inefficiencies in how we (founder ↔ Claude) actually work — token waste,
prompting, and where local AI / a hybrid stack should carry load. Findings are ordered
**highest payoff first**. Numbers below are measured against this repo as of the date above.

---

## TL;DR — the five that matter

1. **The session-start tax is the biggest leak.** Opening this repo loads ~1,100 lines
   (~13K tokens) *before you type a word* — CLAUDE.md (295) + the 4 NARF files + the 6 ZORT
   files (805 lines together). You pay it on every session regardless of the task. **Fix:
   load on demand, not on start.** Est. saving: 60–80% of fixed per-session input.
2. **We are cache-busting our own biggest file.** CLAUDE.md says update `portfolio.md` at
   *every* session end. That file is also a mandatory *start* read — so the largest static
   block changes every session and never earns a cache hit. Prompt-cache reads cost **0.1×**
   input; a stable prefix is a 90% discount we're throwing away.
3. **We run Opus on everything, including routines.** This very review is running on Opus
   4.8. Monitoring/triage/log-reading should default to Haiku or Sonnet and escalate to Opus
   only for real reasoning. Opus↔Haiku is roughly a **10–12× price gap** per token.
4. **We already own a local LLM router and barely use it for our own work.** The t630 runs
   LiteLLM (`:4040`) + a reasoning ladder (`local-reason` deepseek-r1:1.5b, `cloud-gpu-reason`).
   Classification, summarization, log triage, draft generation, and *anything touching real
   customer data* (the `customers` repo) should go local first. Industry hybrid setups report
   **60–83% cost cuts** doing exactly this.
5. **The brief itself is expensive to answer.** "ANYTHING that could help… search the
   web… check the news" with no scope forces a wide, token-heavy sweep. A tighter prompt
   would have gotten the same answer for a fraction of the cost (see *Prompting*, last).

---

## A. The session-start tax (measured)

| What loads every session | Lines | Driver |
| --- | --- | --- |
| `CLAUDE.md` (this repo) | 295 | auto-injected |
| NARF reads (portfolio, roadmap, tech-debt, decisions) | ~part of 805 | CLAUDE.md §5 |
| ZORT reads (portfolio, decisions, metrics, runway, budget + MARKETING ctx) | ~part of 805 | CLAUDE.md §6 |
| **Total before first instruction** | **~1,100** | **~13K tokens** |

The CLAUDE.md mandates *ten* file reads at session start "regardless of task." A session
that only touches stage 06 still pays for the full CFO runway and budget files.

**Fixes (in order):**

- **Demote the mandatory reads to a lookup table.** Replace "At session start, read X, Y, Z"
  with "When working on finance, read `docs/ai-cfo/`; when on roadmap, read `docs/ai-cto/`."
  Claude pulls them only when the task needs them. This is the single highest-payoff change.
- **Split the role state into a tiny always-file + on-demand detail.** Keep a ~30-line
  `portfolio-snapshot.md` (current phase, top 3 priorities, open blockers) as the only
  start-read; move the long-form history into files read on demand.
- **Trim CLAUDE.md to a router.** 295 lines is a brain-dump where a lookup table belongs.
  Keep: house style, the stage map, the verification list, and *pointers*. Move prose
  ("why this tool at each stage") to the docs it already points at. Target < 120 lines.
- **De-duplicate the house-style block.** The identical ~20-line "ordering & typography"
  section is copied into **6** CLAUDE.md files. Maintain it once (e.g. a
  `docs/house-style.md`) and have each CLAUDE.md link to it. Saves edits-in-six-places and
  per-repo tokens.

## B. Stop defeating prompt caching

Cache reads are **0.1×** input and the break-even is two calls (Anthropic docs). Our static
context (CLAUDE.md + reference docs) is a perfect cache candidate — *if it stays byte-stable*
within a session/day.

- **Move the volatile bit to the end.** Anthropic caches the longest stable *prefix*. Put
  the churning content (today's status, the session log) *after* the stable reference, not
  woven through it, so the prefix keeps hitting cache.
- **Batch the session-end writes.** Updating `portfolio.md` every session keeps the big file
  hot. Append session notes to a separate cheap log; reconcile into `portfolio.md` weekly.
- **For API/automation work, turn on 1-hour cache writes** when a routine fires repeatedly
  within the hour (it costs 2× write, but 0.1× on every subsequent read in the window).

## C. Model tiering (we default too high)

Current behavior: Opus for everything, including scheduled routines and doc edits.

| Task class | Right tier | Why |
| --- | --- | --- |
| Monitoring, log triage, "did anything change?" routines | **Haiku** | cheap, fast, no deep reasoning needed |
| Doc edits, refactors, statement composition, normal coding | **Sonnet** | the workhorse; ~5× cheaper than Opus |
| Architecture, multi-repo reasoning, gnarly debugging, this kind of review | **Opus** | escalate *into* it, don't default to it |

- **Set scheduled routines to Haiku/Sonnet explicitly.** This review didn't need Opus until
  the synthesis step.
- **In Claude Code: start sessions on Sonnet, `/model opus` only when stuck.** "Start on
  Sonnet, escalate to Opus" is now the consensus 2026 default.
- **Use `/clear` between unrelated tasks and `/compact` when context drifts** rather than
  letting one long session accumulate (and re-pay for) stale context.

## D. The hybrid stack — use the box we already built

`localDNS` stage 10 already runs LiteLLM + Open WebUI + a reasoning ladder on the t630. Right
now it's framed as a product/lab feature; it should also be *our own first stop* for cheap
and sensitive work. The decision is three questions in order (sensitivity → complexity →
availability):

| Route there first | Examples in this portfolio |
| --- | --- |
| **Sensitive** (must not leave the house) | anything reading `customers/` real roster + stats, statement data, `.env` shaped questions |
| **Cheap & bounded** | classify a lead, summarize a call note, draft a "Handled For You" line, lint docs, first-pass grep/triage |
| **Escalate to Claude API** | multi-repo reasoning, the actual statement-generator logic, anything where an error ships on a kept document |

- **Put a router in front, fail closed.** LiteLLM already does fallback routing: local model
  first, Claude on miss/overflow — except for sensitive data, which must *never* fall over to
  cloud. The existing `cloud-overflow` rung is the pattern; add a `sensitive-local-only` rung
  with no cloud fallback.
- **Local for embeddings/classification/summary; Claude for reasoning.** This split is where
  the documented 60–83% savings come from — don't send a 2-line classification to Opus.
- **Caveat (honesty rule):** local drafts touching a customer-facing Statement still get a
  Claude/ human review pass before they ship. Cheap-to-draft ≠ cheap-to-ship.

## E. Structural / workflow

- **Batch related work in one warm session** instead of one-task-per-session — the context
  is already loaded; reuse it before `/clear`.
- **Plan mode before expensive multi-file changes** (Shift-Tab twice) — planning first beats
  re-doing; rework is the most expensive token there is.
- **Subagents for fan-out, not for one-liners.** Spawning a subagent for a quick grep costs
  more in startup than it saves. Use them when a task genuinely splits into parallel reads
  (e.g. "audit all 7 repos for X") — then they keep the junk out of the main context.
- **Skills/hooks for the repeated rules.** The house-style conventions and the "run
  `check-docs.py` before commit" rule are deterministic — encode them as a hook/skill so
  they don't burn instruction tokens (and reasoning) every time.

## F. Prompting — including the brief that triggered this

The request that generated this doc was, paraphrased: *"Find inefficiencies in our process.
Reduce token use. Better prompting? Leverage other AI, hybrid local + Claude. ANYTHING.
Search the web, check the news. Thanks!"*

What it does well: states the goal, grants tool latitude (web), and explicitly invites a
critique of itself. What costs tokens needlessly:

- **No scope or budget.** "ANYTHING that could help" + "search the web" + "check the news"
  is an open mandate → a wide sweep. A bounded version gets ~the same answer cheaper, e.g.:
  > "Audit our Claude usage for the top 5 token sinks. Assume I already know the basics
  > (caching, model tiering). Focus on what's specific to *our* repos and the t630 LLM
  > router. Web-check only things that changed in the last 60 days. One page, ranked."
- **Two asks in one.** "Fix the process" and "critique this prompt" are separable; splitting
  them lets the cheaper one run on a cheaper model.
- **Politeness costs ~nothing — keep it.** "Thanks!" is a rounding error; don't optimize
  manners. The expensive words are the *unbounded* ones, not the warm ones.
- **Give the model an off-ramp.** Add "if the answer is 'no meaningful waste found,' say so
  in one line" so a routine can return cheap when there's nothing to report.

A reusable template for this kind of ask:
> *[Goal] · [What I already know — skip it] · [Scope + recency bound] · [Output shape &
> length] · [Model hint if you have one] · [Permission to return early if empty].*

---

## Recommended order of action

1. Demote the 10 mandatory session-start reads to on-demand (biggest single win). **(A)**
2. Stop updating `portfolio.md` every session; weekly reconcile + a tiny snapshot file. **(B)**
3. Set routines/monitoring to Haiku/Sonnet; reserve Opus for reasoning. **(C)**
4. Route sensitive + cheap work to the t630 LiteLLM router, fail-closed on sensitive. **(D)**
5. Trim CLAUDE.md to a router; de-dupe the house-style block to one file. **(A)**

Items 1–3 are config/doc edits with no new infrastructure and recover the most tokens for
the least effort. Item 4 leans on infrastructure that already exists.

## Sources (web, checked 2026-06-28)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Token-saving updates on the Anthropic API — Claude blog](https://claude.com/blog/token-saving-updates)
- [Steering Claude Code: skills, hooks, subagents and more — Claude blog](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [How to Run Local AI Models with Claude Code to Cut Costs by 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM Auto Routing — docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
