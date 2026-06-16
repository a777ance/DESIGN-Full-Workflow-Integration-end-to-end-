# Process efficiency review — the user↔AI loop (2026-06-16)

A standing review of *how we work with the AI*, not what it builds: where tokens
(and dollars) leak in the day-to-day loop between a human and Claude across the
A777ance repos, and the cheapest ways to plug each leak. Prices and product facts
are current as of June 2026 — this field moves weekly, so treat the dated rows as
perishable and re-check before acting on the dollar figures.

> **The one-line finding:** we are running the most expensive model
> (**Opus 4.8, 1M context**) against the broadest possible prompts, with every
> repo's full `CLAUDE.md` re-loaded each turn and no prompt caching. The fix is
> not "use the AI less" — it's **right-size the model, cache the static context,
> and scope the ask.** Most of our daily work is doc/Markdown/JSON editing that a
> cheaper tier (or the local box we already own) handles at near-parity.

---

## A. Where the tokens actually go

In order of estimated spend, biggest first:

1. **Model over-spec.** Opus 4.8 is `$5 / $25` per million tokens (in/out);
   Fast Mode is `$10 / $50`. Sonnet 4.6 is `$3 / $15`. Haiku 4.5 is the cheap
   tier (≈`$1 / $5`). Editing READMEs, fixing links, updating `roster.json`,
   reordering lists to house style — none of that needs frontier reasoning.
   Running it on Opus is paying Opus rates for Haiku work. Industry rule of
   thumb: ~60–70% of requests are simple (extract/format/classify), ~20–30%
   moderate, only ~10% need a frontier model — yet teams pay frontier price for
   all of them.
2. **Re-loaded context every turn.** Every session loads the full `CLAUDE.md` of
   each in-scope repo plus the system reminder. Ours are long (the DESIGN
   `CLAUDE.md` alone is multiple KB, and several repos load at once). That's a
   fixed tax paid on *every* turn of *every* session, and right now we pay it at
   full input price because we don't cache (see C).
3. **Compaction churn.** A single Claude Code compaction can burn 100–200K
   tokens. On Opus with the 1M window, autocompact has historically misfired
   early (one report: firing at 76K, wasting ~92% of the window). June 2026
   builds improved reactive compaction and auto-shrink, but the lesson stands:
   long rambling sessions pay a compaction tax. Short, scoped sessions don't.
4. **Verbose tool output in the main context.** File dumps, `git` logs, search
   results all land in the main window and then get re-sent on the next turn.
   Subagents keep that clutter out (they return a summary, not the dump).
5. **The open-ended prompt.** "Find anything that could help" maximizes
   exploration and output length by design (see F).

---

## B. Model right-sizing — the biggest single lever

We already own the routing machinery (`localDNS/10-ai-orchestration` — LiteLLM in
front of local Ollama tiers, cloud as overflow). We just aren't pointing the
*day-to-day editing work* at the cheap tiers.

- **Default the routine doc work down a tier.** Use Claude Code's `/model` to run
  Sonnet 4.6 (or Haiku 4.5) for link-checks, list re-ordering, roster edits,
  changelog appends, doc-integrity passes. Reserve **Opus 4.8 for ADRs,
  architecture, and genuinely hard multi-file reasoning.** This alone is a
  plausible 40–70% cut on the editing half of our spend.
- **Fast Mode is a 2× tax — spend it deliberately.** `$10/$50` vs `$5/$25`. Worth
  it for interactive back-and-forth where latency hurts; wasteful for an
  unattended routine that nobody is watching in real time.
- **Concrete config nit (grounded in our files):** `config.yaml`'s
  `cloud-overflow` failover points at `anthropic/claude-opus-4-8` — the most
  expensive possible failover. For an *overflow/last-resort* tier, point it at
  `claude-haiku-4-5` (or `sonnet-4-6`). A failover should be cheap, not premium;
  the comment block right below it already lists the swap.

---

## C. Prompt caching — turn the static context from a tax into ~10%

This is the highest-ROI change we are *not* doing.

- Cached input reads cost **0.1× normal input** (a 90% discount). 5-minute cache
  writes cost 1.25×, 1-hour writes 2×. The economics win once a prefix is read
  ≥3× (5-min) / ≥5× (1-hour) within its TTL.
- Our `CLAUDE.md` + repo briefing is exactly the kind of large, stable prefix
  that should be cached. Across a working session (and across the daily review
  runs, which all re-load the same context), the static block is read many times.
- In Claude Code, enable longer cache via `ENABLE_PROMPT_CACHING_1H`. For
  API-side work (statement generation, batch doc checks) mark the system /
  briefing block as `cache_control`.
- Combined with batch (below), the published ceiling is ~95% off; "stack caching
  + routing + tight output budgets" lands typical production workloads at 20–30%
  of unoptimized cost.

---

## D. Batch API — for everything that isn't interactive

The **monthly statement build**, doc-integrity sweeps, bulk roster validation,
and these **daily review runs** are not interactive — nobody is waiting on the
keystroke. The Batch API is **50% off** across all models and composes with
caching. The statement generator already runs at "about a penny a home"; batch
roughly halves that, and routing the compose step to Haiku/Sonnet halves it
again.

---

## E. Context hygiene — cheap habits that compound

- **Trim `CLAUDE.md` to the hot path.** Every line in `CLAUDE.md` is re-read all
  the time. Keep the briefing tight; push rarely-needed detail into linked docs
  that get `Read` on demand. (We already link `README.md` / `network-context.md`
  / `workflow-context.md` — good. The deploy-path *tables* and exhaustive
  known-issue lists are candidates to move behind a link and pull in only when a
  task touches them.)
- **Subagents for fan-out.** Searches, "where is X across the repos", log triage
  → delegate to an `Explore`/general-purpose subagent so the dump stays out of
  the main window; only the conclusion comes back.
- **`/clear` between unrelated tasks; `/compact` before they pile up; `/recap`
  (Apr 2026) to resume without replaying the whole transcript.**
- **Ask for diff-only / no-preamble output.** A reusable house prompt that
  suppresses explanation and requests just the change is a steady per-turn saving.

---

## F. The prompt that launched this review — critique

The triggering prompt ("Locate inefficiencies… Anything you could possibly think
of… ANYTHING that could help… Search the web… Check the news. Thanks!") is warm
and clear about intent, but it is **token-expensive by construction**:

- **Unbounded scope** ("anything", "ANYTHING") invites maximal exploration and a
  long answer. Open-ended prompts are the single biggest driver of long,
  meandering, expensive sessions.
- **No output contract.** No length cap, no format, no "stop at the top 5." So the
  model errs toward exhaustive.
- **No model floor.** A broad research/synthesis task on Opus 4.8 1M is the
  costliest way to get a list of suggestions; Sonnet 4.6 would do this at 60% of
  the input price and a third of the output price.
- **Bundled jobs.** "Find inefficiencies" + "critique this prompt" + "search the
  web" + "check the news" are four tasks in one turn, which keeps a large context
  alive across all of them.

**A cheaper version of the same request:**

> "On Sonnet 4.6, give me the **top 5** token/cost inefficiencies in how we use
> Claude across the A777ance repos, each with a one-line fix and a rough
> $-impact. Use ≤3 web searches for 2026 pricing/best-practice facts. Output a
> table, ≤400 words. Then, in ≤5 bullets, critique this prompt."

That swaps unbounded → bounded, Opus → Sonnet, and "narrate everything" → a
fixed deliverable. Same value, a fraction of the tokens.

---

## G. The hybrid local+cloud angle — we are ahead, push further

We already run the architecture every 2026 guide recommends (LiteLLM gateway →
local Ollama default → cloud overflow, with a deterministic privacy gate). To get
more out of it:

- **Move routine NL→structured work to the local box.** Parsing call notes into
  roster fields, tagging leads, first-pass summaries — that's `local-fast` /
  `local-smart` on the t630, not Claude. Escalate to Claude only when local
  confidence is low. Published hybrid setups cut LLM spend 60–80% this way.
- **Close TD-14 first.** The privacy fallback gap (a `sensitive` task can fail
  over from `local-reason` to `cloud-overflow`) means "route it local to save
  money/keep it private" isn't yet guaranteed. The cost lever and the privacy
  guarantee are the same fix: a local-only fallback chain.
- **Don't pay for local idle.** `cloud-gpu-reason` (rented GPU) should be
  spin-up-on-demand, stop-when-done — already the documented intent; just make
  sure it's enforced operationally so we're not renting a GPU between sessions.

---

## H. This review process itself

There is a daily review cadence in `docs/ai-cto/reviews/` (one file per day). If
those runs are on Opus 4.8 1M with full multi-repo context and no caching, they
are the most expensive recurring line in the AI budget. Recommended:

1. Run the daily/scheduled reviews on **Sonnet 4.6** (escalate to Opus only when a
   review surfaces something that needs deep reasoning).
2. **Cache the repo briefing** so the 2nd…Nth review of the day reads it at 0.1×.
3. **Batch** the non-interactive ones (50% off).
4. **Scope each run** to a question with an output contract, per F.

Rough order-of-magnitude: routing + caching + batch on the recurring review/edit
workload is a credible **5–10× reduction** on that slice of spend, with no loss of
quality on the work that doesn't need a frontier model.

---

## Sources (June 2026 — perishable)

- Anthropic API pricing 2026 (models, caching, batch): finout.io/blog/anthropic-api-pricing
- Claude API pricing 2026 (Opus 4.8 / Sonnet 4.6 / Haiku 4.5): metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration
- Prompt caching cost guide: tokenmix.ai/blog/claude-api-cache-pricing ; aiforanything.io/blog/claude-api-prompt-caching-guide-2026
- Caching + batching → 60–95% reduction: dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production
- Hybrid local/cloud architecture + routing savings: sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026 ; buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- Claude Code token optimization / subagents / compaction: kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage ; smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026 ; buildtolaunch.substack.com/p/claude-code-token-optimization
- Claude Code June 2026 changelog (compaction, nested subagents): code.claude.com/docs/en/changelog ; releasebot.io/updates/anthropic/claude-code
