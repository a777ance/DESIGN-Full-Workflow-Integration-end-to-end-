# AI process efficiency — review & recommendations

_Author: NARF (AI CTO) · Date: 2026-06-19 · Status: review log (newest-first)_

A standing review of how we spend tokens and effort working with Claude across the
A777ance repos, plus a current read on best practice (the field moves weekly — re-check
dated claims). Scope: the **process** between the human and the AI, not the product.

**Bottom line.** The single biggest, most concrete win is sitting in front of us: every
session injects **~14.6K tokens of `CLAUDE.md`** before we type a word. Everything else
(caching, model routing, batch, context editing) is real but secondary. Fix the briefing
files first, turn on prompt caching second, route models third.

---

## 1. The big one: `CLAUDE.md` bloat — ~14.6K tokens/turn, mostly wasted

Measured 2026-06-19 across the repos that carry a briefing file:

| Repo | chars | ~tokens |
| ---- | ----: | ------: |
| `localDNS` | 20,472 | ~5,100 |
| `DESIGN-…` (this repo) | 17,987 | ~4,500 |
| `MARKETING` | 10,660 | ~2,700 |
| `customers` | 4,135 | ~1,000 |
| `claude-code-homelab` | 2,896 | ~700 |
| `Azure-lab` | 2,294 | ~600 |
| **Total** | **58,444** | **~14,600** |

That whole block is re-sent on **every turn** of **every** session, whether or not the
task touches it. It is also the *least* compressible part of the context because it's
hand-written prose we keep adding to. Industry guidance converged in 2026 on a hard rule:
a bloated `CLAUDE.md` (5,000+ tokens) measurably shrinks the model's effective working
context, and the fix is **progressive disclosure** — keep the always-loaded file small and
stable, push the rest into files loaded on demand. One widely-cited writeup reports ~15K
tokens/session recovered (≈82% less always-on context) by moving from "everything in
`CLAUDE.md`" to a skills/`@file` architecture.

**What to do (in priority order):**

1. **Cut each `CLAUDE.md` to a navigation page.** Target ≤ ~1,500 tokens: what the repo is,
   the 3–5 non-negotiable rules, and a table of "for X, read `@path`". Move the stage maps,
   deploy-path tables, known-issues logs, and house-style essay into the files they already
   link to. The model pulls them with `@file` only when the task needs them. localDNS and
   this repo are the two worst offenders and the highest-value cuts.
2. **Stop repeating the house-style block verbatim in all 7 files.** It's identical prose
   pasted into every repo (~600–800 tokens each). Keep the canonical copy in one place and
   reference it; the duplication buys nothing and is re-injected per repo.
3. **Don't open 6 repos in one session when the task touches one.** Each added repo's
   briefing is pure overhead for an unrelated task. Scope the session to the repo in play.

This is the change with the best effort-to-saving ratio and it needs no new tooling.

---

## 2. Prompt caching — turn it on for anything programmatic

For any code we write that calls the Claude API directly (the `localDNS` LLM router work,
future statement-generation tooling), prompt caching is the standard 60–90% input-cost cut.
Current economics (verified against the Anthropic SDK reference, 2026-06):

- **Cache read ≈ 0.1×** the normal input price. **Cache write = 1.25×** (5-min TTL) or
  **2×** (1-hour TTL).
- Break-even: **~2 reads** within a 5-min window, **~3 reads** for the 1-hour TTL.
- **Minimum cacheable prefix is model-specific** and a common silent failure: **Opus
  4.8/4.7/4.6 = 4,096 tokens**, **Sonnet 4.6 = 2,048**, Sonnet 4.5 = 1,024. A 3K-token
  prompt caches on Sonnet but *silently won't* on Opus — no error, just no savings.
- Caching is a **prefix match**: any byte change anywhere in the prefix invalidates
  everything after it. Keep the stable stuff (system prompt, tool list) first and frozen;
  put volatile content (timestamps, per-request IDs, the actual question) last. A
  `datetime.now()` or unsorted `json.dumps()` in the system prompt silently kills the cache.
- Verify with `usage.cache_read_input_tokens`; if it's 0 across identical-prefix requests,
  a silent invalidator is at work.

Note this is the API knob, separate from the Claude Code subscription we use interactively —
but the same discipline (small stable prefix) is exactly what point 1 above buys us there.

---

## 3. Hybrid local + cloud — we already have the skeleton; finish wiring it

We are further along here than most: `localDNS` stage 10 already runs **LiteLLM (port
4040) + Open WebUI** with a reasoning ladder (`local-reason` = deepseek-r1:1.5b on the t630
CPU for light work; `cloud-gpu-reason` = full R1 on a rented GPU; `cloud-overflow` as
fallback). The 2026 hybrid-routing playbook says exactly this: an intelligent layer routes
by **(a) data sensitivity, (b) task complexity, (c) availability**, sending routine/private
work local and hard work to the frontier API. Documented results: 60–80% cost cuts; one
fintech case went $47K→$8K/mo.

Concrete next steps that fit our stack:

- **Route by task, not by habit.** Classification, extraction, log-summarizing, "tidy this
  paragraph", commit-message drafting → local model or **Haiku 4.5** ($1/$5 per MTok).
  Reserve **Opus 4.8** ($5/$25) for genuinely hard reasoning/agentic work, **Sonnet 4.6**
  ($3/$15) as the high-volume middle. Don't reach for the most expensive model by default —
  but never silently downgrade a correctness-critical task to save pennies.
- **Keep private lookups local.** This aligns with the repo's own privacy invariant (don't
  leak personal data to third parties) — sensitivity-based routing is a privacy control as
  much as a cost one.
- **The honesty rule applies to the model too:** a local model hallucinating a statement
  figure is worse than a slightly pricier cloud call. Route statement-number generation to
  the strongest available model and keep the "only print what the box measured" gate.

Model IDs (current, 2026-06): `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`,
`claude-fable-5` (most capable, $10/$50 — only for the hardest long-horizon work).

---

## 4. Batch API — 50% off everything non-interactive

Any job that isn't latency-sensitive should go through the **Message Batches API**: a flat
**50% discount** on all token usage, up to 100K requests / 256MB per batch, results within
~1h (24h max), retained 29 days. Candidates in our world: monthly bulk statement-copy
generation, re-summarizing a backlog of "Handled For You" logs, classifying/enriching the
master list (08). If it can wait an hour, it should be batched.

---

## 5. Long-session hygiene — context editing, memory, subagents

For long agentic runs (the kind these routines do), three native features cut the slow
context creep:

- **Context editing** (`clear_tool_uses` / `clear_thinking`) clears stale tool outputs and
  thinking blocks from the window without summarizing. Anthropic's own eval: **84% token
  reduction over a 100-turn run**, plus it enables runs that would otherwise hit the limit.
- **Memory tool** — persist learnings to a `/memories` directory across sessions instead of
  re-establishing context each time. Pairs well with our "one source of truth" rule.
- **Subagents return condensed 1–2K-token summaries** instead of dumping their whole
  exploration into the main context. For "search across all repos" work, fan out to
  subagents and keep only the conclusions — which is exactly how this review was produced.
- Interactively: `/compact` when a thread gets long; cap tool-output size; use `@file`
  instead of pasting; don't let one mega-thread accumulate dead weight.

---

## 6. Critique of the prompt that triggered this review

The triggering prompt was effective at intent but token-inefficient in shape, and it's
worth naming because we'll write many like it:

- **"ANYTHING that could help… search the web… check the news… leverage other AI"** is an
  open-ended fan-out. It invites broad, expensive exploration and a sprawling answer. A
  tighter version names the surfaces to consider and the output wanted, e.g.: *"Audit our
  Claude usage for token waste. Cover: (1) the per-session context we inject, (2) prompt
  caching, (3) local-vs-cloud routing given our LiteLLM stack. Verify current pricing/limits
  against Anthropic docs. Output a prioritized list with rough $/token impact."* Same answer,
  a fraction of the wandering.
- **Front-load the constraint, not just the goal.** Models weight the first and last ~10%
  of a prompt most. "Reduce token use" buried in a paragraph of enthusiasm lands softer than
  it would as the opening line plus a closing "prioritize by impact."
- **Give it permission to be selective.** "Survey everything" produces a survey. "Give me the
  top 3 by impact and skip the rest" produces a decision. For recurring routines especially,
  ask for a ranked shortlist, not an encyclopedia.
- The redundant sign-off lines ("Thanks!", the restated meta-question) are harmless but, at
  scale across many prompts, are the same kind of small constant overhead as the duplicated
  house-style block — worth trimming out of habit, not worth agonizing over.

This is not a criticism of asking broadly when you genuinely want breadth — it's that breadth
is the expensive mode, so spend it deliberately.

---

## Priority / impact summary

| # | Action | Effort | Saving | Where |
| - | ------ | ------ | ------ | ----- |
| 1 | Slim every `CLAUDE.md` to a nav page; progressive disclosure | Low | ~10K+ tok/turn, every session | all repos |
| 2 | De-duplicate the house-style block | Low | ~0.5–0.8K tok/repo/turn | all repos |
| 3 | Scope sessions to the repo in play | None | avoids unrelated briefings | habit |
| 4 | Prompt caching on direct-API code | Med | 60–90% input cost | localDNS stage 10 |
| 5 | Task-based model routing (local/Haiku/Sonnet/Opus) | Med | 60–80% on routed work | localDNS stage 10 |
| 6 | Batch API for non-interactive jobs | Low | 50% flat | 06, 08 |
| 7 | Context editing / memory / subagents on long runs | Med | up to ~84% on long sessions | tooling |

---

## Sources (2026, recheck — field moves weekly)

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic API — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [Reduce Claude Code token usage by 90% (Medium, Apr 2026)](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Context Engineering Beyond CLAUDE.md: The 5-Layer Hierarchy — Pixelmojo](https://www.pixelmojo.io/blogs/context-engineering-ai-coding-agents-beyond-claude-md)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization Guide (2026)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Claude Prompt Engineering Best Practices 2026 — Prompt Builder](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026)
- Model IDs / pricing / caching rates / batch / context-editing facts cross-checked against the bundled `claude-api` skill reference (cached 2026-06-04).
