# Process efficiency review — user ↔ AI workflow

*Audit date 2026-06-14. Scope: how we work with Claude Code (and the cloud Claude API)
across the A777ance repos — token cost, prompting, and where our own local-first LLM
stack (Odin/LiteLLM) could carry load it currently doesn't. This is a findings doc, not
applied changes; each item links to a tech-debt entry to action.*

## TL;DR — the three biggest wins

1. **Our `CLAUDE.md` files are reference manuals, not briefings.** ~58 KB / ≈14.6k tokens
   across the six repos, and the whole set loads on every session that touches them. The
   single largest *recurring, every-turn* token cost we control. Trim to true briefings;
   move reference tables to on-demand linked files. Est. 50–70 % cut to fixed context.
2. **We pay Opus prices for Haiku/Sonnet/local work.** This very routine runs on
   `opus-4-8[1m]`. Doc audits, link-checking, commit-message drafting, triage — most of
   what these routines do — is Sonnet- or Haiku- or *local-model*-shaped. Right-sizing the
   model is a 3–10× cost lever with no quality loss on the easy 80 %.
3. **We built a hybrid local-first router (Odin) and don't point our own busywork at it.**
   `localDNS/10-ai-orchestration` already routes cheap/private work to local Ollama tiers
   and overflows to Claude. It serves chat/apps — not our dev loop. Closing that gap is
   the "hybrid local + Claude API" the founder keeps asking for, already 90 % built.

---

## Findings, ranked by impact

### 1 — `CLAUDE.md` bloat + 6× duplication (P2, biggest recurring cost)

- Each repo's `CLAUDE.md` opens by calling itself "the short briefing — read this first,"
  then carries the full stage map, money-flow diagram, deploy-path table, every known
  issue, and verification command blocks. That is reference material that should be *read
  on demand*, not *preloaded every turn*. `localDNS/CLAUDE.md` (326 lines) and `DESIGN`
  (295) are the worst.
- The **House-style block (~40 lines) is copy-pasted verbatim into all 6** `CLAUDE.md`
  files. The three-repo table and the roles/money-flow diagram are each duplicated 2–3×.
  Every duplicate is re-tokenized on every load.
- **Fix:** cut each `CLAUDE.md` to a real briefing (target <120 lines / ~2k tokens):
  what the repo is, the one or two invariants, and *links* to the deploy table, known
  issues, and verification. Put the House-style block in one `STYLE.md` (or a shared
  `docs/house-style.md`) and link it — don't inline it six times. Claude reads the linked
  detail only when a task needs it. → **TD-17**

### 2 — Model right-sizing for routines and easy tasks (P2, 3–10× lever)

- Routines and most edits don't need a frontier reasoner. Anthropic's own guidance: Sonnet
  is the speed/intelligence sweet spot; Haiku handles triage/extraction. The `[1m]` context
  tier also carries a price premium we rarely need.
- **Fix:** default scheduled routines and mechanical tasks to Sonnet 4.6 (or Haiku 4.5 for
  pure triage/summarize/lint); reserve Opus for genuine architecture/debugging. In Claude
  Code, `/model` per-session or set the routine's model in its config. → **TD-16**

### 3 — Hybrid: route our own busywork through Odin (P2, the founder's ask, mostly built)

- `localDNS/10-ai-orchestration` is a working LiteLLM front door with local Ollama tiers
  (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason`), a Heimdall privacy gate,
  and Claude as overflow. Industry hybrid setups report **60–90 % cost cuts** by doing
  exactly this: cheap/private work local, hard work to the frontier API.
- Today it serves chat + apps, not the dev loop. Candidate offloads to local tiers:
  doc-link checking, draft commit messages, file/PR summarization, first-pass triage of
  webhook events, "explain this config" lookups — none need a frontier model and several
  touch private customer data that *shouldn't* leave the box anyway.
- ⚠️ Don't expand routing onto Odin until **TD-14** (sensitive→cloud failover leak) is
  closed — fail closed first.
- **Fix:** add a thin "ask-local-first" path for mechanical sub-tasks (a script/skill that
  hits `ai.home.lan:4040`), Claude API only on escalation. → **TD-15**

### 4 — Prompt caching TTL (P3, quick config win)

- Claude Code's default cache TTL dropped 60 m → 5 m in March 2026, silently raising cost
  for spaced-out sessions; a March 2026 caching bug caused 10–20× inflation. With our large
  fixed prefix (CLAUDE.md + tool defs), the cache is worth a lot.
- **Fix:** set the 1-hour cache (`ENABLE_PROMPT_CACHING` + 1 h TTL env) for long/returning
  sessions and routines; verify cache-read vs cache-write in `/cost`. (Item 1 shrinks the
  cached prefix regardless.) → **TD-18**

### 5 — Move deterministic checks out of the model (P3)

- `tools/check-docs.py` is already CI-wired (TD-11 resolved). Lean on hooks/CI for anything
  deterministic (link checks, lint, `make statement` dry-runs) instead of asking Claude to
  run and interpret them mid-session — deterministic work shouldn't burn tokens or context.
  A `SessionStart` hook can front-load environment setup so the model doesn't rediscover it.

### 6 — The "reverse the blocks / Z→A / reverse-chronological" house style (note, not a fix)

- The reversed-block walkthrough and Z→A conventions are a deliberate, founder-set style —
  not changing them. But flag the cost: they fight an LLM's forward-order priors, so the
  model spends extra tokens re-reading to follow a procedure and is likelier to misorder
  steps. If a doc ever produces repeated AI mistakes, that's the first suspect. Keeping the
  *numbers* fixed (as the rule already says) is what makes it survivable.

---

## On the prompt that triggered this review

The triggering prompt is itself a good worked example of an expensive prompt — worth
naming because we write a lot of these:

- **Unbounded scope.** "Anything you could possibly think of… ANYTHING that could help"
  forces wide, expensive exploration and over-long output. A token-budget or "top 5 by
  impact" cap would get the same value cheaper.
- **Many asks, no priorities.** Process + tokens + prompting + hybrid LLM + news, with no
  ranking, so the model must cover all of them at depth.
- **Standing need stated as a one-shot.** "Keep UP TO DATE… check the news… this changes
  day by day" is a *recurring monitor*, not a single prompt — which is exactly what this
  scheduled routine is for. Let the routine own the freshness; keep each run scoped.
- **Ambiguous target.** "our PROCESS between the user and the AI" — Claude Code? the Odin
  stack? both? The model has to guess.

**A tighter version:** *"Review our Claude Code workflow for token waste. Give the top 5
fixes by $ impact, each with the concrete change and an estimate. Assume I already run the
Odin local router. ≤1 page. Cite anything time-sensitive."* — same answer, a fraction of
the tokens, and reusable as the routine's standing instruction.

General prompt hygiene that pays off here: state the **goal + the one constraint + the
deliverable shape**, point at **specific files** instead of "the codebase," and **batch**
related asks into one turn rather than a chain of follow-ups (each follow-up re-reads the
whole thread).

---

## Sources (2026, verify periodically — this space moves fast)

- [Best practices for Claude Code — Claude docs](https://code.claude.com/docs/en/best-practices)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code updates, June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [How Prompt Caching Actually Works in Claude Code — Claude Code Camp](https://www.claudecodecamp.com/p/how-prompt-caching-actually-works-in-claude-code)
