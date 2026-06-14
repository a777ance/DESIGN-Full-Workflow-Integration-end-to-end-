# Process Efficiency — User ↔ AI Token & Workflow Audit

How we work *with* the AI (Claude Code, the homelab router), where tokens leak, and how to
spend fewer of them for the same or better output. NARF (AI CTO) owns this file; review it
when costs jump or when adding a new routine.

**Last updated:** 2026-06-14 — first audit, triggered by founder's "find inefficiencies in our
process" routine. Findings are ranked by impact (biggest lever first), not chronologically.

> Methodology: measured our own repo context load, cross-checked against current (June 2026)
> public best-practice writeups on Claude Code token use, prompt caching, model-tier routing,
> and hybrid local/cloud LLM architecture. Sources at the bottom.

---

## TL;DR — the five biggest levers

| # | Lever | Est. saving | Effort | Owner |
| - | ----- | ----------- | ------ | ----- |
| 1 | **Trim every `CLAUDE.md` to a lean core (<~600 tokens) + `@`-reference the detail** | 30–50% of *fixed* per-turn cost; compounds on multi-repo routines | M | NARF |
| 2 | **Run routines/monitoring on Sonnet 4.6 or Haiku 4.5, reserve Opus 4.8 for hard reasoning** | Sonnet ≈40% cheaper, Haiku ≈5× cheaper than Opus | S | NARF |
| 3 | **Confirm prompt caching is live on the stable prefix (CLAUDE.md + tool schemas)** | up to 90% off cached input — the single largest API lever | S | NARF |
| 4 | **Push low-stakes work to the t630 LiteLLM router first; Claude only for the hard part** | 60–80% on the offloaded slice — *but blocked on TD-14* | M | NARF |
| 5 | **Scope prompts: one task, explicit output target, success criteria, token budget** | 40–70% on focused tasks vs. open-ended ones | S | founder |

---

## 1. `CLAUDE.md` bloat is our biggest fixed cost

A `CLAUDE.md` is **never lazy-loaded and never evicted** — it sits in context for the entire
session, so its size is a tax on *every single turn*. Ours are heavy:

| Repo | `CLAUDE.md` words | ≈ tokens |
| ---- | ----------------: | -------: |
| localDNS | 2,728 | ~3,600 |
| DESIGN (this repo) | 2,608 | ~3,500 |
| MARKETING | 1,445 | ~1,900 |
| customers | 562 | ~750 |
| claude-code-homelab | 371 | ~490 |
| azure-lab | 316 | ~420 |

The community-recommended target is **under ~500 tokens**. localDNS and DESIGN are 7× that.

**This bites hardest on multi-repo routines.** A scheduled run scoped to all seven repos (like
the one that produced this file) gets *every* `CLAUDE.md` injected up front — ~11k tokens of
fixed context before a single useful instruction, paid on every run, forever.

**Fix:** keep in `CLAUDE.md` only what the model needs on *most* turns — house style, the
"push to main / branch" rule, the one-source-of-truth rule, the deploy-path table for the
active repo. Move the long rationale (network topology prose, the funnel narrative, the full
deploy walkthrough, the AI-CTO/CFO session protocols) into the README / `network-context.md`
/ `workflow-context.md` we already have, and **`@`-reference them on demand**. The detail is
loaded only when the task touches it, not on every turn.

Also collapse the **"read 4–6 state files at session start"** ritual (CLAUDE.md §5/§6) into a
single short `docs/ai-cto/state-digest.md` the routine reads, instead of opening
`portfolio.md` + `roadmap.md` + `tech-debt.md` + `decisions.md` + the CFO set every time.

## 2. Routines are running on the most expensive model

Current model rates (June 2026, per million tokens):

| Model | Input | Output | vs. Opus |
| ----- | ----: | -----: | -------- |
| Opus 4.8 | $5 | $25 | — (Fast Mode ≈ $10 / $50) |
| Sonnet 4.6 | $3 | $15 | ~40% cheaper |
| Haiku 4.5 | ~$1 | ~$5 | ~5× cheaper |

This routine runs on `claude-opus-4-8[1m]` — the flagship, plus the **1M-context tier carries
a price premium above 200k tokens**. Most of what a *monitoring* routine does — "did anything
change, is everything healthy, do the doc links still resolve, summarize today's diffs" — does
not need Opus-grade reasoning. Default scheduled/monitoring routines to **Sonnet 4.6** (or
**Haiku 4.5** for pure status sweeps and link checks), and reserve Opus for genuinely hard
design/architecture work. Set per-routine model in the routine config, not globally.

Bonus levers in the same family: **Batch API is 50% off** for non-interactive bulk jobs — a
natural fit for monthly statement generation (stage 06) where latency doesn't matter.

## 3. Prompt caching — confirm it's actually on

Caching a stable prefix (system prompt, tool schemas, big reference docs) bills cached input
at ~10% of normal — **up to 90% off**, the single largest API cost lever in 2026. Interactive
Claude Code does this automatically, but **routines spin up fresh containers**, so back-to-back
runs may not be sharing a warm cache. Action: verify cache hit-rate on our recurring routines;
if low, structure the run so the stable bits (CLAUDE.md, tool defs) form a cacheable prefix and
only the per-run delta is fresh. Pick TTL to match cadence (5-min default is wrong for an
hourly routine — that's a cold cache every time; a 1-hour TTL fits better).

## 4. We already have the hybrid rig — use it, after fixing the leak

The t630 already runs the textbook hybrid architecture: **LiteLLM gateway + local models +
Claude as the cloud tier**, with the `local-reason → cloud-gpu-reason → cloud-overflow`
reasoning ladder (localDNS `10-ai-orchestration`). The published 2026 guidance is exactly this,
and reports **60–80% savings** by routing simple work local-first and only escalating the hard
part to the cloud API.

Where we're leaving money on the table: low-stakes, high-volume text work that currently goes
straight to Claude — **log triage, summarizing the day's commits, classifying leads, first-draft
copy, doc-link sanity checks, pre-digesting large inputs before they reach Claude.** Run these
on the local model first; send Claude only the distilled result. Pre-digesting alone cuts *input*
tokens on the expensive tier.

🚧 **Blocker — do not lean harder on the router until TD-14 is fixed.** A `sensitive`-tagged
task can currently fail *over* from `local-reason` to `cloud-overflow` (Claude cloud) because
`allow_cloud=False` isn't enforced at the LiteLLM failover layer. Give `local-reason` a
local-only fallback (fail closed) first; otherwise "route more to local" risks leaking private
lookups to the cloud. This is a P1 already on the tech-debt board.

## 5. Workflow hygiene (cheap, immediate)

- **One task per session; `/compact` or clear between tasks.** Re-establishing a small context
  is almost always cheaper than dragging a long one forward.
- **Offload fan-out reads to subagents** (the `Explore` agent, the `deep-research` /
  `code-review` skills). A subagent works in its *own* context window and returns only the
  conclusion — the file dumps never hit the main thread (~70% reduction on read-heavy tasks).
  Skills load ~100 tokens of name+description until invoked (progressive disclosure), so having
  many available is nearly free.
- **Make recurring routines diff, not re-derive.** Persist a small "last findings" artifact and
  have the next run compare against it instead of re-reading the world. Stay silent when nothing
  changed (the notification model already rewards this).
- **Scope the ask.** "Refactor the login function in `auth.ts`" beats "refactor the auth module."
  Narrow scope = less context pulled = fewer tokens = more focused output.

---

## On the prompt that launched this audit

The founder's own prompt is a clean example of the *expensive* shape, and worth fixing because
it's a recurring routine — the cost repeats:

- **Unbounded scope.** "ANYTHING that could help… search the web… check the news" invites
  maximal exploration: many searches, wide reading, long output. Great for a one-off discovery
  pass; wasteful as a *weekly* routine.
- **No output target or success criteria.** Nothing said *where* the answer should land or what
  "done" looks like, so the model has to guess (and tends to over-produce).
- **No diff against prior runs.** Each run re-derives from scratch instead of "what changed
  since the last audit."

A leaner recurring version:

> *"Re-check process efficiency. Read `docs/ai-cto/process-efficiency.md`; only report items
> that are **new or changed** since last run. Pull web best-practices **only if** >30 days
> since last refresh (noted in the file). Output: update the file's top table + notify me with
> the single highest-impact new finding and its $ estimate. Run on Sonnet. Budget: keep it
> tight."*

That keeps the discovery value, runs on a cheaper model, caches the bulk of its context, and
produces a diff instead of a fresh essay every time.

---

## Sources (June 2026)

- [KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [agensi.io — Reduce Claude Code Token Usage: Skills That Cut Costs (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [claudefa.st — Claude Code Context Window: Optimize Token Usage](https://claudefa.st/blog/guide/mechanics/context-management)
- [Finout — Anthropic API Pricing in 2026 (models, caching, batch)](https://www.finout.io/blog/anthropic-api-pricing)
- [Finout — Claude Opus 4.8 Pricing 2026](https://www.finout.io/blog/claude-opus-4.8-pricing-2026-everything-you-need-to-know)
- [web2md.org — Prompt Caching Cost Optimization: 80% Savings Most Workflows Miss (2026)](https://web2md.org/blog/prompt-caching-cost-optimization-guide-2026)
- [Claude API Docs — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [SitePoint — Hybrid Cloud-Local LLM: Complete Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Markaicode — LiteLLM Pricing: Cut API Costs with Smart Routing](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Nimbalyst — Claude Code Subagents: A Practical 2026 Guide](https://nimbalyst.com/blog/claude-code-subagents-guide/)
- [LeanOps — AI Agents Burn 50x More Tokens Than Chats](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
