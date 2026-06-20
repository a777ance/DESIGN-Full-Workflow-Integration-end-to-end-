# AI Process Efficiency — token & workflow review

A standing review of how we spend tokens working with Claude (and where a cheaper model or
a better-shaped prompt would do the same job). Newest review at the top, per house style.

This doc is also the **diff target for the scheduled efficiency routine**: each run should
compare the field against the latest entry below and only raise a hand (notify) when something
material has changed — not re-derive the whole list every day. See "How to run this as a
routine" at the bottom.

---

## Review — 2026-06-20

### TL;DR — the three levers that matter for us, in ROI order

1. **Trim the context we pay for on *every* session.** Our `CLAUDE.md` files and the mandatory
   NARF/ZORT session-start reads are loaded before a single useful token of work. This is our
   single biggest recurring cost and it's almost entirely fixable.
2. **Use the hybrid router we already built.** The t630 runs LiteLLM + Ollama + a cloud-GPU
   tier (`localDNS` stage 10). ~60–70% of our AI work (doc summaries, link checks, classify,
   reformat, first-draft prose) is "simple" and can run on the local model for ~free, reserving
   the Claude API for actual reasoning. We have the pipes; we're just not routing through them.
3. **Lean on prompt caching and model tiering** instead of always reaching for Opus.

Industry numbers for context: hybrid local/cloud routing cuts LLM spend **60–80%**; RouteLLM
hit **95% of frontier quality sending only 14% of requests to the big model**; prompt caching
gives a **~90% discount** on repeated context. None of this is exotic anymore — it's table
stakes in 2026.

---

### 1. Context bloat — what we pay before we ask anything

**The problem, measured in our repo:**

- `DESIGN/CLAUDE.md` is **295 lines**. Anthropic's own cost guidance: *"Aim to keep CLAUDE.md
  under 200 lines — only essentials. CLAUDE.md is loaded at session start; specialized
  instructions belong in skills that load on demand."*
- A scheduled/web session injects **all repo `CLAUDE.md` files at once** (this routine received
  six of them). Most of that is irrelevant to any single task.
- The **NARF (CTO) ritual** mandates reading `portfolio.md` (155) + `roadmap.md` (64) +
  `tech-debt.md` (23) + `decisions.md` (131) = **~370 lines every session**. The **ZORT (CFO)
  ritual** adds six more files. That spend is paid whether or not the session touches strategy
  or money.

**Fixes (highest ROI first):**

- **Split each `CLAUDE.md` into a lean core (<200 lines) + on-demand Skills.** Move the parts
  that aren't needed every turn into `skills/<name>/SKILL.md`, which load only when invoked:
  - the full **house-style typography/ordering** block (repeated verbatim in *every* repo) →
    one shared `house-style` skill;
  - the **NARF/ZORT session-start reading rituals** → a `cto-session` / `cfo-session` skill the
    session calls *only when the task is strategy/finance*, instead of an unconditional read;
  - the **nftables deploy checklist**, the long **verification command lists**, and the
    deploy-path tables in `localDNS` → a `deploy` skill.
  - Keep in core only: what the repo is, the one or two invariants, and pointers.
- **Make NARF/ZORT reads conditional, not mandatory.** "Read these four docs *if the task
  touches the portfolio*" instead of "at session start, read…". This alone removes ~370+ lines
  of input from routine non-strategy sessions.
- **Scope sessions to one repo.** A routine that only audits `localDNS` shouldn't be loading the
  `MARKETING` and `customers` CLAUDE.md. Where the harness allows, point the session at a single
  working dir.

### 2. Use the router we already own (hybrid local + Claude)

We are paying frontier prices for work a local model does fine. `10-ai-orchestration` already
has the reasoning ladder (`local-reason` deepseek-r1:1.5b on the t630, `cloud-gpu-reason` on a
rented GPU, `cloud-overflow`). Extend that routing discipline to *how we work*, not just chat:

- **Local tier (free, on-box):** link checking, `check-docs.py`-style passes, reformatting to
  house style, Z→A sorting, classification, first-draft prose, summarizing a long doc before
  Claude sees it, "does this file mention X" lookups.
- **Claude Sonnet (default for real work):** most coding/editing, multi-file edits, writing
  that ships to a customer surface.
- **Claude Opus (reserve):** architecture/ADR decisions, cross-repo reasoning, anything where a
  wrong turn is expensive. *Don't default to Opus.*
- **Haiku for subagents:** verbose/mechanical side tasks (`model: haiku` in subagent config).

Rough portfolio split the literature assumes: ~60–70% simple, ~20–30% moderate, ~10% needs a
frontier model. If even half our simple work moves to the local box, that's the bulk of spend.

### 3. Prompt caching & model tiering

- **Claude Code caches automatically** (system prompt, CLAUDE.md, tools). The practical rule:
  **don't edit `CLAUDE.md` mid-session** — every edit invalidates the cache and you re-pay full
  price for the whole prefix on the next turn.
- **For our own LiteLLM/Open-WebUI calls**, set `cache_control` on the big stable blocks (system
  prompt, a pasted spec, the roster schema). Cache reads are **0.1×** input price; a 1-hour TTL
  write is 2× — worth it for anything reused within the hour.

### 4. Claude Code tactics we should adopt (from the official cost guide)

- `/clear` between unrelated tasks; `/compact Focus on …` to steer summarization; `/context` to
  see what's eating the window; `/usage` to track spend per skill/subagent/MCP.
- **Lower thinking effort for simple tasks** — extended thinking is billed as *output* tokens and
  the default budget is large. `/effort` low, or `MAX_THINKING_TOKENS=8000`, on mechanical work.
- **Hooks to pre-filter** — a `PreToolUse` hook that greps logs/test output to errors-only turns
  a 10k-line dump into a few hundred tokens. (We already gate on `check-docs.py`; same idea.)
- **Subagents for verbose ops** — run `check-docs.py`, log scans, dependency audits in a subagent
  so only the summary returns to the main window.
- **Prefer CLI over MCP** where both exist (less per-tool context); disable unused MCP servers;
  MCP tool defs are deferred by default — keep it that way.

---

## How to run this as a routine (so the routine isn't itself wasteful)

The original ask — *"locate inefficiencies… search the web… check the news… keep up to date
day by day"* — is a great one-time brief but an **expensive recurring one**: run verbatim on a
schedule it re-does full web research every time and notifies even when nothing changed.

Make the recurring version cheap and quiet:

1. **Scope + diff.** Run 1–2 targeted searches (e.g. "Claude Code cost feature changelog",
   "Anthropic pricing change"), compare against the latest review above, and **only notify on a
   material delta.** Silence when nothing changed is the correct, kind outcome.
2. **Deliverable is fixed:** append a dated entry here; don't re-explain the basics each run.
3. **Cadence:** weekly is plenty for "keep up to date" — daily mostly notifies noise.

### A tighter version of the original prompt

> *"Weekly: check for changes since the last entry in `docs/ai-cto/ai-process-efficiency.md`
> that affect our token cost — Claude Code cost features, Anthropic pricing, local-model
> routing. Run ≤3 web searches. If something material changed, append a dated entry and notify
> me with the one-line delta and the action it implies. If nothing changed, do nothing."*

Why it's better: bounded search budget, a concrete diff target, an explicit "do nothing" exit,
and a fixed deliverable — versus the open-ended "ANYTHING that could help / check the news,"
which (per the cost guide) is exactly the kind of vague prompt that triggers broad, expensive
exploration.

---

## Sources (2026-06-20 review)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Anthropic Prompt Caching in 2026: Cost, TTL, Latency](https://aicheckerhub.com/anthropic-prompt-caching-2026-cost-latency-guide)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Model Routing in 2026 — Digital Applied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
