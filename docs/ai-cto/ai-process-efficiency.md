# AI process efficiency — how we work with Claude (and where it leaks)

*Review by NARF (AI CTO), 2026-06-15. Standing audit of the **process between the operator
and the AI** — token cost, prompting, and where our own hybrid router should be carrying
load it currently isn't. Re-run quarterly; LLM tooling moves weekly, so treat figures as
"as of June 2026."*

This is a process doc, not a time-based log, so it's ordered by **leverage — biggest
saving first.** Each finding has a concrete fix and a rough size.

---

## TL;DR — the five that pay

| # | Finding | Rough saving | Effort |
| - | ------- | ------------ | ------ |
| 1 | Our `CLAUDE.md` files are large; multi-repo sessions load **~15k tokens before a word is typed** | 30–50% of every turn's fixed cost | Low — trim + link out |
| 2 | We don't lean on **prompt caching** (90% off cached input), and our doc-churn habits break the cache | up to 90% on repeated context | Low — discipline |
| 3 | We **built a hybrid router and don't route to it** — Opus runs chores a 3B local model or Haiku should | 50–80% on routine work | Medium — wire `dispatcher.py` |
| 4 | **Scheduled routines run on Opus 4.8[1m]** end-to-end instead of triage-cheap-then-escalate | 60–90% per routine run | Medium |
| 5 | Our prompts are **open-ended** ("ANYTHING that could help"), inviting expensive wandering | 20–40% per task | Free — prompt habit |

---

## 1. The `CLAUDE.md` baseline is the silent tax

**What's happening.** A multi-repo session (this one included) auto-loads every repo's
`CLAUDE.md` on **every turn**:

| Repo | chars | ≈ tokens |
| ---- | ----: | -------: |
| localDNS | 20,472 | ~5,100 |
| DESIGN (this repo) | 17,987 | ~4,500 |
| MARKETING | 10,660 | ~2,650 |
| customers | 4,135 | ~1,000 |
| claude-code-homelab | 2,896 | ~720 |
| Azure-lab | 2,294 | ~570 |
| **Total** | **58,444** | **~14,600** |

That ~15k tokens is a **constant** — paid before any task, on every message, in every
session that spans repos. It is also the *least* cacheable content because we edit these
files constantly (house-style reorderings, known-issues churn), and every edit busts the
cache for the whole prefix.

**Why it's bloated.** `CLAUDE.md` is supposed to be the *briefing* — the authoritative
short summary — with detail living in `README.md` / context files that Claude reads **on
demand**. Ours have absorbed full deploy-path tables, full known-issues tables, verification
command blocks, and the entire house-style essay (repeated verbatim in all six files). Claude
only needs the house-style rules *once* and only needs the deploy table *when deploying*.

**Fix (low effort, high return):**
- **Deduplicate house style.** It's identical in all six files (~1,100 chars each ≈ 6,600
  tokens of pure duplication across a multi-repo session). Put the canonical copy in one
  place (the DESIGN hub) and have each `CLAUDE.md` carry a two-line pointer, not the essay.
- **Move reference tables out of `CLAUDE.md`.** The localDNS deploy-paths table and the
  nftables checklist are reference material — they belong in `README.md`/`INSTALL-NOTES.md`,
  which Claude reads when the task needs them. Leave a one-line "deploy paths: see README §C."
- **Target ~150 lines / ~1,500 tokens per `CLAUDE.md`.** Briefing + pointers only. That alone
  roughly halves the per-turn baseline.
- **Single-repo by default.** Don't add repos to a session you aren't touching this turn;
  each one is its full `CLAUDE.md` on every message.

---

## 2. Prompt caching — we're leaving 90% on the table

Cached input tokens bill at **~10% of the normal input price**, and a 1-hour cache TTL is
available (`ENABLE_PROMPT_CACHING_1H`). Claude Code caches automatically — **but only the
*stable prefix*.** The cache covers everything up to the first thing that changed since last
turn. Our habits work against it:

- Editing a `CLAUDE.md` mid-session busts the cache for the whole system prefix.
- Long, exploratory sessions that wander across repos keep mutating the prefix.

**Fix:**
- Keep `CLAUDE.md` edits to their own short sessions; do the *work* in sessions where the
  briefing is stable.
- `/clear` between unrelated tasks instead of carrying a stale 100k-token transcript whose
  prefix is re-sent (and re-priced) every turn.
- `/compact` at natural breakpoints on long tasks.
- For batch/non-interactive jobs, the **Batch API is a flat 50% off** and **stacks with
  caching** — see #4.

---

## 3. We built the hybrid router — now actually route to it

This is the big one, and it's *our own infrastructure not being used.* `localDNS` stage 10
already has: a LiteLLM front door, local `qwen2.5:3b/:7b` on the t630, a reasoning ladder, a
rented-GPU offload, **and a deterministic `dispatcher.py`** with a privacy gate. The
`ORCHESTRATION-BLUEPRINT.md` is excellent. The gap is that day-to-day work still goes
straight to Opus 4.8 by reflex.

**Industry rule of thumb (June 2026): 60–80% of agent requests are routine**, and routing
those to a cheap tier (local Ollama → Haiku 4.5 at ~$1/M) while reserving Opus ($5/M) for
genuinely hard reasoning **saves 50–80%** with no quality loss on the routine slice.

**What of *our* work is routine and should leave Opus:**
- The recurring **house-style chores** — reverse-chronological reordering, Z→A list sorting,
  Gill Sans stack insertion. These are mechanical; a local `qwen2.5:7b` or a `sed`/script does
  them. (Better still: most are lint rules, not LLM work — see #6 on `check-docs.py`.)
- **Commit-message drafting, changelog entries, known-issues reformatting** → `local-smart`
  or Haiku.
- **Link/anchor checking** → already a script (`tools/check-docs.py`); don't spend *any*
  model on what a deterministic check covers.
- **First-pass research / summarization** → `local-smart` or Haiku, escalate to Opus only for
  synthesis.

**Reserve Opus/Sonnet for:** cross-repo architectural reasoning, the Statements' honesty
judgments, security-sensitive review, anything where being wrong is expensive.

**Action:** make `dispatcher.py` the front door for non-interactive jobs (it already has the
`sensitive → local-only` privacy lock), and add a routing note to the portfolio so "which
model" is a rule, not a reflex. The privacy gate is a real bonus here — customer/roster data
*must* stay on the local tier, and the deterministic classifier already enforces that.

---

## 4. Scheduled routines: triage cheap, escalate rare

This very review is a scheduled routine — and it ran **entirely on `claude-opus-4-8[1m]`**,
the most expensive tier, including the cheap parts (listing files, counting chars, fetching
search results). That's the routine pattern to fix:

- **Two-stage routines.** Stage 1: a cheap model (Haiku or local) triages — "is there
  anything here worth a human's attention?" Stage 2: escalate to Opus **only if** stage 1
  says yes. A "check the news / health-check" routine that finds nothing should cost pennies,
  not a full Opus run.
- **Batch API for non-interactive routines.** Anything that doesn't need a live human in the
  loop (nightly doc audits, statement pre-rendering, this kind of review) qualifies for the
  **50%-off Batch API**, which **stacks with prompt caching**. Scheduled routines are the
  textbook batch case.
- **Right-size the context window.** The `[1m]` 1-million-token context is billed at a
  premium above 200k. A doc-audit routine never needs 1M; pin routines to the standard
  context tier unless a task genuinely needs the long window.

---

## 5. Prompting — scope beats breadth

**Critique of the prompt that triggered this review** (asked for directly): it was a
*divergent* prompt — *"Locate inefficiencies… Anything you could possibly think of… ANYTHING
that could help… Search the web… Check the news."* That phrasing is honest about wanting wide
coverage, but it is the single most expensive shape of request: it licenses unbounded tool
use, many web searches, and long output, with no stopping rule. Open-ended "do everything"
prompts are where 20–40% of a task's tokens evaporate.

**Make it cheaper without losing the value — a rewrite:**

> *"Audit our Claude usage for the top 3–5 token-saving wins. Prioritise by $ saved vs.
> effort. Use our existing localDNS stage-10 router in the recommendations. One web pass for
> 2026 best practices is enough — don't exhaustively browse. Deliver a ranked table + the
> single highest-leverage change to make this week. Cap: ~6 searches, ~1 page out."*

That keeps every bit of the intent (current, web-backed, hybrid-aware, actionable) while
adding a **budget, a deliverable shape, and a stopping rule.** General prompt habits that pay:

- **Bound the scope.** "Refactor the login function in `auth.ts`," not "refactor auth."
- **Name the deliverable and its size.** "A ranked table, one page" stops sprawl.
- **Set a tool budget.** "~6 searches max" prevents a research rabbit-hole.
- **State the model intent.** "This is mechanical — fine on a small/local model" lets the
  router (or a human) downshift.
- **One task per session; `/clear` between.** Don't let an unrelated transcript ride along as
  re-priced context.

---

## 6. Smaller wins worth banking

- **Lint, don't prompt.** `tools/check-docs.py` already gates broken links for free. Push
  *more* of the house-style rules into deterministic checks (a reverse-chron linter, a Z→A
  list checker). Every rule a script enforces is a rule no model has to be told or paid to
  apply — and the rule lives in CI, not in a 6× duplicated `CLAUDE.md`.
- **Output style.** Set a terse output style for routine/infra repos (less prose, lower
  comment density) — fewer output tokens, which are the *expensive* side ($/M output ≫ input).
- **Subagents are not free.** They isolate context (good for fan-out search) but a
  subagent-heavy workflow can burn ~7× the tokens of a single thread because each child reloads
  startup context (`CLAUDE.md` + MCP + skills). Use them for genuine parallel search, not as a
  default — and note this compounds #1: fat `CLAUDE.md` files make every subagent more
  expensive too.
- **MCP server hygiene.** Each connected MCP server injects its tool schemas into context.
  The GitHub MCP toolset alone is large; only attach servers a session needs.

---

## Recommended order of operations

1. **This week (free/low):** trim the six `CLAUDE.md` files — dedupe house style, move
   reference tables to README. Biggest, easiest win (#1).
2. **This week (habit):** adopt the scoped-prompt template (#5); `/clear` between tasks (#2).
3. **This month:** make scheduled routines two-stage + Batch API (#4).
4. **This month:** wire `dispatcher.py` as the front door for non-interactive jobs and write
   the routing rule into the portfolio (#3).
5. **Ongoing:** move house-style rules into `check-docs.py`-style linters (#6).

---

## Sources (June 2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Cost Optimization 2026: Batch API (50% off) and Prompt Caching (90% off)](https://pecollective.com/tools/claude-pricing-guide/)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Prompt Caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo.io](https://www.tembo.io/blog/claude-code-subagents)
- [Claude Code Agents in 2026: what parallel sessions actually cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [The Complete Claude Code Guide (2026): Context Engineering — generative.inc](https://www.generative.inc/the-complete-claude-code-guide-2026-planning-context-engineering-and-high-leverage-development)
- [What Is an LLM Router? — Morph](https://www.morphllm.com/llm-router)
- [LLM Cost Optimization: 5 Levers to Cut API Spend 70–85% — Morph](https://www.morphllm.com/llm-cost-optimization)
- [Best AI Model for Coding Agents in 2026: A Routing Guide — Augment Code](https://www.augmentcode.com/guides/ai-model-routing-guide)
- [LLM API Cost Comparison 2026 — zenvanriel.com](https://zenvanriel.com/ai-engineer-blog/llm-api-cost-comparison-2026/)
