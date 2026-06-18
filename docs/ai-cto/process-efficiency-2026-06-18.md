# Process efficiency review — user ↔ AI token & workflow

**Date:** 2026-06-18 · **Author:** NARF (AI CTO routine) · **Status:** recommendations, not yet adopted

A scheduled routine asked: where are the inefficiencies between the user and the AI, and
how do we cut token use? Findings are ranked by payoff. Each carries a concrete fix and a
rough token estimate. Sources at the bottom; all checked 2026-06-18 (this space moves fast —
re-verify before acting on anything older than ~30 days).

---

## TL;DR — the five highest-payoff moves

1. **Stop running sessions from `/home/user`.** Every session there ingests *all six*
   repos' `CLAUDE.md` (~8,000 words ≈ **11–12k tokens**) before any work starts. Run each
   routine *inside the one repo it touches* so only that repo's `CLAUDE.md` loads. **~80%
   cut to baseline context** for single-repo tasks.
2. **De-duplicate the house-style block.** The identical ~25-line "ordering & typography"
   block is copy-pasted into all 6 `CLAUDE.md` files — paid on every turn of every session.
   Move it to one `HOUSE-STYLE.md` and replace each copy with a one-line pointer.
3. **Trim the two oversized `CLAUDE.md`.** DESIGN (295 lines) and localDNS (326) exceed
   Anthropic's ~200-line guidance. Push the big reference tables (deploy paths, stage map)
   into the README and let Claude read them on demand, not on every turn.
4. **Lean on prompt caching for routines.** Re-sent context is ~62% of a typical agent
   bill; a cache hit costs ~10% of input price. Keep the stable prefix *stable* so the
   cache keeps hitting.
5. **Use the LiteLLM gateway you already run.** Route cheap/bulk/low-sensitivity routines
   to local models or Haiku 4.5; reserve Opus 4.8 for reasoning. The infrastructure
   (stage 10, port 4040) is already deployed.

---

## 1. Context overhead — the structural problem

Measured today across the checkout:

| Repo | `CLAUDE.md` lines | words |
| ---- | ----- | ----- |
| localDNS | 326 | 2,728 |
| DESIGN-… | 295 | 2,608 |
| MARKETING | 214 | 1,445 |
| customers | 80 | 562 |
| claude-code-homelab | 75 | 371 |
| Azure-lab | 50 | 316 |
| **Total** | **1,040** | **~8,030 (~11–12k tokens)** |

Because all seven repos are cloned side-by-side under `/home/user` and there is no root
`CLAUDE.md`, a session started at `/home/user` loads **every** repo's project instructions
as "codebase instructions" — confirmed: this very routine, which only needed to think about
process, ingested DESIGN + localDNS + customers + MARKETING + Azure-lab + claude-code-homelab.
That is paid on the *first* turn and re-sent (or cached) on every turn after.

**Fixes, in order of payoff:**

- **Scope the working directory to one repo per routine.** A localDNS routine should start
  in `localDNS/`, not `/home/user/`. Then only localDNS's `CLAUDE.md` (+ any parent) loads.
  This alone removes ~9k tokens from a single-repo task's baseline.
- **One `HOUSE-STYLE.md`, six pointers.** The "ordering & typography" block is verbatim in
  all 6 files (confirmed: 6/6 carry the `Adopted 2026-06-05` marker). Replace each with:
  `> House style (ordering, Z→A lists, reversed walkthrough blocks, Gill Sans MT): see HOUSE-STYLE.md`
  Claude reads the full rules only when a task actually touches formatting. Saves ~150 lines
  of duplicated instruction across the portfolio.
- **Get DESIGN and localDNS under ~200 lines.** Keep the briefing (what/why/rules) in
  `CLAUDE.md`; move the exhaustive reference tables — localDNS "Deploy paths" and DESIGN
  "Stage map" / "master list" — to the README, linked. They're lookup tables, not
  every-turn context.
- **Subagents for the start-up rituals.** The NARF/ZORT session-start lists ("read
  portfolio.md, roadmap.md, tech-debt.md, decisions.md, metrics.md, runway.md, budget.md,
  context.md…") pull many files into *main* context. Delegate that to an Explore/Agent
  subagent that reads and returns a summary — subagents run in their own context window, so
  the raw files never touch the main thread.

## 2. Prompt caching — the biggest lever for *recurring* runs

For scheduled routines the static prefix (system prompt + CLAUDE.md + tool schemas) is
identical run-to-run. Pricing today: a **cache hit ≈ 10%** of base input; a **5-min write ≈
1.25×**, a **1-hr write ≈ 2×**. Re-sent context is ~62% of a typical agent bill, so caching
the static prefix is the single largest cost cut available — 70–90% on the cached portion.

Claude Code / the Agent SDK cache automatically *when the prefix is stable*. Practical
implications for this setup:

- **Don't churn the prefix.** Reordering `CLAUDE.md`, editing it mid-session, or injecting a
  changing value early in the prompt invalidates the cache. Keep volatile content (dates,
  per-run params) late, not in the cached header.
- **Cluster routines in time.** Several routines firing within the 5-min (or 1-hr) cache
  window share the warm cache instead of each paying a cold write.
- **Smaller CLAUDE.md still helps even with caching** — the *write* is billed at 1.25–2×, so
  a leaner file is cheaper to cache in the first place.

## 3. Hybrid local + Claude — you already own the pipes

localDNS stage 10 already runs **LiteLLM (4040) + Open WebUI (3000)** with a reasoning
ladder (`local-reason` = deepseek-r1:1.5b on the t630; `cloud-gpu-reason` = full R1 on a
rented GPU; `cloud-overflow` fallback). Extend that pattern to *routine selection*:

- **Tier the work.** Mechanical, low-sensitivity routines — `check-docs.py` link integrity,
  reverse-chronological/Z→A lint, draft generation, summarization, reformatting — do **not**
  need Opus. Run them on a local model or **Haiku 4.5 (~$1 / 1M in)**. Reserve **Opus 4.8**
  ($5/$25 per 1M) for reasoning, architecture, and money/compliance judgment.
- **Let the router decide.** LiteLLM's Complexity Router (rule-based, zero external calls,
  sub-ms) can classify a request and pick the tier automatically. Non-critical Claude Code
  routines can point at your gateway via `ANTHROPIC_BASE_URL` so routing is centralized and
  spend is logged in one place.
- **Privacy bonus.** Anything touching the *customers* repo (real names/figures) is exactly
  the "route locally" case — keep sensitive lookups off the cloud tier, same instinct as the
  DNS split.
- **Match the model to the routine, not the routine to Opus.** This particular review is
  reasoning-heavy, so Opus is right. A nightly "did any link break?" check on Opus is waste.

## 4. Cadence — don't run an Opus analysis daily for a slow-moving answer

The prompt says "keep up to date day by day." The *answer* to "how do we save tokens"
doesn't change daily; the *news* might. So split it:

- A **cheap daily scanner** (Haiku/local) that pulls a few headlines and only escalates when
  something material lands (new model, pricing change, new Claude Code feature).
- A **monthly full review** (this document) on Opus when the scanner flags a change.

That converts ~30 Opus runs/month into ~1 Opus + 29 cheap runs.

## 5. Output verbosity

The voice rule in the repos governs *customer-facing* docs. Add an **internal terseness
rule** for AI chat/routine output (no preamble, no restating the question, no
recap-of-what-I-did unless asked). On heavy routines this measurably cuts *output* tokens,
which are billed at 5× input on Opus.

## 6. New first-party tooling worth adopting (2026)

- **Automatic compaction** keeps long routines inside the window without manual `/compact`.
- **Memory tool** (`memory_20250818`) + **context editing / tool-result clearing** let a
  long agent drop stale tool output and persist only what matters — ideal for the
  multi-file CTO/CFO start-up reads.
- **Subagent memory** (`memory:` frontmatter) lets a recurring reviewer accumulate
  repo-specific knowledge instead of re-deriving it every run.

---

## On the prompt that triggered this (asked for, so: yes, it's inefficient)

The triggering prompt is effective at intent but expensive by construction:

- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of"
  invites open-ended exploration — the most token-hungry possible instruction. Bound it.
- **No deliverable shape.** No format, length, or ranking requested, so the model must guess
  and tends to over-produce.
- **Many sub-questions, one blob.** Token use, prompting, hybrid LLM, "check the news" are
  four tasks; bundling them is fine but they should be a checklist with one defined output.
- **"Day by day" cadence baked into a heavy task** — see §4; that instinct belongs in a
  cheap scanner, not an Opus run.

**Tighter rewrite:**

> Review our user↔AI process for token waste. Produce a ranked list of the top 5 changes,
> each with the concrete fix and an estimated token/cost saving, ≤1 page. Cover: context/
> CLAUDE.md size, prompt caching, model tiering via our LiteLLM gateway, and routine
> cadence. Web-check only items likely to have changed in the last 30 days (pricing, new
> Claude Code features); cite ≤5 sources. If this prompt itself is wasteful, say so.

That version fixes the scope, names the deliverable, caps the research, and still asks for
the self-critique — at a fraction of the tokens.

---

## Sources (checked 2026-06-18)

- [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Context engineering: memory, compaction, tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [LiteLLM Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Hybrid Cloud-Local LLM Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Agentic AI: How to Save on Tokens — Towards Data Science](https://towardsdatascience.com/agentic-ai-how-to-save-on-tokens/)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo](https://www.tembo.io/blog/claude-code-subagents)
