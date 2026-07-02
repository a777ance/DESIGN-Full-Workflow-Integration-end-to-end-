# AI Process Efficiency — reducing token spend between the user and the AI

**As of 2026-07-02.** A living review of where we spend tokens (and money) talking to the AI, and
the concrete levers to spend less without losing quality. This is time-based, so it reads
newest-first per house style; when it's revisited, add a dated block at the top rather than
rewriting below.

This was produced by a scheduled routine on request ("find inefficiencies in our PROCESS between
the user and the AI"). It's grounded in our *actual* stack — the LiteLLM/Odin router in
`localDNS/10-ai-orchestration/` and how Claude Code is run across the seven repos — not generic
advice. Cross-refs: tech-debt `TD-14` (privacy fallback), `ADR-007` (pricing), and
`localDNS` CLAUDE.md §C.

---

## The one-paragraph answer

Yes, there's a lot of slack, and almost all of it is in three places: **(1)** we send the same
large stable context to the cloud on every call without caching it — prompt caching alone would
cut repeated-context cloud cost by up to ~90%; **(2)** we run *routine, non-interactive* work
(daily doc reviews, statement builds) on the most expensive model, when Sonnet 5 or Haiku 4.5
would do the same job at 1/5 to 1/25 the price, and the Batch API would halve it again; and
**(3)** our context payload is bloated — every Claude Code session loads all seven `CLAUDE.md`
files and this routine loaded an entire reference skill it barely needed. The router itself is
well-designed (deterministic keyword routing, local-first, cloud fallback) — the waste is in
*what we send* and *which model we send routine work to*, not in the routing logic.

---

## A. The biggest levers, ranked by payoff

| # | Lever | Where | Rough saving | Effort |
| - | ----- | ----- | ------------ | ------ |
| 1 | **Prompt caching on the cloud path** | LiteLLM router + Claude Code | up to ~90% on repeated context | low |
| 2 | **Right-size the model for routine work** | daily routines, statement builds | 5×–25× on those jobs | low |
| 3 | **Batch API for nightly / non-urgent jobs** | statement runs, daily reviews | additional 50% | low |
| 4 | **Trim the context we send every call** | `CLAUDE.md` files, skill loading | 10–40% of *every* session | medium |
| 5 | **Accurate token metering** | `hoard.py` budget cap | correctness, not savings | low |
| 6 | **Scope prompts + use routines/skills** | how we ask | 20–40% on focused tasks | ongoing |

---

## B. Prompt caching — the single highest-payoff change (lever 1)

**What's true today:** the LiteLLM path (`config.yaml`) does retries and failover but sets **no
`cache_control`** anywhere. `hoard.py` estimates cost but there's no cache. So every cloud call —
`cloud-code`, `cloud-explore`, `cloud-overflow` — re-pays full input price for context it has
already seen this hour (system prompt, house-style rules, the household data file, the statement
template).

**The mechanics** (Anthropic prompt caching, current): caching is a *prefix match*. Cache **reads
cost ~0.1×** the base input price; cache **writes cost 1.25×** (5-minute TTL) or **2×** (1-hour
TTL). Break-even is two requests for the 5-minute TTL. On a large stable prefix reused across many
calls, the cached portion drops to roughly a tenth of its cost.

**What to do:**
- Put `cache_control: {type: "ephemeral"}` on the last stable block of the system/prompt prefix in
  the router's Anthropic calls. Order matters: stable content (house-style rules, statement
  template, schema) first, volatile content (the specific home's numbers, the question) after the
  breakpoint. Any byte change *before* the breakpoint invalidates the whole cache.
- Verify it's working: `usage.cache_read_input_tokens > 0` on the second identical-prefix call. If
  it's zero, a silent invalidator is in the prefix (a timestamp, an unsorted JSON dump, a per-call
  ID).
- **Claude Code already caches** its system prompt + `CLAUDE.md` automatically — so the caching win
  is specifically for our *own* router traffic and any batch statement pipeline, not for
  interactive Claude Code sessions.

---

## C. Right-size the model (lever 2) — we're running routine work on the flagship

**What's true today:** `config.yaml` points `cloud-code` at `claude-sonnet-4-6` and the
`cloud-explore/vision/overflow` tiers at `claude-opus-4-8`. Meanwhile our **daily AI-CTO review
runs as a scheduled routine on Opus 4.8** — a job that is mostly doc-integrity checking and status
summarization, i.e. exactly the kind of mechanical work that does *not* need the flagship.

**Current pricing (per million tokens, cached 2026-06-24):**

| Model | Input | Output | Good for |
| ----- | ----- | ------ | -------- |
| Opus 4.8 (`claude-opus-4-8`) | $5.00 | $25.00 | architecture, hard reasoning, final synthesis |
| Sonnet 5 (`claude-sonnet-5`) | $3.00 (**$2.00 intro → 2026-08-31**) | $15.00 ($10 intro) | standard coding, near-Opus on agentic work |
| Haiku 4.5 (`claude-haiku-4-5`) | $1.00 | $5.00 | classification, extraction, mechanical review |

**What to do:**
- **Move the daily doc-review / status routines off Opus onto Sonnet 5 (or Haiku 4.5).** A
  doc-integrity + "what changed" summary is a Sonnet/Haiku job. This is a 5×–25× cut on a job we
  run *every day*. Reserve Opus for the weekly architecture/synthesis pass, not the daily churn.
- **Upgrade `cloud-code` from Sonnet 4.6 → Sonnet 5.** It's better on coding/agentic work *and*
  cheaper right now under intro pricing ($2/$10 through 2026-08-31). Same request shape; it's
  essentially a model-ID swap (note Sonnet 5 runs adaptive thinking by default — set
  `thinking: {type: "disabled"}` on the router's simple calls if you want the old thinking-off
  behavior, and re-check `max_tokens` headroom).
- Keep Opus only where it earns it: `cloud-explore` (deep research) and final-synthesis steps.

Industry baseline for why local-first + tiering works: ~60–70% of production requests are simple
(classification/extraction/formatting), ~20–30% moderate, ~10% truly need a frontier model. Our
router already exploits this with local tiers — the gap is that our *own routines* skip the tiering
and default to Opus.

---

## D. Batch API for anything not interactive (lever 3)

The **Message Batches API runs at 50% of standard price** and returns within an hour (max 24h). Our
nightly statement builds and the daily review are not latency-sensitive — a human isn't waiting.
Route them through Batches and stack the discount on top of the model-tiering and caching wins.
Caching + Sonnet-tiering + Batch compound: a daily review that costs $X on Opus interactive can
land near $X/20 on Sonnet-Batch-cached.

---

## E. Trim the context we send on every call (lever 4)

Two concrete, observed sources of bloat:

1. **`CLAUDE.md` payload.** Every Claude Code session loads the working directory's `CLAUDE.md`,
   and because our sessions span all seven repos, *all seven* briefings get injected — and
   `CLAUDE.md` is never lazy-loaded or evicted, so it sits in context the whole session. Several of
   ours are long (the `localDNS` and DESIGN briefings especially, with full deploy-path tables and
   known-issues lists). Keep `CLAUDE.md` to the *stable, always-needed* rules (how to build, house
   style, hard constraints) and push the reference tables (full deploy-path map, the long
   known-issues log) into linked docs that are read on demand. This trims a fixed cost off *every*
   session.

2. **Over-loading reference material.** This very routine loaded an entire ~40k-token Claude API
   reference skill when it needed only the pricing and caching sections. Lesson for our own
   automations and prompts: pull the *specific* fact, don't load the whole manual. When we build
   routines, scope their context loading.

---

## F. Fix the token meter and the privacy fallback (lever 5 + a real bug)

- **`hoard.py` estimates tokens as `chars ÷ 4` and assumes a flat 600 output tokens.** That's rough
  and model-dependent — it under/over-counts, so the USD budget cap (`LLM_ROUTER_BUDGET_USD`) is
  approximate. Use the `count_tokens` endpoint for pre-flight estimates, and read the real
  `usage` block back from each response to true up spend. Cheap correctness win; also gives us real
  per-tier cost data to tune routing.
- **`TD-14` is directly relevant and still open:** a `sensitive`-tagged prompt routes to
  `local-reason`, but that tier's LiteLLM fallback chain includes `cloud-overflow` (Claude cloud),
  so if the local model is down a private prompt can *fail open to the cloud*. The dispatcher's
  `allow_cloud=False` is not enforced at the failover layer. Efficiency work here must **fail
  closed** — give `local-reason` a local-only fallback. Don't let a caching/routing refactor paper
  over this; fix it in the same pass.

---

## G. Better prompting & process (lever 6)

- **State the goal and the reason up front, in one well-specified turn.** Opus 4.8 and Sonnet 5 are
  more autonomous and calibrate effort to a clear brief; a scoped prompt with the intent stated
  ("this is for the nightly statement run; only check X, output Y") produces less exploratory
  token spend than an open-ended one and finishes in fewer turns.
- **For recurring work, encode a routine/skill with a fixed rubric** instead of re-issuing a fresh
  open-ended prompt each time. A daily review with a checklist prompt is cheaper and more
  consistent than "look at everything and tell me what's wrong" every morning.
- **Use `/clear` between unrelated tasks and `/compact` early** (while the session is still
  healthy) — stale context is re-sent on every subsequent message. Reported savings on focused
  tasks run 40–70% when context is kept clean.
- **Push mechanical work to subagents** so verbose intermediate output stays isolated and only the
  summary returns to the main context — but only when the task is big enough to beat the subagent's
  startup overhead (skip it for one-line shell/git actions).

---

## H. About the request that triggered this (the prompt critique, as asked)

The prompt was effective at getting a broad answer, but it's an example of the pattern above: it's
open-ended ("ANYTHING that could help… search the web… check the news"), which invites maximal
exploration and maximal token spend. For a *recurring* efficiency check, a tighter version costs
less and returns something comparable:

> "Review our AI process for token/cost inefficiency. Ground it in `localDNS/10-ai-orchestration/`
> and how Claude Code is run across the repos. Cover: prompt caching, model tiering, batch, context
> size. Output a ranked table of levers with rough savings and effort. Skip generic advice."

That version states the goal, the grounding, the scope, and the output shape — so the model spends
tokens on the answer, not on deciding how broad to go. (It would also make a good saved
routine/skill so we're not re-writing it each time.)

---

## Recommended follow-ups (candidate tech-debt / decisions)

1. Add `cache_control` to the router's Anthropic calls; verify `cache_read_input_tokens > 0`. *(new TD)*
2. Point the daily AI-CTO review routine at Sonnet 5 (or Haiku 4.5), not Opus. *(config/routine change)*
3. Bump `cloud-code`: `claude-sonnet-4-6` → `claude-sonnet-5`. *(config change; consider an ADR since it touches ADR-007's model choices)*
4. Route nightly statement builds + daily reviews through the Batch API. *(new TD)*
5. Replace `hoard.py`'s `chars÷4` estimate with `count_tokens` + real `usage` truing-up. *(new TD)*
6. Close `TD-14` (fail-closed local-only fallback for `sensitive`) before shipping any caching/routing refactor.
7. Slim `CLAUDE.md` files to stable rules; move long reference tables to on-demand linked docs. *(new TD)*

---

## Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Gateways & Model Routing: Cut AI Costs 2026 — Lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [Auto Routing — LiteLLM docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- Anthropic model pricing & prompt-caching mechanics: internal `claude-api` reference (cached 2026-06-24).
