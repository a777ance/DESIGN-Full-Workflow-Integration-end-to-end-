# AI process efficiency — how we spend tokens (and how to spend fewer)

A standing review of the **process between the operator and the AI** across the A777ance
guild: where tokens and time leak, and the concrete levers that close the gap. This is a
living doc — the model landscape shifts week to week, so it leads with a dated log
(newest-first, per house style) and keeps the durable playbook below it.

> **Scope.** "The AI" here means three surfaces: (1) Claude Code / routine sessions like
> this one, (2) the self-hosted LLM router on the t630 (`localDNS/10-ai-orchestration`),
> and (3) any direct Claude API calls the statement/automation tooling makes. The single
> highest-leverage fact: **we already run the recommended hybrid shape** (local-first via
> LiteLLM+Ollama, cloud as overflow). Most wins below are *tuning what we have*, not
> rebuilding it.

---

## Review log (newest first)

### 2026-06-20 — First pass

Triggered by the founder's standing question: *"find inefficiencies in our PROCESS between
the user and the AI; reduce token use; better prompting; leverage other AI; run hybrid
local + Claude."* Findings synthesised from current (June 2026) best-practice sources and
the authoritative Anthropic API reference, cross-checked against our live
`10-ai-orchestration/config.yaml`.

**Headline:** the architecture is right; the *settings* are leaving money on the table.
Five concrete levers, ranked by effort-to-payoff, in [The playbook](#the-playbook).

**One correction to the public commentary:** several 2026 blog posts assert "Anthropic has
no batch API." That is **false** — the **Message Batches API** runs async at **50% off**
all token usage (up to 100k requests / 256 MB per batch, results within ~1h typically). For
our non-interactive cloud work (statement copy, bulk classification, overflow that isn't
latency-sensitive) this is a free halving we are not using.

---

## The playbook

Ranked by payoff per unit of effort. Each lever cites where it applies in *our* stack.

### 1. Prompt caching on every repeated-prefix Claude call — **biggest single lever**

Cache reads cost **~0.1×** base input; the static prefix (system prompt, schema, the big
CLAUDE.md briefings, a statement template, few-shot examples) bills at up to **90% off** on
every call after the first. This is the highest-leverage cost lever in production LLM work
in 2026, full stop.

- **Where it bites us:** anything that re-sends a large fixed preamble — statement
  generation (same template + house-style rules each run), the LangGraph supervisor's
  system prompt, any classification loop over the roster.
- **The invariant that makes or breaks it:** caching is a *prefix match*. One byte change
  anywhere in the prefix invalidates everything after it. The silent killers: a
  `datetime.now()` / timestamp in the system prompt, unsorted `json.dumps()` (use
  `sort_keys=True`), a per-request UUID early in the content, or a tool list that varies
  per request. Keep the stable stuff first and frozen; put volatile content last.
- **Verify:** `usage.cache_read_input_tokens` should be non-zero on repeated calls. If it's
  zero, a silent invalidator is at work.
- **Minimum cacheable prefix is model-specific** (Opus 4.8: 4096 tokens; Sonnet 4.6: 2048).
  Shorter prefixes silently won't cache — no error, just no savings.

### 2. Stop defaulting cloud overflow to the most expensive model

`10-ai-orchestration/config.yaml` pins `cloud-overflow` (and `cloud-explore`,
`cloud-vision`) to **`anthropic/claude-opus-4-8`** — the priciest tier at **$5 / $25** per
MTok. Most overflow is not frontier-hard.

- **Tier the overflow** the same way we already tier local models. Sonnet 4.6 ($3/$15) is
  the speed/intelligence sweet spot; Haiku 4.5 ($1/$5) handles classification, extraction,
  short structured answers. The config already names these as "cheaper swaps" in a comment —
  promote them from comment to actual routes.
- Rule of thumb from the 2026 routing literature: a good router sends only ~14% of queries
  to the strong model and keeps ~95% of frontier quality. Match each request to the
  *cheapest model that clears the bar*, escalate on failure.
- `cloud-code` is already correctly on Sonnet 4.6 — extend that discipline to the rest.

### 3. Use the Anthropic Message Batches API for non-interactive cloud work — **50% off**

Anything that doesn't need an answer *this second* — monthly statement copy, bulk roster
classification, overflow research that can wait an hour — should go through Batches, not
synchronous calls. Flat 50% discount on all tokens, every Messages-API feature supported
(caching stacks on top). This pairs naturally with the nightly cron cadence we already run
for stats collection.

### 4. Tune `effort` and thinking on Opus 4.8 / 4.7

The `effort` parameter (`low` | `medium` | `high` | `xhigh` | `max`) is the main
intelligence-vs-token dial. Default is `high`. For routine/structured work, **`medium` or
`low` often matches `high`-quality output at a fraction of the tokens** — lower effort means
fewer tool calls, less preamble, terser confirmations. Reserve `xhigh`/`max` for genuinely
hard agentic runs. Leave adaptive thinking on (`thinking: {type: "adaptive"}`) rather than
disabling it — with thinking off, Opus 4.8 tends to write *longer* visible answers.

### 5. Right-size `max_tokens` and ask for brevity in the prompt

- Set `max_tokens` to the smallest value the task needs (classification: ~256). It's a hard
  ceiling; hitting it truncates and forces a costly retry, but lowballing wastes nothing.
- Output tokens cost 5× input — a "answer in N words / no preamble" instruction is the
  cheapest token cut available, and it compounds across every call.
- Note the 1M-context Claude models have **no long-context surcharge** — a 900K-token
  request bills at the same per-token rate as a 9K one, so the lever is *fewer/cheaper
  tokens*, not fear of large context.

---

## Process-level (operator ↔ AI) inefficiencies

Token math aside, the *interaction pattern* is where a lot of waste hides:

- **Front-load the spec; don't dribble it across turns.** Opus 4.8 is most efficient when
  the full task, intent, and constraints arrive in the first turn. Ambiguous prompts spread
  over many user turns make it reason more after each turn (more tokens) and sometimes
  worse. State the goal once, clearly.
- **Subagents are 7× the tokens of a single session** — each carries its own context
  window. Worth it for genuinely parallel/independent fan-out; wasteful for a single-file
  read or a sequential task. Spawn deliberately.
- **Routine sessions like this one should run cheap.** A scheduled "scan and report" job
  doesn't need `max`/`xhigh` effort or Opus on every internal step. Use local tiers or
  Haiku/Sonnet for the legwork; reserve the expensive brain for synthesis.
- **Keep the briefings frozen and cacheable.** The big `CLAUDE.md` files are re-read every
  session. As long as they don't change mid-session and aren't prefixed with volatile data,
  they cache well — another reason not to interpolate timestamps/IDs into system context.

## Leverage other AI (local-first)

We're already doing the thing the 2026 hybrid-architecture guides recommend: LiteLLM as the
front door, Ollama tiers local and privacy-preserving by default, cloud as failover. The
privacy gate (sensitive tasks pinned local before planning) is exactly right. Remaining
gaps:

- **Semantic caching:** LiteLLM's built-in caching is exact-match only. A semantic cache
  (match on *meaning*, not bytes) catches 15–30% more repeats on classification-heavy
  workloads. Candidate add-on if/when roster classification volume grows — not urgent at
  current scale.
- **The local reasoning ladder is sound:** `local-reason` (distilled R1, runs cool on the
  t630) for light work, `cloud-gpu-reason` (full R1 on a rented GPU, spun up on demand) for
  heavy — this is the right shape and already documented as a known-issue resolution. No
  change needed.

---

## Was this very prompt efficient? (the founder asked)

Honestly: **no, and that's fine for a human-typed kickoff.** It was a broad, open
brainstorm ("ANYTHING that could help… search the web… check the news"). That's the right
mode for *seeding* a standing review like this one — but as a *recurring routine* prompt it
would burn tokens re-deriving the same context every run.

The fix is to convert the open question into a **tight, cacheable routine prompt** now that
this doc exists:

> *"Re-run the AI-process-efficiency review. Read `docs/ai-cto/ai-process-efficiency.md`,
> check only what changed since the last dated log entry (new model releases, new pricing,
> new caching/routing features), append a new dated entry if and only if something material
> changed, and notify only on a material change. Otherwise stay silent."*

That version (a) names the file so the model isn't re-discovering scope, (b) bounds the web
search to deltas, (c) sets a clear silence-by-default contract so a quiet week costs almost
nothing and doesn't spam a notification. Pair it with a cheap model/effort for the scan and
escalate to Opus only when synthesising a real change.

---

## Sources

- [Token optimization 2026 — Obvious Works](https://www.obviousworks.ch/en/token-optimization-saves-up-to-80-percent-llm-costs/)
- [Prompt Caching in 2026 — Digital Applied](https://www.digitalapplied.com/blog/prompt-caching-2026-cut-llm-costs-engineering-guide)
- [LLM Cost Optimization: 5 Levers — Morph](https://www.morphllm.com/llm-cost-optimization)
- [Caching, Batching, Routing — GMI Cloud](https://www.gmicloud.ai/en/blog/llm-inference-cost-optimization-caching-batching-routing)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Model Routing 2026 — Digital Applied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Reduce Claude Code Costs 60% — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Codex vs Claude Code, June 2026 — Morph](https://www.morphllm.com/comparisons/codex-vs-claude-code)
- [A Survey on Collaborating Small and Large Language Models — arXiv 2510.13890](https://arxiv.org/html/2510.13890v1)
- Anthropic API reference (model pricing, prompt caching, Message Batches, effort/thinking) — internal `claude-api` skill, cached 2026-06-04
