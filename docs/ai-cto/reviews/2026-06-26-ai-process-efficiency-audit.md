# AI Process Efficiency Audit — human↔AI workflow & token spend

**Date:** 2026-06-26 · **Author:** NARF (scheduled routine) · **Scope:** how we *use* AI across the
portfolio — token cost, prompting, hybrid local/cloud, and whether more/cheaper AI is even the lever.

> **Shelf life: short.** Model IDs, prices, and Claude Code internals below were current on
> 2026-06-26 and move week to week. Re-verify the pricing/feature numbers against the linked
> sources before acting on any one figure. Treat the *structural* recommendations (§1, §2, §6) as
> the durable part; treat the numbers as a snapshot.

---

## 0. The headline (read this even if you read nothing else)

**Our biggest process inefficiency is not the price of tokens — it's spending AI cycles on work
that is blocked on a human.** Our own portfolio says so: as of the 2026-06-17 review, *nothing
material had shipped since 2026-06-07* across three+ review cycles, and the stated root cause was
**t630-access cadence + pending human decisions, not backlog.** A daily AI review that re-derives
"still blocked on the same lawyer/SSH session" is the most expensive token we spend, because it
*feels* like progress while producing none.

So the first optimization is a **trigger, not a model swap:** don't run a review/analysis pass
unless an *input changed* (a decision landed, the box got touched, a customer paid). Everything in
§2 below cuts the cost of each AI turn by 30–90%; this §0 point cuts the *number* of turns, which
is the bigger number. Cheaper loops on blocked work is still waste — just cheaper waste.

---

## 1. Where the tokens actually go in our process (ranked)

1. **Repeated session bootstrap.** Every Claude Code session re-ingests a large `CLAUDE.md` (the
   localDNS one is very long), *plus* the session-start protocol that reads `portfolio.md` +
   `roadmap.md` + `tech-debt.md` + `decisions.md` + the repo's spoke `context.md`. That's tens of
   thousands of tokens before a single line of work — paid on every fresh session, every repo.
2. **Duplicated boilerplate across repos.** The "House style: ordering & typography" block is
   copy-pasted verbatim into all 7 `CLAUDE.md` files. Useful, but it's the same ~400 words re-read
   every session and maintained in 7 places.
3. **Open-ended analysis turns** like the one that spawned this very document — broad
   ("ANYTHING that could help"), web-search-heavy, no budget. High value once; expensive if recurring.
4. **The actual build/edit work** — the cheapest category relative to the above, because it's
   bounded by a concrete diff.

The pattern: our token spend is dominated by **context we re-load** and **reviews we re-run**, not
by the work itself.

---

## 2. Token levers, ranked by ROI for *our* setup

| # | Lever | Effort | Expected saving | Notes for us |
|---|-------|--------|-----------------|--------------|
| 1 | **Gate reviews on a changed input** (§0) | trivial | Removes whole sessions | The single biggest win. Tie this routine + NARF/ZORT reviews to "did anything change?" |
| 2 | **Trim & dedupe `CLAUDE.md`** | low | 20–40% of every session's prefix | Factor the shared house-style block into one short canonical note and *link* it; keep each `CLAUDE.md` to the repo-specific essentials. Smaller prefix = cheaper every session, cached or not. |
| 3 | **Lean on prompt caching deliberately** | low | 60–90% on input tokens | Claude Code already caches the static prefix (system + `CLAUDE.md`). Keep static content first and *stop putting volatile things early* — e.g. a "Last updated: <date+detail>" line at the **top** of `portfolio.md` busts the cache on every edit. Move timestamps to the bottom or truncate to the day. ([caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)) |
| 4 | **Subagents for fan-out, each with its own context** | low | Keeps main context small | Delegate research/search/review to subagents (default them to **Haiku** for mechanical work); only the conclusion returns to the main thread, so the big file dumps never enter the expensive context. ([Composio](https://composio.dev/content/ways-to-cut-token-consumption-in-claude-code)) |
| 5 | **`/clear` between unrelated tasks; `/compact` mid-task** | trivial | Avoids carrying dead context | Switching repos/topics? `/clear` with a one-line handoff beats letting failed attempts pile up. Autocompact buffer is ~33K tokens as of early 2026. ([genaiskills](https://genaiskills.io/articles/claude-code-token-optimisation), [claudefa.st](https://claudefa.st/blog/guide/mechanics/context-buffer-management)) |
| 6 | **Batch API for any offline bulk job** | low | **50% off** input+output, stacks with caching | Anything not interactive — generating N statements, bulk doc rewrites, the monthly statement run if/when it scales — should go through Message Batches (unconditional 50%, ~24h SLA). Stacks with caching toward ~1/10 of list price. ([batch blog](https://claude.com/blog/message-batches-api), [pricing](https://platform.claude.com/docs/en/about-claude/pricing)) |
| 7 | **Right-size the model per task** | low | 40–85% blended | Opus for hard reasoning/architecture; **Sonnet** for code/diffs (the sweet spot); **Haiku** for mechanical/classification/extraction. Don't run Opus on a rename. |
| 8 | **Terser-by-default output** | trivial | Cuts output tokens (the pricey side) | Output is 5× input price. A short "be concise, no preamble" standing instruction on heavy workflows measurably trims spend. ([token-efficient CLAUDE.md](https://github.com/drona23/claude-token-efficient)) |

**Combined, realistic:** published production write-ups land **60–90% input-cost reduction** from
caching alone, and **45–85% blended** from model right-sizing/routing — but only on the turns you
actually run. (§0 is what bounds how many turns there are.)

---

## 3. Hybrid local + cloud — you've already built the right thing

The industry's 2026 "discovery" is exactly your existing design: a proxy in front of all LLM calls
that routes simple work to a local model and escalates hard work to a frontier API. Reported
savings are **60–80%** (one fintech case: $47K→$8K/mo), and the tool-of-choice everyone names is
**LiteLLM** — which you already run at `ai.home.lan:4040`, with local Ollama tiers, a rented-GPU
reasoning tier, and `cloud-overflow`. You also did the harder-to-find-right things: **route, don't
shard**, and a **deterministic dispatcher** (no LLM in the routing decision). That is ahead of most
write-ups. ([Oflight](https://www.oflight.co.jp/en/columns/hybrid-ai-cloud-local-llm-cost-reduction-2026),
[SitePoint architecture](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/))

So the recommendation here is **not "build hybrid"** — it's:

- **Deploy it.** Per the portfolio, the router/dispatcher is *reference code + config, not yet
  deployed*. The savings are zero until it's the actual front door for routine internal AI work
  (drafting, classification, summarizing the CRM, first-pass statement copy).
- **Fix TD-14 first — it's a correctness bug, not an optimization.** `local-reason`'s fallback
  chain (`["cloud-gpu-reason","cloud-overflow"]`) lets a *sensitive* task fail **open** to Claude
  cloud when the local model is down, while three comments claim the opposite. That's a privacy
  promise the config doesn't keep. 3-line fix (chain sensitive tiers to local-only). This is
  already flagged P1 in the portfolio — it gates trusting the hybrid path at all.
- **Mind the break-even.** 2026 TCO analyses put local-vs-cloud break-even around ~500K tokens/day
  for a 7B model. Below that, cloud is cheaper *per token* — so the local tier earns its keep on
  **privacy and flat cost**, not raw price, at our current volume. Don't justify the t630 tier on
  token economics; justify it on "personal lookups never leave the house."
  ([TCO](https://www.sitepoint.com/local-llms-vs-cloud-api-cost-analysis-2026/),
  [VDF](https://vdf.ai/resources/on-premise-llm-cost-comparison-2026/))
- **Routing maturity (later, optional).** When traffic justifies it, the research direction is
  cost-quality routing / model cascades (cheap-first, escalate-on-failure): ~85% of queries to the
  cheap tier while keeping ~95% of frontier quality. Your deterministic rule-table is the right v1;
  a semantic classifier (e.g. vLLM Semantic Router / ModernBERT) is the v2 *if* volume ever
  warrants it — not now. ([routing guide](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide),
  [vLLM router](https://github.com/vllm-project/semantic-router))

---

## 4. Better prompting — concrete swaps

- **Give every recurring AI job a budget and a stop condition.** "Audit X, max 4 web searches,
  one-page output" beats "look at everything." Open-ended scope is the prompt-level version of the
  §0 problem.
- **Put the ask first, context second, in a fixed structure.** Stable prefix → better cache hits
  and less re-explaining.
- **Ask for the artifact you'll actually use**, in the format you'll use it (a 5-row table, a diff,
  a checklist) — not "tell me about." Shorter output, less back-and-forth.
- **Standing "concise" instruction** on heavy/automated workflows; reserve verbose explanation for
  when you ask for it.
- **For routine/automated runs, prefer structured output** (a schema) over prose the next step has
  to re-parse.

---

## 5. Critique of the prompt that triggered this run

The triggering prompt was, roughly: *"Locate inefficiencies in our process… reduce token use…
better prompting… leverage other AI… hybrid local/cloud… ANYTHING that could help… search the web…
keep up to date… check the news."*

**What worked:** clear intent, explicitly invited web research and self-critique, and named the
real domains (token cost, prompting, hybrid). Good seed for a one-time deep pass.

**Where it's inefficient:**
- **Unbounded scope** ("ANYTHING… anything that could help") maximizes tokens and risks an
  unfocused dump. For a *recurring* routine this is the costliest shape.
- **No budget / no output spec** — nothing caps searches or sets the deliverable's form.
- **"Check the news" with no source set or threshold** invites broad, low-signal searching.
- **Two questions in one** (audit the process *and* critique the prompt) is fine here, but in
  general one ask per run caches and reviews better.

**Tighter rewrite for the recurring version:**
> "Once a week, in ≤6 web searches, list any *new* (past 7 days) development that would cut our
> Claude/LLM token cost or improve our hybrid-router setup. Output: a ≤10-line bullet list, newest
> first, each with a source link and a one-line 'why it matters to us.' If nothing new and
> material, send nothing. Skip anything we've already adopted (caching, batch, LiteLLM hybrid,
> deterministic routing)."

That version is cheap, dedups against what we already do, and respects §0 (silent when nothing changed).

---

## 6. Recommended cadence for *this* routine

- **Don't run the deep version on a schedule.** This audit is a one-time/quarterly artifact, not a
  daily one — the field moves, but not daily-meaningfully for a 7-repo solo shop.
- **If kept recurring, use the tight rewrite in §5** and have it **stay silent unless something new
  and adopted-worthy appears.** A weekly "all quiet" is a notification we shouldn't send.
- **Wire the savings, don't just list them.** The two highest-ROI items (gate reviews on changed
  input; deploy the already-built hybrid router + fix TD-14) are *actions*, and both are already in
  the portfolio. The cheapest next token is the one we don't spend re-discovering them.

---

## Sources (verify before acting — figures are a 2026-06-26 snapshot)

- Prompt caching — [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Batch API (50%, stacks with caching) — [claude.com/blog](https://claude.com/blog/message-batches-api) ·
  [pricing](https://platform.claude.com/docs/en/about-claude/pricing) ·
  [batch in practice](https://claudeapi.com/en/blog/dev-guides/claude-batch-api-cost-optimization/)
- Claude Code token reduction — [Composio](https://composio.dev/content/ways-to-cut-token-consumption-in-claude-code) ·
  [genaiskills](https://genaiskills.io/articles/claude-code-token-optimisation) ·
  [claudefa.st context buffer](https://claudefa.st/blog/guide/mechanics/context-buffer-management)
- Hybrid local+cloud — [Oflight](https://www.oflight.co.jp/en/columns/hybrid-ai-cloud-local-llm-cost-reduction-2026) ·
  [SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
  [local-vs-cloud TCO](https://www.sitepoint.com/local-llms-vs-cloud-api-cost-analysis-2026/)
- Routing / cascades — [DigitalApplied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide) ·
  [vLLM Semantic Router](https://github.com/vllm-project/semantic-router)
