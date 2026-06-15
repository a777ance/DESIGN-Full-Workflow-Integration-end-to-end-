# AI Collaboration Process — Efficiency Review

How we work with AI (Claude Code + the local LLM rig), where the waste is, and how to
spend fewer tokens for the same or better output. This is a *process* doc, not a feature
spec — it sits next to `portfolio.md` and `tech-debt.md` because the way we run the AI is
itself a cost line and a moat-or-drag on the "lean and mean" mandate.

**Last reviewed:** 2026-06-15. This file is time-sensitive — the LLM market moves weekly.
Re-run the review (see §6) and update the date when you do. Newest findings at the top per
house style.

---

## 0. TL;DR — do these first

1. **Today (2026-06-15) Anthropic split human vs. autonomous usage on subscription plans.**
   Our scheduled routines, GitHub Actions, and `claude -p` calls are *autonomous* — they now
   draw from a capped monthly programmatic credit ($20 Pro / $100 Max-5x / $200 Max-20x), then
   bill at full API rates. **This changes our cost structure starting now.** See §1.
2. **Turn on prompt caching discipline** everywhere we control the prompt — it is the single
   biggest throughput/cost multiplier and cached input doesn't count against rate limits. §2.
3. **Route low-stakes work to the local rig we already built** (stage 10: LiteLLM + Ollama +
   deepseek-r1). We have the hybrid hardware; we're under-using it for the boring jobs. §3.
4. **Scope prompts tightly and ask for a recommendation, not a survey.** Open-ended prompts to
   a high-effort model are the most expensive thing we do. §4 — and §5 critiques the prompt
   that generated this very doc.

---

## 1. The 2026-06-15 billing change — the thing that actually moves our bill

Anthropic now separates **human-in-the-loop** usage (you typing in Claude Code interactively)
from **autonomous / programmatic** usage (anything driven by code, not a person watching):

- Programmatic = the **Claude Agent SDK**, the **`claude -p`** one-shot CLI, **Claude Code
  GitHub Actions**, **scheduled routines**, and third-party apps built on the Agent SDK.
- Each paid plan gets a **dedicated monthly programmatic credit**: **$20 Pro · $100 Max-5x ·
  $200 Max-20x**. Unused credit **expires monthly** (no rollover). Past the credit, autonomous
  usage bills at standard API token prices.

**Why this is our problem specifically.** This whole portfolio leans on autonomous AI:
NARF/ZORT session routines, the `check-docs.py` CI gate, and recurring jobs like the one that
wrote this file. All of that is now metered against the programmatic credit, separately from
interactive coding. A run that quietly re-does web research and re-reads seven CLAUDE.md files
every time it fires is now a *direct cash line*, not a free background nicety.

**Actions:**
- **Decide the plan tier on cost, not habit.** If autonomous usage is light, Pro's $20 credit
  may cover it; if the routines run often, model the Max tiers against expected API overage.
  This is a ZORT budget item — see the pointer added to `docs/ai-cfo/budget.md`.
- **Make every scheduled run cheaper** (the rest of this doc). The credit makes §2–§4 pay off
  in real dollars now, not just in latency.
- **Note the Fable 5 trap:** Fable 5 is $10/$50 per MTok — *double* Opus 4.8's $5/$25 — and on
  subscription plans it's only included free through **2026-06-22**, then shifts to usage
  credits. Don't default routines to Fable 5; reserve it for genuinely hard long-horizon work.
  Opus 4.8 is the workhorse; Sonnet 4.6 ($3/$15) and Haiku 4.5 ($1/$5) for lighter jobs.

---

## 2. Token & cost levers, ranked for *our* setup

### 2.1 Prompt caching — biggest lever, lowest effort
Caching is a **prefix match**: stable content first, volatile content last; any byte change in
the prefix invalidates everything after it. Cache **reads cost ~0.1×** base input; **writes
cost 1.25×** (5-min TTL). Break-even is ~2 requests. Crucially, **cached input tokens don't
count against the rate limit** on current models — it's a throughput multiplier, not just a
discount.

For us this means: keep the big stable context (the CLAUDE.md house-style block, the schema,
the roster shape) at the *front* of any programmatic prompt and frozen — no `datetime.now()`,
no per-run IDs interpolated into it. Put the per-run question at the end. Verify with
`usage.cache_read_input_tokens`; if it's zero across runs, a silent invalidator is in the
prefix.

### 2.2 Effort level — match it to the job
`effort: low` for formatting, linting, doc-link checks, simple status summaries — big token cut,
no quality loss on rote work. Reserve `high`/`xhigh` for architecture, security review, and
hard refactors. Don't run a doc-link gate at high effort.

### 2.3 Right-size the model
Default Opus 4.8. Drop to **Sonnet 4.6** for high-volume summarize/extract, **Haiku 4.5** for
classify/label/"is this changed?" checks. Most of our autonomous jobs (did the docs change?
any new known-issue? is the link graph intact?) are Haiku/Sonnet work, not Opus work.

### 2.4 Batch & reuse context
One session that already has the repo loaded beats five cold conversations. The Batch API is
**50% off** for anything non-latency-sensitive — nightly/weekly routines are the textbook case.

### 2.5 Subagents are a context tool, not a free one
Subagents keep the main context clean (delegate "investigate X" to a separate window), but a
subagent-heavy run can burn **~7× the tokens** of a single thread because each carries its own
context. Use them to isolate heavy reads, not as a reflex.

### 2.6 Scope the inputs
`.claudeignore` + permission denies reportedly cut context by ~85% in disciplined setups.
Don't let a run slurp the whole tree when it needs three files.

---

## 3. Hybrid local + Claude — we already own the rig, use it

Stage 10 (`localDNS/10-ai-orchestration/`) already runs **LiteLLM** as a unified gateway,
**Ollama** serving local models, a reasoning ladder (`local-reason` = deepseek-r1:1.5b on the
t630, `cloud-gpu-reason` = full R1 on a rented GPU, `cloud-overflow` = Claude). The industry
pattern for 2026 cost control is exactly this: route the bulk/low-stakes work to a cheap/local
tier and send only high-stakes work (user-facing replies, real coding, tool calls) to a premium
cloud model. Documented results cluster at **60–85% cost reduction**.

What to actually route locally:
- Draft summaries, first-pass classification, "did anything change" diffs, commit-message
  drafts, link/anchor sanity — local model, then a cheap Claude pass only if needed.
- Keep on Claude: anything that writes a kept customer document, anything touching money or the
  roster, anything that ships to a public repo, and final review.

**Privacy guardrail (open):** `TD-14` flags that a `sensitive`-tagged task can currently fail
over from `local-reason` to `cloud-overflow` (Claude) because the LiteLLM failover layer doesn't
enforce `allow_cloud=False`. Until that fails *closed*, don't route anything privacy-sensitive
through the local-first chain expecting it to stay local. Fixing TD-14 is a prerequisite for
trusting hybrid routing on real customer data.

---

## 4. Better prompting (cheaper *and* better)

- **State the decision, not the topic.** "Pick the cheaper of A/B for our nightly routine and
  justify in 3 bullets" beats "tell me everything about cost." Open-ended prompts to a
  high-effort model produce sprawling, expensive runs.
- **Ask for a recommendation, not a survey.** On Opus 4.8 / Fable 5, "give me the answer and a
  one-line why" out-performs "lay out all the options" on both cost and usefulness.
- **Front-load the full task in one well-specified turn** for autonomous runs — the model is
  more autonomous now; dribbling context over many turns wastes tokens and sometimes quality.
- **Add a silence/terseness default** for routine agents so they don't narrate every step.
- **Let routines write findings to a file (like this one) and diff against it next run** instead
  of re-deriving from scratch — turns a recurring full-cost research run into a cheap delta.

---

## 5. Critique of the prompt that generated this doc

The request ("Locate inefficiencies in our PROCESS… reduce token use… better prompting…
leverage other AI… hybrid local/cloud… ANYTHING that could help… search the web… keep UP TO
DATE… check the news") is **broad and open-ended**, which is itself the most expensive prompt
shape — it tells a high-effort model to explore widely with no stop condition. It worked here
because it ran once, but as a **recurring routine** it would re-do the full web sweep and re-read
every CLAUDE.md every fire, on the metered programmatic credit (§1). Tighter, cheaper versions:

- **Scope it:** "Check for AI/LLM cost or feature news since `{last_review_date}` that changes
  our process; if nothing material, say so and stop." (A no-change run should be nearly free and
  silent.)
- **Bound the output:** "Top 3 actions, ranked by dollar impact, ≤1 paragraph each."
- **Pin the freshness anchor:** pass the date of the last review so the run diffs instead of
  re-deriving — and so "keep up to date" has a concrete baseline.
- **Split the jobs:** news-check (cheap, frequent, Haiku/Sonnet) vs. deep process redesign
  (rare, Opus, on demand). Running both every time is the waste.

The instinct behind the prompt is right — this is exactly the kind of standing review worth
having. The fix is to make the *recurring* version cheap and scoped, and keep the broad version
for occasional deep passes.

---

## 6. Staying current (the "keep UP TO DATE" ask)

This changes weekly; treat this doc as a living baseline:
- Re-run a **scoped** version of this review monthly (or when a model launch / pricing change
  hits the news), diffing against this file's "Last reviewed" date. Don't re-derive from zero.
- Watch: Anthropic release notes & pricing, model-id/pricing table in the `claude-api` skill,
  rate-limit and credit-policy changes (the 06-15 split will evolve).
- Update the date at the top and append new findings above the older ones.

---

## Sources (2026-06-15 sweep)

- [Anthropic's June 15 Billing Change — codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [The June 15 Claude Billing Change Explained — Pravin Kumar](https://www.pravinkumar.co/blog/claude-june-15-billing-change-explained-2026)
- [Anthropic Quietly Reprices Claude Pro (June 15) — Level Up Coding](https://levelup.gitconnected.com/anthropic-will-quietly-reprice-your-claude-pro-plan-on-june-15-the-free-20-credit-replacing-1ebd922a7786)
- [Claude Code Token Optimization Guide (2026) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude API Cost Optimization for Enterprises (2026) — Cleveroad](https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo](https://www.tembo.io/blog/claude-code-subagents)
- [Best practices for Claude Code — Anthropic docs](https://code.claude.com/docs/en/best-practices)
- Model IDs / pricing / prompt-caching economics: the `claude-api` skill reference (cached 2026-06-04).
