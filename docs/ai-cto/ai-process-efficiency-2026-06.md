# AI process efficiency review — 2026-06-20

NARF (AI CTO) review, requested by the founder: where are we wasting tokens / money
between the human and the AI, and what's the better way? Researched against current
(June 2026) best practice and our actual setup. Recommendations are ranked by
**impact ÷ effort**; do the top three first.

> One-line answer: the single biggest waste isn't how we *prompt* — it's that these
> scheduled routines run on **Opus 4.8 (1M)** with **all seven repos' CLAUDE.md files
> loaded every run**, most of which the routine doesn't need. Right-size the model and
> scope the context and we cut the recurring bill by a large multiple before changing a
> word of any prompt.

---

## Top wins (do these first)

| # | Change | Effort | Est. impact |
| - | ------ | ------ | ----------- |
| 1 | **Right-size the model per routine.** Don't run watch/triage routines on Opus 4.8 — and never on Fast mode ($10/$50). Use Sonnet 4.6 ($3/$15) for read-and-report, Haiku 4.5 ($1/$5) for pure status checks. Reserve Opus for routines that actually write code or make hard calls. | Low (a per-routine model setting) | **3–10× on recurring routine cost.** Fast-mode Opus is 10×/Haiku on input, 10×/Haiku on output. |
| 2 | **Scope each routine to the repos it needs.** This run loaded ~8,600 words of CLAUDE.md (≈12k tokens) across 7 repos every time. A homelab-health routine needs `localDNS` only; a receivables routine needs `DESIGN`+`customers`. Fewer repos in session = smaller fixed per-run tax. | Low (session scope) | **~50–85% context reduction** per run (matches the documented `.claudeignore` discipline numbers). |
| 3 | **Slim the CLAUDE.md files to lookup tables; link the rest.** They average ~2,000 words (localDNS 2,728, DESIGN 2,608) and are read *every* session. Best practice: CLAUDE.md is a pointer table, not a brain dump. Move the full deploy-path table, full known-issues, and verification blocks into README/linked docs and leave a one-line pointer. | Medium (one-time edit per repo) | **Recurring**: every session, every routine, forever. |

---

## The token math, specific to us

A scheduled routine pays a **fixed tax before it does any work**: the harness system
prompt + every loaded repo's CLAUDE.md + the task description. For this run that fixed
preamble is the bulk of input tokens, and it repeats on *every* scheduled fire.

Two things make that expensive for us specifically:

- **The model.** Opus 4.8 is $5/$25 per M tokens (Fast mode $10/$50). Sonnet 4.6 is
  $3/$15, Haiku 4.5 $1/$5. A watch-routine reading logs and writing a note does not
  need Opus reasoning — that's paying Opus rates to read a dashboard.
- **The breadth.** All six non-stub CLAUDE.md files carry the **same ~250-word
  house-style block, copy-pasted verbatim**. We re-read that block six times per
  multi-repo session. It's the clearest single instance of redundant context we own.

Prompt caching does **not** rescue scheduled routines the way it rescues an interactive
session: the cache TTL is 5 min (1 hr extended), so routines spread across the day start
cold every time. Caching helps *within* a long session, not *across* sleepy cron fires.
That's why for routines the lever is **model + scope**, not caching.

---

## Better prompting (and a critique of the prompt that launched this run)

The request that started this routine was enthusiastic but **unscoped** — and unscoped
is the most expensive kind of prompt, because the model explores everything. Current
best practice (Anthropic + the 2026 context-engineering consensus): a prompt is a
**contract** — role, success criteria, constraints, output format, and an
uncertainty rule. The sweet spot is **150–300 words of *clear spec*, not longer.**

What the launching prompt did that cost tokens:

- **"ANYTHING that could help… Search the web if helpful… Check the news."** Open-ended
  scope + open-ended research = maximal fan-out. No budget, no stop condition.
- **No output contract.** Didn't say *where* to put the answer or *what shape* it should
  take, so the agent has to decide (and a wrong guess means rework).
- **No scope boundary.** "Our PROCESS" could mean one repo or all seven; the safe
  reading is "read everything," which is the expensive reading.

A tighter version of the same request (paste-ready):

> *"Review our AI usage for cost waste. Scope: the scheduled-routine setup + the LiteLLM
> router config in localDNS. Deliver a ranked list of the 5 highest-impact savings with
> rough $ or % each, written to `DESIGN/docs/ai-cto/`. Use web search only to confirm
> current model prices. Skip anything you can't tie to a number. ~1 page."*

Same answer, a fraction of the wandering. **General rule for our routines:** name the
scope, name the deliverable and its location, cap the research, and give permission to
say "nothing to report" (so a quiet day ends cheaply instead of inventing work).

Other prompting practices worth standardizing across the repos:

- **Put the ask at the top or bottom**, never buried mid-prompt — measured >30% accuracy
  drop for instructions stranded in the middle of long context.
- **Give explicit permission to be uncertain** ("say so rather than guess") — fewer
  hallucinated fixes, fewer correction round-trips.
- **Batch related asks into one turn.** Every follow-up re-reads the whole thread; three
  separate "also do X" messages pay the context tax three times.

---

## Hybrid local + cloud — we're most of the way there

The LiteLLM router (`localDNS/10-ai-orchestration/config.yaml`) is genuinely good: local
Ollama tiers as the privacy-preserving default, a reasoning ladder, a deterministic
privacy gate that pins sensitive work local, and cloud as overflow only. That already
matches the 2026 "intelligent routing layer" pattern that's documented to cut LLM cost
60–85%. Keep it. Two gaps to close:

- **Claude Code itself doesn't use that router.** The agent doing dev work (and these
  routines) always goes straight to cloud Opus. The local stack is for the chat
  UI / supervisor, not the coding agent. Opportunity: use the **local tier for cheap
  pre-processing** — summarizing logs before a routine reads them, drafting first passes,
  building the RAG index over the repos — and reserve the Claude API for the reasoning and
  the writes. Let the t630 do the janitorial reading; pay Opus only for judgment.
- **The $489-GPU payback math is real but only if Claude spend is the driver.** Current
  guidance: a hybrid GPU buy pays back in ~5–8 months at $60–100/mo of API spend. If our
  routine spend climbs, routing the heavy-reasoning offload (the `cloud-gpu-reason` tier
  we already scaffolded) onto an owned/rented GPU beats per-token Opus for sustained
  batch work. Track monthly API spend; that number is the trigger.

---

## Product-side cost levers (for ZORT too — these scale with customers)

These don't touch our dev process; they cut the **per-statement** cost as we add homes:

- **Batch API for statement generation.** Statement builds are async, monthly, and
  uniform — the textbook Batch API case: **50% off, no quality penalty.** The generator
  already runs at ~a penny a home; batching halves the AI portion.
- **Prompt caching on the statement system prompt / template.** The template and
  instructions are identical across every home in a run — cache them once and pay 10% on
  the repeat. **Stacking batch + caching is documented at 95%+ effective savings.** At
  scale this is the difference between a penny and a fraction of a penny per home.

---

## New 2026 capabilities worth adopting

- **Skills + subagents for context isolation.** Delegating a noisy task (reading a big
  log, a wide search) to a subagent keeps its output *out* of the main context — the
  result comes back without the session weight. Documented at 25–40% token savings vs.
  monolithic prompts. Good fit for our routines: a "scan all repos" step should be a
  subagent, not inline.
- **Context editing + the memory tool** (Anthropic, public beta Apr 2026). Lets a
  long-running agent compact its own working context and persist learnings across
  sessions — Anthropic measured a **39% lift on long-horizon agentic tasks** from the
  combination. Most relevant to the LangGraph supervisor (Odin) and to any routine we let
  run long.
- **`/recap` over replaying a session.** Resuming a routine with a recap instead of
  re-reading the whole transcript saves the resumption tax.

---

## What we're already doing right (don't undo)

- The router's **privacy-first local default** with a hard gate on sensitive work — keep
  it; it's both cheaper and the right call for customer data.
- **"Make the network dull," one source of truth, honesty of the kept document** — these
  reduce rework, which is the cheapest token saving of all.
- **The reasoning ladder** (don't cook the CPU with a big R1) — correct and well-reasoned.

---

## Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Savings 2026: OpenAI vs Anthropic — AI Cost Check](https://aicostcheck.com/blog/ai-prompt-caching-cost-savings)
- [Claude Opus 4.8 Pricing 2026 — Finout](https://www.finout.io/blog/claude-opus-4.8-pricing-2026-everything-you-need-to-know)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — BuildMVPfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Local LLM vs Claude for Coding: $500 GPU Benchmark [2026] — Kunal Ganglani](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [Prompting best practices — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Context Engineering Guide 2026 — The AI Corner](https://www.the-ai-corner.com/p/context-engineering-guide-2026)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Skills and Subagents Reduce Prompt Bloat — newline](https://www.newline.co/@Dipen/claude-skills-and-subagents-reduce-prompt-bloat--f2920804)
- [Context engineering: memory, compaction, and tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Anthropic's Memory Tool Reframes How We Build Agents — S3P Studios](https://s3p-studios.com/blog/anthropic-memory-tool-context-engineering-agents/)
