# NARF — review — 2026-06-28 — the AI *process* itself (token efficiency, prompting, hybrid local/cloud)

This review answers a CEO question, not a backlog item: **where is the process between us
(human) and the AI inefficient, and how do we spend fewer tokens for the same or better
work?** I checked the live config (`localDNS/10-ai-orchestration/config.yaml`), every repo's
`CLAUDE.md`, and current best practice on the web (June 2026). Findings are ranked by impact —
do them top-down.

> One-line answer: **we already own a local-LLM router and use it only for browser chat, while
> every Claude Code session runs on cloud Opus — and we reload ~3–4k tokens of `CLAUDE.md` on
> every single prompt. Those two facts are the whole bill.**

---

## Top 5 findings, ranked by token saved per hour of effort

### 1. Use the local-LLM router we already built to *drive Claude Code itself* — not just Open WebUI

This is the big one, and it's almost free because the infrastructure exists.

We stood up `Odin` (LiteLLM at `ai.home.lan:4040` + Ollama `qwen2.5:3b/7b` on the t630 + a
rented-GPU DeepSeek tier). Today it serves **only the Open WebUI chat box**. Meanwhile *this*
tool — Claude Code, the thing doing the actual repo work — bills cloud Opus for every keystroke,
including link-fixing, table reformatting, and house-style edits a 7B model does fine.

What changed in 2026 that makes this trivial:

- **Ollama v0.14.0 (Jan 2026) ships a native Anthropic Messages API endpoint.** Claude Code can
  point at a local model with two env vars (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`) and
  one `ollama pull` — no proxy hacks. Our LiteLLM router is already that front door.
- **The 2026 consensus ratio is ~70/30 local for mainstream coding/doc work**, 30/70 only for
  novel-architecture work. Reported total-cost reductions of **8–10×** when routine work is
  offloaded, with local models hitting 85–90% of Claude's quality on well-specified tasks.

**Recommended split for our repos (mostly Markdown/spec/config, low novelty):**

| Work | Route to | Why |
| ---- | -------- | --- |
| House-style passes, link/anchor fixes, table reflows, changelog entries, renaming | **local `qwen2.5:7b`** via the router | mechanical, well-specified, no architecture judgment |
| Statement-copy drafts, README edits, routine spec writing | **local `qwen2.5:7b`**, escalate on dissatisfaction | the "talk like a person" rule is checkable by a human in seconds |
| Cross-repo reasoning, ADR/FIN decisions, the privacy-fallback class of bug, this kind of review | **cloud Sonnet, Opus only when Sonnet stalls** | genuine multi-file judgment is where cloud still wins decisively |

Caveat we must respect: **TD-14 applies here too.** Any local→cloud fallback path can leak a
sensitive prompt. If we drive an agent off the router, the fail-closed fix (local-only fallback
for sensitive tiers) stops being a nice-to-have — it's the thing standing between "private by
default" and a silent Anthropic upload. Close TD-14 *before* routing real customer data through
the router.

### 2. Kill the `CLAUDE.md` context tax — we pay it on *every* prompt

A `CLAUDE.md` loads in full before the model reads a single line of code. A 5k-token file costs
5k tokens *before you type a word*, on every turn, in every session, forever.

Ours are heavy and partly duplicated:

- The **House-style block (~40 lines, ~600 tokens) is pasted verbatim into all 7 repos'
  `CLAUDE.md`.** Seven copies, reloaded every prompt.
- `DESIGN/CLAUDE.md` carries the full funnel ASCII diagram, the stage-map table, the money-flow
  diagram, the master-list diagram — ~3–4k tokens. `localDNS/CLAUDE.md` carries the entire
  deploy-path table and network topology — ~3k tokens. Most of that is *reference*, consulted
  occasionally, not *instruction* needed every turn.

**Fix:** treat `CLAUDE.md` as a lean pointer, not an encyclopedia. Keep only the rules the model
must obey every turn (voice rule, push-to-branch rule, honesty rule, "read X at session start").
Move the diagrams and the big tables into `README.md` / dedicated docs the model reads *on
demand*. Target: each `CLAUDE.md` under ~1k tokens. Reported real-world result of trimming
instructions + caching: **35% cost cut week 1, ~70% stabilized.**
(House style itself could become one shared `STYLE.md` that each `CLAUDE.md` links to in one
line instead of re-pasting — single source of truth, the rule we already preach for facts.)

### 3. Stop running everything on Opus — tier the model to the task

This very session is Opus 4.8 (1M context). For a doc/spec repo that's a Ferrari in a school
zone most of the time. The 2026 pattern: **Haiku for classification/structure checks → Sonnet
for daily work → Opus only when Sonnet has failed or the reasoning is genuinely hard.** Use
`/model` to drop to Sonnet by default; reach for Opus deliberately. Enterprise telemetry puts
the average at ~$13/developer/active-day — the teams below that are the ones tiering.

### 4. Push verbose work into subagents so the main context (and the cache) stays lean

Our review protocol reads many files at session start. Reading them into the *main* thread
pollutes context and bloats every subsequent turn. Delegate broad searches/reads to **subagents**
— each gets its own context window and returns only a bounded summary, so the expensive main
thread never carries the raw file dumps. (June 2026 added Dynamic Workflows: the lead can fan out
many subagents and a grader loops them to a rubric — overkill for us now, but the plain subagent
pattern is a clean win today.)

### 5. Spend the cheapest token: the one a deterministic script spends instead of the model

We already do this right with `tools/check-docs.py` (link/anchor integrity in CI). That's the
model. **Lean into it:** every check that can be a script (house-style linter for ordering/Z→A,
a "no `CHANGE_ME` left in a shipped file" check, a Gill-Sans-stack grep, a statement-honesty
guard that fails if a placeholder number ships) should be a script, run in CI or a hook — not a
thing we pay a model to eyeball each time. The cheapest token is the one you never send.

---

## Prompt-caching discipline (free, just habits)

- Cache reads bill at ~10% of input; a cached prefix breaks even after ~1.4 reads. But the cache
  is cold after **5 minutes** of inactivity, and **any edit to `CLAUDE.md` or re-ordering of
  read files invalidates it.**
- So: **finish a unit of work in one sitting**, don't re-read/re-order files mid-session, and
  don't edit `CLAUDE.md` in the middle of a working session. This dovetails with the portfolio's
  existing "bundle every box-dependent item into one t630 visit" instinct — same principle,
  applied to AI sessions: **batch, don't trickle.**

---

## On the prompt that triggered this review (the CEO asked me to grade it)

The prompt was, in spirit: *"Find inefficiencies in our process. Token use. Prompting. Local +
cloud. Anything that could help. Search the web. Keep up to date. Check the news. Thanks!"*

It's a good *kickoff* prompt — wide net, names the real levers (tokens, prompting, hybrid), and
explicitly licenses web research. But as a **recurring routine** prompt it's the expensive shape:

- **It's unbounded.** "ANYTHING that could help" / "anything you could possibly think of" invites
  an open-ended, re-derive-from-scratch exploration every run — exactly the token pattern we're
  trying to cut. Each firing re-reads everything and re-reasons the whole space.
- **No output contract.** It doesn't say how long, what format, or where the answer should land,
  so the model guesses (and over-produces to be safe).
- **It runs on Opus 1M.** A research/advisory routine like this is a Sonnet job.

**A leaner recurring version** (cheaper *and* more actionable):

> "Monthly efficiency check. Read `docs/ai-cto/reviews/` for the last efficiency review and the
> CHANGELOG since it. Output **only the diff**: what changed in our token picture, any new
> Claude Code / local-LLM capability worth adopting (one web search, name the source + date),
> and the **top 3 actions** ranked by tokens-saved-per-effort. One page. Append it as the next
> dated review file. Run on Sonnet."

That version is bounded, has an output contract, says where the answer lives, and won't re-derive
the universe each month. Net: it does *more* (a tracked diff over time) for *less*.

---

## What to do this week (in order)

1. **Trim all 7 `CLAUDE.md` files to lean pointers**; hoist house-style into one shared
   `STYLE.md`. (Finding 2 — biggest recurring saving, no infra needed.)
2. **Default Claude Code to Sonnet**, Opus on demand. (Finding 3 — one habit change.)
3. **Close TD-14** (already top of the portfolio), *then* point Claude Code at the LiteLLM
   router for mechanical work via Ollama's Anthropic endpoint. (Finding 1 — the 8–10× lever,
   gated on the privacy fix.)
4. **Adopt the bounded recurring-review prompt** above for this routine; move it to Sonnet.

None of these touch the t630 except #3's optional router step, and #3 is the only one with a
hard prerequisite (TD-14). #1, #2, #4 are pure habit/edit changes we can land today.

---

## Sources (June 2026)

- [Claude Code — Manage costs effectively (docs)](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Claude Code Context Window Tax: How to Manage It in 2026 (Ortemtech)](https://ortemtech.com/blog/claude-code-context-window-tax-guide-2026/)
- [Claude Code subagents: the 2026 production playbook (Totalum)](https://www.totalum.app/blog/claude-code-subagents-totalum)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Local LLM vs Claude for Daily Coding: Real Data 2026 (Ganglani)](https://www.kunalganglani.com/blog/local-llm-replace-claude-daily-coding)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Running Claude Code with a Local LLM in 2026: No Proxy Required (Mayzes)](https://www.shawnmayzes.com/ai-engineering/claude-code-local-llm-2026/)
