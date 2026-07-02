# Process efficiency review — user ↔ AI (Claude Code)

*2026-07-02 · NARF (AI CTO). How we spend tokens working with Claude, and where to cut.
Web-sourced best practices are current as of July 2026 (they move fast — re-check quarterly).*

**Bottom line:** the biggest recurring cost isn't the work, it's the *setup tax* we pay
before any work starts — ~14.6k tokens of `CLAUDE.md` loaded across six repos on every
session, plus a "read these ~12 files at session start" ritual, most of it irrelevant to
the task at hand. We also already own the single highest-leverage fix (a local LLM router,
`localDNS` stage 10) and aren't routing anything to it. Estimated achievable reduction:
**40–70% of input tokens** with no loss of output quality.

---

## 1. The setup tax — our #1 recurring cost

Every Claude Code session loads the project `CLAUDE.md` of every in-scope repo **before you
type a word**, and re-pays it on each cold start. Measured today:

| Repo | `CLAUDE.md` size | ~tokens |
| ---- | ---------------- | ------- |
| localDNS | 20.5 KB | ~5,100 |
| DESIGN (this repo) | 18.0 KB | ~4,500 |
| MARKETING | 10.7 KB | ~2,700 |
| customers | 4.1 KB | ~1,000 |
| claude-code-homelab | 2.9 KB | ~720 |
| Azure-lab | 2.3 KB | ~570 |
| **Total** | **58.4 KB** | **~14,600** |

On top of that, `CLAUDE.md` §5/§6 instruct **every** session to open the AI-CTO stack
(portfolio, roadmap, tech-debt, decisions) **and** the AI-CFO stack (portfolio, decisions,
metrics, runway, budget, MARKETING context) — ~11 more file reads whose full contents land
in context. A session that edits one Unbound config file pays for the pricing tables, the
funnel diagram, and the CFO runway before it starts.

**Three concrete cuts:**

1. **De-duplicate the house-style block.** The identical ~1.2 KB "ordering & typography"
   section is pasted verbatim into all six `CLAUDE.md` files (~7 KB of pure duplication).
   Keep it in one canonical file; have the others link to it in one line. Claude only reads
   the linked file when a task actually touches formatting.
2. **Move reference tables out of `CLAUDE.md` into linked docs.** The localDNS *Deploy
   paths* table and the DESIGN *Stage map* are lookup material, not per-turn rules. Put them
   in README (already the case) and cut them from `CLAUDE.md` to a one-line pointer. Rule of
   thumb: `CLAUDE.md` should hold *rules you'd break without it*, not maps you consult
   occasionally. Target: each `CLAUDE.md` under ~1,500 tokens.
3. **Make the session-start reads conditional.** Change §5/§6 from "at session start, read
   these 11 files" to "*when doing CTO/CFO portfolio work*, read these." A config edit
   shouldn't drag in the CFO runway.

> Caching caveat: within one live session, prompt caching amortizes a stable system prompt
> to ~10% cost after the first turn. But the cache TTL was **cut from 1 hour to 5 minutes in
> March 2026**. Automated/scheduled runs (like this very routine) and any session resumed
> after a break start **cold** and pay full price. So trimming the static prefix helps most
> exactly where caching can't: recurring and resumed sessions.

---

## 2. Use the local LLM we already built (biggest single lever)

`localDNS` stage 10 is a **LiteLLM router with a reasoning ladder** (local `deepseek-r1:1.5b`
on the t630, cloud GPU on demand, Claude cloud as overflow) plus Open WebUI. It exists and is
deployed. We route **nothing** operational to it today.

Industry hybrid setups report **60–90% cost cuts** by keeping simple/high-volume work local
and reserving Claude for real reasoning and code. Our natural local-tier candidates — all
cheap, repetitive, and (critically) **privacy-sensitive**:

- Roster/`roster.json` validation and field checks (08 CRM).
- Extracting/normalizing facts from customer records (the `customers` repo holds **real**
  names and figures — keeping this off the cloud *is our own privacy invariant*, not just a
  cost play).
- Drafting boilerplate: "Handled For You" log entries, statement copy first-passes.
- Pre-flight `tools/check-docs.py`-style link/anchor checks before invoking Claude.
- Classifying/triaging inbound leads and call notes.

Reserve Claude (via API/Code) for: multi-step reasoning, real code changes, the honesty-rule
judgment on statements, architecture decisions.

**Blocker to fix first — TD-14.** The router's `local-reason` tier has a cloud fallback
(`cloud-gpu-reason` → `cloud-overflow`), so a *sensitive* task can silently fail over to the
Claude cloud if the local model is down. Give sensitive/local-only chains a **fail-closed**
(local-only) fallback before routing any customer data through it. No privacy guarantee until
that's fixed.

---

## 3. Pick the right model per task (and this routine is over-provisioned)

- **Sonnet 5 is now the Claude Code default** — 1M-token context, promo **$2/$10 per Mtok
  through Aug 31** (then $3/$15). It's the right default for almost all coding here.
- **Haiku 4.5** for mechanical/search/subagent work — a fraction of the cost.
- **Opus** only for genuinely hard reasoning.
- This scheduled routine is running on **Opus 4.8 (1M)** — the priciest tier — for what is
  mostly research + writing. Sonnet 5 would do this job at a large discount. Set scheduled/
  routine work to Sonnet by default; escalate to Opus only when a run needs it.

---

## 4. Subagents & session hygiene (habits, not infra)

- **Delegate search to subagents.** A subagent reads the 15 files in *its* context and
  returns a ~500-token summary; the main context never sees the 150k tokens of file bodies.
  Our CTO/CFO "read many files" pattern is the textbook case for this.
- **`/clear` between unrelated tasks, `/compact` after a work phase, `/recap` on resume.**
  Every file read and command output stays in context verbatim until cleared — a big log read
  once is paid for on every subsequent turn of that session.
- **One repo in scope per focused session.** Multi-repo scope pulls every `CLAUDE.md` and the
  full repo-scope list into the system prompt. Scope to the repo you're actually editing.
- **Batch `CLAUDE.md`/skill edits.** Any edit to a cached prefix busts the cache and forces
  full reprocessing next turn — so make deliberate, batched changes, not constant tweaks.

---

## 5. On the prompt that requested this review

The request was warm and clear on *intent*, but structured in a way that maximizes tokens and
makes the output hard to action:

- **Open-ended mandate** ("ANYTHING that could help," "search the web," "check the news")
  invites exhaustive exploration with no stopping rule — the single most expensive prompt
  shape.
- **No deliverable spec**: no statement of what artifact is wanted, where it should live, or
  what "done" looks like.
- **No scope boundary**: all seven repos are implicitly in play.

A tighter version costs less and returns something you can act on the same day. Template:

> *"Review how we use Claude Code across the repos for token cost. Produce a ranked list of
> the top 5 fixes with estimated savings and the concrete change for each. Focus on the
> recurring per-session overhead; you can assume the hybrid router exists. Write it to
> `docs/ai-cto/` and give me a 5-line summary. Skip anything speculative."*

That names the goal, the artifact, the scope, the format, and a stop rule. General principles
for prompting Claude Code here: **state the deliverable and where it goes; give a stop rule;
scope to one repo when you can; ask for a plan before a large change; prefer "edit X to do Y"
over "improve X."**

---

## Ranked action list

| # | Action | Effort | Est. saving | Owner |
| - | ------ | ------ | ----------- | ----- |
| 1 | Trim each `CLAUDE.md` to rules-only (<1,500 tok); de-dupe house-style; move tables to README | S | ~8–10k tok/session | CTO |
| 2 | Make §5/§6 session-start reads conditional, not unconditional | S | ~several k tok/session | CTO |
| 3 | Set routine/scheduled work to Sonnet 5; reserve Opus for hard reasoning | XS | large $ on recurring runs | CTO |
| 4 | Fix TD-14 (fail-closed local fallback), then route cheap/sensitive ops to the local router | M | 60–90% on routed tasks | CTO |
| 5 | Adopt subagent-for-search + `/clear`·`/compact`·`/recap` habits; one repo per session | XS | 20–40% on long sessions | all |

## Sources (July 2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic dropped prompt cache TTL 1h → 5min (2026-03)](https://dev.to/whoffagents/anthropic-silently-dropped-prompt-cache-ttl-from-1-hour-to-5-minutes-16ao)
- [Reduce Claude Code costs 60% — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [How to reduce Claude Code token usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Run local AI models with Claude Code to cut costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid cloud-local LLM architecture guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM auto-routing docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Claude Code release notes — July 2026](https://releasebot.io/updates/anthropic/claude-code)
