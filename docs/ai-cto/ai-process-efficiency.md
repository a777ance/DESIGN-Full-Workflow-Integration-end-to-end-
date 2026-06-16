# AI process efficiency — token & workflow review

*Standing review of how we (humans + AI) spend tokens across the portfolio, and where a
cheaper/better path exists. Findings are newest-first per house style. Reviewed against the
live `localDNS/10-ai-orchestration` router and the CLAUDE.md set on 2026-06-16.*

**The good news first:** the foundation is already strong. The LiteLLM router
(`10-ai-orchestration`) is a textbook hybrid gateway — local-first, cloud as overflow,
fail-closed for sensitive tasks. That is exactly the architecture the 2026 cost-optimization
literature recommends (hybrid routing saves a documented 60–83% vs. cloud-only). The findings
below are about *tuning what already exists*, not rebuilding.

---

## Findings (newest first)

### F-07 — This routine's own prompt is unbounded → unpredictable spend each run
The prompt that generates this review says "ANYTHING that could help… anything you could
possibly think of… check the news." Open-ended is fine for a one-off, but as a **scheduled
routine** it re-runs broad web research every time, with no stop condition and no budget — so
cost and output drift run-to-run.
- **Action:** tighten the recurring prompt to: (1) a fixed checklist (the F-01…F-06 axes
  below), (2) an explicit token/-search budget ("≤6 web searches, ≤1 subagent"), (3) an output
  contract ("append only *new* findings to this file; notify only if a finding is P1/P2"), and
  (4) a cadence note ("monthly is enough; the field moves weekly but our config doesn't").
- **Why it matters:** a routine that only pings when it finds something *new* is the whole
  point — see the silence-when-healthy rule. A vague prompt forces a full re-derivation every
  run and notifies on noise.
- **Est. impact:** turns an open-ended research burn into a bounded diff; most runs end silent.

### F-06 — Statement generation is a batch workload paying interactive prices
Stage 06 builds statements monthly, in bulk, with no human waiting on any single one — the
textbook case for the **Message Batches API (50% discount on input+output)**. If any part of
statement composition calls a cloud model (or comes to), route that path through batch, not the
synchronous endpoint.
- **Action:** when stage 06 / the `customers` `make statement` path uses a cloud model, submit
  the month's run as one batch job. Combine with caching (F-01) on the shared template/prompt.
- **Est. impact:** 50% on any cloud tokens in the monthly run, stacking with cache savings.
- Logged as tech-debt TD-17.

### F-05 — Manual model selection in Open WebUI leaves routing to the human
Today a person picks `local-fast` / `cloud-overflow` etc. in the chat UI. That means the
*cheapest adequate model* is chosen by memory, not by the task. The `langgraph-router`
supervisor (Heimdall/Odin) is the right place to automate this, but the UI path bypasses it.
- **Action:** add a default "auto" route — a tiny local classifier (qwen2.5:3b is already
  pulled) that tags each prompt simple/complex/sensitive and picks the tier, RouteLLM-style.
  Keep the manual override. Sensitive stays pinned local (already enforced — but see TD-14).
- **Est. impact:** RouteLLM-class routing shows ~85% cost cut at ~95% frontier quality; even a
  coarse classifier shifts the bulk of easy turns off the cloud tier.

### F-04 — No semantic cache in front of the router
LiteLLM supports a response cache (incl. semantic). Repeated/near-repeated prompts (status
checks, "explain this config", regenerated statements) re-pay full price every time.
- **Action:** enable LiteLLM caching. Start with the simple exact-match cache (Redis or in-mem,
  no Postgres needed); evaluate semantic cache for the chat UI. Set short TTLs so config answers
  don't go stale.
- **Est. impact:** "caching eliminates 30–50% of requests entirely" on repeat-heavy workloads.

### F-03 — Cloud tiers default to Opus 4.8 (the most expensive model) almost everywhere
`config.yaml` points `cloud-overflow`, `cloud-explore`, **and** `cloud-vision` at
`claude-opus-4-8`. The file's own comment already notes Sonnet 4.6 / Haiku 4.5 as cheaper swaps,
but the defaults don't follow it. Opus-by-default is a silent cost leak on every overflow.
- **Action:** demote defaults to the cheapest tier that clears the bar — Haiku 4.5 for
  classification/extraction/short chat, Sonnet 4.6 for code/diffs/most overflow, Opus 4.8 only
  for `cloud-explore` (hardest reasoning) and genuinely hard escalations. This is a few
  `model:` lines.
- **Est. impact:** Sonnet vs Opus is a large per-token delta; Haiku larger still. On the
  overflow path this is the single highest-leverage one-line change.
- Logged as tech-debt TD-16.

### F-02 — Giant duplicated CLAUDE.md preamble is re-paid every session, every repo
Every repo's `CLAUDE.md` loads in full before the user types a word. The **House style:
ordering & typography** block (~300 words / ~400 tokens) is copy-pasted *verbatim* into all 6
repos, and the two big repos are large in their own right (DESIGN ~2,600 words, localDNS ~2,700).
A 5,000-token CLAUDE.md costs 5,000 tokens of context on every single session before any work.
- **Action:**
  1. Factor the shared house-style block into one canonical file (e.g. `localDNS/STYLE.md` or a
     portfolio doc) and replace the in-line copy in each CLAUDE.md with a 2-line pointer +
     one-line summary. ~350 tokens × every session × every repo recovered.
  2. Slim the two big CLAUDE.md files to the essential briefing; push the deep reference into
     the README/`network-context.md` they already link, which Claude loads *on demand* instead
     of *always*.
- **Caveat:** CLAUDE.md is also a correctness tool — don't cut the invariants (privacy gate,
  honesty rule, push-to-main). Trim duplication and reference material, not the rules.
- **Est. impact:** lower fixed per-session cost across the whole portfolio; faster, cleaner
  context. Logged as tech-debt TD-15.

### F-01 — Prompt caching is not wired into the cloud path (biggest single win)
Nothing in `config.yaml` or the dispatcher sets Anthropic `cache_control` breakpoints. Claude
Code's own sessions cache automatically, but **our app-level calls** (anything via LiteLLM →
Anthropic, and any future statement/CRM automation hitting the API) re-pay full input price for
the same system prompt, tool defs, and shared template on every call.
- **Action:** add a cache breakpoint after the static prefix (system prompt + tool/route
  definitions + any shared statement template) so dynamic content (the user turn / per-household
  data) stays last. LiteLLM passes `cache_control` through to Anthropic. Order prompts
  static-first, dynamic-last.
- **Rule of thumb:** worth it at ≥3 reads within the 5-min TTL (≥5 for the 1-hr TTL). Our
  repeated system prompts and monthly statement template clear that easily.
- **Est. impact:** cache reads price at ~10% of base input → documented **60–90% input-cost
  reduction** on cache-hit-heavy workloads. This is the highest-ROI change on the list.

---

## Workflow notes (human ↔ AI process, no config change needed)

- **Scope sessions to one repo.** Opening the whole portfolio loads 6 CLAUDE.md files. Work in
  one repo at a time so only its briefing is in context.
- **Delegate research to subagents.** "Use a subagent to investigate X" keeps the main context
  clean — the fan-out happens in a separate window and only the conclusion returns. (This review
  used that pattern.)
- **`/clear` between unrelated tasks; `/compact` (or `/recap`) on long sessions** instead of
  letting history accumulate — context holds *every* message, file read, and command output.
- **Cap tool output.** Long logs/test output flood context; filter before the model sees them.
- **Prefer short, concrete prompts.** Over-long prompts raise token cost without improving
  output; incremental, narrow asks are cheaper and more focused. (See F-07.)

---

## Verdict on the current architecture

Keep it — it's right. LiteLLM is still a leading 2026 gateway choice; the local-first,
fail-closed-for-sensitive design is the recommended hybrid pattern. The wins here are *tuning*:
turn on caching (F-01), stop defaulting to Opus (F-03), batch the monthly run (F-06), slim the
always-loaded context (F-02), and automate the route choice (F-05). None require a rebuild.

## Sources
- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude API cost optimization: caching, batching, 60% token reduction](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Claude Code best practices (docs)](https://code.claude.com/docs/en/best-practices)
- [How to reduce Claude Code token usage — 8 methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM gateways & model routing — cut AI costs (2026)](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [LLM model routing 2026 — cost-quality optimization](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
