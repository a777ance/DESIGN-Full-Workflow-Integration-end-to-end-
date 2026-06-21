# Process efficiency review — user↔AI workflow & token spend — 2026-06-21

Requested: find inefficiencies in *the process* (between the founder and the AI),
reduce token use, improve prompting, leverage other AI (incl. a local-LLM + Claude
hybrid), and keep current with fast-moving best practice. This is a one-off audit,
not a recurring routine. Web sources checked 2026-06-21 are listed at the bottom.

---

## Headline

**The biggest token waste isn't in any single prompt — it's structural, and you can
fix most of it without spending a dollar:** (1) ~11k tokens of `CLAUDE.md` are
re-ingested on *every* session across the portfolio; (2) the daily NARF/ZORT review
routine re-derives the same conclusions every day because nothing ships between runs
— the 2026-06-20 review literally says "fourth review cycle with zero real Statements";
and (3) you're running these scheduled, mostly-mechanical routines on **Opus 4.8 with
the 1M-context variant** — the most expensive configuration Anthropic sells — when
the work (status sweeps, doc-link checks, monitoring) is Haiku/Sonnet-grade. You
already own the fix for the hybrid piece: the LiteLLM router + reasoning ladder on the
t630 is built but under-used for *your own* tooling.

Rough order-of-magnitude: a daily review on Opus-1M re-reading the hubs and all
CLAUDE.md files is likely **$1–3/run**; the same run, slimmed + on Sonnet/Haiku +
warm cache, is **cents**. Across ~daily cadence × 7 repos that compounds.

---

## 1. Your prompt (the one that launched this) — critique

You asked me to grade it, so: it's a good *brainstorming* prompt and a poor
*routine* prompt. Specifically —

- **Open-ended by design** ("ANYTHING that could help", "Anything you could possibly
  think of"). That invites maximal fan-out every single run. Fine once; expensive on
  a schedule, because each run re-does the whole web sweep from scratch.
- **Bundles ~6 distinct questions** (token use, prompting, other AI, hybrid local,
  news, self-critique). Each is independently answerable; bundled, they force one
  giant context instead of cheap, cacheable, parallel pieces.
- **No output contract.** No "write to file X", "≤N words", "diff against last run".
  So the model guesses the deliverable — and a scheduled run with nobody watching can
  guess "write a lot into a transcript no one reads."
- **"Keep UP TO DATE… day by day"** implies a *recurring* watch, but the body reads
  like a *one-time* deep-dive. Those want different shapes (see §6).

**Rewrite, if you want this as a standing watch** (scoped, cheap, diff-based):

> Once a week, check for material changes since the last run in: Anthropic model
> lineup & API pricing, Claude Code token/cost features, and local-LLM-for-coding
> tooling. Output ONLY what changed vs. `docs/ai-cto/ai-cost-watch.md`, append a dated
> bullet to that file, and notify me only if a change would alter our model routing or
> cut cost >10%. ≤200 words. Use Haiku.

That version caches the standing instructions, does a small delta each run, stays
silent when nothing changed (the routine's whole point), and runs on a cheap model.

---

## 2. Inefficiencies observed in *your actual* setup

**a. CLAUDE.md re-ingestion (~11k tokens/session, every session).**
Word counts: DESIGN 2,608 · localDNS 2,728 · MARKETING 1,445 · customers 562 ·
homelab 371 · Azure-lab 316. The DESIGN and localDNS files are excellent *reference*
but most of it isn't needed on most runs. Best practice (Anthropic's own context-
engineering guidance): keep `CLAUDE.md` lean, push detail to README/linked docs that
load *just-in-time* via grep/glob. **Action:** cut each `CLAUDE.md` to the ~20% that's
load-bearing every session (the rules, the map, the "read these at start" list); move
the rest behind links. The house-style block is ~250 words duplicated in all 6 files —
factor it to one `docs/house-style.md` and link it.

**b. The daily review re-derives the same answer.**
The review log shows the same top-3 (close TD-14, book one t630 session, decide dues)
repeating across cycles because the blockers are human/access decisions, not work the
AI can do. Paying Opus-1M daily to re-discover an unchanged blocker is the single most
repetitive spend. **Action:** make the review *event-driven or delta-only* — run on a
new commit / a changed `portfolio.md`, or have it emit "no change since YYYY-MM-DD"
and stop, instead of regenerating a full essay. A blocker that's 4 cycles old needs a
calendar nudge, not a fresh 6k-token analysis.

**c. Model over-provisioning for mechanical routines.**
`tools/check-docs.py`, status sweeps, monitoring, roster lint, link-checks — none need
Opus, let alone the 1M variant (which carries a long-context price premium on top of
Opus's $5/$25 per-M). Reserve Opus for genuine reasoning (architecture, pricing
strategy, the NARF "two poles"); run the rest on Sonnet 4.6 ($3/$15) or Haiku 4.5
($1/$5). Industry data: ~60–70% of agent requests are mechanical and frontier-priced
needlessly.

**d. No `.claudeignore` discipline.**
Rendered statement HTML, node_modules-equivalents, generated stats, and large data
files can get pulled into tool searches. A `.claudeignore` per repo (works like
`.gitignore`) keeps them out of context.

---

## 3. Token-reduction levers (ranked by effort:payoff)

1. **Let the cache work — keep static content stable.** Claude Code auto-caches the
   system prompt + tool defs + `CLAUDE.md` prefix; cache reads cost ~10% of input.
   The win is automatic *only if you don't churn the prefix*. So: slim `CLAUDE.md`
   once, then leave it alone; put volatile notes in files read later, not in the
   always-loaded header. Frequent scheduled runs benefit most from a warm cache.
2. **Batch API (50% off) for the monthly statement job.** Statement generation is the
   textbook batch workload — bulk, asynchronous, no real-time need. At "a penny a
   home" today, batch halves it, and most of it could run on a local model (§4) for
   ~free. Combine batch + caching + routing → published numbers cite 80–95% cuts.
3. **Subagents / the `Explore` agent for fan-out reads.** Cross-repo sweeps and "read
   15 files to answer one question" should go to a subagent: it reads in its own
   context and returns a ~500-token summary instead of dumping 150k tokens into the
   main thread. (This review used parallel web search + a single targeted file read
   for exactly that reason.)
4. **Delta/event-driven scheduling** over fixed daily cadence (see §2b).
5. **`/compact` + keep context <40%.** Context "rot" sets in around 300–400k on the 1M
   model; power users hold <30%. Long routines should compact, not accrete.

---

## 4. Hybrid local-LLM + Claude — you already built the hard part

`localDNS/10-ai-orchestration` is a LiteLLM gateway with a reasoning ladder
(`local-reason` on the t630 CPU, `cloud-gpu-reason` on a rented GPU, `cloud-overflow`
to Opus). The pattern the whole industry is converging on — local for the cheap 60–70%,
cloud for the hard 10% — is **already standing in your stack.** Two moves:

- **Point more of *your own* tooling at it.** Doc-link checks, roster lint, draft "Handled
  For You" copy, classification/extraction over the master list, first-pass summaries —
  route to a local model (Ollama/llama.cpp class) via the gateway; escalate to Claude
  only when it fails or the task is genuinely hard. Published savings: 60–80%.
- **⚠️ Fix the privacy fallback first (TD-14, already on your tech-debt list).** The
  current `local-reason: ["cloud-gpu-reason","cloud-overflow"]` chain means a
  *sensitive* task silently fails *open* to Claude cloud when the local box stutters.
  Before you route customer data locally "for privacy," that chain must fail **closed**
  (`["local-smart","local-fast"]`). It's ~3 lines and needs no box access — do it
  before expanding local routing, or the privacy claim is false.

One caution from the benchmarks: local models on a CPU-only t630 are fine for
classification/extraction/short drafts but weak for agentic *coding*. Keep code-gen on
Claude; push the bulk text/data chores local.

## 5. Better prompting (cuts the back-and-forth that quietly burns tokens)

- **State the output contract up front:** file to write, length cap, format (JSON
  schema when downstream code consumes it), and "notify only if X." Ambiguity is the
  #1 cause of re-runs.
- **Separate instructions from data** with headings/XML tags so the model never
  re-reads the brief looking for the payload.
- **One job per prompt.** Split the 6-in-1 into scoped routines that each cache and
  run independently (and in parallel) rather than one monolith.
- **For routines specifically: define the "nothing happened" path.** Tell it to go
  silent on no-change. Half of a watch's value is *not* pinging you.

## 6. Keeping current (the part that "changes day by day") — June 2026 snapshot

What actually moved recently and touches you:

- **Models/pricing now:** Opus 4.8 $5/$25 per-M (flagship, 2026-05-28) · Sonnet 4.6
  $3/$15 · Haiku 4.5 $1/$5 · **Fable 5** the new premium tier at $10/$50 (≈2× Opus) —
  on subscription plans Fable 5 is included only through **2026-06-22**, then moves to
  usage credits. Don't default routines to Fable 5 or Opus-1M.
- **Billing churn:** the **June 15 2026 Claude Code / Agent SDK credit change was
  announced, then paused** — Anthropic says it'll give notice before anything takes
  effect. Worth a standing watch (this is exactly the delta-watch in §1) because it
  directly hits the cost of running these scheduled agents.
- **Caching caveat:** there was a **March 2026 prompt-caching incident** (two bugs →
  10–20× token inflation, silently). Caching is still the right call, but keep an eye
  on token dashboards after Anthropic-side changes.
- **Don't over-engineer the rules files.** Anthropic's current guidance: build context
  files *gradually*; what was needed 6 months ago often isn't now. Models got better;
  trim accordingly.

**The right shape for "keep up to date":** not a daily web sweep (expensive, mostly
no-change), but a **weekly delta-watch on Haiku** appending to a single
`docs/ai-cto/ai-cost-watch.md`, notifying only on a routing- or cost-material change.

---

## Do-this-week list (ranked)

1. **Fail TD-14 closed** (~3 lines, no box access) — prerequisite to any local routing
   of customer data. *Highest value, lowest effort.*
2. **Downgrade scheduled/mechanical routines off Opus-1M** to Sonnet/Haiku; reserve
   Opus for reasoning. Biggest recurring-cost cut, ~zero risk.
3. **Make the daily review delta-only / event-driven** (emit "no change since…" and
   stop). Kills the largest repetitive spend.
4. **Slim the 6 `CLAUDE.md` files** to load-bearing essentials; factor the shared
   house-style block to one linked doc. Cuts the ~11k/session fixed cost and warms the
   cache.
5. **Route bulk text/data chores (and the monthly statement job) to the local LiteLLM
   ladder + Batch API.** Reserve Claude for hard reasoning and code.
6. **Convert the open-ended "keep current" ask into a weekly Haiku delta-watch** writing
   to `ai-cost-watch.md`, silent on no-change.
7. **Add `.claudeignore`** to each repo (generated HTML, stats, data dumps).

---

## Sources (checked 2026-06-21)

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Code Docs — Prompt caching](https://code.claude.com/docs/en/prompt-caching) · [Manage costs](https://code.claude.com/docs/en/costs) · [Best practices](https://code.claude.com/docs/en/best-practices)
- [Claude API Docs — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude API Cost Optimization: Caching, Batching, 60% reduction (DEV)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Hybrid Cloud-Local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [Run local AI with Claude Code (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) · [Local LLM vs Claude coding benchmark](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [Anthropic June 15 2026 billing change](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/) · [Credit overhaul paused](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Every Claude model: Claude 3 → Fable 5](https://claudefa.st/blog/models) · [Anthropic API pricing 2026 (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Reduce Claude Code token usage: 8 methods](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage) · [Cut costs 60% — four habits (systemprompt.io)](https://systemprompt.io/guides/claude-code-cost-optimisation)
