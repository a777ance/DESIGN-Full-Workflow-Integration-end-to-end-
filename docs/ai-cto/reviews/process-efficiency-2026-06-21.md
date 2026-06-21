# Process efficiency review — the user↔AI loop (2026-06-21)

NARF (AI CTO) review. Scope: how we *work with* Claude across the A777ance repos —
token spend, prompting, and where to offload to cheaper/local models. Time-based;
newest entries lead per house style.

**TL;DR.** We already do the hard part right (a tiered LiteLLM router with a local
reasoning ladder exists in `localDNS/10-ai-orchestration`). The cheap wins left are:
(1) shrink the CLAUDE.md files we load into *every* session, (2) push monthly
statement generation onto the Batch API (50% off) with prompt caching, (3) route
private-customer work to the local box, never the API, and (4) scope our prompts
(including the one that triggered this review). Estimated blended saving on
AI-touched work: **50–75%**, with no loss of quality on the work that matters.

---

## 1. The biggest leak: CLAUDE.md is loaded on every turn, and it's huge + duplicated

Every Claude Code session ingests the repo's `CLAUDE.md` as context on **every turn**.
Ours are large (DESIGN ≈ 300+ lines; localDNS comparable), and the
**House style: ordering & typography** block is copied verbatim into all 7 repos.
That's the same ~25 lines re-tokenized in every session, in every repo, forever.

What to do:
- **Target < 200 lines per CLAUDE.md** (industry guidance; keeps the cached prefix
  small and cheap). Keep only what a session needs *every* time; move the rest to
  referenced docs (README, workflow-context) that Claude reads on demand, or to a
  **Skill** that loads only when relevant.
- **De-duplicate the house-style block.** Put it once (e.g. a `STYLE.md` in a shared
  spot or each repo's README) and have each CLAUDE.md link to it in one line. The
  rules don't need to sit in the model's context on every keystroke — they need to
  be *findable* when writing docs.
- This protects **prompt caching**: a big, frequently-edited CLAUDE.md invalidates
  the cached prefix on every change. A small, stable one stays cached (~0.1× input
  cost on reads vs full price).

## 2. Monthly statements → Batch API (50%) + prompt caching (~90% on the shared part)

Statement generation (06) is the textbook batch workload: **non-latency-sensitive,
high-volume, one job per household, run monthly**. Today CLAUDE.md cites "about a
penny a home."

- The **Message Batches API** processes asynchronously at **50% of standard price**,
  up to 100k requests/batch, most finish within an hour. The monthly run does not
  need real-time responses — it qualifies.
- The statement *template, system prompt, and house-style/honesty rules* are
  identical across every household in a run. Put them in a **cached prefix** and only
  the per-home data file varies → the shared prefix bills at ~0.1× after the first
  call.
- Combined, "a penny a home" plausibly becomes **~half a penny**, and the honesty
  rule (never print a number the box didn't measure) is better enforced by the
  deterministic data-file check than by the model anyway (see §5).

## 3. Route private-customer work to the LOCAL box — cost *and* the privacy invariant

The `customers` repo is **private and must stay private** (real names, real figures).
We also own a t630 with a working local LLM stack and a LiteLLM router
(`localDNS/10-ai-orchestration`, with `local-reason` = deepseek-r1:1.5b on CPU).

- Sensitive customer data should resolve to **local models by default**, never the
  Claude API. This is the same instinct as the Unbound DNS split ("never hand the
  forward-path your private lookups") applied to LLM calls — and it's free.
- Reserve the Claude API for the public/non-sensitive surface (localDNS docs, the
  Statement *template*, marketing copy, this kind of cross-repo reasoning).

## 4. Apply the router discipline to *agentic* work, not just chat

Hybrid local/cloud routing cuts LLM cost **60–80%** in production because ~60–70% of
requests are simple (classify/extract/format), ~20–30% moderate, and only ~10% need a
frontier model. We have the ladder; extend it to the jobs we actually run:

| Task | Send to |
| ---- | ------- |
| Doc-link checking, schema validation, lint, the `check-docs.py` gate | **Deterministic code — no LLM** (already true for check-docs; keep pushing here) |
| Classification, extraction, short rewrites, statement data prep | **Local (deepseek-r1:1.5b) or Haiku 4.5** ($1/$5 per MTok) |
| Routine doc edits, summaries, single-file changes | **Sonnet 4.6** ($3/$15) |
| Hard cross-repo reasoning, architecture, long-horizon agentic runs | **Opus 4.8** ($5/$25) — keep the good model for the work that needs it |

Don't downgrade the hard work to save pennies; *do* stop paying Opus rates for a
link check.

## 5. Prefer deterministic gates over asking the model

`tools/check-docs.py` is the right pattern — link integrity is code, not a prompt.
Extend it:
- A **schema validator** for `08-client-list-and-crm/schema.md` / `roster.json`.
- A **"numbers are real" linter** for statements: assert every figure on a statement
  traces to a measured field in the home data file (enforces the honesty rule cheaply
  and reliably). The model shouldn't be the thing we trust to not hallucinate a
  number on a document people keep.
Every check we move from prompt → code is tokens we never spend again.

## 6. Knobs we should be setting (current Claude API, June 2026)

- **`effort`** (`output_config.effort`): defaults to `high`. Drop to `low`/`medium`
  for routine work; reserve `high`/`xhigh` for genuinely hard tasks. Lower effort =
  fewer tool calls, less preamble, terser output.
- **Context editing** (`clear_tool_uses_*`) and **compaction** (`compact_*`) on long
  agent runs — clear stale tool results / summarize history so we stop re-paying for
  context we no longer need. Claude Code's `/clear` and `/compact` are the
  interactive equivalents; use `/clear` between unrelated tasks.
- **Verify caching is actually happening:** `usage.cache_read_input_tokens` should be
  non-zero on repeated runs. If it's zero, a silent invalidator (a timestamp, a
  churning CLAUDE.md, unsorted JSON) is breaking the prefix.
- **Skills over fat prompts:** move specialized, occasionally-needed instructions
  into Skills that load on demand instead of carrying them in context always.

## 7. Scheduled-routine hygiene (this review is a routine)

Routines are great leverage but quietly expensive if open-ended:
- **Scope each routine to a specific signal** and have it **notify only when the
  signal fires** — silence when all's well. (This run notifies because it was asked
  to produce findings; a health-check routine should stay quiet on a clean day.)
- Pin routine prompts to **cheaper models** where the task allows; a daily "are there
  new auth errors" check does not need Opus.
- Keep routine prompts **narrow and structured** so the agent doesn't fan out.

## 8. On the prompt that triggered this review

The triggering prompt was, candidly, an anti-pattern for cost — and we asked it to
critique itself, so: it was broad and open-ended ("ANYTHING that could help… Search
the web… Check the news… Keep UP TO DATE"). Open-ended scope invites long
exploration and maximal token spend, and "anything" gives the agent no stopping
condition. A scoped version gets a better answer *and* costs less:

> *Review how we use Claude across the A777ance repos for cost. Cover, in order:
> (1) CLAUDE.md size/caching, (2) batch + caching for monthly statements,
> (3) local-vs-API routing for private data, (4) model-tier routing for agentic
> tasks. For each, give the concrete change and an estimated saving. Search the web
> only to confirm current pricing/limits. Deliver a single committed markdown report
> ≤ 2 pages; notify with a one-paragraph summary.*

Same intent, bounded scope, explicit deliverable, explicit stop — cheaper and
sharper. General prompting rules that follow from this: state the deliverable and its
size; give an ordered checklist instead of "anything"; bound web use to what you need
to confirm; say when to stop.

---

## Recommended order of operations

1. **Trim + de-duplicate CLAUDE.md** across all 7 repos (biggest per-session win,
   zero risk). — *tech-debt candidate*
2. **Local-first routing for `customers`** (privacy invariant + free). — *config in
   `10-ai-orchestration`*
3. **Batch + cached prefix for the monthly statement run.** — *stage 06 / localDNS
   statement tool*
4. **Deterministic linters** for schema + statement-number honesty.
5. **Set `effort`/caching/skills defaults**; tighten scheduled-routine prompts.

## Sources (current as of 2026-06-21)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Context engineering: memory, compaction, tool clearing (Claude Cookbook)](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Effective harnesses for long-running agents — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Internal: Claude API reference (Batch API 50%, caching economics, `effort`, context editing/compaction), `localDNS/10-ai-orchestration` reasoning ladder.
