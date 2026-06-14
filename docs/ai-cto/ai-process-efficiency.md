# AI Process Efficiency — Audit & Recommendations

**Author:** NARF (AI CTO), automated review · **Date:** 2026-06-14
**Scope:** the human↔AI process across all A777ance repos — token cost, prompting,
local/cloud hybrid routing. A living document; the field moves weekly, so re-run this
audit roughly monthly.

> TL;DR — The infrastructure is already right (LiteLLM gateway, a reasoning ladder, a
> local model on the t630). The waste is in **what we feed Claude every session**: our
> `CLAUDE.md` files are 5–10× the recommended size and load on every turn, and our
> session-start rituals read ~10 files before any work starts. Fixing those two things is
> the single biggest, cheapest win. Then: route the easy 60–70% of tasks to the local
> model we already run, and turn on prompt caching + Batch API for statement generation.

---

## 1. The biggest finding: our context baseline is bloated

Every `CLAUDE.md` is re-sent to the model on **every turn of every session** — it's a
fixed tax you pay before typing a word. Current best practice is to keep it **under ~500
tokens** and push detail into files loaded on demand. Ours (chars ÷ 4 ≈ tokens):

| Repo | `CLAUDE.md` size | ≈ tokens | vs. 500-tok target |
| ---- | ---------------- | -------- | ------------------ |
| localDNS | 20.5 KB | ~5,100 | **10×** |
| DESIGN (this repo) | 18.0 KB | ~4,500 | **9×** |
| MARKETING | 10.7 KB | ~2,700 | **5×** |
| customers | 4.1 KB | ~1,000 | 2× |
| claude-code-homelab | 2.9 KB | ~725 | ~1.5× |
| Azure-lab | 2.3 KB | ~575 | ~1× |

Two compounding problems on top of raw size:

- **The House-style block is duplicated verbatim in all 7 repos** (~1.5 KB / ~370 tokens
  each). That's the same text re-billed seven ways, and re-sent every turn.
- **Session-start rituals read ~10 files before work begins.** This repo's `CLAUDE.md`
  tells the agent to read 4 NARF files + 6 ZORT files at session start. Tool-call output
  (file reads) is the single largest drain on a token budget — bigger than conversation
  length. We're front-loading the most expensive category by default.

### Fixes (ranked by payoff ÷ effort)

1. **Slim each `CLAUDE.md` to a thin core** (what the repo is, the 3–5 hard rules, a map
   of where detail lives) and move the rest into the files already referenced under
   "Further reading." Target ≤ 800 tokens for the big three. *Pure win — no new habit.*
2. **De-duplicate House style.** Put it in one file (e.g. `docs/house-style.md` in DESIGN)
   and have each `CLAUDE.md` link to it in one line instead of pasting the block. Saves
   ~370 tok × every turn × every repo.
3. **Make session-start reads on-demand, not automatic.** Replace "at session start, read
   these 10 files" with "current state lives in `portfolio.md`; read it when a task needs
   cross-repo context." Most sessions touch one repo and don't need the CFO runway.
   Better still: collapse the live state into a single short `STATE.md` pointer the agent
   reads once, that links out only when needed.
4. **Lean on Skills for progressive disclosure.** A Claude Code *skill* loads only when
   relevant. The NARF/ZORT session rituals and the bulky stage detail are natural skills:
   they cost ~0 tokens until invoked, instead of riding in `CLAUDE.md` every turn.

Estimated baseline reduction from items 1–3 alone: roughly **6–8K tokens off the top of
every single turn** in the heavy repos.

---

## 2. Use the hybrid stack we already built

We're ahead of most write-ups here — `10-ai-orchestration` already has a LiteLLM gateway,
a reasoning ladder (`local-reason` on the t630, `cloud-gpu-reason` on a rented GPU,
`cloud-overflow` to Claude), and an OpenAI-compatible front door. The gap is that the
**day-to-day workflow doesn't actually route through it** — it goes straight to Claude.

Industry numbers: ~60–70% of real workloads are simple (classify / extract / format), only
~10% need a frontier model. Routing the easy bulk to a local model cuts spend **60–80%**.

**A777ance tasks that should run on the local model, not Claude:**

| Task | Why it's local-able |
| ---- | ------------------- |
| `tools/check-docs.py` triage, link/anchor fixes | Mechanical; no reasoning |
| Roster / `sidecar.json` validation & schema checks | Pattern matching |
| Statement *data prep* (shaping `stats/*.json`) | Deterministic transform |
| First-draft "Handled For You" log entries | Templated, then human/Claude polish |
| Commit-message drafting, changelog formatting | Low-stakes text |
| Routine "what changed" summaries | Summarization, the local model's strength |

**Reserve Claude (and Opus specifically) for:** architecture decisions (ADRs), the honesty
review on customer-facing numbers, multi-repo reasoning, and anything where a wrong answer
ships to a paying household.

> ⚠️ Privacy gate first: **TD-14** is open — a `sensitive`-tagged task can currently fail
> over from `local-reason` to `cloud-overflow` (Claude cloud). Don't expand routing of
> customer data through the ladder until `local-reason` has a local-only, fail-closed
> fallback. Honesty/privacy beats the token saving.

---

## 3. Turn on the cheap-mode levers for statement generation

The monthly statement run is a textbook **Batch + cache** workload: many near-identical
requests, a big shared system prompt, no latency requirement. If/where the generator calls
a hosted model:

- **Prompt caching** — up to **90%** off repeated input (the shared template/system
  prompt). Code-assistant / RAG-shaped workloads see 88–95%.
- **Batch API** — flat **50%** off all tokens for async jobs that can wait up to 24h. The
  monthly run easily tolerates that.
- **Stacked**, these reach ~**95%** off standard pricing. For a "penny a home" generator,
  that's the difference between a penny and ~a twentieth of one at scale.

Action: confirm whether `generate_client.py` / `compose.py` hit a hosted model at all
(they may be pure-template today). If they do, wire caching + batch before customer count
grows. If they don't, note it — pure local templating is already optimal and needs nothing.

---

## 4. Claude Code session hygiene (habits, ~0 cost to adopt)

- **Default to Sonnet; escalate to Opus deliberately.** Opus is ~5× Sonnet per token. This
  routine and most edits don't need 4.8. Start sessions on Sonnet 4.6; switch up only for
  deep analysis. (`/fast` keeps Opus but speeds output — orthogonal to cost.)
- **`/clear` between unrelated tasks.** A long thread re-bills the whole history every turn.
- **`/recap`** (new April 2026) summarizes where you left off without replaying the thread.
- **Compact earlier** — override the default ~95% trigger down to ~70% for routine work.
- **Narrow the scope in the ask.** "Fix the link in `06/README.md`," not "audit the docs."
  Smaller scope → less context pulled in → fewer tokens.
- **Don't paste large blobs.** Point the agent at a path; let it read only what it needs.
- **Delegate fan-out reads to a subagent.** Anything that needs reading 3–4+ large files to
  produce a *summary* should go to a subagent — it works in an isolated window and returns
  only the conclusion, keeping the main context clean. But don't over-delegate: each
  subagent gets its own window, so indiscriminate use *raises* total tokens. Rule of thumb:
  3–4 agents max, use for research/exploration, not for everything.

---

## 5. Heads-up: news that affects us (as of June 2026)

- **Agent SDK / `claude -p` billing split (June 15, 2026):** on subscription plans, SDK and
  headless `claude -p` usage draws from a **separate monthly Agent SDK credit**, distinct
  from interactive limits. Relevant because our automations (stage 11, scheduled routines
  like this one) may run headless — watch that this new bucket doesn't throttle the glue.
- **New Claude Code primitives worth adopting:** `/reload-skills` (no restart), `SessionStart`
  hooks can install skills mid-session (`reloadSkills: true`), skills/commands can set
  `disallowed-tools` in frontmatter to shrink the active toolset, and a `MessageDisplay`
  hook can transform output. These make the "Skills for progressive disclosure" move in §1
  cleaner to implement.

---

## 6. On the prompt that triggered this review (the meta-ask)

The founder's request was effective — it got a real audit — but it modeled a few of the
inefficiencies it asked about, so worth naming:

**What worked:** open framing invites breadth; "search the web / keep up to date / check
the news" correctly signaled this is a freshness-sensitive topic (good — memory would've
been stale); "if THIS prompt is inefficient, tell me" is exactly the right instinct.

**What cost tokens or focus:**
- *Unbounded scope.* "ANYTHING that could help… Perhaps also… Anything you could possibly
  think of." invites the model to sprawl. A bounded ask ("top 5 wins ranked by
  payoff/effort, ≤1 page") gets a tighter, cheaper answer.
- *No output contract.* It didn't say where the answer should land or in what shape — for a
  scheduled routine nobody's watching, that matters (the output has to be a file + a
  notification, not chat). Naming the deliverable up front avoids re-work.
- *Stacked sub-questions* (token use + prompting + other AI + hybrid local/cloud + news)
  are five tasks in one. Fine for a research routine, but for interactive work, one task
  per turn keeps context lean.

**A tighter rewrite for next time:**

> "Audit our AI process for cost/efficiency. Use web search (cite sources, June 2026).
> Output: a ranked list of the top 5 changes by payoff ÷ effort, each with the concrete
> action and rough saving. Cover: CLAUDE.md/context size, local↔cloud routing on our
> existing LiteLLM stack, and prompt caching/batch for statements. Write it to
> `docs/ai-cto/ai-process-efficiency.md` and notify me with the headline. ≤1 page."

Same intent, bounded scope, explicit deliverable, lower token cost, easier to act on.

---

## Recommended order of work

1. Slim the big-three `CLAUDE.md` files + de-dupe House style (§1.1–1.2) — do first.
2. Make session-start reads on-demand / move rituals to Skills (§1.3–1.4).
3. Close **TD-14**, then route the §2 task list through LiteLLM to the local model.
4. Check whether the statement generator calls a hosted model; if so, add caching + batch (§3).
5. Adopt the session-hygiene habits (§4) — free, immediate.

## Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Reduce Claude Code Costs 60% With These Four Habits — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo.io](https://www.tembo.io/blog/claude-code-subagents)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [What Is LiteLLM? (2026 Guide) — a2a mcp](https://a2a-mcp.org/blog/what-is-litellm)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Batch processing — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [Claude Cost Optimization 2026: Batch API + Prompt Caching — PE Collective](https://pecollective.com/tools/claude-pricing-guide/)
- [Stop Wasting Your Tokens: Efficient Runtime Multi-Agent Systems — arXiv](https://arxiv.org/html/2510.26585v2)
- [Claude Code Updates — June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
- [Claude Code & Agent SDK Hooks (2026) — Morph](https://www.morphllm.com/claude-code-hooks)
