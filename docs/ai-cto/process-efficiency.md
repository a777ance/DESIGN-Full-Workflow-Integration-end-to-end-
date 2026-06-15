# Process efficiency — the user ↔ AI loop

**Author:** NARF (AI CTO) routine · **Date:** 2026-06-15 · **Status:** review, then act on §1
**Scope:** how we (the founder) and the AI (Claude Code / the API) work together — where
tokens and time leak, and the better way. Companion CFO view: token spend is a line item
ZORT should track (see §6).

This is a routine output: a standing instruction asked for an up-to-date audit of our
working process. Findings are ordered **highest-leverage first** (this section is an
audit, not a walkthrough, so house-style block-reversal doesn't apply).

---

## 0. The one-line answer

We already have the *right architecture* for cheap AI (the stage-10 LiteLLM router +
reasoning ladder + the deterministic dispatcher). The leak isn't the design — it's that
**(a)** every session pays a large fixed "context tax" from six long `CLAUDE.md` files,
**(b)** the cheap-local tier is wired for *chat* but not for the *bulk drudge work* we
actually hand the cloud, and **(c)** our prompts are often unbounded ("do ANYTHING that
helps"), which buys breadth at frontier-token prices. Fix those three and most of the
spend goes away without losing any capability.

Industry baseline for 2026: a cheap-first / cascade router cuts blended LLM cost
**30–85%**, and mature teams run **60–95% of traffic on a cheap/local tier**, escalating
only the hard ~20% to a frontier model. We are positioned to capture that and currently
aren't.

---

## 1. Do these now (highest leverage, low effort)

| # | Action | Why it pays | Effort |
| - | ------ | ----------- | ------ |
| 1 | **Cut the context tax.** The six `CLAUDE.md` files total ~1,040 lines (~9–12k tokens) and are injected *before the first word*, every turn, every session. The 35-line house-style block is duplicated verbatim in all six. Trim each `CLAUDE.md` to a tight "read-first" core; push detail into `README`/`network-context` that the model opens only when needed. | A 5k-token `CLAUDE.md` costs 5k tokens every turn forever. Halving the always-on context is a permanent per-turn discount and a *better* cache prefix (see #2). | 1–2 h |
| 2 | **Stop editing `CLAUDE.md` mid-session; keep stable content stable & first.** Prompt caching gives a ~90% discount on the cached prefix, but only when the prefix doesn't change. Editing a project file or reordering tools mid-session invalidates the cache and you re-pay full price. Batch instruction changes between sessions. | Caching is the single biggest API lever; real-world wins are 5–15% when prefixes drift, vs. the 70–90% ceiling when they're stable. | habit |
| 3 | **Route the drudge to local.** Wire the *real* cheap-first split we designed: doc edits, summaries, classification, first-draft prose, link-checking, "which file is this" → `local-fast`/`local-smart` (Qwen 2.5 on the t630) or Open WebUI. Reserve Claude Code/API for the hard 20% (architecture, multi-file refactors, the kept-document honesty calls). | The 30–85% routing win is only captured on tasks we *actually* route. Today the local tier serves chat; the bulk drudge still goes to frontier. | 0.5 day |
| 4 | **Bound the prompt.** Give scope + a token/▢time budget + an output shape. "Audit X and Y, ≤2 pages, push a doc" beats "find ANYTHING that helps." (This very task is the worked example — see §4.) | Unbounded prompts buy a wide, expensive search every time. A scoped prompt is cheaper *and* sharper. | habit |
| 5 | **Prune always-loaded tools / MCP.** Each connected MCP server injects its tool schemas into context. The GitHub MCP alone is ~50 tools. Prefer the deferred-tool / `ToolSearch` pattern (load a schema only when needed) and disable MCP servers a given repo doesn't use. | Tool schemas are pure overhead on the cache prefix; trimming them shrinks every turn. | 0.5 h |

---

## 2. The token leaks, ranked

1. **Fixed context tax (biggest).** ~1,040 lines of `CLAUDE.md` across repos, all injected
   up front. In a multi-repo session (like this one) *several* load at once. Duplicated
   house-style blocks are the easiest cut. **Target: each `CLAUDE.md` ≤ ~120 lines of
   genuinely always-needed briefing; everything else one `Read` away.**
2. **Cache misses from churn.** Any mid-session edit to a file in the stable prefix, a
   reordered tool list, or a model swap re-bills the whole prefix at full rate. Treat the
   prefix as immutable during a session.
3. **Unbounded / kitchen-sink prompts.** "Anything that could help" + "search the web" +
   "check the news" fans out into many searches and a long synthesis. Great for a
   *scheduled* divergent sweep (fine here); expensive as an everyday habit.
4. **Frontier model doing cheap work.** Summaries, doc tidy-ups, link checks, commit-message
   drafting, and "what does this file do" are Haiku/local-class tasks being run on Opus/Sonnet.
5. **Re-reading instead of recapping.** Long sessions that replay history rather than using
   `/compact` (summarize history → shorter prefix) or `/recap` (reuses the parent cache for
   near-zero cost) carry a growing tail every turn.
6. **PR-babysitting loops.** Subscribed PR-activity sessions that re-investigate on every
   webhook event can rack up tokens; keep the per-event work scoped and lean on the diff as
   the record rather than re-deriving state.

---

## 3. The hybrid we already designed — close the last mile

Stage 10 (`localDNS/10-ai-orchestration/`) is genuinely good and matches 2026 best
practice: **one OpenAI-compatible front door (LiteLLM), whole-model backends, a
deterministic privacy gate, a reasoning ladder (light-local → rented-GPU → cloud
overflow), and a scripted dispatcher** — *route, don't shard*. The cheap-first cascade the
industry now recommends is exactly this shape.

What's missing is **usage, not architecture**:

- **The dispatcher's cheap-first rule is designed but the drudge still goes to frontier.**
  Land the `if/elif` table so the common, low-sensitivity tasks default to `local-fast`/
  `local-smart`, and only the flagged-hard or flagged-cloud tasks reach Claude. The privacy
  lock (sensitive → local-only, no cloud fallback) already exists — extend the same table
  with a *cost* axis, not just a privacy axis.
- **Consider a stronger local coder.** 2026 open weights (Qwen 3 Coder, DeepSeek V4, Kimi
  K2.6) land within a few points of frontier on routine coding at a fraction of cost; the
  32B-class is self-hostable. The t630's CPU can't run those well — but the **rented-GPU
  path we already built** (`cloud-gpu-reason` over Tailscale) can host one for a heavy
  session, then stop. That turns "the hard 20%" cheaper too, not just the easy 80%.
- **Keep the routing decision LLM-free.** The blueprint's invariant — *no model in the
  routing decision* — is correct and is itself a token saving. Don't regress it into an
  LLM-classifier.
- **Measure the blend.** Add a one-line JSONL route log (the dispatcher already has the
  hook) and report monthly: % local vs. cloud, $ saved. Without the number we can't tell if
  we're hitting the 60–95%-local target.

---

## 4. Critique of the prompt that launched this (as requested)

The launching prompt was, in spirit: *"Find inefficiencies in our process. Reduce token
use. Better prompting? Leverage other AI, hybrid local+cloud. ANYTHING that could help.
Search the web, check the news, keep up to date. Also critique this prompt."*

**What it did well:** clear intent; explicitly asked for current/dated info; asked for a
self-critique; and — crucially — it was run as a **scheduled routine that pushes a doc**,
which is the *right* delivery mode (no human round-trips, output is durable).

**Where it's inefficient:**

- **Unbounded surface.** "ANYTHING that could help" has no scope, no budget, no stop
  condition — it invites the widest (most expensive) possible search every run. For a
  one-off divergent sweep that's acceptable; as a recurring routine it should be scoped.
- **No output contract.** No length, format, or destination specified, so the model has to
  guess (here: a ≤2-page doc pushed to `docs/ai-cto/`). Stating it removes a guess and trims
  output tokens.
- **"Check the news / keep up to date" with no cadence.** Re-researching the whole field on
  every run is wasteful. Better: a cheap-local first pass that only escalates to web search
  + frontier synthesis when something actually changed.

**A tighter rewrite (reusable as the routine's standing prompt):**

> *"Monthly: audit our AI working process for cost leaks. Check `localDNS/10-ai-orchestration`
> and the repo `CLAUDE.md` sizes against current best practice (1–2 fresh web sources max,
> only if something material changed since last run). Output: update
> `docs/ai-cto/process-efficiency.md` in place — keep §1 to the top 5 actions, note what
> changed since last run, ≤2 pages. Run the cheap-local model for the first pass; escalate
> to me only if you find a >$X/mo or >Y% saving. Don't notify if nothing changed."*

That keeps every quality this prompt wanted while bounding the spend and giving the model a
clear target.

---

## 5. Claude Code hygiene worth adopting (2026 features)

- **`/compact`** to fold history into a summary when a session runs long; **`/recap`** on
  resume (reuses the parent prompt cache, near-zero cost) instead of replaying.
- **Microcompact / context editing:** Claude Code now spills tool results >50KB to disk and
  keeps a ~2KB preview — lean into tools that read targeted slices rather than whole files
  (we already do: dedicated Read/Grep/Glob over `cat`/`grep`).
- **Subagents for fan-out + cheap routing:** push light, parallelizable lookups to subagents
  (and, where supported, a Haiku-class model) so the main, expensive context stays small.
- **Skills over bespoke MCP** where possible: a skill is loaded on demand; an always-on MCP
  server taxes every turn.
- **Incremental, named requests** ("edit the login function in `auth.ts`") over broad ones
  ("refactor the auth module") — smaller scope, fewer tokens, sharper output.

---

## 6. For ZORT (CFO) — make it a tracked number

Token/API spend is currently invisible in the books. Add it:

- A monthly **AI-spend KPI** in `docs/ai-cfo/metrics.md`: $ cloud API + $ rented-GPU hours,
  with the **local-vs-cloud blend %** from the dispatcher log as the efficiency ratio.
- Target the industry blend (**≥60% local**) and the cascade saving (**30–85%**) as the
  goal line; if we're below it, §1/§3 are the levers.
- This ties to the "make the network dull / every problem is a cost" philosophy: an unbounded
  AI habit is the same kind of silent recurring cost a flat-retainer operator wants gone.

---

## Sources (2026, dated where checked 2026-06-15)

- [How to Reduce Claude Code Token Usage (agensi.io)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude Code Token Optimization (buildtolaunch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Claude Code Token-Saving Guide — models, MCP, CLAUDE.md, skills & cache (knightli.com)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Claude Code Guide 2026 — 25 features (MarkTechPost, 2026-06-14)](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [How Claude Code Compresses Context — the 5-level pipeline (HarrisonSec)](https://harrisonsec.com/blog/claude-code-context-engineering-compression-pipeline/)
- [Intelligent LLM Routing: cost & quality-aware selection (TrueFoundry)](https://www.truefoundry.com/blog/llm-routing-cost-quality-aware-model-selection)
- [LLM Routing in production — stop paying frontier prices for simple queries (TianPan)](https://tianpan.co/blog/2025-10-19-llm-routing-production)
- [The Best LLMs for Agentic Coding in 2026 (dev.to)](https://dev.to/danishashko/the-best-llms-for-agentic-coding-in-2026-real-world-not-just-benchmarks-96n)
