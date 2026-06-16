# Process efficiency — human↔AI workflow & token spend

*Review date: 2026-06-16. Inputs: current Anthropic API pricing, Claude Code best-practice
write-ups (Apr–Jun 2026), and our own setup (the 7 A777ance repos + the t630 LLM router).
Re-check quarterly — pricing and Claude Code features move week to week.*

This is a findings doc, not an ADR. The top three levers below are worth an ADR each once
we decide to act. Ranked by impact **for how we actually work** (broad, scheduled Claude Code
routines across many repos).

---

## The headline

We are leaving the two biggest savings on the table, and both are things we already own:

1. **We run everything on the most expensive model.** This very review ran on **Opus 4.8
   [1m]** — $5/$25 per Mtok, the flagship. Most of what these routines do (research, doc
   edits, link-checking, status sweeps, drafting) is Sonnet- or Haiku-grade work. Opus input
   is **5× Sonnet, 5× Haiku**; output is 5× Haiku. Reserving Opus for genuinely hard
   architecture/reasoning and running the rest on Sonnet 4.6 is the single biggest lever, and
   it costs nothing to adopt.

2. **We built a hybrid local/cloud router and don't route through it.** `localDNS`
   stage 10 already runs LiteLLM + Ollama + the langgraph "Odin" supervisor with a reasoning
   ladder (`local-reason` deepseek-r1:1.5b on the t630, `cloud-gpu-reason`, `cloud-overflow`).
   Published hybrid setups cut LLM spend **60–86%** by sending the easy 70% of calls to a
   local/cheap model and reserving Claude for the hard 30%. Our automations (statement
   narratives, marketing drafts, lead classification, the stage-11 glue) are exactly that easy
   70% — and they'd run on hardware we already pay for.

---

## Ranked levers

### 1. Tier the model to the task (biggest, free)
- Default routines to **Sonnet 4.6** ($3/$15). Drop to **Haiku 4.5** ($1/$5) for classify /
  extract / summarize / link-check. Promote to **Opus 4.8** only for architecture, tricky
  debugging, or multi-repo reasoning.
- Rule of thumb from the field: route ~70% of calls to the cheapest *adequate* model.
- In Claude Code: pick the model per session/routine; don't leave scheduled maintenance on
  Opus 1M by default. The 1M context window especially is overkill for single-repo work.

### 2. Use prompt caching on the standing context (90% off cached input)
- Cache hits read at **0.1×** input price ($0.30/Mtok Sonnet, $0.10 Haiku). Our CLAUDE.md +
  system prompt + repo briefings are identical across runs — perfect cache targets.
- Claude Code caches automatically; for long/recurring routines enable the 1-hour TTL
  (`ENABLE_PROMPT_CACHING_1H`) so the cache survives between turns and runs.

### 3. Trim the CLAUDE.md files — they're a per-run tax (concrete, do this week)
- Current word counts (≈1.4 tokens/word): DESIGN **2,608w (~3.6k tok)**, localDNS **2,728w
  (~3.8k tok)**, MARKETING 1,445w, customers 562w, homelab 371w, azure 316w. **~8,030w total.**
- Every session in a repo loads that repo's CLAUDE.md *on every turn*; a routine scoped to all
  7 repos (like this one) carries **~11k tokens of preamble before it does any work** — paid on
  Opus.
- Fix: keep CLAUDE.md to a tight **index + invariants**, and push the prose (funnel diagrams,
  full stage tables, money-flow narrative) into README/context files Claude reads *on demand*.
  Target each CLAUDE.md under ~1k tokens. The detail isn't lost — it's just not pre-loaded.

### 4. Batch the non-interactive work (50% off, stacks with caching)
- The **Batch API** is 50% cheaper across all models and stacks with caching → a cached batch
  request can cost ~5% of a naive call.
- Fits our recurring, not-real-time jobs: monthly statement narratives (stage 06), marketing
  copy drafts, bulk lead/CRM classification. Wrong tool for interactive Claude Code chat;
  right tool for the glue (stage 11) and the statement generator.

### 5. Scope tighter, batch your asks, manage context
- Small scope beats big scope: "rewrite the login function" not "refactor auth." Less context
  in, fewer tokens, sharper output.
- Batch follow-ups into one message instead of "now fix that… now this…" — each turn re-reads
  the whole thread.
- Use `/clear` between unrelated tasks, `/recap` to resume without replaying history, and lean
  on **subagents / the Explore agent** for fan-out search so big file dumps land in a throwaway
  context instead of polluting (and re-billing) the main thread. Auto-compaction handles the
  rest.
- `.claudeignore` / `.gitignore` discipline keeps the working set small (reported ~85% context
  reduction from ignore-file hygiene alone).

### 6. Close the privacy gap before leaning on local routing (prereq for lever 2)
- **TD-14** is open: a `sensitive`-tagged task can fail over from `local-reason` to
  `cloud-overflow` (Claude cloud) because `allow_cloud=False` isn't enforced at the LiteLLM
  failover layer. Before we route real customer data through the hybrid stack, give
  `local-reason` a **local-only, fail-closed** fallback. Otherwise lever 2 quietly leaks the
  exact lookups our whole pitch promises to keep private.

---

## On the prompt that triggered this review

The request was thoughtful and self-aware (it even asked to be critiqued). Two efficiency notes:

- **It bundles ~5 open-ended questions** (token use, prompting, other AI, hybrid local, news)
  behind "ANYTHING that could help." Open scope + "search the web" + "check the news" invites
  unbounded exploration — which is itself the token cost we're trying to cut. A broad sweep
  like this is also Sonnet-grade work; it didn't need Opus 1M.
- **Tighter form for a recurring routine:** pick *one* focus per run and constrain it, e.g.
  *"Rank the top 3 token levers for our Claude Code routines this month; ≤5 sources, last 60
  days; output a 1-paragraph recommendation + a diff to one CLAUDE.md."* That yields a cheaper,
  sharper run, and a recurring routine can rotate the focus week to week.
- **Keep:** the standing instructions (CLAUDE.md, branch rules) — those are exactly the
  "don't retype the rules every time" pattern that saves tokens. The fix is to *shrink* them
  (lever 3), not remove them.

Net: the prompt isn't broken; it's a research brief running on a luxury engine with all the
lights on. Scope it, cache the standing context, and run it on Sonnet.

---

## Sources

- [Anthropic API pricing 2026 (finout.io)](https://www.finout.io/blog/anthropic-api-pricing) ·
  [CloudZero Claude API pricing](https://www.cloudzero.com/blog/claude-api-pricing/)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) ·
  [Manage costs — Claude Code docs](https://code.claude.com/docs/en/costs)
- [12 Ways to Cut Token Consumption in Claude Code (Firecrawl)](https://www.firecrawl.dev/blog/claude-code-token-efficiency) ·
  [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
  [Hybrid Cloud-Local AI Cost Optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Claude API Cost Optimization: Caching, Batching, 60% reduction (dev.to)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Claude Code Guide 2026: 25 Features (MarkTechPost)](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/) ·
  [Claude Code Subagents 2026 (Tembo)](https://www.tembo.io/blog/claude-code-subagents)
