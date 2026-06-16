# AI process efficiency — how we talk to the models

A NARF review of where tokens and money leak in the way *we* use AI — the loop between a
person (or a routine) and the model — and what to change. Tied to our actual setup (the
localDNS LiteLLM ladder, the CLAUDE.md files, the scheduled routines), not generic advice.

**Reviewed:** 2026-06-16. Prices/model IDs current as of June 2026 — re-check quarterly,
this moves fast. Sources at the bottom.

---

## TL;DR — the five biggest levers, in order

1. **Turn on prompt caching for every Claude call we make.** Cache reads cost ~0.1× input;
   our repeated agent sessions over the same repos + CLAUDE.md are the ideal case. 60–85%
   off the input bill, near-zero effort. **Biggest win, lowest disruption.**
2. **Right-size the model per task.** Opus 4.8 is 5× Haiku per token. Routine work (link
   checks, log triage, this monitoring routine, classification) should run on Haiku/Sonnet;
   reserve Opus 4.8 for hard reasoning. We already do exactly this *locally* with the
   reasoning ladder — extend the same discipline to which **cloud tier** we call.
3. **Batch anything that isn't interactive (50% off).** Monthly statement generation (Stage
   06), CI doc checks, bulk classification, scheduled digests — all candidates for the
   Message Batches API or a Claude subscription's batch lane.
4. **Trim the always-loaded context.** Our CLAUDE.md files (esp. localDNS) are large and
   re-read every session. Keep the briefing lean; push detail behind links. Same logic as
   `.claudeignore` discipline (reported ~85% context reduction in the wild).
5. **Keep the local-first hybrid we already have — and close the privacy gap.** The LiteLLM
   ladder is the right architecture (industry reports 60–86% savings). TD-14 (sensitive →
   cloud-overflow failover) undpercuts the privacy promise; fix it before leaning harder on
   the local tier.

---

## 1. This very prompt is the worked example

The request that triggered this review — *"is there a better way to reduce token use… hybrid
local LLM and Claude API… anything"* — named "Claude API" and "hybrid local LLM," which made
the harness auto-load the **entire `claude-api` skill** (model tables, every SDK's code, the
full Managed Agents reference — tens of thousands of tokens) before a single word was written.
The question needed maybe 5% of that.

That is the inefficiency pattern in miniature, and it has two lessons:

- **Scope the ask.** A broad "anything that could help?" pulls broad context. "Cut our Claude
  bill — we run scheduled routines and agent sessions over the repos" would have pulled the
  same useful answer with a fraction of the load. Narrow prompts → narrow context → fewer
  tokens *and* sharper output.
- **Keyword-triggered skill loads are real cost.** Mentioning a product name in passing can
  load its whole skill. Worth knowing when writing prompts and when configuring which skills
  are enabled per repo (see `PLUGINS.md` — "keep it lean" already applies here).

**On the meta-prompt:** it was effective at getting a thorough answer, but it was the
*expensive* way to ask. For recurring questions, a short scoped prompt + an explicit model
choice (`/model haiku` for triage, Opus only when reasoning is the point) beats an open
"think of everything" every time.

## 2. Prompt caching — the highest-leverage change

The single biggest lever, and we're almost certainly leaving it on the table. Caching is a
**prefix match**: stable content first (frozen system prompt, CLAUDE.md, tool list), volatile
content last. Cache **reads cost ~0.1×** input; **writes cost ~1.25×** (5-min) or 2× (1-hr).
Break-even is two requests on the 5-min TTL.

What to do:

- **In the localDNS LiteLLM router:** ensure the Anthropic calls set `cache_control` on the
  stable system-prompt prefix. LiteLLM passes this through. Verify hits via
  `usage.cache_read_input_tokens` — if it's zero across repeated calls, a silent invalidator
  is at work (a `datetime.now()` in the prompt, an unsorted JSON blob, a per-request ID).
- **Keep the prefix byte-identical.** Don't interpolate timestamps/session IDs into the
  system prompt — they sit at the front and invalidate everything after. Put dynamic context
  at the end of the message list.
- **Pre-warm only when first-request latency is user-visible** (a `max_tokens: 0` call writes
  the cache and returns immediately). For background routines, skip it.

Real-world production teams report **60–85% cost reduction** from cache-hit-rate engineering
alone.

## 3. Right-size the model — the local ladder, applied to the cloud

Current cloud pricing (per million tokens, input / output, June 2026):

| Model | $/1M in | $/1M out | Use for |
| ----- | ------- | -------- | ------- |
| Haiku 4.5 | $1 | $5 | Triage, link checks, classification, monitoring routines, log scans |
| Sonnet 4.6 | $3 | $15 | Most production work; doc edits; balanced agent loops |
| Opus 4.8 | $5 | $25 | Hard reasoning, long-horizon agentic builds, cross-repo decisions |
| Fable 5 | $10 | $50 | Only the genuinely hardest long-horizon work — above Opus pricing |

We already run a **reasoning ladder locally** (`local-reason` deepseek-r1:1.5b on the t630 for
light work; `cloud-gpu-reason` for heavy). The gap: our *cloud* calls don't visibly apply the
same tiering. A monitoring routine that just checks "did anything change?" should not run on
Opus 4.8. Recommendation:

- **Default scheduled/monitoring routines to Haiku or Sonnet**, and escalate to Opus only when
  the routine actually surfaces something that needs reasoning.
- **Don't downgrade reflexively for hard work** — Opus 4.8's higher ceiling often means
  *fewer* turns and lower total cost on a genuinely hard task than a cheaper model thrashing.
  The rule is "cheapest model that does the job well," not "cheapest model."

## 4. Batch API — 50% off everything non-interactive

The Message Batches API runs the same requests asynchronously at **half price**, completes
most batches within an hour (max 24h), and stacks with prompt caching (combined, up to ~95%
off the cached-input portion). Candidates in our world:

- **Monthly statement generation (Stage 06).** It's scheduled, not interactive — perfect fit.
- **CI doc checks / bulk text passes.** If we ever LLM-assist `check-docs.py` or content
  linting, batch it.
- **Any "generate N things overnight" job** — digests, bulk classification of the master list.

Operational note (June 2026): headless/Agent-SDK usage now bills against a **separate API
credit pool** on subscription plans ($20 Pro / $100 Max-5x / $200 Max-20x per month), and a
pay-per-token API key is where the 50% batch discount applies. Worth structuring our automated
jobs (CI, this routine, statement runs) against the lane that's cheapest for *non-interactive*
volume.

## 5. Context hygiene — stop re-paying for the same tokens

- **Trim CLAUDE.md to a true briefing.** It's read every session; every line is a recurring
  tax. The localDNS deploy-path table and the full Managed-Agents-style detail belong behind
  a link, not in the always-loaded file. CLAUDE.md should be the map, README the territory.
- **`/clear` between unrelated tasks.** A long thread makes the model re-read the whole
  history each turn. Start fresh when the task changes; use `/recap` to resume without
  replaying.
- **Batch follow-ups into one message** instead of a chain of one-liners — each follow-up
  reprocesses the full context.
- **Scope requests** ("fix the link in `portfolio.md`", not "audit all the docs").

## 6. The hybrid we already have — keep it, and harden it

The LiteLLM + Ollama + Claude-API stack on the t630 is exactly the architecture the field is
converging on (LiteLLM gateway, local Ollama tier, cloud Claude tier, route by
sensitivity/complexity). Reported savings: 60–86% with minimal quality loss, because the hard
queries still go to the strong model. We're ahead of the curve here.

Two cautions:

- **TD-14 is load-bearing for this.** A `sensitive`-tagged task that falls over to
  `cloud-overflow` (Claude cloud) breaks the privacy promise that justifies running locally at
  all. Fail closed (local-only fallback for the sensitive chain) before routing more volume
  through the ladder. Privacy *is* the product here — the same honesty rule as the Statements.
- **Don't run heavy chain-of-thought models on the t630 CPU** (already a known issue) — that's
  a latency/heat cost, not a token cost, but it's part of the same right-sizing discipline.

---

## What NOT to do

- **Don't chase token savings that cost more in rework.** A too-small model that produces a
  wrong Statement, or a truncated input that drops a real figure, violates the honesty rule
  and costs a redo. Cheapest-that-works, measured on output quality.
- **Don't build an elaborate router for a one-person volume.** We already have the ladder;
  tuning caching + model choice + batch covers most of the savings without new surface. This
  is "liquidity before app" applied to our own tooling.

---

## Sources (June 2026)

- Prompt caching cost engineering (60–85% reductions): agentmarketcap.ai, web2md.org,
  aicostcheck.com; arXiv 2601.06007 "Don't Break the Cache."
- Hybrid local/cloud architecture + 60–86% savings: sitepoint.com hybrid-LLM guide,
  buildmvpfast.com, cleveroad.com Claude cost-optimization.
- Claude Code token reduction (CLAUDE.md, `.claudeignore`, `/clear`, `/recap`, model choice):
  firecrawl.dev, kdnuggets.com, agensi.io, analyticsvidhya.com.
- June 2026 billing changes (separate Agent-SDK credit pool; batch discount; per-token rates):
  morphllm.com, usagebox.com, finout.io.
- Model IDs/pricing: the bundled `claude-api` skill model table (cached 2026-06-04).
