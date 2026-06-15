# Process efficiency review — user ↔ AI workflow (2026-06-15)

A scheduled-routine audit of how we (founder ↔ Claude/AI) actually spend tokens and
turns, what's wasteful, and what to change. Ordered by impact. Numbers are measured
from this repo set on 2026-06-15; token figures are ~`words × 4/3` estimates.

> TL;DR — the biggest lever is **what we load before work starts**, not how we prompt
> mid-task. The DESIGN repo forces ~15K tokens of fixed reading at every session start
> (3.5K CLAUDE.md + ~12K of CTO/CFO ritual docs), and that cost recurs on *every turn*.
> Fix loading first, then turn on prompt caching, then push routine work down to the
> local/cheaper tier we already run.

---

## 1. Findings, by impact

### 1.1 — Session-start ritual is the dominant token sink  ⚠️ highest impact
`CLAUDE.md` §5 (NARF/CTO) tells every session to read 4 docs; §6 (ZORT/CFO) tells it to
read 6 more. Measured:

| Ritual | Files | ~words | ~tokens |
| ------ | ----- | ------ | ------- |
| CTO (NARF) | portfolio, roadmap, tech-debt, decisions | 3,258 | ~4,340 |
| CFO (ZORT) | portfolio, decisions, metrics, runway, budget (+ MARKETING/context) | 4,945 | ~6,590 |
| DESIGN `CLAUDE.md` itself | 1 | 2,608 | ~3,477 |
| **Total before any work** | **11** | **~10,800** | **~14,400** |

That ~14K is paid up front *and re-read on every subsequent turn* in the session. A
10-turn session pays it ~10×.

**Do this:**
- Make the ritual **lazy, not mandatory.** Replace "read these 10 files at session
  start" with "read the relevant hub doc *when the task touches CTO/CFO state*." Most
  sessions touch neither.
- Add a tiny **`docs/INDEX.md`** (≤300 tokens) that lists what each doc covers in one
  line, so the model loads the one file it needs instead of all ten.
- Have the routine/agent state its role at the top (`role: CTO` / `role: CFO` / `none`)
  and only trigger the matching ritual.

### 1.2 — `CLAUDE.md` files are large and partly duplicated
Loaded in full on **every turn** of every session:

| Repo | ~tokens/turn |
| ---- | ------------ |
| localDNS | ~3,637 |
| DESIGN | ~3,477 |
| MARKETING | ~1,926 |
| customers | ~749 |
| claude-code-homelab | ~494 |
| Azure-lab | ~421 |

The **"House style: ordering & typography"** block (~171 words / ~230 tokens) is
copy-pasted **verbatim into all of them**. Useful, but it's loaded once per turn per
repo and drifts out of sync on edit.

**Do this:**
- Trim each `CLAUDE.md` toward a **lookup table**, not a brain dump (the localDNS/DESIGN
  ones read like full manuals). Keep the map + the rules; push the prose to README and
  reference it. Target <1,500 tokens each.
- Make house-style **canonical in one place** (e.g. `claude-code-homelab/templates/` or
  a short `HOUSE-STYLE.md`) and have each `CLAUDE.md` link to it in one line instead of
  inlining the whole block.

### 1.3 — Prompt caching looks unused (90% savings on the table)
Anthropic prompt caching cuts **cached input cost by ~90%** (vs OpenAI's 50%). Given our
large, stable prefixes (CLAUDE.md + ritual docs + tool schemas), this is the single
highest-ROI switch. Reported real-world: a research workflow dropped ~$26 → ~$7.50
across 8 turns; one team went $720 → $72/mo.

**Do this:**
- In Claude Code: enable the longer cache window (`ENABLE_PROMPT_CACHING_1H`) for long
  sessions — keeps the warm cache alive past the 5-min ephemeral TTL.
- In the LiteLLM router (`localDNS/10-ai-orchestration`): turn on caching of the system
  prompt / fixed context for any API-backed workflow. Cache blocks must be ≥1,024
  tokens to qualify — our CLAUDE.md + ritual easily clears that.
- Keep the cacheable prefix **stable** (don't reorder CLAUDE.md mid-day) so reads stay
  warm.

### 1.4 — Model tiering: default down, escalate up
Current pricing (2026-06): **Sonnet 4.6 = $3/$15 per M in/out; Opus 4.8 = $5/$25.**
Sonnet delivers ~85% of Opus quality at ~20% of the cost for routine work
(classification, RAG, content gen, routine tool use). Typical task mix is ~60–70% simple
/ 20–30% moderate / ~10% genuine frontier reasoning.

**Do this:**
- **Default to Sonnet 4.6**; reserve Opus 4.8 for sustained multi-step reasoning where
  quality moves money. This routine is running on Opus — most doc-audit work like it
  would run fine on Sonnet.
- Route classification/extraction/formatting to **Haiku or the local tier.**

### 1.5 — Hybrid local/cloud: we're already set up; use it more
We already run the recommended stack — **LiteLLM gateway + Ollama local + cloud GPU on
demand**, with a reasoning ladder (`local-reason` deepseek-r1:1.5b → `cloud-gpu-reason`
→ `cloud-overflow`). That's ahead of most teams. Industry result: routing ~70% of
queries to the cheapest adequate model cuts LLM cost **60–80%**.

**Do this:**
- Push the **bulk, low-stakes** jobs to the local tier: monthly statement-draft first
  passes, doc-integrity scans (`tools/check-docs.py` is deterministic — no LLM needed),
  log summarization, "Handled For You" rough drafts. Reserve Claude API for the final,
  customer-facing polish and the honesty check.
- Add an explicit **router rule** keyed on task type, not just model name, so "summarize
  / extract / classify" never hits Opus.

---

## 2. Process between user and AI — turn efficiency

From 2026 agentic-prompting research (sources below):

- **One well-built prompt beats conversational back-and-forth.** Structured prompts cut
  errors up to ~76%; once an LLM "takes a wrong turn in a conversation, it gets lost and
  does not recover." Front-load context, constraints, and the success criterion.
- **`/clear` between unrelated tasks** cuts per-message token cost ~30–50% by dropping
  stale context. Don't run a new task in a thread fat with an old one.
- **`/recap` on resume** (Apr 2026) summarizes where you left off without replaying the
  whole transcript.
- **Subagents for fan-out reads.** Anything needing >3–4 large files read is a subagent
  candidate — the subagent burns the tokens reading, returns only the conclusion, and
  the parent context stays lean. (This routine used that pattern.)
- **`.claudeignore` discipline** — measured ~85% context reduction by keeping junk
  out of proactive inclusion; pair with `permissions.deny` for hard blocks.
- **Scope the routine to the repos it needs.** This run loaded all 7 repos' CLAUDE.md
  (~10.7K tokens) when the task only needed to *read* them once. A routine that targets
  one repo shouldn't mount seven.

---

## 3. Critique of the prompt that launched this routine

The originating prompt was, in effect: *"Locate inefficiencies in our process… Is there
a better way to reduce token use? Better prompting? Leverage other AI? Hybrid local +
Claude? ANYTHING. Search the web. Keep up to date. Check the news."*

**What it did well:** set a clear goal (efficiency), named concrete angles (tokens,
prompting, hybrid), and authorized web research + recency. Good creative latitude.

**Where it costs tokens / turns:**
- **Unbounded scope** — "ANYTHING you could possibly think of" has no stopping
  condition, so the agent must guess when "enough" is. Agentic prompts work best as a
  runbook: goal, scope, tools, decision criteria, *and stopping condition.*
- **No output contract** — format, length, or destination unspecified, so the agent
  guesses (report? notification? PR?). State the deliverable.
- **No repo scope / budget** — didn't say "DESIGN repo only" or "spend ≤X." With 7 repos
  mounted, the default is to consider all of them.
- **Several asks bundled** — process audit + prompt critique + model strategy + news
  scan in one shot. Fine for a brainstorm, but each would be cheaper run separately
  with `/clear` between.

**Rewrite that would have been ~cheaper and more deterministic:**

> *"Audit the **DESIGN repo only** for token/process inefficiency in how we work with
> Claude. Cover: (a) session-start loading cost, (b) CLAUDE.md size, (c) where to use
> caching / cheaper models / our local router. Use the web for 2026 best practices.
> Deliver a ≤2-page markdown report committed to `docs/ai-cto/`, top 5 actions ranked by
> impact with rough token/$ savings. Don't open a PR. Stop after the report."*

That version fixes scope, format, length, destination, and stopping condition — the four
things whose absence forces the agent to spend tokens guessing.

---

## 4. The five things to actually do (ranked)

1. **Make the CTO/CFO session-start ritual lazy + add `docs/INDEX.md`.** Saves ~10K
   tokens/session on sessions that don't touch that state (most of them).
2. **Turn on prompt caching** (Claude Code 1h window + LiteLLM system-prompt caching).
   ~90% off the repeated prefix — the highest $/effort ratio here.
3. **Trim CLAUDE.md to lookup tables; de-duplicate house-style into one linked file.**
   Recurring per-turn savings across all 7 repos.
4. **Default to Sonnet 4.6, escalate to Opus only for hard reasoning; send
   classify/extract/summarize to Haiku or the local tier.**
5. **Write task prompts as runbooks** — goal, scope, output contract, stopping condition
   — and `/clear` between unrelated tasks. Scope routines to the one repo they need.

---

## Sources
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Anthropic Prompt Caching in 2026: Cost, TTL, Latency — AI Checker Hub](https://aicheckerhub.com/anthropic-prompt-caching-2026-cost-latency-guide)
- [Prompt Caching is a Must ($720 → $72/mo) — Du'An Lightfoot, Medium](https://medium.com/@labeveryday/prompt-caching-is-a-must-how-i-went-from-spending-720-to-72-monthly-on-api-costs-3086f3635d63)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Opus 4.8 Pricing 2026 — CloudZero](https://www.cloudzero.com/blog/claude-opus-4-8-pricing/)
- [Sonnet 4.6 vs Opus 4.8: Benchmarks & Pricing — llm-stats](https://llm-stats.com/models/compare/claude-sonnet-4-6-vs-claude-opus-4-8)
- [Claude Code Sub-Agents: Context, Cost, Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Claude Code Agents in 2026: what parallel sessions cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Agents At Work: The 2026 Playbook for Reliable Agentic Workflows — promptengineering.org](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)
- [9 tips to write more effective AI prompts — Journal of Accountancy](https://www.journalofaccountancy.com/issues/2026/may/9-tips-to-write-more-effective-ai-prompts/)
- [Writing effective tools for AI agents — Anthropic](https://www.anthropic.com/engineering/writing-tools-for-agents)
