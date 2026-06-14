# Process Efficiency Review — the user↔AI loop, token cost, hybrid routing — 2026-06-14

Prepared by: NARF (AI CTO), on a scheduled routine
Install location: `DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/reviews/`

## Why this belongs here

The founder asked a cross-cutting question — *"find inefficiencies in our PROCESS between
the user and the AI; reduce token use; better prompting; hybrid local LLM + Claude; keep
up to date."* It spans the LiteLLM ladder (`localDNS/10-ai-orchestration`), the NARF/ZORT
review cadence, the CFO API budget, and how every session is prompted. So it lands in the
portfolio hub, not a spoke. Implementation lands in the affected repos.

---

## 0. HEADLINE — act before June 15 (tomorrow): Anthropic is moving agent/automation usage off the subscription

This is the single most important finding and it is **time-critical**.

**What changes (June 15, 2026):** Anthropic splits subscription billing. The
**Claude Agent SDK, `claude -p`, Claude Code GitHub Actions, and third-party apps that
authenticate with your Claude subscription** stop drawing on your normal subscription
limit and instead draw from a **separate monthly "Agent SDK credit," metered at full API
rates, with no rollover.** Interactive use (Claude Code in the terminal, chat) is
unaffected.

**This routine is exactly that kind of usage.** Scheduled routines / Claude Code on the
web / Actions run via the Agent SDK path, so as of tomorrow they bill against the Agent
SDK credit, not the flat subscription.

**The credit pools (reported):** Pro **$20/mo**, Max 5× **$100/mo**, Max 20× **$200/mo**.

**When the credit runs out:** automation **stops** unless you enable **overflow billing**,
at which point further usage bills at **standard API rates**.

**Why it matters for A777ance specifically:** ZORT's budget assumes ~$5–15/mo Anthropic
API against a **<$30/mo total burn** target (ADR / CFO portfolio). If NARF + ZORT reviews,
this efficiency routine, and any GitHub-Actions automations all run through the Agent SDK
path, they now compete for one metered credit pool. Two failure modes to avoid:
1. **Silent stop** — a daily review routine just stops mid-month when the pool empties, and
   nobody notices because it fails quietly.
2. **Silent overspend** — overflow billing is on, and a chatty open-ended routine (like the
   prompt that generated *this* review) quietly blows past the $5–15 line.

**Action items (do today/tomorrow):**
- [ ] Confirm which plan tier the A777ance account is on and what the Agent SDK credit is.
- [ ] Decide the **overflow-billing** posture deliberately: ON with a hard cap (don't let
      reviews die silently), or OFF (accept that automation pauses when the pool empties).
- [ ] Add a line to ZORT's budget/runway for the **Agent SDK credit** as its own item,
      separate from interactive API spend.
- [ ] Audit the routine cadence (below, §4) — the cheapest token is the call you don't make.
- [ ] Verify the related "Claude 4 retirement" rumor for June 15 against the official
      release notes; if older 4.x model ids are being pinned anywhere
      (`10-ai-orchestration/config.yaml` pins `claude-opus-4-8` / `claude-sonnet-4-6`),
      confirm they're still served.

Sources: [Tech Times](https://www.techtimes.com/articles/317625/20260602/anthropic-ends-subscription-subsidy-agents-june-15-credit-pool-replaces-flat-rate-access.htm),
[Codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/),
[Zed blog](https://zed.dev/blog/anthropic-subscription-changes),
[Releasebot — Anthropic June 2026](https://releasebot.io/updates/anthropic).

---

## 1. Token-reduction levers, ranked by leverage *for our usage*

| # | Lever | Savings | Fit for A777ance | Effort |
| - | ----- | ------- | ---------------- | ------ |
| 1 | **Prompt caching** | up to **90%** off the cached prefix | High — our CLAUDE.md files + schema are stable, large prefixes re-sent every call | Low |
| 2 | **Batch API** | flat **50%** off | High — Statement generation, NARF/ZORT nightly reviews, doc-integrity sweeps are not interactive | Low |
| 3 | **Model tiering** (Sonnet default, Opus only when needed) | Opus ≈ 5× Sonnet | Partly done (the ladder); enforce it at the *task* level too | Low |
| 4 | **Hybrid local↔cloud routing** | 60–80% on a mixed workload | Already built (LiteLLM ladder) — needs tuning + TD-14 fix | Med |
| 5 | **Trim CLAUDE.md / context** | per-call fixed cost | High — see §3, our CLAUDE.md files are large and load every session | Med |
| 6 | **Session hygiene** (`/compact`, scope, `.claudeignore`, subagents) | 40–70% on focused tasks | High — cheap habits | Low |

### 1.1 Prompt caching — the highest-leverage, lowest-effort win
Cache reads price at ~**10%** of base input; cache writes at 1.25× (5-min TTL) or 2× (1-hr
TTL). The catch is **exact-prefix matching**: any change to the cached block invalidates
everything downstream. Two rules we're currently at risk of breaking:
- **Never put dynamic content in a cached prefix.** A "current date is …" line in a system
  prompt invalidates the whole cache at midnight. Put volatile facts in the *user* message.
- **Pin JSON key ordering** in tool definitions, or serialization reshuffles defeat the cache.

For *interactive* Claude Code this is mostly automatic. For **our routines and the LiteLLM
path it is not** — a once-a-day routine that starts cold gets **zero** cache benefit (TTL is
5 min / 1 hr). That argues for batching same-context work into one run rather than many
cold starts (see §4).

### 1.2 Batch API — free 50% on everything we don't watch in real time
Anything asynchronous should go through Batches (results within 24h, 50% off, stackable
with caching). Direct candidates:
- **Statement generation** (Stage 06) — inherently a nightly/monthly job.
- **NARF + ZORT daily reviews** — they don't need to be synchronous.
- **`check-docs.py`-adjacent doc/QA passes** and any bulk content generation.

### 1.3 Model tiering — extend the ladder down to the task
The config already tiers (`local-fast/smart/reason` → `cloud-code` Sonnet → `cloud-explore`
Opus). The missing discipline is at the *prompt* level: default new work to Sonnet, escalate
to Opus only for genuinely hard reasoning. (This review didn't need Opus.)

---

## 2. Hybrid local + cloud — we're ahead here; tune what exists

We already run the recommended 2026 architecture (LiteLLM gateway + Ollama local +
Anthropic cloud tier + a privacy gate). Industry guidance says 60–70% of agent traffic is
simple (classify/extract/format) and belongs local; ~10% needs a frontier model. Our ladder
encodes this. Three concrete tunings:

- **Close TD-14 first (P1, privacy + cost).** `local-reason` lists `cloud-overflow` as a
  LiteLLM failover, but the dispatcher's `allow_cloud=False` isn't enforced *at the failover
  layer* — a sensitive local task can leak to Claude if the local model is down. Give
  sensitive tiers a **local-only fallback (fail closed)**. This is both a privacy fix and a
  cost fix (no surprise cloud calls).
- **Push more default traffic local.** Routine classification/extraction/formatting (CRM
  field tidy, lead triage, log summarizing) should hit `qwen2.5:3b/7b` on the t630 ($0),
  not Claude. Reserve cloud for explore/code/vision and the hard 10%.
- **Mind the GPU-rental tail.** `cloud-gpu-reason` (DeepSeek-R1 32B/70B on rented Vast.ai/
  RunPod) is on-demand; make sure pods actually stop. An idle-but-running pod is the classic
  hybrid cost leak — worse than just calling Claude.

---

## 3. Better prompting & context engineering

The 2026 consensus has shifted from *prompt* engineering to **context engineering**: treat
context as a *budget*, not a dumping ground; more tokens ≠ better reasoning. Practices that
apply to us:

- **Trim CLAUDE.md.** Best-practice target is lean (~500 tokens); our CLAUDE.md files are
  many thousands of tokens **and every session loads them**. They're excellent documents —
  but for *machine context* they're oversized. Split: keep a tight operational core in
  CLAUDE.md, move the prose rationale to linked files the agent reads *only when needed*.
  (This routine's context loaded **all seven** repos' CLAUDE.md before doing anything — a
  large fixed cost paid on every run regardless of task.)
- **Add `.claudeignore`** so sessions don't index `.env`, build output, `stats/`, vendored
  data, rendered statements, etc.
- **Separate instructions from data** with delimiters/XML-ish tags (we already do this in
  templates) — most prompt failures are ambiguity, not model limits.
- **Scope tightly.** "Refactor the login function in `auth.ts`" beats "refactor the auth
  module." Narrow scope = less context = fewer tokens = better output.
- **Define what the agent should *not* do** — our CLAUDE.md "don't build X yet" lists are
  good; keep them and reference them rather than re-pasting them.
- **Use subagents/`/compact`/`/recap`** for long work so old turns don't get re-read each
  step. Claude Code now supports nested subagents (up to 5 deep) — fan out read-heavy
  research to a cheap subagent that returns only the conclusion (this review used that
  pattern).

---

## 4. The cadence question — the cheapest token is the call you don't make

Given §0, *how often* automations run is now a direct line item. Recommendations:

- **Make open-ended research routines deltas, not full re-runs.** A routine that re-searches
  the whole web every day is the most expensive shape possible. Have it check *"what changed
  since last run"* against a stored watermark, and stay silent when nothing changed.
- **Batch the daily reviews.** If NARF + ZORT + doc-integrity all run daily, fold them into
  one batched job (shared cached context, 50% batch discount) instead of three cold starts.
- **Set a notify-only-on-signal rule** for routines so they don't spend tokens producing
  prose nobody reads when the answer is "all healthy."

---

## 5. Critique of the prompt that triggered this review

The founder explicitly asked for this. The prompt was effective at *getting breadth* but is
**inefficient by design** for a scheduled routine:

**What worked:** clear direction ("search the web," "check the news," "keep up to date"),
and it asked for self-critique. Good instincts.

**What costs tokens for little gain:**
- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of"
  invites maximal exploration — maximal tokens, diffuse output. It's the opposite of "scope
  tightly."
- **Kitchen-sink.** Four distinct asks (token reduction · prompting · hybrid LLM · news) in
  one prompt. Each is a cleaner, cacheable, repeatable job on its own.
- **Run as a recurring routine, it re-does full web research every time** — exactly the
  expensive shape §4 warns against.

**A tighter rewrite (drop-in):**
> *"Weekly: check for Anthropic/Claude pricing, model, or Claude-Code changes since
> {last_run_date} that affect our cost or our LiteLLM ladder. List only what changed and the
> one action each implies. If nothing material changed, reply 'no change' and send no
> notification. Cap: use Sonnet; no Opus."*

That version is bounded, dated (delta-based), model-capped, silent-when-empty, and single-
purpose — cheaper and more useful every run. Keep the broad open-ended version as an
occasional *one-off*, not a schedule.

---

## 6. Prioritized action list

1. **[today]** Decide overflow-billing posture + confirm Agent SDK credit tier (§0).
2. **[today]** Add "Agent SDK credit" as its own ZORT budget line; separate from API spend.
3. **[this week]** Turn on **prompt caching** for the LiteLLM/Agent paths; keep dynamic
   content out of cached prefixes; pin tool-def JSON ordering.
4. **[this week]** Move Statement generation + NARF/ZORT reviews to the **Batch API** (50%).
5. **[this week]** Fix **TD-14** (sensitive tiers fail closed to local) — privacy + cost.
6. **[ongoing]** Trim CLAUDE.md to a lean core + linked rationale; add `.claudeignore`.
7. **[ongoing]** Convert recurring research routines to **delta + silent-when-empty**;
   batch the daily reviews into one run.

---

## Sources

- [Tech Times — Anthropic ends subscription subsidy for agents June 15](https://www.techtimes.com/articles/317625/20260602/anthropic-ends-subscription-subsidy-agents-june-15-credit-pool-replaces-flat-rate-access.htm)
- [Codersera — June 2026 billing change: what every Claude Code & Agent SDK user must do](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [Zed blog — what Anthropic's new billing means](https://zed.dev/blog/anthropic-subscription-changes)
- [Releasebot — Anthropic updates June 2026](https://releasebot.io/updates/anthropic)
- [Finout — Anthropic API pricing 2026 (caching, batch, optimization)](https://www.finout.io/blog/anthropic-api-pricing)
- [PE Collective — Batch API (50% off) and prompt caching (90% off)](https://pecollective.com/tools/claude-pricing-guide/)
- [Elevated AI — Claude prompt caching best practices 2026](https://www.elevatedaico.com/blog/claude-prompt-caching-guide/)
- [Codewords — Anthropic batch API at 50% cost](https://www.codewords.ai/blog/anthropic-batch-api)
- [SitePoint — hybrid cloud-local LLM architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [BuildMVPFast — hybrid cloud-local AI workflow cost optimization 2026](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Analytics Vidhya — 23 tips for Claude Code token saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [KDnuggets — 7 practical ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Sombra — AI context engineering 2026: why prompt engineering is no longer enough](https://sombrainc.com/blog/ai-context-engineering-guide)
- [MindStudio — Code with Claude 2026: new agent features (nested subagents)](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
