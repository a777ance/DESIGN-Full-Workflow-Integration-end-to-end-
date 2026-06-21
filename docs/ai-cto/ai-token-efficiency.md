# AI token efficiency & workflow audit

**Author:** NARF/ZORT routine (scheduled) · **Date:** 2026-06-21 · **Status:** recommendations, not yet actioned

A standing audit of how we spend tokens in the human↔AI loop — Claude Code sessions and the
self-hosted LiteLLM router on the t630 — plus the current best practices behind each call.
Time-ordered sections read newest-first per house style. Re-run this audit when models,
pricing, or the router config change (it moves fast — re-checked 2026-06-21).

---

## Top 5 wins, by impact (do these first)

1. **Re-point `cloud-overflow` off Opus 4.8.** `localDNS/10-ai-orchestration/config.yaml`
   makes **Opus 4.8 ($5/$25 per M)** the failover for *every* local tier. When a local
   backend cools down (`allowed_fails: 2`), routine chat silently spills to the most
   expensive frontier model. Switch overflow to **Haiku 4.5 ($1/$5)** or Sonnet 4.6
   ($3/$15); keep Opus only on the explicit `cloud-explore` tier. **~5× cheaper on every
   spillover.** One-line change the config already invites.
2. **Scope Claude Code sessions to one repo.** A session opened across the portfolio loads
   *all seven* `CLAUDE.md` files into context every turn (this routine's own context did
   exactly that). Work in one repo at a time; use `portfolio.md` for cross-repo facts.
   **Cuts base context by ~80% on focused work.**
3. **Trim the big `CLAUDE.md` files.** `localDNS` and this repo's `CLAUDE.md` run many
   hundreds of lines and reload every session. Prompt caching makes the *dollar* cost cheap
   (90% off reads), but the tokens still occupy the window and force earlier compaction.
   Keep `CLAUDE.md` to the essential briefing (target <200 lines); push deep reference (the
   full deploy-paths table, the known-issues log) into linked docs or **skills** that load
   on demand.
4. **Default Claude Code to Sonnet; reserve Opus.** Sonnet 4.6 handles 90%+ of coding. Use
   `/model` to drop to Sonnet as the daily driver, Haiku for routine reads, Opus 4.8 only
   for genuinely hard reasoning. This very routine runs on Opus 4.8 1M — over-spec for a
   research/summarize job; Sonnet would do it cheaper.
5. **Delegate exploration to subagents.** A subagent runs in its own context and returns
   only a conclusion — verbose file/log/web reads never land in the main window. Reach for
   the Task tool for "search the codebase N ways," "run tests and report failures," and
   research. **30–70% lower per-message cost** on heavy-context work.

---

## A. The Claude Code loop (human ↔ AI)

**Context is the meter.** Cost and the speed of hitting compaction both scale with how many
tokens ride along on every turn. Levers, cheapest-effort first:

- **`/context` and `/usage`** — measure before optimizing. `/context` shows what's eating the
  window (system prompt, tools, CLAUDE.md, MCP servers, history); `/usage` attributes spend
  to skills/subagents/MCP over 24h/7d. Run weekly.
- **`/clear` + `/rename` between tasks.** Stale history is re-sent every turn; clearing cuts
  per-message cost 30–50%. Rename first so the session is resumable.
- **`/compact "focus on …"`** when a long thread must continue — steer what's kept.
- **Plan mode (Shift+Tab)** before multi-file changes — catches a wrong direction before it
  costs a round of rework (often 30–50% of a session's total).
- **Specific prompts beat vague ones.** "Add input validation to `login()` in `auth.ts`" is
  2–5× cheaper than "improve the codebase" — the latter triggers broad scanning. (See the
  prompt critique in §D.)
- **Skills / hooks / slash commands** carry repeated instructions without re-typing or
  re-sending them. A hook can pre-filter test/log output so Claude reads 200 lines of
  failures, not a 10k-line log (50–80% saved on log reads).
- **MCP discipline.** Tool defs are deferred (only names load until used), but disable unused
  servers via `/mcp`, and prefer a CLI (`gh`, `aws`) over a heavyweight MCP server where one
  exists.

**Prompt caching is automatic in Claude Code** for the stable prefix (system prompt + tools +
`CLAUDE.md`): cache **reads cost 0.1×** the base input rate (90% off), writes 1.25× (5-min) or
2× (1-hour). Two rules to keep the cache warm:
- **No timestamps or per-turn-varying text in the stable prefix** (a "current time" line in
  `CLAUDE.md` busts the cache every turn). Static dates like our "Adopted 2026-06-05" are fine.
- **Stable content first, volatile last** — which is already how `CLAUDE.md` → user message is
  ordered.

---

## B. The hybrid router (LiteLLM on the t630)

The architecture is already on the 2026 best-practice line: **local-first** (60–70% of simple
work runs free on the t630 CPU), **rented-GPU offload** for heavy reasoning (flat hourly, not
per token), **cloud overflow** as failover, and a **deterministic dispatcher** with *no LLM in
the routing decision* — exactly the pattern the guides recommend (zero token cost on routing,
fully debuggable). Refinements:

- **Overflow model = cost trap** (see win #1). `cloud-overflow: claude-opus-4-8` is the
  fallback target for `local-fast`, `local-smart`, and the reasoning ladder. Demote it to
  Haiku/Sonnet.
- **Enable Anthropic prompt caching through LiteLLM.** Any flow that resends a stable prefix
  to a `cloud-*` tier (Odin's planner, RAG context, repeated system prompts) can pass
  `cache_control` for the 90% read discount — LiteLLM supports the passthrough. Biggest payoff
  on the LangGraph supervisor, which resends workflow state.
- **Batch API (50% off) for non-interactive bulk jobs.** Stacks with caching to ~95% off.
  Applies to anything offline and high-volume (bulk classification/summarization). *Not*
  statement rendering — those are template-rendered at ~a penny a home, no LLM in the path.
- **Keep the privacy gate exactly as is.** Heimdall/`classify()` pinning `sensitive` tasks
  local-first with no cloud fallback is both the privacy invariant *and* a cost control
  (sensitive work never bills a token). Don't trade it for routing "intelligence."
- **Right-size the cloud tiers.** `cloud-code` = Sonnet 4.6 is the correct sweet spot;
  `cloud-explore`/`cloud-vision` = Opus 4.8 is defensible for the hardest reasoning and image
  input. Consider Haiku for a `cloud-fast` overflow lane.

---

## C. What's already right (keep)

- Deterministic, LLM-free routing decision (`dispatcher.py`) — determinism + zero routing cost.
- "Route, don't shard" — whole models behind one front door; heals on node loss.
- Local-first default — privacy and ~zero marginal cost on the bulk of traffic.
- Rented-GPU "GeForce Now for LLMs" for heavy R1 — flat hourly beats per-token at volume.
- The privacy lock as a hard line in code, not a hope.

---

## D. Critique of the prompt that triggered this audit

The triggering prompt ("Locate inefficiencies in our PROCESS … ANYTHING that could help …")
worked, but it modelled the very inefficiency it asked about:

- **Too broad.** "Anything you could possibly think of" invites broad scanning — the
  expensive failure mode. A scoped ask ("audit token cost in the LiteLLM router and our
  CLAUDE.md sizes; web-check current Claude pricing") gets a tighter, cheaper answer.
- **Many asks in one.** Inefficiencies + token reduction + prompting + hybrid LLM + web
  research + news + self-critique. Enumerate and prioritise; let the model fan out to
  subagents per branch (as this run did).
- **No target or format.** Naming the goal (lower $/session? less context bloat? one repo?)
  and the wanted output (a committed doc, a checklist) avoids guesswork rounds.
- **Recurring-routine smell.** If this runs on a schedule, the standing instructions belong
  in a **skill or the routine's prompt file**, not re-typed each run — and the routine should
  run on **Sonnet**, scoped to the relevant repos, not Opus 4.8 across all seven.
- **Good instincts to keep:** asking for web/news currency, asking the model to critique its
  own prompt, and pointing at the hybrid local+cloud angle.

A tighter version: *"On Sonnet, scoped to localDNS + this repo: audit our token spend. Web-check
current Claude pricing/caching. Output a prioritised checklist committed to
docs/ai-cto/. Flag the single biggest cost lever."*

---

## E. Reference figures (verified 2026-06-21)

| Metric | Value |
| ------ | ----- |
| Cache read discount | 90% (0.1× base input) |
| Cache write | 1.25× (5-min TTL) / 2× (1-hour TTL) |
| Cache breakeven | 3+ reads (5-min) / 5+ reads (1-hour) |
| Batch API discount | 50%; stacks with cache to ~95% off |
| Opus 4.8 | ~$5 / $25 per M (in/out) |
| Sonnet 4.6 | ~$3 / $15 per M |
| Haiku 4.5 | ~$1 / $5 per M |
| Subagent isolation saving | 30–70% per-message on heavy-context tasks |
| Hybrid local-first saving | 60–80% vs all-cloud (simple tasks run local) |
| `CLAUDE.md` target | <200 lines |

**Sources:** Claude API — Prompt Caching, Pricing, Context Windows (platform.claude.com);
Claude Code — Manage costs, Subagents (code.claude.com); Anthropic context-management +
Opus 4.8 / Sonnet 4.6 release notes; LiteLLM routing/load-balancing docs; 2026 hybrid
local/cloud routing and Claude Code token-saving write-ups.
