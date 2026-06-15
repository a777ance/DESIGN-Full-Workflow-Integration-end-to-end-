# AI Process Efficiency — the user↔AI working loop

How we spend tokens and attention working *with* Claude across the A777ance repos, where
the waste is, and what to change. This is a meta-doc: it's about the process, not the
product. Time-sensitive findings lead (newest-first, per house style).

**Compiled:** 2026-06-15. Recompile when Anthropic ships pricing/feature changes — this
area moves week to week, so treat anything below older than ~30 days as suspect and
re-check against the live docs.

---

## 0. TL;DR — do these first

1. **TODAY (2026-06-15) the billing model changed.** Anthropic split *non-interactive*
   usage — Agent SDK, `claude -p` headless runs, the GitHub Actions integration, scheduled
   routines like this one, and any third-party app authenticating with your subscription —
   into a **separate monthly dollar credit pool**, sized to the plan fee. Interactive
   Claude Code (you at a terminal) draws from the normal pool. **Action:** watch the new
   Agent-SDK credit meter this month; our scheduled routines + the GitHub Actions path now
   compete for that budget, not the interactive one. Right-size routine frequency before
   the meter teaches us the hard way.
2. **Turn on prompt caching everywhere we control the system prompt.** Cache reads cost
   **0.1×** base input (≈$0.50/MTok Opus, $0.30 Sonnet); a 5-min cache write costs 1.25×,
   so it **pays for itself on the first hit.** Our big CLAUDE.md files are re-sent every
   session — they are the ideal cache target.
3. **Default to Sonnet; reserve Opus for genuinely hard reasoning.** Most repo work
   (doc edits, link-checking, roster changes, statement composition) is Sonnet-class. This
   alone is the single biggest lever.
4. **Use subagents for research/search, keep the main thread for the decision.** Fan-out
   reads burn the main context; a subagent returns the conclusion, not the file dumps.
5. **Close the local-router privacy gap (TD-14)** before leaning on the hybrid path for
   anything sensitive — a `sensitive` task can currently fail *open* to cloud.

---

## 1. Where the user↔AI loop wastes tokens (ranked)

| # | Inefficiency | Cost | Fix |
| - | ------------ | ---- | --- |
| 1 | **Wrong model for the job.** Opus on a doc edit is ~3–5× the price of Sonnet for no quality gain. | High, every session | Sonnet by default; `/model` up to Opus only for hard reasoning. |
| 2 | **CLAUDE.md weight.** Our five CLAUDE.md files are large and load *before the task* — every session pays for them up front. The DESIGN one alone is multiple KB. | High, every session | Keep CLAUDE.md to a tight briefing; push detail into linked files Claude reads *on demand*. Measure with `/context`. Lean on prompt caching so the cost is paid once, not per turn. |
| 3 | **Re-reading whole files to "verify" an edit.** The harness already confirms edits; re-reads just re-bill the file. | Medium | Trust the edit; don't re-Read to confirm. |
| 4 | **Broad reads/greps in the main thread.** A 500-line read or a wide grep dumps everything into context. | Medium | Targeted Read (offset/limit), `Grep` with globs, or delegate the sweep to a subagent. |
| 5 | **Multi-turn what-should-I-do loops.** Each clarifying round re-sends the whole context. | Medium | Front-load intent + output format in the first prompt (see §4). |
| 6 | **Letting context run past ~70%.** Quality degrades and every turn is more expensive as it fills. | Medium | `/compact` at natural breakpoints; split big work into context-sized chunks. |
| 7 | **Routines that run too often or do too much.** A scheduled run that finds nothing still costs a full context load — and now draws the new Agent-SDK credit. | Medium, recurring | Right-size cadence; have routines exit cheap when there's nothing to report (and stay silent — notify only on signal). |
| 8 | **One-prompt-per-step where one prompt would do.** "Audit, then write the report, then update the changelog" in one structured prompt beats three. | Low–medium | Batch related steps into a single instruction. |

---

## 2. Token-reduction playbook (Claude Code specifics)

- **`/context`** — the diagnostic. Shows token counts per element (CLAUDE.md, tools,
  history). Run it before changing workflow; you usually find one fat item.
- **`/compact`** at natural breakpoints, not at exhaustion. Summarizes history, frees room.
- **`/clear`** between unrelated tasks so old context doesn't ride along.
- **Subagents** (`Explore`, `general-purpose`, or nested) for research and wide searches —
  they burn a *separate* context and hand back the conclusion.
- **Prompt caching** for stable prefaces (CLAUDE.md, schemas, long specs). 90% off on the
  cached portion. Anthropic's biggest single cost lever right now.
- **Batch API** (50% off) for anything that doesn't need to be interactive — e.g. a monthly
  statement-render fan-out across households, or bulk doc checks. Worth wiring into Stage 06.
- **Model laddering:** Haiku for trivial/classify, Sonnet for daily work, Opus for hard
  reasoning. Mirror this on the box (see §3).

> **Caveat — caching can bite.** The March 2026 prompt-caching incident (two Anthropic bugs
> caused 10–20× silent token inflation) is a reminder: watch the usage meter after enabling
> caching, don't assume it's free money.

---

## 3. Hybrid local + cloud — we already have the skeleton

The t630 already runs the right architecture: **LiteLLM** as a unified gateway with a
reasoning ladder (`localDNS/10-ai-orchestration/config.yaml`) — `local-reason`
(deepseek-r1:1.5b on the t630 CPU) for light work, `cloud-gpu-reason` (full R1 on a rented
GPU) and `cloud-overflow` (Claude) for heavy work. This is exactly the pattern the 2026
guides recommend, and the published numbers are real: routing the routine 60–70% of traffic
to local models cuts spend **60–80%** with little quality loss.

**What to actually do with it:**

- **Route by task class, not by habit.** Classification, extraction, formatting, link-checks,
  first-draft prose → local. Reserve Claude for reasoning, final customer-facing copy, and
  anything where a wrong answer is expensive.
- **Use the box as a pre-filter for the routines.** A scheduled routine can do its cheap
  triage locally (did anything change? is there a signal?) and only escalate to Claude when
  there's something worth the spend. Directly lowers the new Agent-SDK credit draw.
- **Close TD-14 first (P1).** Today a `sensitive`-tagged task routed to `local-reason` can
  fail *over* to `cloud-overflow` (Claude cloud) if local is down — `allow_cloud=False`
  isn't enforced at the LiteLLM failover layer. Until that's a local-only, fail-*closed*
  chain, the hybrid path has no privacy guarantee. Fix before trusting it with private data.
- **Don't over-build.** Per our own philosophy (liquidity before app, keep the stack dull):
  the router is plumbing, not the product. Tune routing; don't gold-plate it.

---

## 4. Better prompting — patterns that cut round-trips

- **State the output shape up front.** "Reply as a 5-row table" or "commit + push, no PR"
  in the first message avoids a reformat round-trip.
- **Give the destination, not just the task.** "Write findings to `docs/ai-cto/X.md`,
  commit to branch Y" lets the AI finish in one pass.
- **Bound the scope.** "Two searches max, then write" prevents open-ended fan-out.
- **One structured prompt > a chain of small ones** when steps are dependent.
- **Say what *not* to do.** "Don't re-read to verify," "don't open a PR" save whole actions.
- **Lead with the ask; context after.** Long preambles before the actual request mean the
  model processes more before it knows what you want.

---

## 5. Critique of this routine's own prompt

The prompt that generated this doc ("Locate inefficiencies in our PROCESS… ANYTHING that
could help… Search the web… Check the news. Thanks!") is a good *brief* but an inefficient
*instruction*:

- **Too open-ended.** "ANYTHING that could help" invites unbounded fan-out — many searches,
  long output, high token cost. **Better:** "Find the top 5 token-saving changes for our
  Claude Code workflow; ≤4 web searches; write to `docs/ai-cto/ai-process-efficiency.md`."
- **No output target named.** Without "write it here," a scheduled run with no human reading
  risks producing a long reply nobody sees. Naming a file makes the work persist.
- **No budget/cadence.** "Keep UP TO DATE… day by day" implies a frequent rerun; a daily
  deep-research run on this is overkill (and now bills the Agent-SDK credit). **Better:**
  monthly, or triggered when Anthropic ships pricing news.
- **Mixed registers + filler.** "Thanks!" twice, "ANYTHING," emphatic caps — harmless but
  pure tokens. For a recurring machine prompt, terser is cheaper.
- **What it got right:** clear domain, explicitly asked for currency + web search, and asked
  for self-critique — all good. The fix is *bounding* it, not rewriting it.

**Tightened version (drop-in):**
> "Monthly: review our Claude Code / AI working process for token waste. Do ≤4 web searches
> for current best practices and any Anthropic pricing/feature news. Update
> `docs/ai-cto/ai-process-efficiency.md` (newest-first), commit + push to the dev branch.
> Notify only if something time-sensitive or costly changed. No PR."

---

## 6. Sources

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Context Window: Optimize Token Usage — claudefa.st](https://claudefa.st/blog/guide/mechanics/context-management)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude Credit Overhaul 2026: What Changes on June 15 — Digital Applied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic Release Notes — June 2026 — Releasebot](https://releasebot.io/updates/anthropic)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM Request Routing: GPT-4 vs Claude vs Local — BuildMVPFast](https://www.buildmvpfast.com/blog/llm-request-routing-gpt4-claude-local-models-2026)
