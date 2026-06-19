# Process efficiency — user ↔ AI workflow (token & cost review)

**Author:** NARF (AI CTO), scheduled-routine review · **Date:** 2026-06-19
**Scope:** how we work *with* Claude (Code + API) across the portfolio — where we
spend tokens we don't need to, and the cheaper way to get the same result.
**Status:** findings + recommendations. Each item is independently actionable; the
priority column is the order to do them in (effort vs. saving).

This file is the durable record; a one-paragraph version went out as the routine
notification on 2026-06-19. Nothing here changes a customer-facing surface.

---

## TL;DR — the seven levers, by payback

| # | Lever | Effort | Rough saving | Where |
| - | ----- | ------ | ------------ | ----- |
| 1 | **Right-size the model per job** — stop running Opus on routines/research | 5 min | 60–90% on those runs | Claude Code `/model`, routine config |
| 2 | **Fix the prompt habit** — scope + output contract + budget (see §1) | per-prompt | 30–60% fewer exploratory tokens | every session |
| 3 | **Trim & de-duplicate CLAUDE.md** — shared house-style via `@import` | 30 min | per-session load tax, every session | all 7 repos |
| 4 | **Route cheap work to the homelab** — we already own the gateway | 1–2 hr | 60–80% on triage/draft/summarize | localDNS stage 10 |
| 5 | **Prompt caching** on any programmatic Claude call | 1 hr | up to 90% on cached input | statement gen, AI-CTO/CFO jobs |
| 6 | **Batch API** for non-realtime jobs | 1 hr | 50% flat | nightly stats, bulk statements, evals |
| 7 | **Claude Code token hygiene** — concise output, scoped reads, subagents | ongoing | ~40–65% per session | every session |

Stacking 1 + 5 + 7 is where the published numbers land production workloads at
**20–30% of unoptimized cost**. ([dev.to](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49))

---

## 1. The prompt habit (the thing you asked me to grade)

The prompt that triggered this review is a fair example of the dominant
inefficiency: **open-ended scope, no output contract, no budget.** "Locate
inefficiencies… is there a better way… better prompting… leveraging other AI…
ANYTHING that could help… search the web… check the news" tells the model to
explore in every direction and keep going. That maximises tokens before the first
useful word — exactly the failure mode the 2026 guidance warns about: *structure
beats length, and LLM reasoning starts degrading past ~3k tokens of instruction.*
([promptbuilder](https://promptbuilder.cc/blog/prompt-engineering-best-practices-2026),
[lakera](https://www.lakera.ai/blog/prompt-engineering-guide))

It worked here because the task genuinely was "go wide," but as a daily habit it's
expensive. The fix is a 4-block contract (INSTRUCTIONS / CONTEXT / TASK / OUTPUT),
XML tags for structure (Claude follows tags better than prose or Markdown), one
example not five, and explicit permission to say "I don't know" instead of guessing.
([claude.com](https://claude.com/blog/best-practices-for-prompt-engineering))

**Same intent, ~⅓ the tokens, sharper output — template:**

```xml
<task>Find the 3 highest-payback ways to cut our Claude token spend.</task>
<context>We run Claude Code (web + scheduled routines) over 7 repos, plus a
LiteLLM gateway with local DeepSeek + a rented-GPU tier (localDNS stage 10).</context>
<constraints>Web-check anything that may have changed since Jan 2026.
Skip anything saving <10%. Stop after 3 findings.</constraints>
<output>A table: lever | effort | est. saving | first step. Then 3 sentences max each.</output>
```

Three rules cover 90% of it: **bound the scope** ("top 3," "stop after"), **name the
output shape**, **set a budget** ("skip < 10%," "3 sentences each"). Claude 4.x takes
you literally — under-specifying the *output* is what makes it wander.

---

## 2. Right-size the model (lever 1 — do this first)

This routine ran on **Opus 4.8**, the most expensive tier, to do *research and
summarise* — a Sonnet/Haiku job. The 2026 rule of thumb: pick the cheapest model
that clears your quality bar, scale up only for hard reasoning / deep coding /
large context. ([aiproductivity](https://aiproductivity.ai/blog/which-claude-model-for-coding/))

- **Scheduled routines** (this one, doc-link checks, status sweeps) → **Haiku 4.5**
  or **Sonnet 4.6**. Reserve Opus for architecture, gnarly debugging, security review.
- Use **`/usage`** (per-category breakdown landed June 2026) to see where tokens
  actually go before optimising. ([jangwook.net](https://jangwook.net/en/blog/en/claude-code-june-2026-new-features-changelog-developer-guide/))
- **Safe Mode** (June 2026) disables CLAUDE.md/skills/MCP/hooks for a clean, cheap
  run when you don't need the full harness — good for a quick scoped routine.
- Note: **Opus 4.8 doubled rate limits** in June, so the constraint is increasingly
  cost, not throughput — which makes model choice the lever, not rationing.

---

## 3. Trim & de-duplicate CLAUDE.md (lever 3)

CLAUDE.md loads into **every** session. Current sizes: localDNS 326 lines, DESIGN
295, MARKETING 214 — and the **~25-line "House style" block is copy-pasted verbatim
into all 7 repos.** A multi-repo session (like this one) pays for all of them at once.

- Factor the shared house-style block into one file and pull it in with an
  **`@import`** line in each CLAUDE.md (Claude Code supports `@path` imports). One
  source of truth, and the per-repo files shrink.
- Keep CLAUDE.md to the *authoritative summary*; push detail to README/context files
  that are read on demand, not auto-loaded. "Token costs come from bloated context,
  not long prompts." ([kdnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage))
- Within a single session, the system prompt + CLAUDE.md + tool defs are cached
  automatically, so the tax is *per new session* — which is exactly what routines
  spawn a lot of. Shrinking the static prefix compounds across every run.

---

## 4. Route cheap work to the homelab (lever 4) — we already own the gateway

This is the highest-leverage *structural* move and we're already 80% built: localDNS
stage 10 runs **LiteLLM (port 4040) + local DeepSeek + a rented-GPU tier + Open
WebUI.** The 2026 pattern is exactly this — an intelligent routing layer that sends
work to local vs. cloud by **task complexity, data sensitivity, and availability**,
cutting 60–80% of spend by keeping simple/sensitive work off the paid API.
([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026))

**What to send local vs. Claude:**

- **Local (DeepSeek / rented GPU):** first-pass triage, summarising logs & web
  fetches, draft "Handled For You" copy, classification/tagging, the cheap half of a
  draft→refine loop, anything touching real customer data (privacy).
- **Claude API:** final reasoning, code that has to be right, security review,
  customer-facing prose, anything where a wrong answer is expensive.
- **Pattern:** draft locally, *refine* with Claude — you pay Claude only for the
  delta, not the blank-page cost.

**Blocker:** **TD-14** — the privacy fallback gap. A `sensitive`-tagged task can
fail over from `local-reason` to `cloud-overflow` (Claude cloud) because
`allow_cloud=False` isn't enforced at the LiteLLM failover layer. **Fix that before
routing any real customer data through the gateway** — otherwise "route sensitive
work local" isn't actually guaranteed. Make `local-reason` fail *closed* to a
local-only chain.

---

## 5. Prompt caching on programmatic calls (lever 5)

Anywhere we call the Claude API in code (the statement generator's compose step, the
AI-CTO/CFO automations, any Stage-11 glue): order the request **static content first**
(system prompt, tool defs, the household data template) and **dynamic last** (the one
household's figures), then set `cache_control`. Cache reads bill at ~10% of input —
**up to 90% off** the repeated prefix. Breakeven is ~3 reads inside the 5-min TTL
(~5 for the 1-hr TTL), which monthly statement batches clear easily. Log
`cache_read_input_tokens` vs `input_tokens` to confirm the hit ratio (74–84% is
achievable on stable workloads). ([platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[tokenmix](https://tokenmix.ai/blog/claude-api-cache-pricing))

---

## 6. Batch API for non-realtime jobs (lever 6)

A flat **50% off** input *and* output for anything that tolerates up to 24h latency,
with no quality difference — only timing. ([codewords](https://www.codewords.ai/blog/anthropic-batch-api))
Our batch-shaped jobs:

- **Monthly statement generation** across all households (already "a penny a home" —
  batch halves it, and stacks with caching).
- **Nightly** stats roll-ups / `collect_stats.py`-adjacent summarisation.
- **Offline evals** of prompt/model variants, bulk classification, content drafts.

Keep interactive/customer-facing turns on the realtime API; move the cron-shaped work
to batch.

---

## 7. Claude Code token hygiene (lever 7) — every session

- **Concise output / output styles** — terse mode reports ~65% fewer tokens over a
  session. ([genaiskills](https://genaiskills.io/articles/claude-code-token-optimisation))
- **Subagents / Explore for verbose work** — fan-out searches and log dumps stay in an
  isolated context and only the conclusion returns. Caveat: subagents add startup
  overhead, so use them when the saved main-context clutter beats that overhead, not
  for trivial lookups. ([nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/))
- **Scoped reads** — read line ranges, not whole files; don't re-read a file you just
  edited (the harness tracks it).
- **`/recap`** (April 2026) to resume without replaying the whole conversation; tune
  the **compaction threshold** so long sessions compress earlier.

---

## 8. Cadence — how to run "keep up to date" cheaply

The standing ask is "keep this current, it changes daily." Don't do that with an
open-ended Opus routine:

- Use the **`loop`** skill with a *scoped* prompt on **Haiku/Sonnet** for the regular
  "anything change?" sweep — bounded output, cheap model, only escalate to a full
  write-up when something actually moved.
- Reserve the **`deep-research`** skill (with this doc as the baseline) for a periodic
  deeper pass — monthly, not daily.
- This whole review is the kind of thing to re-run **monthly**, diffing against this
  file, rather than re-deriving from scratch each time.

---

## Sources

- Prompt caching: [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [tokenmix](https://tokenmix.ai/blog/claude-api-cache-pricing) · [dev.to (caching+batching+routing)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- Batch API: [codewords](https://www.codewords.ai/blog/anthropic-batch-api) · [finout](https://www.finout.io/blog/anthropic-api-pricing)
- Claude Code token reduction: [kdnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) · [genaiskills](https://genaiskills.io/articles/claude-code-token-optimisation) · [analyticsvidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- Subagents: [nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/)
- June 2026 Claude Code features: [jangwook.net](https://jangwook.net/en/blog/en/claude-code-june-2026-new-features-changelog-developer-guide/) · model choice [aiproductivity](https://aiproductivity.ai/blog/which-claude-model-for-coding/)
- Hybrid local/cloud routing: [sitepoint architecture](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026) · [digitalapplied routing](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- Prompt engineering: [claude.com best practices](https://claude.com/blog/best-practices-for-prompt-engineering) · [promptbuilder 2026](https://promptbuilder.cc/blog/prompt-engineering-best-practices-2026) · [lakera](https://www.lakera.ai/blog/prompt-engineering-guide)
