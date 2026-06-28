# Process Efficiency Review — Human↔AI Workflow & Token Spend

**Date:** 2026-06-28 · **Author:** NARF (AI CTO) · **Trigger:** founder request — "locate
inefficiencies in our PROCESS between the user and the AI; reduce token use; better prompting;
hybrid local LLM + Claude; keep up to date."

This review is current as of late June 2026 — the landscape moves weekly, so treat the dated
findings (esp. the June 15 pricing change and the 5-minute cache TTL) as the live state and
re-check monthly. Sources are listed at the bottom.

---

## TL;DR — the five highest-leverage moves

1. **Trim the CLAUDE.md tax.** Seven repos each load a large CLAUDE.md *every turn, every
   session*. The DESIGN one alone is ~3k tokens; the localDNS one is larger. This is a fixed
   cost paid before a single useful word. Cutting these to lean "always-true rules" + linked
   detail is the single biggest recurring saving available to us. **(P1, free, do first.)**
2. **Stop reading the portfolio hub on every session.** The NARF/ZORT bootstrap ("read these
   4–6 files at session start") fires whether or not the session is CTO/CFO work. Gate it.
3. **Actually route to the local box we already built.** Stage 10's LiteLLM + reasoning ladder
   exists but Claude (cloud) is still doing mechanical work — doc-link checks, reverse-chrono
   reordering, lead classification, first-draft summaries. That's the 60–70% of tasks the
   industry routes to a 1.5–13B local model. We own the hardware; we're not using it.
4. **Exploit prompt caching deliberately, and mind the 5-minute TTL.** Stable content first,
   dynamic content last; never let a scheduled routine idle 5–60 min mid-cache and pay the
   miss. This is 60–90% off input on repeat work.
5. **The June 15 pricing change makes all of the above matter more.** Programmatic /
   scheduled Claude Code usage now bills from a credit pool at full API rates — our cron-style
   routines (like the one that generated this doc) are no longer "free under the subscription."

---

## A. Where our process leaks tokens today

Ordered worst-first.

### A1. The always-loaded context is huge (P1)
Every Claude Code session ingests the repo's CLAUDE.md *before* it reads any code or the task.
A 5k-token CLAUDE.md costs 5k tokens on turn one and stays resident every turn after. We have
**seven** of them, several large, plus a house-style block duplicated verbatim in all seven.

- **Fix:** Demote each CLAUDE.md to a short, high-impact rule set (target < 1k tokens). Move
  the stage maps, deploy-path tables, and known-issues tables into the README/linked files that
  Claude reads *on demand* only when a task needs them. The house-style block is identical
  across repos — collapse it to a one-line pointer ("House style: see DESIGN/STYLE.md") instead
  of pasting the full block seven times.
- **Why it's safe:** Claude already follows links in CLAUDE.md. Detail isn't lost; it's just
  not pre-paid every turn.

### A2. The CTO/CFO bootstrap reads 4–6 files unconditionally (P1)
Both NARF and ZORT instructions say "at session start, read portfolio.md, roadmap.md,
tech-debt.md, decisions.md…". A session that only fixes a typo in localDNS still pays for the
whole hub read if the agent obeys literally.

- **Fix:** Reword the trigger to be *conditional*: "When the task involves cross-repo status,
  roadmap, or financial decisions, read the hub. Otherwise skip it." Better still, keep a
  single short `portfolio-snapshot.md` (≤ 40 lines, the live state only) that the agent reads,
  and only open the full logs when it needs history.

### A3. Mechanical work is done by the most expensive model (P1)
Tasks we currently hand to Claude that a local 7–13B (or even the 1.5B reasoning model on the
t630) does fine:
- `tools/check-docs.py`-style link/anchor validation and reordering to house style.
- Reverse-chronological / Z→A reordering of logs and lists (pure mechanical transform).
- Lead/booking classification and field extraction for the master list (stage 02–08).
- First-pass summarization before a Claude polish pass.
- Drafting boilerplate (sidecar.json scaffolds, statement stubs).

We have the router for this (`10-ai-orchestration`). See Section C.

### A4. Long-running sessions accumulate stale tool output (P2)
Every file read, shell dump, and MCP result is appended to context and stays there. A noisy
`git log` or a 500-line file read pollutes every subsequent turn.

- **Fix:** `/clear` between unrelated tasks (the most-cited single token-saver in the field);
  `/compact` mid-task with an explicit "preserve X" instruction; `/rewind` (June 2026) to step
  back before a `/clear` without replaying everything. Use **subagents** for noisy work
  (log analysis, test-failure inspection, dependency/doc search) so the verbose output stays
  in the subagent's context and only the summary returns to main.

### A5. This very routine is an open-ended, recurring research run (P2)
A scheduled "find any inefficiency, check the news, anything that helps" job re-does broad web
research on every fire with diminishing returns, and now bills at API rates. See Section E for
the prompt critique and a cheaper cadence.

---

## B. Claude-native features we should turn on (2026)

These are first-party and mostly free to adopt:

| Feature | What it buys | Our action |
| --- | --- | --- |
| **Prompt caching** (stable-prefix) | 60–90% off repeated input; cache-read ≈ 10% of input price | Put CLAUDE.md + tool defs + standing context first; keep timestamps/user data out of the cached prefix. **Note:** TTL dropped from 60→5 min in early 2026 — a routine that sleeps >5 min eats a full re-write. |
| **Context editing** (auto-clear stale tool results) | Up to **84% token reduction** on long agentic runs; lets runs finish that would otherwise exhaust context | Enable in any SDK/agent we build (the LangGraph "Odin" router especially). |
| **Memory tool** (file-based, outside context) | +39% task quality with context editing; persists state across sessions without re-loading it into context | Use for the portfolio hub state instead of re-reading 6 files each session. |
| **Tool Search Tool** | **~85%** reduction in tool-definition tokens — loads tool schemas on demand instead of all upfront | Relevant the moment we attach many MCP servers to an agent (we already have a large GitHub MCP surface). |
| **Batch API** | 50% off everything, for non-interactive work | Route nightly/periodic LLM jobs (digests, bulk statement composition) through Batch, not the live API. |
| **`/clear`, `/compact`, `/rewind`, subagents** | Keep main context small | Bake into our working habits + slash commands. |

Combining routing + caching + Batch is multiplicative — field reports land at 79–90%+ total
reduction on suitable workloads.

---

## C. Hybrid local + Claude — we're closer than most shops

We already run the architecture the 2026 guides recommend: **LiteLLM as the gateway, local
models for cheap tasks, Claude as the cloud tier** (`10-ai-orchestration`: LiteLLM on :4040,
Open WebUI on :3000, the `local-reason` / `cloud-gpu-reason` / `cloud-overflow` ladder, the
LangGraph "Odin" supervisor). The industry consensus is 60–80% cost reduction from routing
the simple 60–70% of traffic to local models. **Our gap is usage, not capability.**

Recommended moves, cheapest first:

1. **Add a complexity classifier in front of the ladder.** A tiny local model (or a rules
   pass) tags each task `mechanical | moderate | reasoning` and the router picks the tier.
   Mechanical → local 1.5–7B; reasoning → Claude. This is the "router pattern" every 2026
   guide describes; we have the dispatcher already.
2. **Consider a Claude Code Router / OpenAI-compatible proxy** (e.g. Claude Code Router,
   NadirClaw) so even *coding* sessions can offload trivial edits to a local/cheap model and
   reserve Opus for the hard parts. Caveat: quality drops on the offloaded tier — keep
   anything customer-facing or money-touching on Claude.
3. **Use the box for the funnel's bulk NL work** — lead triage, call-note cleanup, statement
   first drafts — keeping Claude for the judgment calls and the kept-document honesty checks.

### ⚠ Privacy gate before we scale routing (ties to TD-14)
TD-14 already flags that a `sensitive`-tagged task can fail over from `local-reason` to
`cloud-overflow` (Claude cloud) because `allow_cloud=False` isn't enforced at the LiteLLM
failover layer. **Do not expand routing of customer/household data until that fails closed.**
Routing more traffic through the ladder widens the blast radius of that bug. Fix TD-14 first.

---

## D. Better prompting (cheap, compounding)

- **Scope tight.** "Refactor the login function in `auth.ts`" beats "refactor the auth
  module" — less context pulled, fewer tokens, more focused output.
- **Structure with XML-ish tags** (`<context>`, `<task>`, `<constraints>`) to separate
  instructions from data and cut the costly follow-up correction loop ("instruction drift").
- **Ask for terse output** when you don't need prose. A "be terse, no preamble" instruction
  (the "caveman"/concise pattern) cuts output tokens materially on heavy workflows.
- **State the deliverable format up front** (file path, table, diff) so the model doesn't
  produce a long narrative you then ask it to convert.
- **One task per session; `/clear` between.** Don't let yesterday's bug hunt ride along in
  today's feature work.

---

## E. Critique of the request prompt itself

The founder asked me to flag this — fair game.

**What's inefficient about it:**
- **Unbounded scope.** "ANYTHING that could possibly help… anything you could think of" has no
  stop condition, so the agent over-researches and the run is expensive and hard to call
  "done."
- **No success metric.** There's no target ("cut spend 30%", "get session-start context under
  2k tokens"), so output can't be measured against intent.
- **No output spec.** It doesn't say where the answer should land or in what form — left to
  guess (report? PR? doc? notification?).
- **Caps-lock emphasis doesn't help the model** and adds tokens; "keep UP TO DATE… check the
  news… search the web if helpful" is repeated three ways.
- **Run as a frequent recurring routine, it re-pays broad web research every fire** for
  marginal new signal.

**A tighter version:**

> ```
> <task>Audit our Claude usage for cost/efficiency wins.</task>
> <scope>Only: CLAUDE.md size, session-start context, local-vs-cloud routing,
>   prompt caching, and the scheduled-routine cadence.</scope>
> <goal>Concrete changes that cut monthly Claude spend ≥30% or session-start
>   context ≤2k tokens. Skip anything we already do.</goal>
> <output>Append findings to docs/ai-cto/reviews/<date>-efficiency.md as a
>   table: change | est. saving | effort | risk. Notify with the top 3.</output>
> <cadence>Monthly, not daily. One web pass for what changed since last run;
>   otherwise reuse the prior report.</cadence>
> ```

**On cadence:** make this a **monthly** digest that diffs against the previous report, not a
frequent run. The vendor landscape changes weekly but *our* actionable surface doesn't — a
monthly "what changed + are we still leaking" pass captures ~all the value at a fraction of the
spend. (And per Section A5, scheduled runs now cost real credits.)

---

## F. The 2026 cost context (why this is urgent now)

- **June 15, 2026:** Claude Code programmatic usage moved to a dedicated credit pool billed at
  full API rates — scheduled/headless runs are no longer bundled into the subscription. Pro
  gets $20 of credits/mo, Max 5x $100, Max 20x $200.
- **Opus 4.8 tokenizer** counts up to ~35% more tokens per prompt than older models — effective
  cost per task is higher than the sticker rate, which raises the payoff of every reduction
  above.
- **Prompt-cache TTL** fell from 60→5 min in early 2026; a 2026 caching bug caused 10–20×
  inflation for a window — worth monitoring our own token counts for anomalies, not trusting
  the bill blindly.

---

## Recommended action list (for tech-debt / roadmap)

| # | Action | Est. saving | Effort | Risk |
| - | ------ | ----------- | ------ | ---- |
| 1 | Trim all 7 CLAUDE.md to lean rules + links; dedupe house-style block | High (every turn) | Low | Low |
| 2 | Make NARF/ZORT hub-read conditional; add `portfolio-snapshot.md` | Med (every CTO/CFO session) | Low | Low |
| 3 | Fix TD-14 (fail-closed local routing) **before** expanding routing | — (unblocks 4) | Med | — |
| 4 | Add complexity classifier; route mechanical tasks to the t630 ladder | High (60–80% on routed work) | Med | Med (quality on offloaded tier) |
| 5 | Adopt prompt caching layout + Batch API for periodic LLM jobs | High | Low–Med | Low |
| 6 | Enable context editing + memory tool in the LangGraph/Odin agent | High on long runs | Med | Low |
| 7 | Convert this routine to a monthly diff-based digest | Med (avoids repeated research) | Low | Low |
| 8 | Working habits: `/clear` per task, subagents for noisy work, terse output | Med | None | None |

---

## Sources (retrieved 2026-06-28)

- Anthropic — Managing context, context editing, memory tool: https://anthropic.com/news/context-management · https://platform.claude.com/docs/en/build-with-claude/context-editing
- Anthropic — Token-saving updates / advanced tool use (Tool Search Tool): https://claude.com/blog/token-saving-updates · https://www.anthropic.com/engineering/advanced-tool-use
- Claude Code docs — manage costs, prompt caching, what's new: https://code.claude.com/docs/en/costs · https://code.claude.com/docs/en/prompt-caching · https://code.claude.com/docs/en/whats-new
- Prompt caching cost guides (5-min TTL, 60–90% savings): https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026 · https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363
- Hybrid local/cloud architecture & routing: https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/ · https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs · https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide
- LLM routers (Claude Code Router, NadirClaw): https://github.com/NadirRouter/NadirClaw · https://www.morphllm.com/claude-code-router
- Claude Code token-saving practices & June pricing: https://composio.dev/content/ways-to-cut-token-consumption-in-claude-code · https://blog.getbind.co/claude-code-pricing-changes-june-15-what-youll-actually-pay-2026/ · https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/
