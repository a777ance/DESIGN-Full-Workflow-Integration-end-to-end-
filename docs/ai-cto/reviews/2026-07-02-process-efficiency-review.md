# NARF — special review — 2026-07-02 — Process efficiency: the user↔AI loop

**Question from the CEO:** *"Locate inefficiencies in our PROCESS — between the user and
the AI. Reduce token use. Better prompting. Leverage other AI. Run hybrid local LLM +
Claude. Keep up to date. And if this prompt is inefficient, say so."*

This is not the daily portfolio review — it's a one-off audit of **how we spend tokens
and attention**, not what we're building. Everything below is verified against current
(July 2026) Anthropic pricing/features and against our own repo state. Sources at the end.

---

## TL;DR — the five biggest wins, in ROI order

1. **Stop re-deriving static facts every cycle.** Our own review log is the clearest
   inefficiency in the whole system (see §1). A cheap "has anything changed?" gate in
   front of the daily review would cut its token cost by an estimated **70–90%** on
   no-change days — which, lately, is *most* days.
2. **Run the routine reviews through the Batch API + prompt caching, not interactively.**
   Non-urgent, scheduled work (these NARF/ZORT reviews) is the textbook batch case:
   **50% off** for batch, stacked with **~90% off** cached context = **~95% effective
   discount**. We are currently paying full interactive rate for work nobody is waiting on.
3. **Use the router we already built (TD-14 notwithstanding).** `localDNS`'s LiteLLM
   stack on `:4040` already has a local reasoning ladder + cloud tiers. ~60–70% of our
   AI work (link-checking, doc-lint, "did the CHANGELOG change", formatting, first-pass
   triage) is *mechanical* and should never touch Opus. Route it to local Ollama or Haiku.
4. **Trim the CLAUDE.md files.** They are the single largest fixed token cost of every
   session — loaded in full, never evicted (see §4). Ours are big and getting bigger.
5. **Fix our prompting defaults.** Scope, format, and a token budget up front beat
   "explore ANYTHING." The CEO's own prompt (this one) is a good example — critique in §5.

---

## 1. The inefficiency already in our own logs (the expensive one)

Look at `docs/ai-cto/reviews/`: **~20 daily reviews, 2026-06-04 → 2026-07-01.** Read three
in a row. The last four cycles re-establish the *same three facts*:

- TD-14 is still live (verified "a third time against the live config" on 07-01).
- CHANGELOG's newest entry is still 2026-06-07 (unchanged ~3 weeks).
- The t630 SSH session is still the critical path.

Each cycle re-loads full context and re-verifies facts that **provably did not change** —
the review itself keeps saying so. That is the exact anti-pattern the token-optimization
literature names first: *paying to re-derive stable state.* On a no-change day the entire
review could be replaced by a ~200-token diff check.

**Fix (concrete, low effort):**
- Keep a tiny `docs/ai-cto/state-hash.json` — a hash of `CHANGELOG.md` HEAD, `config.yaml`
  TD-14 line, and the phase-gate checklist. The review's *first* step is: compare hashes.
- **No change → emit a one-line "no-delta, TD-14 still open, nothing shipped" and stop.**
  Don't re-open every file. (This is exactly what the `/compact` + short-circuit pattern is for.)
- **Change detected → run the full review, but only on the changed surface.**
- Persist "known-true, last-verified" facts so the model trusts them instead of re-checking.

This one change probably saves more tokens than every other item here combined, because
it attacks *frequency × context size*, not just per-call price.

---

## 2. Model routing — we already own the hard part

`localDNS/10-ai-orchestration/` is a LiteLLM gateway (`:4040`) with a local reasoning
ladder (`local-reason` = deepseek-r1:1.5b on the t630) and cloud tiers. The infrastructure
exists. We are just not *routing to it* for our own dev/ops work.

The industry rule of thumb (2026): **~60–70% of agent requests are simple** (classify,
extract, format, "did X change") and belong on a local or cheap model; ~20–30% moderate;
only ~10% need a frontier model. Reported savings from routing this way: **60–80%**.

**Current Claude API pricing (per 1M tokens, in/out), July 2026:**

| Model | Input | Output | Use it for |
| ----- | ----- | ------ | ---------- |
| **Haiku 4.5** | $1 | $5 | Mechanical: link-checks, doc-lint, triage, formatting, "did it change" |
| **Sonnet 5** | $3 ($2 intro thru Aug 31) | $15 ($10 intro) | Default workhorse; most reviews & edits |
| **Opus 4.8** | $5 | $25 | Only the genuinely hard reasoning / architecture calls |
| **Opus 4.8 Fast** | $10 | $50 | Only when latency matters *and* it's hard |

Notes: Opus 4.8 **cache-hit input is $0.50/M** (90% off); batch is $2.50/$12.50. Sonnet 5
now has a native **1M-token** context and is the new default in Claude Code.

**Actions:**
- In Claude Code, stop defaulting everything to Opus. `/model sonnet` for normal work;
  reserve Opus for the 10% that's actually hard. Use **effort controls** (low/med/high/max)
  — most edits don't need `high`.
- Route our *automated* jobs (doc-checks, the change-detector in §1, first-pass triage)
  to **local Ollama via the `:4040` router** or to **Haiku**. `check-docs.py` doesn't need
  an LLM at all — but any LLM glue around it should be Haiku-or-local, never Opus.
- **Caveat — TD-14 blocks trusting the router for anything sensitive.** The `local-reason`
  fallback chain still fails *open* to `cloud-overflow` (Claude cloud). Until that's fixed
  (3-line edit, flagged four reviews running), only route **non-sensitive** work through
  it. Fix TD-14 first, then the router becomes safe to lean on.

---

## 3. Prompt caching + Batch API — the two discounts we're leaving on the table

**Prompt caching** (cached input ~90% cheaper): the cache stays warm ~5 min (Anthropic
recently shortened the longer cache window — don't rely on the old 1-hour behavior).
Cache mechanics: min 1,024 tokens, static-content-first, cache *write* costs 1.25×, so
break-even is after 2 reads. Practical wins for us:
- Our CLAUDE.md files and the portfolio docs are large and *stable* → ideal cache content.
  Working in **focused bursts** (not one call every few hours) keeps the cache warm.
- Structure any repeated-prompt tooling static-first, dynamic-last.

**Batch API** (50% off, async, results within the window): our scheduled NARF/ZORT reviews
and doc-audits have **no human waiting** — that is exactly what Batch is for. Stacking
batch + cache reportedly reaches **95%+** effective savings on this class of work.
Migrating the routine reviews from interactive to batch is the single highest-leverage
*billing* change available to us.

---

## 4. Claude Code session hygiene (fixed cost, every session)

- **CLAUDE.md is loaded in full and never evicted.** Ours are large (this cross-repo
  session loads *five* of them). That's a fixed tax on every turn. Push folder-specific
  detail into nested `CLAUDE.md`/`.md` files loaded on demand with `@file`; keep the root
  ones lean. Candidate: the house-style block is duplicated verbatim across all repos —
  factor it once and reference it.
- **`/context`** to see where tokens go (system prompt, tools, memory, skills, history).
- **`/compact`** at task boundaries; **`/clear`** when switching to unrelated work.
- **Plan mode** (Shift+Tab) before expensive multi-file work — review the plan, cut waste,
  then execute. Kills trial-and-error token burn.
- **Subagents** for research/exploration so the main context stays clean (we do this).
- **`disableBundledSkills` / `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`** hides skills/workflows
  we don't use from the model's context — relevant for these lean infra repos (PLUGINS.md
  in `localDNS` already says "keep it lean").

---

## 5. Better prompting — including a critique of the prompt that triggered this review

The CEO's prompt was **strong on intent, weak on efficiency**. What it did well: named the
real levers (tokens, prompting, hybrid, other AI), asked for currency, invited a
meta-critique. Where it cost tokens:

- **Unbounded scope.** "ANYTHING that could help… Search the web… Check the news" with no
  ceiling invites an open-ended crawl. Open-endedness is the #1 token sink.
- **No output contract.** No length, no format, no "where to put it." The agent has to
  guess (I chose: a dated review doc + a phone summary).
- **Didn't hand over known state.** It didn't mention that *we already run a LiteLLM
  hybrid router* — so a naive agent would spend tokens rediscovering it (or, worse,
  recommend building what already exists). Always give the AI the facts it would otherwise
  pay to re-derive.
- **Two questions in one.** "Audit the process" + "critique this prompt" is fine, but
  stating them as an explicit 2-item deliverable would have tightened the response.

**A tighter rewrite (same intent, ~⅓ the wandering):**

> *"Audit our user↔AI process for token/cost waste. Context: we run a LiteLLM hybrid
> router (`localDNS/10-ai-orchestration`, local Ollama + Claude cloud tiers) and a daily
> NARF/ZORT review routine. Deliver (a) top 5 fixes ranked by ROI with rough token/$
> impact, (b) a critique of this prompt. Use current (2026) Anthropic pricing — search if
> needed. Cap at ~1,500 words, write it to `docs/ai-cto/reviews/`. Skip anything we
> already do."*

General defaults worth adopting for **all** our AI prompts:
- Lead with scope + the deliverable format + a rough budget ("top 5", "≤1500 words").
- Front-load known state so the model doesn't pay to rediscover it.
- Ask for a recommendation, not a survey. "Give me the answer, not the options."
- For recurring jobs, write the prompt *once* as a stable, cacheable template.

---

## 6. Keeping up to date (the CEO asked to stay current, cheaply)

The landscape moves weekly, but *chasing* it is itself a token cost. Cheap cadence:
- A **monthly** (not per-session) 20-min scan of the Claude Code changelog + Anthropic
  release notes, captured as a dated line in this reviews folder. Batch/Haiku it.
- Watch specifically for: cache-window changes (the 1-hour window was recently trimmed),
  new cheaper models, and Batch/effort-control changes — those directly move our bill.

---

## Recommended follow-ups (for the tech-debt log, if the CEO agrees)

- **New TD:** "Daily review routine re-derives static state — add a change-detector gate
  and move to Batch API." (P2, DESIGN — this is the biggest recurring token sink.)
- **Existing TD-14** gets a second reason to fix: it's not just a privacy bug, it's the
  blocker to safely routing our own work through the local-first router (§2).

---

## Sources (verified July 2026)

- [Claude Platform — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Platform — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code — Changelog](https://code.claude.com/docs/en/changelog)
- [Anthropic API Pricing 2026 (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing 2026: Opus 4.8 / Sonnet / Haiku (MetaCTO)](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Run Claude Code with local agents using LiteLLM + Ollama (Matejuk)](https://medium.com/@kamilmatejuk/run-claude-code-with-local-agents-using-litellm-and-ollama-ab88869cbd00)
- [Prompt Caching in 2026: cut API costs up to 90% (DevToolLab)](https://devtoollab.com/blog/prompt-caching-guide)
- [Anthropic quietly nerfed Claude Code's 1-hour cache (XDA)](https://www.xda-developers.com/anthropic-quietly-nerfed-claude-code-hour-cache-token-budget/)
- [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
