# Process Efficiency Review — User ↔ AI

**Date:** 2026-06-21 · **Author:** NARF (AI CTO) · **Trigger:** founder asked for inefficiencies
in our process, token-reduction options, better prompting, and hybrid local/cloud LLM ideas.

Brief: where the money and attention leak in how we (the founder) work with Claude, ranked by
payoff. Tied to our actual stack. Up to date as of the 2026-06 model line (Opus 4.8 / Sonnet 4.6
/ Haiku 4.5). Sources at the bottom.

---

## TL;DR — the 5 changes that pay, ranked

| # | Change | Effort | Est. saving | Where |
| - | ------ | ------ | ----------- | ----- |
| 1 | **Right-size the model.** This routine runs on **Opus 4.8 (1M ctx)** — the most expensive tier — for work that is mostly doc edits, link-checks, status digests, and reordering. Move routine/recurring runs to **Haiku 4.5** (≈1/15th the cost of Opus) or **Sonnet 4.6**; reserve Opus for genuinely hard reasoning. | Low (config) | **Biggest single lever** — Haiku is ~15× cheaper per token than Opus | every session |
| 2 | **Turn on prompt caching for the static prefix.** Our CLAUDE.md briefings are large and injected every session unchanged. Cached reads cost **~10%** of normal input; batch API another **50% off**; stacked ≈ **95%+** off. | Low–Med (2–4h once per workload) | 60–90% of *input* cost | API-driven jobs |
| 3 | **Stop the daily full-portfolio review when nothing changed.** The portfolio itself notes "nothing material shipped since 2026-06-07" across *multiple* daily review cycles. A daily Opus sweep of 7 repos that finds no change is pure burn. Gate it: a cheap **local model** diffs the repos; only escalate to Claude when something actually changed (or weekly). | Low | One full Opus session/day avoided | this routine |
| 4 | **Deploy the hybrid router we already built — and fix TD-14 first.** `localDNS/10-ai-orchestration` is the right 2026 architecture (sensitivity→complexity→availability). It is **not deployed**, and its privacy gate **fails open** (TD-14). Route deterministic chores (link-checks, changelog/Z→A reordering, digest drafts) to **local qwen2.5** at zero API cost; keep Claude for reasoning/writing. | Med (needs t630 session) | 60–80% of cloud spend on routable work | localDNS |
| 5 | **De-duplicate the briefings.** The ~30-line house-style block and the three-repo table are copy-pasted verbatim into all 7 CLAUDE.md files, so multi-repo sessions pay for the same text 7×. Keep one canonical `HOUSE-STYLE.md`; have each CLAUDE.md link to it. | Low | Recurring per-session input | all repos |

---

## A. Where the process leaks today

1. **Model over-provisioning.** We're defaulting to the flagship for clerical work. Per the
   2026 pricing line, Opus 4.8 is $5/$25 per M tokens; Haiku 4.5 is roughly 1/15th of that.
   Most of what these routines do (formatting, link integrity, status digests, ADR logging)
   is Haiku-grade. **Fast Mode on Opus is 2× the base rate** ($10/$50) — only worth it when
   latency matters, not for an unattended routine.

2. **Static context re-billed every run.** Seven CLAUDE.md files (plus README/context files)
   are large and stable. Without prompt caching, every session pays full input price to
   re-read them. With caching that's a 90% discount on the repeated prefix.

3. **Cadence mismatch.** A *daily* AI review of a portfolio that changes weekly (gated on a
   single t630 SSH session — see Blocker #1) produces review files with no new shipped work.
   The review cadence should track the *change* cadence, not the calendar.

4. **Duplication across repos.** House-style and the repo-map table are duplicated 7×. Edits
   must be made 7× (error-prone) and are re-billed every multi-repo session.

5. **The house style itself has a cost.** Reverse-chronological logs are fine, but
   "alphabetical Z→A" and "reverse the blocks, keep the steps" force both humans and the model
   to reorder content against its natural training distribution — more tokens spent reordering,
   more chances to get it wrong. Worth asking whether the novelty earns its keep. (Not a
   token-only call — flagging for the founder, not auto-changing.)

## B. Token-reduction toolkit (2026, verified)

- **Prompt caching** — cache hit ≈ 10% of input price; break-even after ~3 reads (5-min TTL) or
  ~5 reads (1-hour TTL). Put static content (system prompt, tool defs, big docs) *first*, dynamic
  content (user msg, history) *last*. **Never put a live timestamp in the cached prefix** — it
  invalidates the cache every call (truncate to the day).
- **Batch API** — 50% off input *and* output for non-interactive jobs. A nightly review or
  digest is a perfect batch candidate. Stacks with caching for 95%+ reduction.
- **Subagents / context isolation** — fan-out searches into subagents so only summaries return
  to the main context; reported 40–70% savings on focused tasks. (This review used that pattern.)
- **Context editing + memory tool** — Anthropic's own eval shows **84% token reduction** on a
  100-turn web-search task and +39% quality when memory is combined with context editing. Relevant
  if/when we build long-running agents (the Phase-2 PWA assistant).
- **`/compact` and `/recap`** — custom compaction to preserve key facts; `/recap` summarizes where
  a session left off without replaying the whole transcript.
- **Scope the request.** "Add validation to the login function in auth.ts" reads one file;
  "improve auth" reads the repo. Specificity is a token lever.

## C. Hybrid local + cloud — we're closer than it looks

Our `localDNS/10-ai-orchestration` (LiteLLM + Ollama + LangGraph supervisor) is, on paper, the
exact pattern 2026 guides recommend: a unified proxy, model aliases, fallback chains, and a
**three-pillar router (sensitivity → complexity → availability)** with fail-closed handling for
sensitive data. Two gaps keep it from paying off:

- **It isn't deployed** (TD-03/TD-14 family; gated on the t630 session — Blocker #1).
- **The privacy gate fails OPEN (TD-14):** `local-reason → ["cloud-gpu-reason","cloud-overflow"]`
  means a *sensitive* task can spill to Claude cloud if the local model is down. Best practice is
  explicit: **fail closed for sensitive data.** Fix is a 3-line edit (local-only fallback) and
  needs no box access — do it before relying on the router for anything private.

Once deployed, the win is routing the **cheap, deterministic, privacy-irrelevant** chores to local
qwen2.5 (link-checking, Z→A reordering, changelog formatting, first-draft digests) at **zero API
cost**, and reserving Claude for reasoning and customer-facing prose. Add **semantic caching** in
front of the proxy (15–30% fewer requests on repetitive work). Industry reports put hybrid savings
at 60–80% of cloud spend on routable workloads.

## D. On the founder's prompt (you asked)

The prompt that launched this run is **deliberately unbounded** — "ANYTHING that could help,"
"search the web," "check the news," "leverage other AI." That openness is itself the most
expensive instruction we give: it defeats prioritization and invites unlimited fan-out, so the
model spends tokens *deciding what to look at* before doing anything. Three cheap fixes:

1. **State the decision/output, not the topic.** "Give me a ranked list of ≤5 process changes with
   estimated $ savings and effort, and write it to `docs/ai-cto/`" beats "find inefficiencies."
2. **Bound depth and scope.** "≤3 web sources, don't deep-dive; cover only the AI-workflow process,
   not the business funnel." A budget turns an open sweep into a focused pass.
3. **Drop the maximalist words.** "Anything / everything / keep up to date day by day" reads as
   "spare no tokens." If you want frugality, the prompt has to model it.

**Rewritten, frugal version of this very request:**

> "Audit how I work with Claude across the repos for token waste. Give me a ranked list of ≤5
> changes, each with rough effort and $ saving, written to `docs/ai-cto/process-efficiency-review.md`.
> Use ≤3 recent web sources for 2026 best practices. Don't change any config — just recommend.
> One-paragraph notification with the top item when done."

Same answer, a fraction of the spend, and a clear stopping point.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing in 2026 (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing 2026: Opus 4.8 / Sonnet 4.6 / Haiku 4.5 (MetaCTO)](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Claude API Cost Optimization: Caching, Batching, 60% Token Reduction (DEV)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Agents in 2026: Subagents, Teams, and What They Cost (CloudZero)](https://www.cloudzero.com/blog/claude-code-agents/)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows: Cost Optimization (BuildMVPFast)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM Routing & Load Balancing (docs)](https://docs.litellm.ai/docs/routing-load-balancing)
- [Anthropic Claude Updates — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude)
