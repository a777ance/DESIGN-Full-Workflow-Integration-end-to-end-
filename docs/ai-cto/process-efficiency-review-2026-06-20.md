# Process efficiency review — user ↔ AI (2026-06-20)

A standing review of how we spend tokens and attention working with Claude across the
A777ance repos, and where a cheaper/better path exists. Newest findings at the top per house
style. Sources are dated — this area moves week to week, so re-check before acting on a number.

> **TL;DR (the five levers, biggest first)**
> 1. **Right-size the model.** Default to Sonnet 4.6 ($3/$15), drop to Haiku 4.5 ($1/$5) for
>    routine work, reserve Opus 4.8 ($5/$25) for hard reasoning. This very routine ran on Opus
>    for a research/writing task — Sonnet would have been ~the same quality at a fraction of the cost.
> 2. **Trim the auto-loaded context.** Every session loads all 7 `CLAUDE.md` files (~8.7k words
>    ≈ 11–12k tokens) *before any work*, then NARF/ZORT ask to read 4–6 more docs. Move reference
>    tables out of `CLAUDE.md` into linked files read on demand.
> 3. **Use the hybrid stack we already own.** The t630 LiteLLM router + reasoning ladder is exactly
>    the architecture the industry recommends; route bulk/low-sensitivity work there, Claude for the rest.
> 4. **Scope each request; make routines delta-only.** Narrow asks and "report only what changed"
>    cut both token spend and noise.
> 5. **Know the billing math.** A Max plan almost certainly beats pay-as-you-go API at our usage —
>    and the June-15 change that would have pulled automation out of subscriptions was *paused*, not cancelled.

---

## A. Right-size the model (the single biggest lever)

Current per-MTok pricing (Anthropic, June 2026):

| Model | Input / Output ($/MTok) | Use for |
| ----- | ----------------------- | ------- |
| Opus 4.8 | $5 / $25 | Hard cross-repo reasoning, architecture, the gnarly debug |
| Sonnet 4.6 | $3 / $15 | **Default.** Almost everything: edits, docs, normal coding |
| Haiku 4.5 | $1 / $5 | Routine/bulk: link-checks, classification, log triage, first drafts |

Opus output is **5× the price of Haiku and 1.7× Sonnet.** Most of our work (doc edits, README
upkeep, statement composing, link checking) does not need Opus. A simple rule: *start on Sonnet,
escalate to Opus only when a task actually stalls.* Batch API is 50% off for anything non-interactive
(e.g. a nightly doc pass).

## B. Trim what loads on every session

The expensive part of our setup is the **fixed preamble**, paid on every single session:

- All 7 `CLAUDE.md` files are injected up front. `localDNS` (~2,728 w) and `DESIGN` (~2,608 w) are
  the heavy ones; combined ≈ 8.7k words ≈ **11–12k tokens before the first real instruction.**
- Then `CLAUDE.md` §5/§6 tell every DESIGN session to read `portfolio.md`, `roadmap.md`,
  `tech-debt.md`, `decisions.md` (NARF) **and** six CFO files (ZORT) — easily another 20–40k tokens.

Fixes:
1. **`CLAUDE.md` is a briefing, not a manual.** Today it carries full deploy-path tables, the entire
   known-issues table, etc. Those are *reference* — move them to `README`/dedicated files and link.
   Target each `CLAUDE.md` under ~1,000 words. Keep only rules that change behavior.
2. **Make the NARF/ZORT reading lists conditional.** Load the CFO bundle only for finance tasks, the
   CTO bundle only for architecture tasks. Right now every DESIGN session pays for both personas.
3. **Prompt caching helps the stable prefix** — but Anthropic cut the cache TTL from 60 → 5 minutes
   in early 2026, so it only pays off within a burst of calls, not across a day. Keep the cached prefix
   *stable*: no timestamps or per-run data inside `CLAUDE.md` (the once-a-day `currentDate` injection is fine).

## C. Lean on the hybrid stack we already built

`localDNS` already runs the textbook hybrid architecture: **LiteLLM gateway (:4040) + local Ollama
models + cloud tiers**, with a reasoning ladder (`local-reason` = deepseek-r1:1.5b on the t630;
`cloud-gpu-reason` = full R1 on a rented GPU via Tailscale; `cloud-overflow`). Industry reports
60–80% cost cuts from exactly this pattern (LiteLLM + local + Claude cloud tier).

How to actually use it:
- **Local tier (t630 CPU) is for *tiny* jobs only.** The box is a quad-core Carrizo; our own known-issue
  warns deepseek-r1:7b cooks it. Good for: classification, short summaries, "tidy this paragraph,"
  log triage. Not for: anything long.
- **Rented-GPU tier is the real local-ish workhorse** for heavier offline reasoning.
- **Claude (via API) stays the tier for** customer-facing copy, cross-repo reasoning, and anything where
  a wrong answer is expensive.
- Add Claude **Haiku** as a model behind the LiteLLM router so routine cloud calls don't default to Opus.
- Privacy: route order respects our rules already — private-repo/customer data only goes to tiers we
  control (all of them are), and the honesty rule still gates any number that reaches a Statement.

## D. Workflow habits that cut tokens

- **Delegate research to subagents.** Fan-out web/codebase research in a separate context and keep only
  the conclusion — this routine did its web research that way; the main context never held the raw pages.
- **Scope tightly.** "Fix the login function in `auth.ts`," not "refactor auth." Smaller scope = less
  context pulled = fewer tokens and better output.
- **`/clear` between unrelated tasks; `/recap` on resume** (saves 15–40k tokens vs. replaying history).
- **Cap tool output** (~8k tokens) so a noisy command can't blow the window.
- **Routines notify only on signal.** A routine that posts "all good" every day burns tokens and
  attention; silence is the correct output when nothing changed. (That's the contract this run follows.)

## E. Billing math — and the June-15 news

- **News (verify before acting):** Anthropic's plan to pull Agent SDK / `claude-p` (headless) /
  GitHub-Actions usage *out* of subscription pools into a separate dollar credit (full API rates, no
  rollover) was scheduled for **June 15, 2026** and **paused on the day it was due to go live.** Right
  now automation — including scheduled routines like this one — still draws from normal subscription
  limits. Treat the subsidy as living on borrowed time: keep automation lean and assume it ends.
- **Plan vs. API break-even:** Max 5x ($100/mo) wins above ~$3.33/day API-equivalent; Max 20x ($200/mo)
  above ~$6.67/day. At our mix (interactive + several scheduled routines), a Max plan is very likely
  cheaper than pay-as-you-go API. Action: confirm which billing we're on and right-size the plan.

## F. Critique of the recurring prompt (it was asked for)

The driving prompt ("locate inefficiencies… ANYTHING… search the web… keep up to date… check the
news") is an excellent *one-off brainstorm* but an **expensive recurring routine**, and it embodies the
very inefficiency it asks about:

- **It's unbounded.** "ANYTHING that could help" forces wide, every-time research and leaves "done"
  undefined — maximal tokens by construction.
- **It bundles two different jobs:** (1) a cheap, frequent *news watch* and (2) a rare, deliberate
  *deep process review*. Running both on every tick is wasteful.
- **It re-derives the same advice each run** because nothing tells it to only report changes.

Suggested rewrite for the recurring slot (cheap, delta-only, Sonnet/Haiku):

> *"News watch only. Since the last run (date in this file), search for Anthropic model/pricing/billing
> changes and Claude Code feature changes that would alter our cost math or workflow. If nothing
> material changed, send no notification. If something did, append a dated 1-line entry to
> `process-efficiency-review` and notify with ≤120 words. Use Sonnet. Don't re-explain known advice."*

And keep the **deep review** (this document) as a deliberate, occasional ask — quarterly, or when a
news entry flags something big — run on Opus, with the explicit goal "update sections A–E."

---

### Sources (dated June 2026)
- Anthropic API pricing & caching — <https://platform.claude.com/docs/en/about-claude/pricing>, <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- Prompt-cache 5-min TTL change (2026) — <https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363>
- Claude Code token-saving tips — <https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/>, <https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage>
- Subagents / context best practices — <https://code.claude.com/docs/en/best-practices>, <https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/>
- Hybrid local+cloud architecture & savings — <https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/>, <https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026>
- Plan vs. API break-even — <https://www.buildthisnow.com/blog/guide/development/claude-code-max-plan-vs-api>, <https://www.morphllm.com/claude-code-pricing>
- June-15 billing change paused — <https://thenewstack.io/anthropic-pauses-claude-agent-sdk-subscription-change/>, <https://letsdatascience.com/news/anthropic-pauses-claude-agent-sdk-billing-overhaul-1cff2071>
- June 2026 model/pricing news (Opus 4.8, Fable 5 export-control suspension) — <https://releasebot.io/updates/anthropic>
