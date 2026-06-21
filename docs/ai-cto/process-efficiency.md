# Process efficiency review — user ↔ AI workflow

*Prepared 2026-06-21 by the AI CTO routine. Scope: how we work with Claude (and other
AI), where tokens/money leak, and what to change. Sources are dated — recheck quarterly;
this space moves weekly.*

> **Bottom line up front.** The three biggest levers, in order of payback:
> 1. **Trim & deduplicate the always-loaded `CLAUDE.md` context** — it's a tax paid on
>    *every* turn of *every* session (~14.5K tokens today, with ~1.5K pure duplication).
> 2. **Route by difficulty** — Haiku/Sonnet (or the local t630 stack) for mechanical work,
>    Opus/Fable only for hard reasoning. Single biggest lever on the monthly bill, and now
>    also our defense against the new routine-credit pool (see §6, the June 15 change).
> 3. **Batch + cache the statement pipeline** — it's the textbook case for the Batch API
>    (50% off) stacked with prompt caching (90% off the cached prefix).

---

## 1. The always-loaded context tax (highest-payback fix)

Every session loads the repo's `CLAUDE.md` *before you type a word*, every turn, as a fixed
baseline. Measured today:

| File | Bytes | ≈ tokens |
| ---- | ----: | -------: |
| `localDNS/CLAUDE.md` | 20,472 | ~5,100 |
| `DESIGN-…/CLAUDE.md` | 17,987 | ~4,500 |
| `MARKETING/CLAUDE.md` | 10,660 | ~2,700 |
| `customers` / `claude-code-homelab` / `Azure-lab` | ~9,300 | ~2,300 |
| **Total across repos** | **~58 KB** | **~14,500** |

Two concrete wins:

- **The "House style: ordering & typography" block is duplicated verbatim in 6 `CLAUDE.md`
  files** (~20 lines each ≈ **~1.5K tokens of pure repetition**, paid in full on any
  cross-repo session like this one). It's also *verbose procedural rules* — exactly what
  Anthropic now recommends moving **out of always-on context and into a Skill** that loads
  only when relevant. Action: replace the block in each `CLAUDE.md` with a one-line pointer
  (`House style → /house-style skill`) and put the full rules in a single
  `.claude/skills/house-style/SKILL.md`. Saves the duplication on every turn and keeps one
  source of truth.
- **`localDNS/CLAUDE.md` and `DESIGN/CLAUDE.md` carry deep reference tables** (full deploy-
  path table, every Known-Issue row, the nftables deploy checklist). Those belong in
  `README.md` / `INSTALL-NOTES.md` (which the model reads on demand), not in the always-on
  brief. Target: a `CLAUDE.md` that is a *map + the 5 rules that must never be missed*, and
  defer the rest. Aim < ~1,500 tokens each.

**Why it matters more than it looks:** prompt caching only helps the *stable prefix*. A lean,
stable `CLAUDE.md` placed first maximizes cache hits (cached input = 10% of normal price);
a bloated one that you edit mid-session keeps busting the cache. Treat `CLAUDE.md` as a
between-sessions config file — set it, then leave it alone during work.

## 2. Tool / MCP overhead — already mostly handled ✅

The GitHub MCP server alone exposes ~50 tools; connected MCP servers can silently add
10–20K tokens of schema per request. **We're already using deferred tool schemas
(`ToolSearch` / tool-search mode)** in these sessions, which is the recommended fix —
schemas load only when a tool is actually needed. Keep it on. Don't connect MCP servers a
given session won't use.

## 3. Right-size the model per job (routing)

Rough industry split: ~60–70% of requests are simple (classify/extract/format), ~20–30%
moderate, ~10% truly need a frontier model. We pay Opus rates for all of it by default.

- **This very routine runs on Opus 4.8 (1M).** For a process-review/research routine that's
  defensible, but recurring *mechanical* routines (lint a doc, check links, reformat a
  webhook, summarize call notes) should run on **Sonnet 4.6 or Haiku 4.5**. Opus is
  $5/$25 per MTok; Sonnet $3/$15; Haiku $1/$5 — Haiku is 5× cheaper than Opus on input.
- **We already own a router.** `localDNS` stage 10 (LiteLLM + Open WebUI + the reasoning
  ladder: `local-reason` deepseek-r1:1.5b on the t630, `cloud-gpu-reason` on a rented GPU,
  `cloud-overflow`). That's the natural home for the **high-volume, low-stakes NLP** in this
  business: first-pass "Handled For You" log drafting, lead/call-note classification,
  statement-copy drafts, FAQ tidying. Keep those off the Claude meter; reserve Claude for
  agentic coding and judgment calls (honesty-rule checks, pricing logic, anything customer-
  facing-final). Note the existing guardrail: don't run heavy `deepseek-r1:7b`+ on the t630
  CPU — it cooks the box. Keep local work to the 1.5b/quantized tier or the rented GPU.
- **Don't point Claude *Code* at local small models for the coding itself** — local 3B–7B
  models are measurably worse at multi-step agentic tool-use. The hybrid win is *task
  splitting* (local for bulk NLP, Claude for the hard 10%), not swapping Claude's brain out.

## 4. Batch + cache the statement run (real money at scale)

Building the monthly Network Activity Statements is the ideal candidate:

- It's **async** (24h turnaround is fine) → **Batch API = 50% off input *and* output**.
- Every household shares a **large identical prefix** (the template, the house style, the
  honesty rules) with only the per-home stats changing → **prompt caching = 90% off** the
  cached portion. Order prompts stable-first, variable-last.
- Stacked, that's a ~95% cut on the per-statement token cost. At ~a penny a home today this
  is small; at 10–20+ homes (Phase 2) it compounds — bake it into the generator now.

## 5. Use subagents / Explore for fan-out, keep the main thread lean

For "search the whole codebase" or "research N sources" work, spawn a subagent/`Explore`
agent: the verbose reading happens in *its* context and only the conclusion returns to the
main thread. Prevents large search dumps from bloating (and busting the cache on) the main
session. This routine did its web fan-out this way.

## 6. NEWS — the June 15 2026 billing change (directly affects our routines) ⚠️

As of **2026-06-15**, **Claude Agent SDK usage and headless `claude -p` invocations no
longer count toward the Claude plan's normal usage limits — they bill against a separate,
API-rate credit pool** (~$20/mo on Pro, $100 on Max 5×, $200 on Max 20×). **Scheduled
routines and Claude-Code-on-the-web sessions run through exactly this path.** Implications:

- Routine spend is now metered and capped separately — a runaway/verbose routine can drain
  the credit pool and stall the others. Model routing (§3) is now also a *budget defense*,
  not just a cost-saver.
- Set explicit budgets/limits in `settings.json` and prefer cheaper models for routine
  bodies. Reserve Opus routines for ones that genuinely need it (like this review).
- Re-confirm exact figures against the official pricing page before acting — third-party
  blogs disagree on the edges.

Also current (May–June 2026): Opus 4.8 = $5/$25 per MTok (Fast Mode now $10/$50, down from
$30/$150 on 4.7); Sonnet 4.6 = $3/$15; Haiku 4.5 = $1/$5.

## 7. Prompting — including a critique of the prompt that triggered this review

**General practices that cut tokens *and* improve output:**
- Put stable context first, the variable ask last (cache-friendly).
- State the **output format and a length cap** up front ("≤1 page", "table only", "diff
  only"). Open-ended prompts produce long, expensive, unfocused answers.
- One job per prompt where practical; scope it to the files/repo that matter.
- Prefer pointers over paste ("see `schema.md`") so the model pulls context on demand.
- For recurring asks, make a **Skill/slash-command** so the framing isn't re-typed (and
  re-tokenized) each time.

**Critique of the triggering prompt** (paraphrased: *"Locate inefficiencies in our process…
Is there a better way… Perhaps better prompting… Anything you could possibly think of…
Leveraging other AI… hybrid local LLM and Claude… ANYTHING that could help. Search the web…
Keep UP TO DATE… Check the news. If THIS prompt is inefficient also let me know."*) — the
ask is excellent in *intent*, but as a prompt it is itself a mild example of the inefficiency
it's hunting:

- **Unbounded scope.** "ANYTHING that could help" + "anything you could possibly think of"
  invites a maximal, token-heavy sweep with no stopping rule. A bounded ask ("top 5 levers,
  ranked by payback, ≤2 pages") gets you the same signal for a fraction of the tokens.
- **Several asks stacked into one** (inefficiencies + prompting + other AI + hybrid + news +
  self-critique). Each is answerable; together they push toward a long essay. Splitting into
  a standing **"efficiency-review" Skill** lets you re-run it cheaply on a schedule instead
  of re-specifying it each time.
- **No output contract** (format, length, where to put the result). The model has to guess —
  here it chose "durable doc + notification," but that's a guess.
- **No freshness window.** "Keep up to date / check the news" is good, but "as of the last 30
  days, cite dates" makes the recency check cheap and verifiable.

**Tighter rewrite (drop-in):**

> *"Efficiency review of our Claude workflow. Give me the **top 5 levers** to cut token spend
> across our repos, **ranked by payback**, each ≤3 sentences with the concrete action.
> Include: (a) anything specific to our setup you can see, (b) one current best-practice from
> the last ~30 days with a dated source, (c) one line on whether this prompt itself could be
> tighter. **≤2 pages.** Write it to `docs/ai-cto/process-efficiency.md` and notify me with
> the headline."*

That version is reproducible, bounded, and self-documenting — and it's the seed of the
standing Skill recommended above.

---

## Recommended actions (in payback order)

1. **Lean the `CLAUDE.md`s**: move the house-style block to one `house-style` Skill; demote
   reference tables to README/INSTALL-NOTES; target < ~1,500 tokens each. *(§1)*
2. **Set model routing + `settings.json` budgets** so mechanical routines run on Haiku/Sonnet
   or the local t630 stack; reserve Opus/Fable for hard reasoning. *(§3, §6)*
3. **Batch + cache the statement generator** (stable-first prompts) before Phase-2 scale. *(§4)*
4. **Standardize prompts**: an `efficiency-review` Skill + a house "output contract" habit
   (format + length cap up front). *(§7)*
5. **Keep deferred tool schemas on; don't over-connect MCP servers per session.** *(§2)*

## Sources (recheck — this field moves weekly)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Anthropic API Pricing in 2026: Caching, Batch & Optimization — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [What Claude Code Actually Costs in 2026 (two June deadlines) — UsageBox](https://usagebox.com/articles/claude-code-cost-2026-per-token-per-month-june-deadlines)
- [Claude Code Subscription Split — June 15, 2026 (gist)](https://gist.github.com/yurukusa/7d854616809e673ca8d23353ed8267a6)
- [Claude Code best practices: hooks, subagents & context management (2026) — SmartScope](https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/)
- [Claude Code Routines guide — claudefa.st](https://claudefa.st/blog/guide/development/routines-guide)
