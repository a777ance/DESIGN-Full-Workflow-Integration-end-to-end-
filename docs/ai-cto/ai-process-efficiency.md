# AI Process Efficiency — reducing token use & tightening the human⇄AI loop

**Author:** NARF (AI CTO)  ·  **Date:** 2026-07-02  ·  **Status:** review / recommendations

Founder asked: *where are the inefficiencies in our process between the user and the AI?
Can we reduce token use? Better prompting? Leverage other AI / a hybrid local-LLM + Claude
setup? Keep it up to date — this changes day by day.*

This is the answer, tailored to what we actually run. The good news up front: **we already
own most of the machinery** (the Odin/LiteLLM router in `localDNS/10-ai-orchestration/`, a
local Ollama tier, a cloud-overflow tier). The waste is mostly in *how we drive the loop*,
not in missing tools.

---

## 0. The five wins, ranked by payoff-per-effort

*(do them in this order — newest thinking first per house style, but this list is priority-ordered)*

| # | Win | Effort | Est. saving | Where |
| - | --- | ------ | ----------- | ----- |
| 1 | **Prune the CLAUDE.md files** — they load *every turn* | 1 session | 30–90% of per-turn fixed cost | all repos |
| 2 | **Session hygiene** — `/clear` on task switch, `/recap` to resume, don't marathon one session | free, habit | biggest single real-world drain | all work |
| 3 | **Turn prompt caching on and keep the prefix frozen** | config + habit | ~90% off repeated input tokens | Claude API / Claude Code |
| 4 | **Route by task class** — local Ollama for cheap work, Claude for hard agentic work | we have the router | 60–80% on the offloadable slice | Odin stack |
| 5 | **Delegate to subagents** for search/review so file-dumps never touch the main thread | free, habit | keeps context small = cheaper every turn | Claude Code |

---

## 1. Our single biggest, most specific leak: the CLAUDE.md files

A CLAUDE.md is re-sent to the model **on every single turn** of a session — it is fixed
overhead you pay all day. Benchmarks this year found a 3,847-token CLAUDE.md pruned to
312 tokens ("only what the model can't infer") gave a **91.9% context reduction with no
quality regression." ([firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency),
[agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage))

**Our files are the opposite of pruned.** The `DESIGN-…/CLAUDE.md` alone is a full funnel
diagram, a stage map, a money-flow diagram, a known-issues table, and two AI-persona
protocols — easily several thousand tokens. Every repo repeats the ~40-line "House style"
block verbatim. When a scheduled routine like *this* one boots, it loads the CLAUDE.md of
**every repo in scope** before doing any work — we paid to read six house-style blocks just
to start this analysis.

**What to do**

- Cut each CLAUDE.md to what the model genuinely can't infer from the tree: the invariants,
  the "don't do X," the non-obvious wiring. A new reader's onboarding narrative belongs in
  `README.md`, which is *not* auto-loaded every turn.
- The House-style block is identical across seven repos. Keep the canonical copy in one
  place (it already lives in each CLAUDE.md); in the others, compress to a one-line pointer
  + the two rules that actually bite (newest-first, Gill Sans). The full prose doesn't need
  to be resident in context in all seven.
- Move "read these six files at session start" persona protocols (NARF/ZORT) out of the
  always-loaded CLAUDE.md and into a skill or a `/start` command the human invokes when they
  actually want that boot sequence — not on every turn of every session.
- **Caveat (caching interaction, see §3):** editing CLAUDE.md invalidates the prompt cache
  for the rest of that prefix. So prune it *once*, deliberately, then leave it alone — don't
  fiddle with it mid-session. ([knightli](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/))

This one change compounds against every other session we run, forever.

---

## 2. Session hygiene — the drain nobody sees

Long threads are the biggest hidden cost: every new message re-reads the whole
conversation, including stale instructions and dead code. ([kdnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage))
The 1M-token window made this *worse* in practice — people now marathon a single session
because they can, and pay to re-read 400K tokens of irrelevant history on every turn.
"A bigger window does not fix bad session management." ([buildthisnow](https://www.buildthisnow.com/blog/guide/mechanics/context-management))

**Habits to adopt**

- `/clear` when switching tasks. A fresh session is cheap; a bloated one bills on every turn.
- `/recap` (added April 2026) to resume where you left off without replaying the whole thread.
- One session ≈ one task. When a task is done, clear before the next — don't let context
  accumulate across unrelated work.
- Tell CLAUDE.md what compaction must preserve (e.g. "on compaction, keep the modified-file
  list and the test/verify commands") so the summary doesn't drop the load-bearing facts.

---

## 3. Prompt caching — the 90% discount most people leave off

Cached input tokens bill at ~10% of the normal rate — a **90% reduction** (Sonnet input
$3/1M → $0.30/1M on a cache hit). It pays off from the 3rd repeated request and is
"substantial by the tenth." ([platform docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[tokenmix](https://tokenmix.ai/blog/claude-api-cache-pricing))

The catch is **prefix stability**: change one token before the cache breakpoint — a date, a
timestamp, a tweak to CLAUDE.md — and everything after it is recomputed at full price.
([mindstudio](https://www.mindstudio.ai/blog/prompt-caching-cut-token-costs-claude-dynamic-workflows))

**What to do**

- Claude Code caches automatically — the lever is *don't break the prefix*. Keep dynamic
  content (dates, run IDs) out of the system prompt / CLAUDE.md; let it live in the message body.
- Our nightly/scheduled routines that hit the same big context repeatedly are *ideal* cache
  candidates — as long as we stop editing the CLAUDE.md they read.
- If we ever call the Anthropic API directly (not through Claude Code) for a batch job over
  the roster or statements, set explicit `cache_control` breakpoints on the stable prefix
  (the schema, the template, the instructions) and vary only the per-record tail. Cache
  isolation moved to workspace-level on 2026-02-05, so this is safe per-workspace.

---

## 4. Hybrid local + Claude — we're 80% built; here's the missing piece

The industry pattern for 2026 is exactly our Odin design: an LLM gateway (LiteLLM) fronting
a **local Ollama tier** for cheap/simple/sensitive work and a **Claude cloud tier** for hard
work, routed by *data sensitivity, task complexity, and availability*. Reported savings:
**60–80% with minimal quality impact** on the offloadable slice.
([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026),
[mindstudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs))

**What we already have** (`localDNS/10-ai-orchestration/config.yaml`): `local-fast`
(qwen2.5:3b), `local-smart` (qwen2.5:7b), a reasoning ladder, `local-embed`, and
`cloud-overflow` → Claude, with graceful failover. This is a textbook hybrid gateway.

**The missing piece is *policy*, not plumbing.** Today the router picks a backend by
*health/failover*; it does not yet pick by *task class*. The saving comes from deciding
**what runs where**:

- **Send to the local tier (free, private, already paid for):** first-draft copy for
  marketing/statements, classification/tagging of leads, summarizing a call log into the
  roster, extracting fields from a form, "rewrite this plainer," commit-message drafts,
  RAG-grounded Q&A over our own repos (embeddings are already local). None of this needs a
  frontier model, and much of it is *sensitive customer data that shouldn't leave the box
  anyway* — the privacy gate and the cost gate point the same direction here.
- **Keep on Claude (worth the tokens):** multi-file agentic coding, the hard architecture
  calls, anything that plans-then-edits across the repo, statement-generator changes where a
  bug ships to a paying customer. Frontier reasoning earns its price here; a CPU 7B does not.
- **Concrete next step:** add a short "route card" to `10-ai-orchestration/README.md` — a
  table of task → tier — and (optionally) wire LiteLLM auto-routing / a tiny classifier so
  the *default* for chat-style work is local, with Claude as an explicit escalation. LiteLLM
  supports auto-routing by request class natively.
  ([litellm auto_routing](https://docs.litellm.ai/docs/proxy/auto_routing))
- **Reality check (our own honesty rule):** the t630 is CPU-only, memory-bandwidth bound. A
  7B is "submit-and-wait," not snappy. So offload *async, latency-tolerant* work locally;
  don't put an interactive human behind a CPU 7B and call it a saving — that trades tokens
  for wall-clock and frustration. The heavy-reasoning path already correctly points at a
  rented GPU, not local CPU. ([kunalganglani benchmark](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark))

---

## 5. Subagents & scoping — keep the main thread clean

Delegate search, exploration, and diff-review to **subagents**: they run in a *separate*
context, do the noisy work (file dumps, logs, greps), and hand back only a concise result —
so the expensive main thread never carries the mess. A subagent can also run on a cheaper
model without cold-starting the main conversation's cache.
([tembo](https://www.tembo.io/blog/claude-code-subagents),
[claude code best practices](https://code.claude.com/docs/en/best-practices))

- "Use a subagent to investigate X" instead of reading twelve files into the main thread.
- Before calling non-trivial work done, have a **fresh subagent review the diff** against the
  criteria — it sees the result, not the reasoning that produced it, so it catches gaps.
- Scope requests tightly: "refactor the login function in `auth.ts`," not "refactor auth."
  Smaller scope = less context pulled in = fewer tokens and a more focused edit.
  ([analyticsvidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/))

---

## 6. Model selection

Opus bills ~5× Sonnet per token; on subscription it drains the quota window faster. Default
to **Sonnet**, escalate to **Opus** only for genuinely hard analysis/refactors, and use a
**Haiku** subagent for cheap side-lookups. Don't switch models deep into a long thread just
for a "quick question" — the cheaper model rebuilds its cache from scratch and the cold write
can cost more than just finishing on the model you're already on.
([agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage),
[buildthisnow](https://www.buildthisnow.com/blog/guide/development/claude-code-prompt-caching))

---

## 7. Critique of the request that started this (as asked)

The founder asked me to flag if *this very prompt* was inefficient. It was — usefully so in
places, wasteful in others:

**What worked:** stating the goal (reduce token use), naming the specific angles (hybrid
local/Claude, better prompting), and explicitly authorizing web search + "keep up to date."
That gave me a clear objective and permission to act — good prompting.

**What cost tokens for little return:**

- *"Anything you could possibly think of… ANYTHING that could help."* Open-ended maximalism
  invites a sprawling answer and a long, unfocused research phase. A tighter frame —
  "top 5 by ROI, tied to our stack" — gets the same value for fewer tokens. (This report
  self-imposed that frame in §0.)
- **Repetition/emphasis** ("Thanks!" ×2, ALL-CAPS, "day by day") is friendly but pure
  overhead in a prompt that's re-read as context. Say it once, plainly.
- **No scope boundary.** "Our PROCESS" could mean the sales funnel, the git workflow, or the
  human⇄AI loop. I inferred the last one. A one-line "I mean how we drive Claude Code, not the
  business funnel" would have removed a guess.

**The higher-leverage version of this same ask:**

> "Audit how we use Claude Code for token efficiency. Give me the top 5 changes by
> ROI, tied to our Odin router and CLAUDE.md files. Web-search for anything from the
> last ~30 days. Land it as a doc under docs/ai-cto/."

Same outcome, a fraction of the ambiguity — and it names the deliverable so I don't have to
guess where to put it.

**Meta-point for recurring/scheduled prompts especially:** a routine's prompt is paid *every
time it fires*. It's the highest-value text to keep tight. Worth a one-time editing pass on
each cron/routine prompt for the same reason we're pruning CLAUDE.md.

---

## 8. Keeping this current (it changes weekly)

This space moves fast; treat this doc as a snapshot, not gospel. Cheap ways to stay current
without spending a research session each time:

- **Anthropic's own docs are the source of truth** for pricing, caching, and Claude Code
  features — check `platform.claude.com/docs` and `code.claude.com/docs` before trusting a
  third-party blog. Model IDs and prices in third-party posts go stale within weeks.
- Re-run a short version of this audit **quarterly**, or whenever Anthropic ships a pricing /
  caching / context change. A scheduled routine could do exactly this and only notify on a
  *material* change (a new price tier, a new context-management feature) — otherwise stay quiet.
- Watch specifically for: cheaper/faster model tiers (would shift the §4 route card), changes
  to prompt-cache TTL or pricing, and new Claude Code context-management primitives.

---

## Sources

- [Anthropic — Prompt caching (Platform docs)](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching)
- [Anthropic — Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Firecrawl — 12 ways to cut token consumption in Claude Code](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Agensi — How to reduce Claude Code token usage (8 methods)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [KDnuggets — 7 practical ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Analytics Vidhya — 23 tips for Claude Code token saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Knightli — Claude Code token-saving guide (models, MCP, CLAUDE.md, skills & cache)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Build This Now — Claude Code prompt caching](https://www.buildthisnow.com/blog/guide/development/claude-code-prompt-caching) · [Context management](https://www.buildthisnow.com/blog/guide/mechanics/context-management)
- [MindStudio — Prompt caching in dynamic workflows](https://www.mindstudio.ai/blog/prompt-caching-cut-token-costs-claude-dynamic-workflows) · [Run local models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [TokenMix — Claude API cache pricing 2026](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [SitePoint — Hybrid cloud-local LLM architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [BuildMVPfast — Hybrid cloud-local AI cost optimization 2026](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM — Auto routing docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Kunal Ganglani — Local LLM vs Claude for coding: $500 GPU benchmark 2026](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [Tembo — Claude Code subagents: a 2026 practical guide](https://www.tembo.io/blog/claude-code-subagents)
