# Process Efficiency Review — User ↔ AI

**Date:** 2026-06-19 · **Author:** NARF (AI CTO routine) · **Status:** advisory, not yet an ADR

A standing review of how we (founder ↔ Claude) actually spend tokens and attention, what's
wasteful, and where the homelab's own infra can carry load that's currently going to the
frontier model. Findings are ranked by leverage. Numbers are measured against this repo on
2026-06-19, not estimated from memory.

---

## TL;DR — the three things worth doing this week

1. **Stop reading 9 files (~14.3K tokens) at the start of every session.** The DESIGN
   CLAUDE.md §5/§6 mandate reading the full NARF + ZORT doc set on *every* session. That's a
   fixed ~14K-token tax before any work begins, on top of the ~4.5K CLAUDE.md itself —
   **~18.8K tokens of overhead per session, most of it irrelevant to the task at hand.**
   Replace with one ~500-token state digest + read-on-demand.
2. **Route the cheap 70% of work to the t630 LiteLLM router you already run.** We have the
   hybrid infra (stage 10) sitting idle for this. Classification, extraction, link-checking,
   commit messages, first-draft summaries → local/Haiku. Opus only for real reasoning.
   Industry split is ~60–70% simple / 20–30% moderate / ~10% frontier-grade.
3. **Tighten prompts into asset-grade specs with a success criterion and an output
   contract.** Open-ended "do anything that helps" prompts (this review's own prompt is the
   textbook example — see §5) maximize both spend and variance.

---

## 1. The recurring-cost problem: per-session overhead

Measured today:

| What loads | Tokens | When |
| ---------- | -----: | ---- |
| `DESIGN…/CLAUDE.md` | ~4,500 | every session, automatically |
| NARF mandatory reads (portfolio, roadmap, tech-debt, decisions) | ~5,540 | every session, per §5 |
| ZORT mandatory reads (portfolio, decisions, metrics, runway, budget) | ~8,740 | every session, per §6 |
| **Fixed overhead before the first useful token** | **~18,800** | **every session** |

`localDNS/CLAUDE.md` is ~5,120 tokens on its own; the others range 570–2,700.

Two distinct costs hide here:

- **Dollar cost** — partly absorbed by prompt caching (cached input is ~90% cheaper, and
  Claude Code caches the system/CLAUDE.md prefix automatically *as long as it doesn't
  change mid-session*). So the CLAUDE.md itself is the cheap part.
- **Attention/quality cost — the real one.** The 14K of session-start file reads are
  *active* (tool-driven), land deep in context, and aren't cache-stable across edits. A
  bloated context measurably degrades the model's focus on the actual task ("context rot").
  Every session pays this whether the task touches finance or not.

### Fixes (ranked)

1. **Make session-start reading lazy and conditional.** Replace "read these 9 files" with:
   *"Read `docs/state-digest.md` (a ~500-token rollup of current phase, open decisions,
   and top-3 priorities). Read the full NARF or ZORT docs only if the task touches that
   domain."* Maintain the digest as the single mandatory read; it points to the rest.
   **Saving: ~12–13K tokens/session** with no loss of the facts that actually steer work.
2. **Slim CLAUDE.md to the always-true contract; demote reference tables.** The big
   deploy-path table (localDNS) and stage map (DESIGN) are lookup material, not
   always-needed context — move to README and link. CLAUDE.md should be the minimal
   standing instructions + a map of where to look, not the map itself.
3. **Deduplicate the House style block.** It's ~300 tokens copied verbatim into all 7
   repos' CLAUDE.md (1,211 chars each). That's not a per-session cost (one repo loads per
   session) but it's a drift/maintenance cost — 7 places to update, already at risk of
   diverging. Keep one canonical copy (e.g. in `claude-code-homelab/templates/`) and have
   each repo's CLAUDE.md link to it with a one-line summary.
4. **Don't edit CLAUDE.md mid-session if you can help it** — it invalidates the cached
   prefix and re-bills the whole thing as fresh input.

---

## 2. Token & context discipline (Claude Code mechanics, current as of mid-2026)

- **Subagents = disposable context.** Fan-out/search/read-heavy work should run in a
  subagent (or `Explore`/`general-purpose`), which reads in its *own* window and returns
  only the conclusion. The main thread stays small. This routine itself is the pattern:
  research happened, only the report comes back. Use it for anything that means sweeping
  many files.
- **`/clear` between unrelated tasks; `/compact` before the 95% auto-trigger** (override
  to ~70% for routine work). `/recap` (added April 2026) summarizes where you left off on
  resume instead of replaying the whole thread.
- **Scope every task.** "Refactor the login function in `auth.ts`" not "refactor auth."
  Smaller scope = less context pulled = fewer tokens and better output.
- **Tool output is the silent drain** — it compounds every turn and usually dwarfs your
  messages. Prefer narrow searches (Grep/Glob with globs) over dumping whole files; read
  only the lines you need.

---

## 3. Hybrid local + cloud — we already own the router, we're just not using it for this

Stage 10 already runs **LiteLLM on the t630** with a reasoning ladder
(`local-reason` = deepseek-r1:1.5b on CPU; `cloud-gpu-reason` = full R1 on a rented GPU;
`cloud-overflow` fallback) and Open WebUI. That's exactly the gateway the 2026 hybrid
playbooks describe — and it's currently scoped to chat, not to offloading our day-to-day
agent work.

**The opportunity:** most production AI workloads break down ~60–70% simple (classify,
extract, format), 20–30% moderate (summarize, translate), ~10% genuinely needs a frontier
model. Routing the cheap tiers off Opus is a documented **60–90% cost cut on the routable
share**, same quality ceiling.

Concrete candidates to push to local / Haiku 4.5 via the router:

| Task | Route to | Why |
| ---- | -------- | --- |
| `tools/check-docs.py` triage, link/anchor checks | local | deterministic, no reasoning |
| Commit-message + PR-body drafts | local / Haiku | cheap, templated |
| First-pass summaries of logs, metrics, stats files | local / Haiku | bulk, low-stakes |
| Classify/extract from roster or stats JSON | local | structured, repetitive |
| Watcher/routine first-pass triage (like this run) | local | escalate to Opus *only on a hit* |
| Statement copy drafting (before honesty review) | Haiku | draft, then Opus/human checks numbers |
| Architecture, ADRs, multi-repo reasoning, the honesty review on a kept document | **Opus** | this is what frontier is for |

**Two more stackable cloud levers for non-interactive bulk jobs:**
- **Prompt caching** — ~90% off cached input; structure reused context into ≥1,024-token
  stable blocks at the front.
- **Batch API** — 50% off for anything that doesn't need to be real-time (bulk statement
  regen, bulk doc edits). Caching + batch stacked ≈ up to 95% off.

**Caveat (honesty rule still applies):** never let a local/cheap model put a number on a
kept document. Local models draft; Opus or a human verifies every figure on a Statement.
That's the existing §E discipline, unchanged.

---

## 4. Prompting — treat prompts as versioned assets

The 2026 consensus: a good prompt is a *repeatable asset with a success criterion and an
output contract*, not a phrasing. Practically, every non-trivial ask should carry:

- **Goal + success criterion** — "done" is testable ("returns a ranked list of ≤5 findings,
  each with a measured number and a fix").
- **Scope & exclusions** — what's in, what's out, what to do when uncertain (ask vs.
  assume).
- **Output contract** — format, length, required sections.
- **Context, not a context dump** — link the source of truth, don't paste it.

For recurring routines (this one, the PR babysitter, etc.), keep the prompt in version
control and iterate it like code. "One good output proves nothing; ten across varied inputs
proves something."

---

## 5. Critique of the prompt that triggered this review

The instruction was, paraphrased: *"Locate inefficiencies… is there a better way… anything
you could possibly think of… ANYTHING that could help… search the web… keep up to date…
check the news."* The user also (correctly) asked whether the prompt itself was inefficient.

It is — it's the canonical anti-pattern, and it's worth naming because we'll write many more:

- **Unbounded scope.** "ANYTHING that could help" has no edges, so the model must explore
  broadly and defensively — the single biggest driver of token spend and output variance.
- **No success criterion.** Nothing defines "done," so the run can't self-limit.
- **No output contract.** Format/length/destination unspecified; the model guesses (here:
  a committed report + a notification).
- **Six questions bundled as one** (token use, prompting, other AI, hybrid local, news,
  self-critique) with no priority, so effort is spread evenly instead of by value.
- **"Check the news / keep up to date"** is a cadence instruction, not a one-shot — it
  belongs in a *scheduled routine with pinned sources*, which is exactly the right call;
  just pin the sources (Anthropic changelog, Claude Code release notes) and define "notify
  only on material change."

It worked out *here* because the task genuinely was open-ended discovery and the agent had
rich repo context — but it cost far more than a scoped version would, and a less-grounded
run would have rambled.

**A tighter rewrite of the same request:**

> *Audit our Claude usage for cost/efficiency. Deliverable: a ranked list of ≤7 changes,
> each with (a) the measured cost today, (b) the expected saving, (c) the concrete change.
> Cover: per-session context overhead, local/cloud routing via our existing t630 LiteLLM
> router, and prompt hygiene. Check the Anthropic changelog + Claude Code release notes for
> anything new since last run; flag only material changes. Write it to
> `docs/ai-cto/process-efficiency-review.md` and push. Notify me only if a finding is worth
> ≥$X/mo or changes how I work.*

Same intent, bounded scope, testable output, pinned sources, clear notify threshold.

---

## 6. Keeping up to date (the "check the news" ask, done right)

- **Pin sources, don't free-search:** Anthropic changelog, Claude Code release notes, the
  pricing page. A free web search re-discovers the same blogspam every run and burns tokens
  on it.
- **Run as a scheduled routine** (this already is one) with a **material-change gate**:
  notify only when a price, model, or feature actually changes something we do. Silence on a
  no-change run is the correct, kind default for a routine nobody is watching live.
- **Cadence:** monthly is plenty for pricing/feature drift; the model landscape moves in
  weeks, not hours, despite the hype.

---

## 7. Prioritized action list

| # | Action | Effort | Payoff |
| - | ------ | ------ | ------ |
| 1 | Replace §5/§6 "read 9 files" with a ~500-tok `state-digest.md` + read-on-demand | S | ~12–13K tok/session |
| 2 | Wire day-to-day cheap tasks through the existing t630 LiteLLM router (table in §3) | M | 60–90% off the routable share |
| 3 | Slim CLAUDE.md: demote deploy-path/stage-map tables to README + link | S | smaller stable prefix, better focus |
| 4 | Adopt a prompt template (goal / success / scope / output / notify-threshold) for routines | S | less spend + less variance |
| 5 | Deduplicate the House-style block to one canonical copy | S | kills drift across 7 repos |
| 6 | For bulk non-interactive jobs, stack prompt caching + Batch API | M | up to ~95% off those jobs |
| 7 | Turn "check the news" into a pinned-source monthly routine with a material-change gate | S | stops re-searching blogspam |

Items 1, 3, 4, 5, 7 are doc/process changes we can land here. Item 2 touches the t630
(`10-ai-orchestration`) and Item 6 is per-job — both are CTO follow-ups, not one-commit
changes.

---

## Sources

- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Code Token Optimization (2026 Guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Savings 2026 — AI Cost Check](https://aicostcheck.com/blog/ai-prompt-caching-cost-savings)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Build MVP Fast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Claude Code Sub-Agents Explained — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Prompt Engineering Best Practices 2026 — PE Collective](https://pecollective.com/blog/prompt-engineering-best-practices/)
- [Prompt Engineering in 2026: Tips + Best Practices — orq.ai](https://orq.ai/blog/what-is-the-best-way-to-think-of-prompt-engineering)
