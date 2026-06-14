# AI Process Efficiency — audit & recommendations

**Owner:** NARF (AI CTO) · **First written:** 2026-06-14 · **Cadence:** revisit when a
material change lands (new Claude Code release, new model, new pricing). Stay silent
between changes — this is a living reference, not a daily log.

This is an audit of the **process between the founder and the AI** — token spend, prompting,
and where local compute can carry load — *not* a portfolio review. Findings are ordered by
leverage (biggest token/cost saving first). Dollar figures are order-of-magnitude.

---

## TL;DR — the five highest-leverage moves

1. **Tier the model.** Stop doing doc edits, link fixes, changelog reconciliation, and
   formatting on **Opus 4.8 / 1M**. Use Haiku/Sonnet for mechanical work; reserve Opus for
   architecture and money decisions. Single biggest cost lever — output on Opus is roughly
   **5–12× the price** of Haiku/Sonnet.
2. **Cut the session-start read fan-out.** NARF mandates 4 files + spoke context; ZORT
   mandates 6. Re-read every session, they're the dominant input cost. Collapse to **one
   cached START-HERE snapshot per persona**; pull detail on demand; **delegate multi-file
   reads to a subagent** so raw file text never lands in the main window.
3. **De-duplicate the house-style block.** The identical ~40-line "House style: ordering &
   typography" block is copy-pasted into **all 7 `CLAUDE.md` files**. In a cross-repo session
   every copy auto-loads. Factor it into one file and `@import` it; or trim to a one-line
   pointer. Kills both the token tax and the drift risk.
4. **Use the hybrid rig you already built — for dev chores, not just the product.** The t630
   LiteLLM router + Ollama tiers exist. Route cheap, non-sensitive chores (commit-message
   drafts, diff summaries, first-pass doc lint, tech-debt triage) to **local**. Reserve the
   Claude API/Code session for reasoning. **Caveat: TD-14 must be fixed first** (see §4).
5. **Make mechanical rules deterministic, not LLM-judged.** `check-docs.py` is the right
   pattern (Python, zero tokens). Extend it to enforce the house-style ordering and regenerate
   TOCs. Every rule a script can check is a rule the model shouldn't be spending tokens
   re-deriving — and getting wrong.

Combined, published case studies put savings from caching + model-tiering + local-offload at
**60–90%** of LLM cost (sources below). A 50–70% per-session reduction here is realistic.

---

## 1. Token sinks in the current process

### 1a. Session-start reading is the dominant input cost
`CLAUDE.md` §5/§6 instruct: at every session start read `portfolio.md`, `roadmap.md`,
`tech-debt.md`, `decisions.md` (NARF) **and** `portfolio.md`, `decisions.md`, `metrics.md`,
`runway.md`, `budget.md`, plus `MARKETING/.../context.md` (ZORT). That's ~10 files re-read on
every session, before any work begins. Most of it is unchanged turn-to-turn.

- **Fix:** maintain a single short `START-HERE.md` per persona — the 20-line snapshot that
  actually changes (current focus, top-3, open blockers). Read *that* every session. Pull the
  full `decisions.md` / `metrics.md` only when a task touches them.
- **Fix:** when you *do* need to sweep several files, spawn an **Explore subagent** to read and
  return the conclusion. Subagents have their own context window (June 2026: nestable up to 5
  deep) — the file bodies never enter, or pollute, the main thread.

### 1b. Seven duplicated house-style blocks
The "House style" block is verbatim in every `CLAUDE.md`. Per-repo that's fine; in a
**cross-repo session like this one, all seven auto-load** — several thousand tokens of pure
repetition, every session, plus a maintenance hazard (change it once = drift in six).

- **Fix:** one `docs/house-style.md`, referenced by `@docs/house-style.md` import in each
  `CLAUDE.md`, or reduced to a single pointer line. Single source of truth, loaded once.

### 1c. Prompt caching is being defeated, not used
Claude Code auto-caches stable prefix content (the long, stable `CLAUDE.md` is *good* for
this). But the session-start protocol that pulls fresh file contents each session, and long
exploratory threads, blow past the cache.

- **Fix:** front-load the stable stuff (already true), churn little once a task starts, and
  run **`/compact` proactively** before threads get long. June 2026 adds Rewind →
  **"Summarize up to here"** and API-side **context editing + the memory tool** —
  Anthropic benchmarks **84% token savings on long-running tasks** with those paired.
- **Fix:** run **`/usage`** — it now attributes spend to cache misses, long context,
  subagents, and per-skill/agent/MCP. Measure before optimizing; confirm cache is hitting.

### 1d. House-style conventions are token- *and* error-expensive for the model
Reverse-chronological logs, **Z→A** alphabetical lists, and "reverse the blocks, keep the
steps" walkthroughs are unusual. The model must re-derive them on every write and is
*more likely to get them wrong* — and rework is the most expensive tokens of all.

- **Fix:** keep these for customer-facing surfaces where they're a deliberate brand choice;
  relax or **lint them deterministically** for internal AI-facing docs so the model never has
  to reason about ordering.

---

## 2. Model tiering — the single biggest dollar lever

This session is **Opus 4.8 (1M ctx)** — the most expensive configuration, doing work that's
mostly doc maintenance. The right split (which your own `config.yaml` already encodes for the
*product* — `cloud-code` = Sonnet, `cloud-explore` = Opus — just apply it to the *dev session*):

| Work | Model |
| --- | --- |
| Architecture, financial reasoning, cross-repo strategy, ambiguous calls | **Opus 4.8** |
| Code, diffs, structured doc edits, reviews | **Sonnet 4.6** |
| Link fixes, formatting, changelog/TOC sync, classification, renaming | **Haiku 4.5** |

`/model` mid-session is the lever. Also drop the **1M context** unless a task genuinely needs
it — long-context requests bill at a premium and the `/usage` panel breaks it out.

---

## 3. Lean on local compute (the rig is already built)

Stage 10 ships a LiteLLM gateway (`ai.home.lan:4040`) fronting Ollama tiers on the t630:
`local-fast` (qwen2.5:3b), `local-smart` (qwen2.5:7b), `local-reason` (deepseek-r1:1.5b),
plus `local-embed`. This is the hybrid architecture the 2026 guides describe — and it's idle
for *dev-process* work.

**Route to local (free, private):** commit-message drafts, diff/PR summaries, first-pass
doc-lint and tone checks, tech-debt triage/classification, embedding the repos for RAG lookup
(Mímir's well is already scaffolded). The 2026 rule of thumb: **60–70% of agent requests are
simple** (classify/extract/format) and don't need a frontier model.

**Keep on Claude (cloud):** architecture, the honesty-rule judgment calls, anything touching
real customer data in the `customers` repo, final customer-facing prose.

> ⚠️ **Blocker — fix TD-14 before routing anything sensitive locally.** Today `local-reason`
> falls back to `cloud-overflow` (Claude cloud), so a `sensitive` prompt can egress if the
> local model is down — the gate isn't fail-closed at the LiteLLM layer. Until that's fixed,
> treat the local rig as **non-sensitive chores only**. (This is the top actionable in the
> 2026-06-14 portfolio review for exactly this reason.)

---

## 4. Deterministic over LLM wherever a rule is mechanical

`tools/check-docs.py` (link/anchor integrity, wired into CI) is the model to copy: a rule a
script enforces costs zero tokens and never drifts. Candidates to add:

- Regenerate each file's **Contents/TOC** from its headings.
- Validate the house-style **ordering rules** (newest-first sections, Z→A lists).
- Sync/lint the **CHANGELOG** entry shape.

Every one of these moves work off the token meter and removes a class of model mistakes.

---

## 5. This prompt's own efficiency (you asked)

The triggering prompt is motivating but **unscoped** — *"ANYTHING that could help,"* *"search
the web,"* *"check the news,"* *"keep UP TO DATE day by day."* For a **recurring routine** that
is the costliest possible shape: every run does broad, open-ended web research with steeply
diminishing returns, and produces a fresh essay whether or not anything changed.

Make it cheap and sharp:

1. **One lever per run, rotated.** Run N audits caching; N+1 audits model-tiering; N+2 audits
   local-offload. Narrow scope = short, deep, cheap.
2. **Diff, don't re-survey.** "What changed since the last run?" If nothing material changed,
   **send no notification and write nothing** — silence is the correct output for a healthy
   routine (and saves the whole run's tokens).
3. **Allowlist the sources.** Point web research at the Anthropic changelog + Claude Code docs
   (`code.claude.com/docs/en/changelog`) instead of re-searching the open web each time.
4. **Specify the output contract.** Target file, max length, format — so the model doesn't
   default to an exhaustive sweep.
5. **Lower the cadence.** Weekly beats daily here: the field moves fast, but *actionable*
   changes for a one-person shop don't land daily, and a daily open-ended research run is a
   standing token cost for mostly-null results.
6. **A reusable prompt skeleton:**
   > "Check {Anthropic changelog, Claude Code docs} for releases since {last-run date}
   > affecting token cost or context management. If none material, reply 'no change' and stop.
   > If yes: name the change, the one process tweak it enables here, and the file to edit.
   > ≤200 words. Don't re-derive what's already in `process-efficiency.md`."

---

## Sources (2026)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
- [Code with Claude 2026: new agent features (subagents, context editing) — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude memory tool guide](https://claudeapi.com/en/blog/dev-guides/claude-memory-tool-guide/)
- [Hybrid cloud-local LLM architecture guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI with Claude Code to cut costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Token optimization & cost management — IntuitionLabs](https://intuitionlabs.ai/articles/token-optimization-chatgpt-claude-costs)
- [LLM request routing: GPT-4 vs Claude vs local — buildmvpfast](https://www.buildmvpfast.com/blog/llm-request-routing-gpt4-claude-local-models-2026)
