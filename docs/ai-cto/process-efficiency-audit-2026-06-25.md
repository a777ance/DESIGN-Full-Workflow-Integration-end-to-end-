# AI Process Efficiency Audit — 2026-06-25

> Scope: the **process between the human and the AI** across the A777ance repos — token
> use, prompting, model choice, and where the existing local-LLM stack should be doing
> work the Claude API is paying for. Researched against current (June 2026) best practice;
> see Sources at the end. NARF (AI CTO) note — fold the accepted items into `tech-debt.md`.

## TL;DR — the five biggest wins, in order

1. **This routine is running on the most expensive model config that exists.**
   `claude-opus-4-8[1m]` = Opus ($5/MTok in, $25 out) **plus** the 1M-context long-window
   premium. For a recurring *research + summarize* job, that's the wrong tier. Move the
   routine to **Sonnet 4.6** ($3/$15) and let it spawn **Haiku** subagents for the search
   legs. Industry benchmark: three-tier routing cuts ~51–77% vs uniform-Opus with no
   quality loss on this kind of task. **Est. saving on this routine alone: 40–80%.**

2. **Every session loads ~6 large `CLAUDE.md` files (all 7 repos in scope).** That's a
   fixed tax of roughly 8–12k tokens *re-read on context refresh*, whether the session
   touches those repos or not. Scope sessions to the 1–2 repos in play, and trim the
   `CLAUDE.md` files (they're guide-length; CLAUDE.md is loaded before anything, on every
   turn).

3. **You already built the hybrid router the whole industry is now writing blog posts
   about — and it's idle.** `localDNS/10-ai-orchestration/config.yaml` has local-first
   capability tiers (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason`) with cloud
   failover. The cheap/bulk/**private** work is still going to the Claude API. Route it
   local.

4. **`cloud-overflow` defaults to Opus.** Your *failover* tier — the one that fires when a
   local box dies — bills at the top rate silently. Set it to Haiku or Sonnet.

5. **The prompt that launched this audit is itself the textbook inefficient prompt.** No
   scope, no output format, no budget, "ANYTHING that could help," "check the news." That
   forces maximal exploration. A rewritten template is in §5 — you asked, so: yes, it cost
   more than it needed to.

---

## 1. Model choice — stop paying Opus rates for Sonnet/Haiku work

Current price ladder (per 1M tokens, June 2026):

| Model | Input | Output | Cached read (90% off) | Use it for |
| ----- | ----- | ------ | --------------------- | ---------- |
| Opus 4.8 | $5 | $25 | $0.50 | Hard reasoning, architecture, the final synthesis |
| Sonnet 4.6 | $3 | $15 | $0.30 | Almost all implementation + research |
| Haiku 4.5 | $1 | $5 | $0.10 | Search, file ops, classification, link-checks |
| `[1m]` long-context | adds a premium **on top** of the above past ~200k tokens | | | only when the task genuinely needs >200k |

**Actions**
- Set this and similar **routines to Sonnet by default**, escalate to Opus only for the
  synthesis step if a routine proves it needs it. Start interactive sessions on Sonnet too
  (`/model sonnet`), switch up to Opus deliberately.
- Only invoke the **`[1m]` variant** when a task actually needs >200k tokens of context.
  A web-research routine does not — it reads a few pages and writes a page.
- Use **Haiku-backed subagents** (Claude Code's `Explore` agent is read-only and runs on
  Haiku by default) for the "go read N files / search the codebase" legs, so that token
  volume never touches Opus.

## 2. Context hygiene — the per-turn tax

- **Scope the working set.** All 7 repos in scope means ~6 `CLAUDE.md` files in context
  every turn. For a session that only touches `localDNS`, that's 5 files of pure overhead.
  Open Claude on the repo(s) you're actually editing.
- **Trim `CLAUDE.md`.** These files are excellent *guides* but heavy as *always-loaded
  headers*. A 5k-token CLAUDE.md costs 5k tokens on every turn. Keep CLAUDE.md to the
  invariants + a pointer to README for depth; the briefing model already does this, push
  it further. (Pattern: the "token-efficient CLAUDE.md" — terse rules, no prose.)
- **`/clear` between unrelated tasks**, `/compact` with a focus hint
  (`/compact keep the decisions, drop the file dumps`) when a session must continue.
- **Plan mode before expensive runs** (Shift+Tab): review the plan, cut dead ends, *then*
  execute. The biggest single token sink is trial-and-error exploration.
- **Prompt caching is automatic** in Claude Code (system prompt + CLAUDE.md cache at 10%
  on hit). The lever you control is *not re-invalidating it* — don't reorder or edit the
  early context mid-session if you can avoid it.

## 3. Hybrid local + cloud — turn on the router you already built

The current best-practice hybrid architecture (route by **data sensitivity, task
complexity, availability**; smallest-model-that-works; cloud as failover) is *exactly*
what `localDNS/10-ai-orchestration/` already encodes. It is not wired into day-to-day work.

Most workloads are ~60–70% "simple" (classify, extract, format, draft), ~20–30% moderate,
~10% needs a frontier model. Send the bottom two-thirds local:

| Send **local** (t630, ~$0, private) | Keep on **Claude API** |
| ----------------------------------- | ---------------------- |
| First-draft statement narrative / "Handled For You" prose | Final voice/honesty pass on a kept document |
| Roster lookups, field extraction, CSV/JSON munging | Architecture + cross-repo decisions (NARF/ZORT) |
| `check-docs.py`-style link/anchor checks, lint | Anything touching the pricing/strategy reasoning |
| Marketing copy first drafts, summarizing a thread | Security-sensitive review |
| **Anything with real customer data** (privacy!) | |

The privacy angle is a real win for you specifically: the `customers` repo holds real
names + figures. Drafting over that data on a **local** model never crosses the Bifröst —
which is on-brand for a privacy product and removes a "real data to a third party" risk.

**Actions**
- Point a local OpenAI-compatible client (Open WebUI, or scripts) at `ai.home.lan:4040`
  for the bulk/private tasks above. The router already fails over to cloud if the box is
  down.
- **Change `cloud-overflow` from `claude-opus-4-8` to `claude-haiku-4-5`** (or sonnet).
  Failover should be cheap, not the priciest model in the catalog.
- Keep Claude Code for what it's best at (multi-file edits, agentic codebase work); use
  the local router for the high-volume, low-stakes, or private generation.

## 4. Workflow-level

- **Batch related questions** into one prompt instead of a back-and-forth — each round
  re-sends the whole context.
- **Run "keep up to date" scans weekly, not daily.** A news/best-practice sweep that
  changes on a weekly cadence doesn't need a daily Opus run. Or: let a *local* model do a
  cheap first-pass triage and only wake Claude when it flags something.
- **For this routine specifically:** notification is the only output anyone sees (no one
  watches the transcript). So the routine should be cheap to *run* and rich only in the
  *notification* — the opposite of running Opus[1m] to produce a banner.

## 5. The prompt — you asked, so: here's the rewrite

The launching prompt was the canonical "expensive" prompt: open-ended ("ANYTHING"), no
output contract, no scope, no budget, two separate "go explore the whole web" instructions
("search the web", "check the news"). 2026 prompt research is blunt about this:
*specifying the output format up front cuts revisions ~60%; specificity halves iteration;
constraints beat adjectives; structure, not length.*

**Reusable template for this exact job:**

> Audit our human↔AI process for cost/efficiency. **Output:** a ranked list of ≤7
> concrete changes, each with (a) the change, (b) est. % token saving, (c) effort.
> **Scope:** model choice, context/CLAUDE.md size, local-vs-cloud routing, prompting.
> **Constraints:** ground every claim in our actual config files or a dated source; mark
> anything you couldn't verify as "unverified"; ≤1 web search per sub-question; don't
> rewrite any repo files — propose only. **Budget:** finish in one pass, Sonnet-tier.

What changed and why it's cheaper: a capped, formatted deliverable stops open-ended
sprawl; "≤1 search per sub-question" bounds the most expensive action; "propose only"
prevents speculative edits; "Sonnet-tier" sets the model expectation; "ground in our
config or a dated source" is the honesty rule you already apply to Statements.

---

## Verified vs. unverified

- **Verified against your repos:** routine model is `claude-opus-4-8[1m]`; 7 repos in
  scope with full CLAUDE.md files; `10-ai-orchestration/config.yaml` has local tiers +
  `cloud-overflow: claude-opus-4-8` + a sensitivity gate.
- **From dated external sources (June 2026), not measured on your traffic:** the 40–88%
  saving ranges, the 60/30/10 task-complexity split, the per-token prices. Treat the
  percentages as directional until measured with `/usage`.

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to Reduce Claude Code Token Usage (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude API Cache Pricing 2026 — TokenMix](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization (2026) — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LLM model routing with Ollama + LiteLLM — Medium](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Best AI Model for Coding Agents in 2026: A Routing Guide — Augment Code](https://www.augmentcode.com/guides/ai-model-routing-guide)
- [Prompt Engineering Best Practices in 2026 — UC Strategies](https://ucstrategies.com/news/prompt-engineering-best-practices-in-2026-the-ultimate-guide-to-better-ai-prompts/)
- [Claude Prompt Engineering Best Practices 2026 — Prompt Builder](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026)
