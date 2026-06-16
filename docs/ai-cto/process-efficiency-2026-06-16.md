# AI Process Efficiency Review — 2026-06-16

A scan of how we (the founder) and the AI (Claude Code) actually work together, hunting for
token waste, better prompting, and places our own local LLM fleet should be carrying load
instead of the Claude API. Produced by a scheduled routine. Findings are ordered
**highest-leverage first**.

> **House-style note:** this is a time-based review log, so newer reviews go *above* this one
> when they're written. See finding #5 — that same newest-first rule has a hidden cost when a
> file is fed to a cached LLM context.

---

## TL;DR — the five that matter

1. **The billing floor moved under us (June 15, 2026).** Headless Claude Code, GitHub Actions,
   and third-party/scheduled agents are now billed as **metered API credits**, *not* off the
   Max subscription. Every scheduled routine — including the one that wrote this — now spends
   real per-token money. This makes everything below worth doing.
2. **Routines run on the wrong model.** This routine ran on **Opus 4.8 (1M context)**. A
   "scan + summarize + write a report" job is Sonnet/Haiku work. Opus on a 1M window is the
   single most expensive way to do it.
3. **The biggest per-session sink is the session-start read fan-out**, not the work itself.
   Our CLAUDE.md files order ~10+ mandatory file reads *before any task starts* — re-paid on
   every run, in an ephemeral container that keeps no cache between runs.
4. **CLAUDE.md files are ~58 KB (~15K tokens) and load every turn.** They're well-written but
   carry prose that belongs in README. Trimming the prepended-every-turn layer is free savings.
5. **Our "newest-first" house style fights prompt caching.** Prepending to the top of a log
   invalidates the cached prefix on every change. For any file that becomes a *cached* LLM
   context, append-to-bottom is 90% cheaper on re-reads.

---

## 1. The billing change — why this review suddenly pays for itself

As of **2026-06-15**, Anthropic moved the Agent SDK, **headless Claude Code, Claude Code GitHub
Actions, and third-party agents** off subscription limits onto a **separate monthly credit
billed at API rates** (~$20 Pro / $100 Max-5x / $200 Max-20x, then metered).

Practical consequence for us: our **scheduled routines and any GitHub-Action-driven Claude runs
are now a metered line item.** Interactive Claude Code in the terminal still draws on the
subscription; the unattended automation does not. So the cost-control target is specifically the
*automated* surface — exactly the routines we've been adding.

**Action:** treat each scheduled routine as a budgeted job. Decide per routine: does it need a
frontier model, or can it run local (#6) or on Haiku? Audit how many routines are armed and on
what cadence.

## 2. Right-size the model per routine (biggest one-line win)

This routine is configured on `claude-opus-4-8[1m]`. The 1M context is pure overhead for a job
whose inputs are a few config files and six web searches.

- **Reserve Opus** for genuinely hard reasoning (architecture, gnarly debugging, the operator
  economics math).
- **Default routines to Sonnet 4.6**; drop scan/summarize/lint/format routines to **Haiku 4.5**.
- **Never attach the 1M context variant to a routine** unless it is actually reading >200K
  tokens of material. The 1M tier carries a price premium for capacity we aren't using.
- New lever: **`effort: low` frontmatter on skills** and lighter effort settings cut tokens
  substantially on routine work with little quality loss.

Rough order-of-magnitude: moving a recurring scan routine from Opus-1M to Haiku is a
double-digit-X cost cut for the same output.

## 3. Kill the session-start read fan-out (the silent tax)

Our CLAUDE.md files instruct, before any task:

- DESIGN: read `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md` (NARF) **and** 6
  more files for ZORT (CFO) at session start.
- localDNS / MARKETING / customers / homelab: each points at its own `ai-cto/context.md` + hub.

That's a large, **mandatory** read every session — and because the web/routine container is
**ephemeral and cached fresh per run**, we re-pay it every single time with zero carry-over.

**Actions:**
- Make the reads **conditional, not unconditional**: "read X *when the task touches finances*,"
  not "read all six at session start." Most routines touch one domain.
- Keep a single **compact state file** (a few hundred tokens: phase gate, top 3 priorities, open
  blockers) that a session reads instead of four full logs. Let the agent open the full log only
  when it needs detail.
- For multi-repo questions, **delegate to a subagent** so the heavy reads accumulate in the
  subagent's context and only the conclusion returns to the main thread — it doesn't bloat the
  parent's running context (and cost) for the rest of the session.

## 4. Slim the CLAUDE.md layer (loaded on every turn)

CLAUDE.md is prepended to context **every turn**, so size there is multiplied by conversation
length. Current sizes:

| Repo | CLAUDE.md |
| ---- | --------- |
| localDNS | ~20.5 KB (326 lines) |
| DESIGN | ~18.0 KB (295 lines) |
| MARKETING | ~10.7 KB (214 lines) |
| customers | ~4.1 KB |
| homelab | ~2.9 KB |
| Azure-lab | ~2.3 KB |

The full house-style block (identical ~25 lines) is duplicated verbatim in all six. The
localDNS and DESIGN files carry deploy-path tables and topology that belong in README and are
re-read into context on turns that never touch them.

**Actions:** keep CLAUDE.md to the briefing + pointers; move the deploy-path table, the full
topology, and the known-issues catalog to README/INSTALL-NOTES and *link* them. Compress the
shared house-style block to 3 bullet lines + a link to one canonical copy. Target: each
CLAUDE.md under ~150 lines. (Net: smaller fixed cost on **every** turn of **every** session.)

## 5. The "newest-first" convention vs. prompt caching (non-obvious)

Our house style mandates **newest-at-top** for every log/changelog/decision file. That's great
for a human skimmer. But prompt caching keys on an **exact, stable prefix** — cache reads cost
~10% of base input. **Prepending to the top changes the prefix and invalidates the whole cached
context** on every update; appending to the bottom keeps the prefix stable and keeps the cache
hot.

This only bites for files that are actually fed as a **cached LLM context** (e.g. anything the
LangGraph supervisor / RAG index re-reads, or a doc pinned into a system prompt). It does *not*
matter for files only humans read.

**Action:** keep newest-first for human-facing docs; for any file that becomes a cached model
context, either store it append-only (newest-last) and render the reversed view for humans, or
split the volatile "latest" section out so the stable bulk stays cacheable. Also: keep
volatile tokens (timestamps, "current date") **out of cached prefixes** — a "Current time" line
in a system prompt invalidates the cache every request.

## 6. Use the fleet we already built (hybrid is built — routines don't use it)

`localDNS/10-ai-orchestration/` is a genuinely good hybrid: LiteLLM front door, local Ollama
tiers (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason` deepseek-r1:1.5b), a rented-GPU
heavy tier, Claude as **overflow only**, and a LangGraph supervisor with a deterministic privacy
gate. The architecture matches 2026 best practice (route simple→local, reserve frontier for hard
work; hybrid setups report 60–80% cost cuts).

**The gap:** our *Claude Code routines* bypass it and go straight to Opus. The recurring cheap
work this routine just did — "search the web, summarize, draft a report" — is exactly the
60–70% of tasks the hybrid guide says should run **local**.

**Actions:**
- Stand up a **local first-pass** for recurring scan/summarize routines: a t630 cron that runs
  `local-smart` over the inputs and writes a draft, escalating to Claude **only when it flags
  something non-trivial.** Claude reviews/finishes instead of doing the whole job.
- This is the pattern we already designed for the reasoning ladder — extend it from "chat" to
  "routines."
- Privacy bonus: the deterministic gate already guarantees sensitive (customer) data never
  leaves the box. Recurring work over `customers/` data is *especially* a local-first job.

## 7. Prompting hygiene (cheaper turns, fewer re-reads)

From current best-practice writeups, the levers that actually move the needle:

- **Batch related changes into one instruction** — "do A, B, and C" reads the codebase context
  once; three separate prompts re-read it three times.
- **`/clear` between unrelated tasks; `/compact` (or the newer micro-compaction) within a long
  one** — stale history is re-read on every subsequent turn.
- **Cap tool output** (e.g. 8K) so a chatty command doesn't flood context.
- **Point, don't paste** — name the file and let the agent open the relevant span rather than
  pasting whole files into the prompt.
- **Scope the task** — an open-ended task fans out unpredictably (see #8).

## 8. Critique of the prompt that launched this routine

The asking prompt was, paraphrased: *"Locate inefficiencies in our process. Reduce token use.
Better prompting. Leverage other AI. Hybrid local/Claude. ANYTHING that could help. Search the
web. Keep up to date. Check the news."*

What's inefficient about it, and the fix:

- **Unbounded scope.** "ANYTHING that could help" gives the agent no stopping rule, so it
  explores wide and long — the most expensive failure mode on a metered routine. → State the
  question and a budget: *"Find the top 5 token-cost inefficiencies in our scheduled-routine
  usage and propose fixes. ≤8 web searches. Write to `docs/ai-cto/process-efficiency-<date>.md`.
  Notify only if you find something material."*
- **No deliverable named.** Without a target file the result lives only in a transcript nobody
  reads (this is a scheduled routine — there's no human watching). → Always name an output
  artifact for an unattended routine.
- **"Check the news / keep up to date" with no source set** invites broad searching. → Pin it:
  *"Check the Claude Code release notes + Anthropic release log; ignore the rest."*
- **Runs on Opus-1M.** A scoped version of this is a Haiku/Sonnet job (#2).
- **Cadence unstated.** "Keep up to date, day by day" implies daily — daily Opus-1M web-research
  routines are the exact pattern the new billing punishes. → Weekly, on Haiku, is plenty for a
  best-practices scan; reserve frontier+manual for when it finds something.

A tightened version would cost a fraction and produce the same artifact.

---

## Concrete next actions (in order)

1. **Audit armed routines** — list every scheduled/Action-driven Claude job, its model, and its
   cadence. Anything on Opus-1M doing scan/summarize → move to Haiku/Sonnet. *(biggest $ win,
   post-June-15)*
2. **Add a stopping rule + output artifact + model floor to each routine's prompt** (see #8).
3. **Make session-start reads conditional** and add a compact `state.md` per hub (#3).
4. **Trim CLAUDE.md** to briefing + links; dedupe the house-style block (#4).
5. **Route recurring scan/summarize routines through the local fleet first**, Claude as
   reviewer/overflow (#6).
6. **Flag the caching caveat** in the house-style note so newest-first isn't applied to cached
   model contexts (#5).

## Sources

- [Manage costs — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude June 15 billing change explained](https://www.pravinkumar.co/blog/claude-june-15-billing-change-explained-2026)
- [Claude Code updates — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-code)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude cost optimization 2026: Batch API + prompt caching](https://pecollective.com/tools/claude-pricing-guide/)
- [Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid cloud-local AI workflow cost optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [23 tips for Claude Code token saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [How to reduce Claude Code token usage (8 methods, 2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code subagents — practical 2026 guide](https://nimbalyst.com/blog/claude-code-subagents-guide/)
