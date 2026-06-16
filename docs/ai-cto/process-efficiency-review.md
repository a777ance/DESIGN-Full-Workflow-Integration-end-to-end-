# AI Process Efficiency Review — Token & Workflow Audit

*Prepared 2026-06-16. A standing review of how we (the founder + the AI agents NARF/ZORT/
Claude Code) spend tokens and attention across the A777ance repos. Newest entry first, per
house style.*

> **Scope note.** This is an advisory audit, not a change to the funnel or the product. It
> looks at one thing: where the human↔AI loop wastes tokens, money, and focus — and the
> cheapest fixes. Findings are ranked by payoff. Measured figures are from this repo set on
> 2026-06-16; "tokens" are estimated at ~1.33× word count (English prose) unless noted.

---

## TL;DR — the five that matter

1. **Every session pays a ~21,000-token "boot tax" before any work happens** (DESIGN repo).
   That's the single biggest lever. Most of it is *unconditional* reading we could make
   *conditional*. **Fix first.**
2. **The "House style" block is copy-pasted verbatim into all 6 `CLAUDE.md` files** (~250
   words × 6). Pure duplication, re-sent on every session of every repo.
3. **The reverse-ordering house style (newest-first / Z→A / reversed walkthrough blocks) is
   itself a tax** — it fights the model's training grain, so it costs reasoning tokens and
   raises error rates on every read and write.
4. **We already own a hybrid local/cloud LLM stack** (LiteLLM + Ollama, localDNS stage 10)
   **and aren't routing this workflow's cheap tasks to it.** 60–80% cost cuts are on the table
   for bulk/simple work.
5. **The interactive Claude Code loop has free wins we're not taking**: prompt caching, `/clear`
   between tasks, subagents for search, Haiku/Sonnet for bulk, Batch API for the monthly run.

---

## 1. The session-start "boot tax" (highest payoff)

What loads before the agent does a single useful thing in a **DESIGN** session:

| Loaded every session | Words | ~Tokens |
| --- | ---: | ---: |
| 6× `CLAUDE.md` (all in-scope repos, auto-loaded by the harness) | 8,030 | ~10,700 |
| DESIGN-mandated reads — AI CTO (`portfolio` + `roadmap` + `tech-debt` + `decisions`) | 3,258 | ~4,300 |
| DESIGN-mandated reads — AI CFO (`portfolio` + `decisions` + `metrics` + `runway` + `budget`) | 4,616 | ~6,100 |
| **Total fixed overhead, before the task** | **~15,900** | **~21,000** |

At Opus 4.8 input pricing ($5/MTok) that's **~$0.10 of pure boilerplate per session**, *re-sent
on context rebuilds*, and — more costly than the dollars — it crowds the working context and
dilutes attention before the real task starts. CLAUDE.md instructs reading **9 state docs at
session start regardless of what the session is for.** A session that just fixes a typo in a
README pays the full CFO-runway-and-metrics tax.

**Fixes (cheapest first):**
- **Make the reads conditional, not unconditional.** Change CLAUDE.md from "at session start,
  read these 9 files" to "*when the task touches finances*, read the CFO docs; *when it touches
  architecture/roadmap*, read the CTO docs." A typo fix should load neither.
- **Collapse the 9 state docs into one short `STATE.md` per role** (a 1-screen snapshot: current
  phase, open decisions, last 3 changes) and link out to the long logs. The agent reads the
  snapshot always, the full log only on demand. This is *progressive disclosure* — the pattern
  the statement generator already uses for "Have you tried?".
- **Prompt-cache the stable prefix.** For the NARF/ZORT API agents, the CLAUDE.md + state docs
  are a near-constant prefix. A `cache_control` breakpoint makes repeat reads cost ~0.1×
  (90% off the cached span). Keep the volatile bits (today's date, the specific question) *after*
  the breakpoint or the cache silently misses. (In Claude Code the CLAUDE.md is already in the
  cached system prompt — but the 9 mandated `Read`-tool pulls are fresh tokens each time, so #1
  and #2 above still apply.)

## 2. CLAUDE.md files are 2–3× larger than they earn

`localDNS` (2,728 w) and `DESIGN` (2,608 w) CLAUDE.md are essentially full handbooks. CLAUDE.md
is re-injected on **every turn** — it's the most expensive real estate we have. Best practice
(and Anthropic's own guidance) is to keep it to the load-bearing few hundred words and link the
rest. The funnel diagram, the stage-map table, the verification walkthrough — valuable, but they
belong in `README.md` (which is read on demand), not in the always-on briefing.

- **Target:** each CLAUDE.md ≤ ~600 words of "what you must know to not break things," everything
  else one click away. Rough saving: ~5,000 words (~6,600 tokens) off every session.

## 3. The "House style" block is duplicated 6×

The identical ~250-word ordering/typography section sits verbatim in all six CLAUDE.md files.
It's maintained in six places and paid for in six places.

- **Fix:** put it in one file (e.g. `localDNS/docs/house-style.md` or a shared gist), and in each
  CLAUDE.md replace the block with a one-line link. Saves ~1,250 words of duplication and removes
  a six-way sync hazard.

## 4. The reverse-ordering convention is a hidden, recurring tax

This one is uncomfortable because it's deliberate house style — but an honest efficiency review
has to name it. **Newest-first logs, descending (Z→A) alphabetical lists, and reversed
walkthrough blocks all run against the grain of how the model was trained.** Effectively every
corpus the model learned from is chronological, A→Z, and forward-stepped. Consequences we pay
for repeatedly:

- **Reasoning tokens on every read.** The model re-orients ("oh, this list is reversed") before
  it can use the content — and is measurably more error-prone at it (off-by-one, wrong-end edits).
- **Write-time friction.** Inserting a log entry "newest-first" means the model must locate the
  top, not append — more tokens, more chance of a misplaced edit, noisier diffs.
- **Onboarding cost.** Every new contributor (human or AI) re-derives the rule.

It's a real aesthetic choice and a legitimate one — but if the goal is *AI process efficiency*,
this convention is a standing drag. **Recommendation:** keep it for customer-facing surfaces if
it's part of the brand, but consider exempting *internal, AI-maintained* files (logs, decision
records, trackers) and letting those be plain chronological/A→Z. The walkthrough-block reversal
in particular ("present blocks last-first, keep steps forward, never renumber") is the costliest
— it's a rule the agent has to actively hold in working memory the whole time it edits a guide.

## 5. Route cheap work to the local stack we already built

localDNS stage 10 already runs **LiteLLM (router) + Ollama + a reasoning ladder**
(`local-reason` on the t630, `cloud-gpu-reason` for heavy work). That infrastructure exists for
the homelab but the *business* agents (NARF/ZORT/Claude Code work) route everything to frontier
Opus. Industry reports in 2026 put hybrid local-first/cloud-fallback savings at **60–80%** on
mixed workloads.

- **Send to local SLM or Haiku 4.5 ($1/$5):** drafting boilerplate, classifying leads, formatting
  logs, summarizing, first-pass extraction, commit-message generation.
- **Send to Sonnet 4.6 ($3/$15):** routine edits, doc updates, most CRM/statement glue.
- **Reserve Opus 4.8 ($5/$25):** architecture, financial reasoning, anything on the kept document.
- The `claude-api` skill defaults everything to Opus — fine for hard work, wasteful for bulk. Set
  per-task model selection in the agent configs.

## 6. Free wins in the interactive Claude Code loop

- **`/clear` between unrelated tasks.** Long threads re-read the whole history every turn — the
  biggest silent drain in interactive use. Clear when you switch context.
- **Use subagents/Explore for searches.** Fan-out reads happen in an isolated context on a cheaper
  model; only the conclusion returns to the main thread. Keeps the expensive context lean.
- **`.claudeignore`** for build output, vendored data, `.git`, generated statements — stop them
  ever entering context.
- **Batch API (50% off)** for the non-interactive monthly run: generating statements across all
  households, the doc-integrity sweep, bulk classification. None of it is latency-sensitive.
- **Keep `tools/check-docs.py` deterministic.** Good instinct already — link-checking is a script,
  not an LLM job. Don't let that migrate into an agent prompt. Same for any future lint/format.
- **`/recap`** (new April 2026) to resume a session without replaying the whole conversation.

---

## On the prompt that triggered this review (you asked)

The prompt was clear and well-motivated, but it's optimized for *coverage* ("ANYTHING that could
help"), which makes the agent do broad, expensive exploration. Three cheap improvements:

1. **Name the cost you're optimizing.** "Reduce tokens" across *what* — the interactive Claude
   Code sessions, the NARF/ZORT API agents, or the statement generator? Each has a different
   biggest lever. Scoping the target would have cut this analysis in half.
2. **Give a budget or a baseline.** "We spend ~$X/month, mostly on Y" turns an open hunt into a
   targeted one. Without a number, the agent guesses where the spend is.
3. **Split the omnibus.** "Find inefficiencies" + "research best practices" + "critique this
   prompt" are three jobs. One per turn (or one scoped turn) is cheaper and sharper than one
   sweep — which is itself the lesson in finding #1: unbounded context is the cost.

The "keep up to date / check the news" instinct is right and cheap to honor — a dated, scoped
web pass (as done here) beats a from-memory answer for anything pricing- or model-related, which
moves weekly.

---

## Sources

- [Reduce Claude Code token usage by 90% (Medium, Apr 2026)](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [9 Ways to Cut Token Consumption in Claude Code (Composio)](https://composio.dev/content/ways-to-cut-token-consumption-in-claude-code)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (Agensi, 2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: Architecture Guide (SitePoint, 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization (BuildMVPfast, 2026)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LLM Model Routing in 2026: Cost-Quality Optimization (Digital Applied)](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- Anthropic prompt-caching & model pricing (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5; cache reads ~0.1×, Batch API −50%) — `claude-api` skill reference, 2026-06.
