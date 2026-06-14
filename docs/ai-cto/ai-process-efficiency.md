# AI Process Efficiency — User ↔ AI Review

How we work *with* the AI (Claude Code, the Claude API, and the local LiteLLM stack),
where tokens and money leak, and what to change. Owned by NARF (AI CTO); financial
items cross-reference ZORT. Web-sourced best practices as of **2026-06-14** — this
file dates fast, so re-check the linked sources each quarter.

> House style note: the *Change log* at the bottom reads newest-first. Everything else
> is reference, ordered by priority, not time.

---

## TL;DR — do these first

1. **🔴 ACT BEFORE JUNE 15 (tomorrow).** Anthropic splits agent/automation billing off
   the subscription into a separate, **capped, non-rollover** API-credit pool ($20 Pro /
   $100 Max-5x / $200 Max-20x, at list rates). Scheduled routines, `claude -p`, Claude
   Code GitHub Actions, and Agent-SDK apps **all draw from it, and HARD-STOP when it's
   empty** — no automatic fallback unless you pre-enable overflow billing. *This very
   routine is in scope.* See [§1](#1-the-june-15-billing-change-urgent).
2. **Turn on prompt caching** for any repeated-context call (the CLAUDE.md files, the
   roster, statement templates). ~90% off the cached portion; breaks even after one hit.
3. **Use the Batch API for non-interactive jobs** (monthly statement copy, bulk
   classification) — flat **50% off**, stacks with caching.
4. **Route the cheap work to the local box you already built.** The LiteLLM stack
   (`localDNS/10-ai-orchestration`) exists but isn't in the day-to-day loop. 60–70% of
   LLM calls (classify / extract / format) can run on the t630 for ~$0.
5. **Keep CLAUDE.md lean and one-task-per-session.** A 5k-token CLAUDE.md is a 5k-token
   tax on *every* turn; long threads re-bill the whole transcript each message.

---

## 1. The June 15 billing change (URGENT)

Starting **2026-06-15**, automated workloads stop drawing from the interactive
subscription pool and instead consume a **separate monthly credit**, billed at standard
API list rates:

| Plan | New automation credit / mo | Rollover? | When it's gone |
| ---- | -------------------------- | --------- | -------------- |
| Pro | $20 | No | Automated requests **stop** unless overflow billing is on |
| Max 5x | $100 | No | same |
| Max 20x | $200 | No | same |

**Covers:** Claude Agent SDK, `claude -p` CLI, Claude Code GitHub Actions, third-party
Agent-SDK apps, and **Claude Code on the web routines like this one.**
**Not affected:** interactive Claude.ai chat and interactive terminal Claude Code.

**Why it matters to A777ance specifically:** our whole operating model is "NARF/ZORT as
standing AI officers" plus scheduled routines (cross-repo reviews, this efficiency sweep,
statement-build automation under Stage 11). That is *exactly* the usage pattern being
repriced. The risk is not just cost — it's a **silent hard-stop** mid-routine when the
pool empties, with no rollover and no fallback.

**Before tomorrow, decide and act:**
- [ ] Confirm which plan tier we're on and the matching credit size.
- [ ] Decide overflow billing: **on** (routines keep running, pay-as-you-go past the cap)
      or **off** (hard cap, routines stop — safer for runaway cost, worse for reliability).
      Recommend **on, with a billing alert**, so a half-finished statement run doesn't
      strand mid-month.
- [ ] Re-point heavy automation at the local LiteLLM stack where the work is
      non-frontier (see [§4](#4-use-the-hybrid-stack-we-already-built)) to keep the
      metered pool for work that genuinely needs Claude.
- [ ] Log the decision as a FIN entry (ZORT) — it changes the cost structure in
      `runway.md` / `budget.md`.

---

## 2. Token leaks in the Claude Code loop

Reported field results: **40–85% token reduction** from these alone.

| Leak | Fix | Est. impact |
| ---- | --- | ----------- |
| Fat context files. Every CLAUDE.md injects into **every** request. Ours are large (the DESIGN one is the biggest), and a co-located session loads several. | Keep each CLAUDE.md tight; push detail into READMEs that are read *on demand*, not auto-injected. Target the briefing under ~200 lines. | High — it's a per-turn tax |
| Long-running sessions. Every new message re-reads the whole transcript, including stale tool output. | One task per session; `/compact` proactively; `/recap` (Apr 2026) to resume without replaying. | High |
| "Read the whole repo." Broad exploration pulls huge file dumps into context. | Point at specific files; delegate broad sweeps to **subagents/Explore** so the dump stays in the child context and only the conclusion returns. | High on big repos |
| Uncapped command output. Long test/log output drains tokens fast. | Cap bash output (e.g. `BASH_MAX_OUTPUT_LENGTH=20000`); pipe to a file and grep. | Medium |
| Verbose model output. | A 10-line "concise-output" skill in `~/.claude/skills/` trims every answer. | Medium |
| Skill/MCP bloat. Every loaded skill and MCP tool costs context whether used or not. | Keep ~8–12 skills; audit monthly, drop anything not triggered in 30 days. Only attach the MCP servers a session needs. | Medium, grows with tool count |

---

## 3. API-level cost levers (for anything we call programmatically)

These apply to the statement-copy generator, any bulk CRM enrichment, and Stage-11 glue —
not to interactive Claude Code, which is already flat-rate (until §1 bites for automation).

- **Prompt caching** — cache reads cost **0.1×** base input (≈90% off); cache writes
  1.25× (5-min) or 2× (1-hr). Break-even after **one** hit (5-min) / two (1-hr). Mark the
  stable prefix — CLAUDE.md/system prompt, roster, statement template — as the cache
  breakpoint; let only the per-home data vary. RAG/code-assistant workloads see 88–95% off
  repeated context.
- **Batch API** — async, results within 24h, **exactly 50% off** every model, no quality
  difference. Perfect for the **monthly statement run** and any "process all households"
  job — it's inherently batchy and not latency-sensitive. **Stacks with caching.**
- **Right-size the model.** Don't default everything to Opus 4.8. Use Haiku 4.5 for
  classify/extract/format, Sonnet 4.6 for most code/structured build, Opus 4.8 only for the
  hardest reasoning/research. Our LiteLLM `config.yaml` already encodes this as
  `cloud-code: sonnet` / `cloud-explore: opus` — apply the same discipline by hand in
  Claude Code (pick the model to match the task).

---

## 4. Use the hybrid stack we already built

We did the hard part — `localDNS/10-ai-orchestration` is a working LiteLLM gateway with
local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason`
deepseek-r1:1.5b, `local-embed`) in front of cloud Claude tiers, with a deterministic
privacy gate. **But it isn't deployed (TD-03 family) and isn't in our daily loop.** The
industry pattern this implements — local for the 60–70% simple work, cloud frontier for
the ~10% that needs it — reports **60–90% lower cost than all-cloud at the same quality
ceiling.** Two concrete wins:

- **Embeddings/RAG over our own repos run local and free** (`local-embed`,
  nomic-embed-text). No reason to pay cloud tokens to search our own docs.
- **Classification / extraction / first-draft copy** (lead tagging, parsing a booking
  form, a rough "Handled For You" line) → `local-fast`/`local-smart` on the t630, with
  cloud as failover only.

**Open risk to fix first (already tracked):** **TD-14** — a `sensitive`-tagged task can
fail over from `local-reason` to `cloud-overflow` (Claude cloud) because the local-only
chain isn't enforced at the LiteLLM failover layer. Close that **before** we route any
real customer data through the gateway, or the privacy guarantee is hollow.

**Caveat (keep it honest):** the t630 is a 4-core Carrizo with no usable GPU offload —
local tiers are fine for small/snappy work but slow for anything heavy, and heavy
reasoning is deliberately offloaded (rented GPU or cloud). Hybrid saves money on *volume*,
not on the hardest 10%. Don't over-claim local capacity.

---

## 5. Prompting improvements

- **Structure prompts with XML tags, not prose** — `<context>`, `<task>`,
  `<instructions>`, `<output_format>`. Claude parses tagged prompts more accurately.
  Don't over-tag: 3–5 tags is the sweet spot; a one-sentence section needs no tag.
- **Adaptive thinking** (Opus 4.8 / Sonnet 4.6): let the model decide depth via the effort
  parameter rather than forcing long chains everywhere — long reasoning is tokens too.
- **Lead with the deliverable shape.** Tell it the output format and length up front; it
  stops the model padding.

### Critique of the prompt that triggered this review

The founder asked for this review with: *"Locate inefficiencies in our PROCESS … Is there
a better way … Perhaps also better prompting … Anything you could possibly think of …
ANYTHING that could help … Keep UP TO DATE … Check the news."* Honest read:

- **Strength:** clear intent and an explicit "search the web / stay current" instruction —
  that's what surfaced the time-critical June-15 item.
- **Inefficiency:** it's open-ended and superlative-driven ("ANYTHING," "Anything you could
  possibly think of"). Unbounded scope invites a long, token-heavy exploration and a sprawling
  answer. The "Thanks!" lines and repetition add tokens without steering the model.
- **Tighter version** (same intent, less drift, cheaper run):

  ```
  <task>Review how we use AI (Claude Code + Claude API + the local LiteLLM stack)
  and find the top ways to cut token cost and improve our prompting.</task>
  <constraints>
  - Search the web for 2026 best practices; flag anything time-sensitive.
  - Ground every suggestion in our actual repos/config, not generic advice.
  - Rank by impact; cap at the ~8 highest-leverage items.
  </constraints>
  <output_format>A prioritized table + a short action list, committed as a doc.</output_format>
  ```

  Same ask, bounded scope, explicit ranking and cap, a defined deliverable — less wandering,
  fewer tokens, and a more actionable result. (For a recurring sweep, save it as a skill or a
  `/loop` so it isn't re-typed each time.)

---

## 6. Prioritized action list

| # | Action | Owner | Effort | Payoff |
| - | ------ | ----- | ------ | ------ |
| 1 | Decide overflow billing + confirm plan/credit before **2026-06-15**; log as a FIN entry | ZORT | 15 min | Avoid silent routine hard-stops |
| 2 | Trim each CLAUDE.md; move detail to on-demand READMEs | NARF | 1–2 h | Per-turn token cut across all sessions |
| 3 | Adopt prompt caching + Batch API for the monthly statement run | NARF/ZORT | 2–4 h | ~50–90% off that recurring job |
| 4 | Close **TD-14** (local-only failover), then deploy the LiteLLM gateway and route cheap/RAG work local | NARF | TD-14 small; deploy = box access | 60–90% off non-frontier volume |
| 5 | Add a "concise-output" skill + cap bash output; one-task-per-session habit | NARF | 30 min | Steady drip savings |
| 6 | Save this review as a reusable skill/`/loop` with the tightened prompt | NARF | 15 min | Cheaper, repeatable sweeps |

---

## Change log

- **2026-06-14** — Created. Triggered by founder's "find AI process inefficiencies" routine.
  Lead finding: the June-15 agent-billing split hard-caps automation credits — act before
  the cutover. Web best practices captured below.

## Sources

- [Anthropic ends subscription subsidy for agents June 15 (TechTimes)](https://www.techtimes.com/articles/317625/20260602/anthropic-ends-subscription-subsidy-agents-june-15-credit-pool-replaces-flat-rate-access.htm)
- [Anthropic's June 15 billing change — what Claude Code & Agent SDK users must do (Codersera)](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [Claude Code pricing after June 15: the decision table (FindSkill)](https://findskill.ai/blog/claude-code-pricing-after-june-15-decision-table/)
- [Anthropic API pricing 2026 — caching, batch & optimization (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt caching: cut repeated-context cost up to 90% (Tygart Media)](https://tygartmedia.com/anthropic-prompt-caching-90-percent-token-savings/)
- [Reduce Claude Code token usage by 90% (Medium / Mehul Gupta)](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [23 tips for Claude Code token saving (Analytics Vidhya)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Code advanced best practices — hooks, subagents, context (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/)
- [Claude Code subagents: a 2026 practical guide (Tembo)](https://www.tembo.io/blog/claude-code-subagents)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid cloud-local AI workflows — cost optimization (BuildMVPFast)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM AI gateway: route local + cloud (Local AI Master)](https://localaimaster.com/blog/ai-gateway-litellm)
- [Prompting best practices — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Claude XML tags — prompt engineering (AI Prompt Library)](https://www.aipromptlibrary.app/blog/claude-xml-tags-prompt-engineering)
