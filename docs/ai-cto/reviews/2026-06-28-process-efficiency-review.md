# 2026-06-28 — Process efficiency review: the user↔AI loop

**Question asked:** Where are the inefficiencies in how we work with the AI? How do we cut
token use, prompt better, and lean on the local LLM ladder we already run? Keep it current.

**Scope:** the *process* between a human and Claude across the A777ance repos — not any one
feature. Measured against this repo's live state plus best-practice sources from the last ~60
days. Ranked by payback. Newest-first per house style; this is a point-in-time review.

---

## TL;DR — do this first

**Trim and de-duplicate the CLAUDE.md files.** This session loaded **~14.6K tokens of
CLAUDE.md on *every* turn** (six repos, because all are in GitHub scope at once), and the
~250-word house-style block is copy-pasted verbatim into all seven. That tax is paid on every
message of every session before a single line of work happens. Fixing it is free, reversible,
and compounds across every future session. Everything else below is real but smaller.

---

## The ranked findings

| # | Lever | Current state (measured) | Fix | Est. saving | Effort |
| - | ----- | ------------------------ | --- | ----------- | ------ |
| 1 | **CLAUDE.md context tax** | 6 files auto-loaded/turn ≈ 14.6K tok. DESIGN 4.5K, localDNS 5.1K, MARKETING 2.7K. House-style block duplicated ×7 | Trim each to always-true facts; push stage detail to READMEs Claude reads on demand; de-dup house style into ONE file the others link to | 30–90% of per-turn fixed cost | Low |
| 2 | **Scope sessions to one repo** | All 7 repos in scope every session → every CLAUDE.md loads even when irrelevant | Work one repo per session where possible; only widen scope for genuine cross-repo tasks | Stacks on #1 | Low |
| 3 | **Use the local LLM ladder we already run** | LiteLLM + Ollama on t630 (`local-reason` deepseek-r1:1.5b, `cloud-gpu-reason`, `cloud-overflow`) exists but is under-used for routine drafting | Route simple work (extract/classify/summarize/draft) local; reserve Claude for reasoning, codegen, customer copy | 60–80% on routed tasks (10× on the simple slice) | Med |
| 4 | **Prompt caching for our own API tooling** | Claude Code caches automatically; our statement generator + router do not exploit it | Put stable content first; never interpolate date/names into the cached prefix | cache reads = 0.1× input (≈90% off); 40–70% on agent loops | Med |
| 5 | **Claude model/subagent routing** | Daily AI-CTO reviews + doc edits run at top tier; subagents not used to quarantine verbose output | Planner on Opus, workers on Haiku/Sonnet (Haiku ≈5× cheaper); use subagents to keep big logs/searches out of the main context | task-dependent | Low |
| 6 | **Session hygiene** | Long threads re-read full history each turn | Batch related work in one session; `/compact` long threads; `/clear` between unrelated tasks; cap bash/test output | 10–40% on long sessions | Low |

---

## Detail

### 1–2. The CLAUDE.md tax is our biggest, cheapest win
CLAUDE.md loads before the task, before any code — so a 5K-token file costs 5K tokens *every
turn*. Because all seven repos are in GitHub scope, a session loads them **all**: ~14.6K tokens
of fixed overhead per message regardless of what we're doing. A published benchmark trimmed a
3,847-token CLAUDE.md to 312 tokens for a **91.9% context reduction with no quality regression**
— headroom we have in full.

Concrete moves:
- **De-duplicate house style.** The reverse-chron / Z→A / walkthrough-reversal / Gill Sans
  block is identical in all 7 CLAUDE.md files (~1,750 words of pure repetition loaded every
  turn). Keep it canonical in one place; have each CLAUDE.md carry a one-line pointer.
- **Demote stage-by-stage detail.** The DESIGN funnel diagram, full stage map, and verification
  walkthrough are reference material — move to README/linked files Claude opens on demand
  instead of paying for them on turn 1 of every session.
- **Scope to one repo** unless the task is genuinely cross-repo.

### 3. We already own the hybrid; use it on purpose
Industry split: ~60–70% of agent requests are simple (classification, extraction, formatting,
short summarization) — local-model territory at ~$0/inference — 20–30% moderate, ~10% need a
frontier model. We pay frontier prices for all of it today.

Our `10-ai-orchestration` ladder is built for exactly this. Route to **local**: drafting
"Handled For You" lines from raw box logs, classifying inbound leads, booking-form intent
detection, roster dedup/embeddings, log summarization. Reserve **Claude (Opus)** for: code,
cross-repo reasoning, the AI-CTO/CFO synthesis, and customer-facing copy where voice matters.

⚠️ **Gate this on TD-14 first.** Our own P1 says a `sensitive`-tagged task can fail *over* to
`cloud-overflow` (Claude cloud) when the local model is down — `allow_cloud=False` isn't
enforced at the LiteLLM failover layer. Don't route more customer data through the ladder until
`local-reason` fails *closed* to a local-only chain. The privacy fix is also what makes the
cost routing safe.

### 4. Prompt caching — for anything we build on the API
Cache reads bill at 0.1× input (≈90% off); agent loops see 40–70% total savings. Claude Code
already does this for us. The win is in *our own* tooling (statement generator, router): put the
least-changing content first (tool defs, then system prompt, then stable context), and **never
interpolate dynamic values — date, customer name — into the cached prefix**, since that
invalidates everything downstream. For bulk, non-interactive statement runs, the **Batch API is
50% off** input+output.

### 5. Model + subagent routing
Multi-agent isn't free: subagent workflows run ~4–7× tokens, experimental Agent Teams ~15×.
Their value is **context isolation** — delegate a verbose job (test runs, doc fetches, wide
searches) so the noise stays in the subagent and only a summary returns to the main thread. For
linear work, skip them. And don't run routine doc edits or the daily review at top tier — a
cheaper model can draft, with Opus reserved for the parts that need it.

### 6. Session hygiene
Batch related tasks into one warm-context session instead of many cold starts; `/compact` when a
thread grows; `/clear` between unrelated tasks; cap test/bash output so a noisy log doesn't eat
the window.

---

## On the prompt that triggered this (asked for directly)

**What worked:** clear intent, named the hybrid angle, asked for recency. Good instincts.

**What costs tokens and focus:**
- **Unbounded asks** ("ANYTHING that could help", "Anything you could possibly think of") invite
  open-ended exploration and a sprawling answer — expensive on both sides.
- **No output contract or success criteria** — the model can't tell when it's "done", so it
  over-produces.
- **"Check the news / keep up to date"** with no recency window or source bound — the agent
  guesses how deep to go.
- Minor: polite filler ("Thanks!", "Perhaps also…") adds tokens without instruction value.

**Tighter template (bounded, ordered, has an output contract):**

> Audit our user↔AI workflow for token/cost efficiency. Cover, in order: (1) CLAUDE.md/context
> size, (2) prompt caching, (3) local-vs-Claude routing on our existing LiteLLM ladder, (4)
> Claude model/subagent routing, (5) this prompt. For each: current state → the fix → est. %
> saving → effort. Cite sources from the last 60 days. Output a ranked table plus a one-paragraph
> "do this first." Commit findings to `docs/ai-cto/reviews/`.

Same answer, a fraction of the wandering. The rule of thumb: **role + concrete goal + ordered
scope + output format + recency bound.** Open-ended is fine for brainstorming; for a recurring
audit, bound it.

---

## Sources (last ~60 days)

- [Reduce Claude Code token usage by 90% — Medium](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Why Claude Code Subagents Burn So Many Tokens — youcanbuildthings](https://youcanbuildthings.com/articles/claude-code-subagents-token-usage/)
- [Complete Guide to Every Claude Update in Q1 2026 — aimaker](https://aimaker.substack.com/p/anthropic-claude-updates-q1-2026-guide)
