# AI Process Efficiency — the user↔AI loop

How we spend tokens and human attention working *with* the AI across the A777ance repos,
and where to cut waste without losing quality. Reviewed **2026-06-15**. Findings are
ordered newest-first per house style; the priority table is the place to start.

This is a CTO-state spoke. Roll resolved items into `tech-debt.md`; record any decision
this triggers in `decisions.md`.

---

## TL;DR — prioritized

| # | Move | Effort | Payoff | Owner stage |
| - | ---- | ------ | ------ | ----------- |
| 1 | **Turn on prompt caching** for the standing context (CLAUDE.md + tool defs + roster) on every Claude API/Open WebUI path | Low | 30–60% fewer input-token charges on repeated context; ~90% off the cached portion | localDNS stage 10 |
| 2 | **Fix TD-14 first** — sensitive tasks must fail *closed* to a local-only chain before we lean harder on hybrid routing | Low | Closes a privacy hole; precondition for trusting the router | localDNS stage 10 |
| 3 | **Tier the model by node, not by session** — Opus only at decision nodes; Sonnet for the dozens of mechanical calls; local for classify/extract/format | Med | 60–80% cost cut on the routine 60–70% of calls | localDNS stage 10 / all |
| 4 | **Scope prompts + use subagents for fan-out reads** so big search/research output never lands in the main context | Low | Keeps the main thread small; the single biggest hidden token drain | all |
| 5 | **`/clear` between unrelated tasks; one CLAUDE.md fact, never re-typed** | Low | Stops re-reading stale threads every turn | all |
| 6 | **Tighten the prompts we hand the AI** (see "The prompt that triggered this") | Low | Fewer wasted exploration loops; more actionable output per run | human |

---

## The prompt that triggered this run (a worked critique)

The request that spawned this doc was, in spirit: *"Find inefficiencies between user and AI.
Reduce tokens. Better prompting. Hybrid local + Claude. Search the web. Anything you could
possibly think of. ANYTHING."*

It's a good *intent* but an **expensive prompt**, and it illustrates the #1 process fix:

- **No scope or stopping rule.** "Anything… ANYTHING" invites unbounded fan-out — the model
  searches widely and reads broadly because nothing told it where the edges are. On a
  scheduled, unattended run that is pure token burn with no one steering.
- **No target artifact or format.** It didn't say *where* the answer should land (a doc? a
  notification? a PR?) or *how long*. The model has to guess, and guessing wrong means redo.
- **No success criteria.** "Better" against what baseline? Without a yardstick the run can't
  tell "done" from "keep going."

**A tighter version of the same ask** (copy-paste pattern for future routines):

> Review how we use the AI across the repos for token waste. Output a prioritized,
> ≤2-page doc at `docs/ai-cto/ai-process-efficiency.md` (create the branch, push, notify me
> with the top 3). Cover: prompt caching, model tiering, the local/cloud router. Cite
> sources. Skip anything that doesn't change cost or quality. Stop after the top ~6 moves.

Same coverage, a fraction of the wandering. The rule of thumb: **a prompt should name the
scope, the artifact, and the stopping condition.** Vague prompts are the most direct lever
we control on token cost — bigger than any model setting.

---

## 1. The biggest drain isn't the prompt — it's the thread

Every turn re-reads the entire conversation, including stale instructions and superseded
code. Long-running threads are where tokens quietly multiply.

- **`/clear` between unrelated tasks.** Don't carry a finished task's context into the next.
- **One source of truth, stated once.** Our CLAUDE.md files already do this well — they load
  before the code and stop us re-typing the rules. Keep facts there, not in chat.
- **Subagents for verbose reads.** Fan-out searches and research should run in a subagent
  that reads in its own context and returns a clean summary — the big output never pollutes
  the main thread. (This very run should have delegated the web sweep to a subagent.)
- **Scope the ask.** "Refactor the login function in `auth.ts`" beats "refactor auth" — less
  context pulled in, tighter output.
- **Cap tool output** so a noisy command can't flood the window.

Typical reported savings from these alone: **40–70%**.

## 2. Prompt caching — the cheapest win we're probably leaving on the table

Anthropic caching: **cache reads cost ~10% of normal input** (a 90% discount), writes cost
1.25×, default 5-min TTL (1-hr option available). For an agent loop with a fixed system
prompt + tool defs + standing context (exactly our shape: CLAUDE.md + roster + schema),
caching that block yields a reported **~59% input-token reduction**, no quality change.

**Action:** ensure the LiteLLM/Open WebUI Claude path sends our standing context as a cached
prefix. This is config, not new code. Pair it with stable ordering (cached block first,
volatile user content last) so the cache actually hits.

## 3. Hybrid local + Claude — we already have the bones; sharpen them

We run the right architecture already: **LiteLLM gateway (stage 10) + Ollama-served local
models + Claude cloud tier**, with a reasoning ladder (`local-reason` on the t630 CPU →
`cloud-gpu-reason` on a rented GPU → `cloud-overflow`). Industry pattern for 2026 matches
ours: route by **data sensitivity, task complexity, availability**.

The work isn't building it — it's the routing discipline:

- **TD-14 is the gating bug.** A `sensitive`-tagged task can currently fail *over* to
  `cloud-overflow` (Claude cloud) if the local model is down, because `allow_cloud=False`
  isn't enforced at the LiteLLM failover layer. **Fix to fail closed** (local-only fallback
  chain for sensitive work) before we route more through the box. Until then there is no
  privacy guarantee, and the whole point of local-first is privacy.
- **Match the task distribution.** ~60–70% of real calls are simple (classify, extract,
  format) → local. ~20–30% moderate (summarize, structured output) → Sonnet. ~10% true
  frontier reasoning → Opus. Routing to that shape is where the **60–80% cost cut** lives.
- **Keep heavy reasoning off the thin client** (already a known issue) — long chains pin the
  cores; that's what `cloud-gpu-reason` is for.

## 4. Model tiering — stop paying Opus rates for mechanical work

2026 pricing: **Opus 4.8 $5/$25** per 1M in/out; **Sonnet 4.6 $3/$15** (~1.7× cheaper
blended); **Haiku 4.5** cheaper still. Opus's real edge is agentic decision-making
(~80 vs ~65 on agentic benchmarks). So:

- **Reserve Opus for the decision nodes** — the architecture call, the tricky migration, the
  step where output quality changes the business result.
- **Sonnet for the dozens of mechanical calls** in a pipeline (~85% of Opus quality at a
  fraction of cost for routine work).
- **Local for the trivial** (see §3).
- On Claude Code specifically: heavier models also drain the subscription quota window
  faster — model choice is a quota lever, not just a per-token one. **Fast mode on Opus**
  now runs faster at lower price; prefer it for interactive work.

## 5. Claude Code features worth adopting (June 2026)

- **Skills** for repeatable domain logic (we have several already) — they load only when
  triggered, so they don't tax every turn.
- **Subagents** for isolated, parallel, verbose work (see §1).
- **Stop / SubagentStop hooks** can return context — useful to auto-summarize or checkpoint.
- **`check-docs.py` is already wired into CI** (TD-11 resolved) — that's the right pattern:
  push verification into deterministic tools so the model isn't paid to eyeball links.

The 2026 consensus pattern is a **control stack**: project rules (CLAUDE.md) + reusable
skills + bounded subagents + deterministic tools *around* the model. We're most of the way
there; the gaps are caching (§2) and routing discipline (§3).

---

## Sources

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Cost Optimization (2026) — Web2MD](https://web2md.org/blog/prompt-caching-cost-optimization-guide-2026)
- [AI Agents Burn 50x More Tokens Than Chats — LeanOps](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM Pricing: Cut API Costs 60% with Smart Routing — Markaicode](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Claude Code Guide 2026: 25 Features — MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [Claude Code Sub-Agents Explained — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Claude Opus 4.8 Pricing & which model to run in 2026 — CloudZero](https://www.cloudzero.com/blog/claude-opus-4-8-pricing/)
- [Claude Sonnet 4.6 vs Opus 4.8 — llm-stats](https://llm-stats.com/models/compare/claude-sonnet-4-6-vs-claude-opus-4-8)
