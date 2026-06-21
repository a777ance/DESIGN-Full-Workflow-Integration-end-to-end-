# Process efficiency review — user ↔ AI (2026-06-21)

A standing review of how we spend tokens and attention working with Claude (Code + API),
what to route to the local stack vs. the cloud, and where the prompting itself leaks. Findings
are ranked by payback. Web sources are listed at the foot. (Routine-generated; verify before
acting on the bigger structural ones.)

---

## TL;DR — the five that matter

1. **The session-start reading ritual is our biggest single leak.** A DESIGN-repo session that
   obeys CLAUDE.md reads NARF's 4 files + ZORT's 6 files = **~9,400 words (~13K tokens)**, on top
   of the **~3,500-token CLAUDE.md** itself. That's **~16K tokens burned before a single word of
   work**, every fresh session. Fix: make the reads *lazy* (read on demand, not at start).
2. **CLAUDE.md files are 2–3× too long.** DESIGN 2,608 words, localDNS 2,728, MARKETING 1,445.
   These load on *every* turn of *every* session. Cut each to a ~400–600-word index of pointers.
3. **We already run a hybrid local/cloud stack** (LiteLLM @4040, Open WebUI, the deepseek
   reasoning ladder) — we're ahead of most. The win is *routing more deterministic/cheap work to
   it* and reserving Claude for genuine reasoning.
4. **Prompt caching is free money we're not provably claiming.** Any API path (NARF/ZORT
   automations, the LiteLLM router) that resends our big static context should mark it cacheable —
   60–90% input-cost cut on the repeated prefix.
5. **This routine's own prompt is inefficient** (see last section) — open-ended "find ANYTHING"
   is a great one-off brainstorm but an expensive *recurring* job. Tighten and bound it.

---

## 1. Context bloat — the recurring tax (highest payback)

Every token in CLAUDE.md and every mandated session-start file is paid **per turn / per session**,
forever. Measured today:

| What loads | Words | ~Tokens |
| ---------- | ----: | ------: |
| DESIGN CLAUDE.md | 2,608 | ~3,500 |
| localDNS CLAUDE.md | 2,728 | ~3,650 |
| MARKETING CLAUDE.md | 1,445 | ~1,900 |
| NARF session-start (4 files) | 3,300 | ~4,400 |
| ZORT session-start (6 files) | 6,144 | ~8,200 |
| **DESIGN session floor (CLAUDE.md + NARF + ZORT)** | **~12,100** | **~16,100** |

**Actions:**
- **Lazy-load the persona state.** Change the NARF/ZORT instructions from "read these N files at
  session start" to "the portfolio hub is `X`; read it *when a task needs cross-repo state*."
  Claude will pull them on demand. This alone reclaims ~13K tokens off the common path.
- **Slim every CLAUDE.md to an index.** Keep the high-impact invariants (the honesty rule, the
  "push to main / push to branch" rule, secrets rule, the one-source-of-truth rule) inline; move
  the funnel diagram, full stage-map table, deploy-path table, and the full Known-Issues tables
  out to README/their own files and *link* them. Target ≤600 words each. A 5K-token CLAUDE.md
  costs 5K tokens before you've typed a word.
- **`.claudeignore` discipline.** Generated/rendered HTML statements, stats JSON, vendored data,
  `open-webui-data/` — exclude from proactive inclusion. Reported ~85% context reduction from this
  alone on data-heavy repos.
- **`/clear` between tasks, `/compact` mid-long-task, `/recap` on resume** (the last is the
  cheap way back into a session — summary instead of replaying the whole thread).

## 2. Route more to the local stack (we own the hardware)

Industry pattern: ~60–70% of agent requests are "simple" (classify, extract, format, short
summarize) and don't need a frontier model; hybrid setups report 60–83% cost cuts. Our t630
already serves `local-reason` (deepseek-r1:1.5b) + `cloud-gpu-reason` (full R1 on a rented GPU).
**Send these to local, keep Claude for the hard 10–20%:**

- **Deterministic checks → not an LLM at all.** `tools/check-docs.py` is already pure Python —
  good. Add the same for: house-style lint (newest-first ordering, Z→A lists, Gill Sans stack
  present), link/anchor resolution, "no `CHANGE_ME` left in a shipped file," "statement only
  ships measured figures." A pre-commit hook running these is ~0 tokens and catches the errors we
  currently spend Claude reasoning-time to avoid.
- **Local LLM:** commit-message drafting, log/diff summarization, classifying inbound leads,
  routine roster-field extraction, first-pass "Handled For You" phrasing. Cheap, private, and
  keeps real customer data off the cloud (aligns with the `customers` repo privacy rule).
- **Claude (cloud):** cross-repo reasoning, statement composition judgment, anything touching the
  honesty rule, architecture/ADR decisions, this kind of review.
- A `PreToolUse` hook that compresses verbose Bash output (the "RTK" pattern) before it hits
  context saves 60–90% on `git status`/test/`nft list` dumps that we never re-read.

## 3. Prompt caching (if/when we hit the API directly)

Single highest-leverage *API* optimization in 2026. Cache-read ≈ 10% of normal input cost; 5-min
TTL that resets on each use, so it stays warm in an active session.
- Mark the static system prompt + tool schemas + the big CLAUDE-style context as a cacheable
  prefix in any NARF/ZORT automation or the LiteLLM gateway.
- **Anti-patterns to avoid:** dynamic timestamps in the cached prefix (invalidates every call —
  truncate to the day), per-user strings in the shared prefix, inconsistent whitespace. We have a
  live example of the timestamp trap to *keep*: prompt-cache prefixes must NOT carry a
  second-resolution "current time."

## 4. Subagents — use with intent, not by reflex

Subagents isolate noisy work (big searches, log sweeps) and hand back only a summary — 40–70% main-
context savings *on the right task*. But Anthropic notes subagent-heavy flows can burn ~7× the
tokens of a single thread, and 3–5 concurrent is the practical ceiling. Rule: spawn one only when
the clutter it keeps out of the main thread is worth more than its startup overhead. Don't wrap
quick git/shell steps in a subagent.

## 5. House-style rules are a hidden correctness/re-read cost

The "reverse the blocks, keep the steps," "Z→A alphabetical," and "newest-first within a section"
conventions are unusual enough that the model must re-reason (and sometimes re-read) to apply them
correctly — and they're easy to get subtly wrong on edits. They don't save tokens; they spend
them. Keep them (they're a deliberate brand choice) but **enforce them with a deterministic linter**
(see §2) instead of relying on the model to remember — that converts a per-edit reasoning cost into
a free check.

## 6. Output verbosity

Default Claude prose is polite and explanatory. For routine internal work, a terse output style /
"caveman"-type skill cuts ~65% of *output* tokens with no information loss. Worth a project-level
output style for the internal repos; keep the warm voice for anything customer-facing (the pitch
rule still wins there).

---

## Is THIS prompt inefficient? — yes, and here's the fix

The triggering prompt ("Locate inefficiencies… Is there a better way… ANYTHING that could help…
Search the web… Check the news") is excellent as a **one-off brainstorm**, but as a **recurring
routine** it's expensive and unbounded:

- **Unbounded scope** ("ANYTHING") forces broad, open-ended exploration every run — max token
  spend, and the same general findings re-derived each time.
- **No diff/state anchor** — it doesn't say "compared to last run" or "only flag what changed,"
  so each run re-reports the standing advice instead of new signal. (As a watch-routine, silence
  on "nothing changed" is the goal.)
- **Mixed asks** (token use + prompting + local LLM + news) pull in four directions at once.

**Tighter recurring version:**

> Weekly: re-read `docs/ai-cto/process-efficiency-review-*.md` (latest). Check Anthropic's
> changelog + Claude Code release notes since the last run's date. Report **only** (a) new
> model/pricing/feature changes that affect our hybrid setup, and (b) any efficiency item from the
> review we still haven't done. If nothing new and nothing actionable, send no notification.
> Keep it under 300 words.

That bounds scope, anchors to prior state, and makes "all quiet" a valid (silent) outcome.

---

## Sources

- [Claude Code Token Optimization (2026 guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [How to Reduce Claude Code Token Usage — 8 methods](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code (Firecrawl)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Run Local AI Models with Claude Code to Cut Costs 10× (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — cost optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Prompt Caching: 5-minute TTL change (dev.to)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Claude Code Subagents — practical 2026 guide (Nimbalyst)](https://nimbalyst.com/blog/claude-code-subagents-guide/)
- [Create custom subagents — Claude Code docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Hooks 2026 (Morph)](https://www.morphllm.com/claude-code-hooks)
- [How I Cut Claude Code Token Usage 90%+ with hooks (Medium)](https://medium.com/@abdulgafoorabid/how-i-cut-claude-code-token-usage-by-90-with-4-tools-custom-hooks-and-enforcement-d3f8d2488cd6)
- [Introducing Claude Fable 5 / Mythos 5 (June 9, 2026)](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [Introducing Claude Opus 4.5 (Anthropic)](https://www.anthropic.com/news/claude-opus-4-5)
