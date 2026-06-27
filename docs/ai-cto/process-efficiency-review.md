# Process efficiency review — user ↔ AI token spend

**Date:** 2026-06-27 · **Author:** NARF (AI CTO), scheduled review · **Status:** findings, for founder decision

A standing question from the founder: *where is our process between the human and the
AI wasteful, and how do we spend fewer tokens for the same or better result?* This is the
first pass. It is ordered by **return on effort** — do the top items first; they are cheap
and pay back immediately. Figures are grounded in the live `localDNS/10-ai-orchestration/`
stack and current (June 2026) Claude API behaviour, not generic advice.

---

## TL;DR — the five that matter

1. **Turn on prompt caching for the big stable prefixes (`CLAUDE.md`, system, tool defs).**
   Biggest single lever. Cache reads cost ~10% of normal input; our `CLAUDE.md` files are
   18–20 KB each and reload **uncached on every session**. 60–90% off the repeated portion.
2. **Trim the `CLAUDE.md` / README prefix that loads every turn.** `localDNS/README.md` is
   67 KB (~17 K tokens). Caching makes it cheap; trimming makes it *free*. Do both.
3. **Actually route work through the dispatcher we already built.** `dispatcher.py` +
   LiteLLM exist but route nothing real yet. Sending classification/extraction/formatting to
   local Qwen and keeping Opus for hard reasoning is the documented 60–80% cut on that share.
4. **Batch the non-interactive jobs (monthly statements, `check-docs`, bulk classification)
   through the Message Batches API — 50% off, no quality loss.**
5. **The founder's own prompt is a cost driver.** "Search the web, keep up to date day by
   day, ANYTHING that could help" invites an exhaustive sweep. Scoping the ask to one lever
   with a stated target is the cheapest optimization of all (see §5).

---

## 1. Prompt caching — the highest-ROI change, currently unused

**What it is.** The Claude API lets you mark a stable prefix (system prompt, tool
definitions, a big doc) as cacheable. First call pays a ~1.25× write premium; every call
within the TTL pays ~**0.1×** for that prefix. Break-even is **two calls**.

**Why it's our #1 lever.** Caching is a *prefix match* — the cached bytes are everything up
to the breakpoint, in order `tools → system → messages`. Our every-session overhead is
exactly that shape: a large, byte-stable `CLAUDE.md` + house-style block that does not
change between turns. Measured today:

| File (loaded every session in its repo) | Size | ≈ tokens |
| --- | --- | --- |
| `localDNS/README.md` | 67 KB | ~17 K |
| `localDNS/CLAUDE.md` | 20 KB | ~5 K |
| `DESIGN/CLAUDE.md` | 18 KB | ~4.5 K |
| `DESIGN/README.md` + `workflow-context.md` | 26 KB | ~6.5 K |

Across 7 repos, every working session re-pays the full input price for its `CLAUDE.md` (and
often the README) **before any task starts**. With caching, the second turn onward pays ~10%.

**Do this:**
- In any code that calls the Claude API directly (the statement generator, future
  dispatcher cloud calls), put a `cache_control: {type: "ephemeral"}` breakpoint on the last
  stable system/doc block. Use the **1-hour TTL** for bursty sessions.
- **Audit for silent cache-busters:** never interpolate `datetime.now()`, a UUID, a
  per-session ID, or unsorted JSON into the cached prefix — one changed byte invalidates
  everything after it. Our house-style "Today's date" injection is exactly the trap; keep
  any date/volatile value *after* the breakpoint or out of the prefix.
- Verify with `usage.cache_read_input_tokens`; if it's 0 across identical-prefix calls,
  a buster is in the prefix.

> In Claude Code / web sessions the harness already caches automatically — the win above is
> for **our own API-calling code** (statement tool, dispatcher), which controls its own prompts.

## 2. Cut the always-loaded prefix itself

Caching makes the prefix *cheap*; trimming makes it *free* and also speeds the first
(uncached) turn and any cache write. Targets:

- `localDNS/README.md` at 67 KB is doing two jobs (briefing + full setup reference). The
  CLAUDE.md already says "README is the complete guide." Consider splitting rarely-needed
  setup detail into `INSTALL-NOTES.md` (already exists) so the always-read file is leaner.
- The house-style block is duplicated verbatim in all 7 `CLAUDE.md` files. It's correct to
  repeat for standalone repos, but it's ~1 KB × every session. Acceptable; flag only if we
  later centralize.
- **Principle:** the `CLAUDE.md` should be the *index*, not the *encyclopedia*. Anything a
  session reads on-demand (READMEs, schemas) doesn't need to sit in the always-loaded file.

## 3. Hybrid local + Claude — finish wiring what we designed

We are ahead of most shops here: `10-ai-orchestration/` already has LiteLLM, a local
Qwen/DeepSeek tier ladder, a rented-GPU offload, and a deterministic privacy-routing
`dispatcher.py`. The gap is that **it routes nothing real yet** ("design, not built").

Current research consensus (multiple 2026 sources): production traffic is ~60–70% simple
(classify/extract/format), ~20–30% moderate, ~10% frontier-reasoning. Routing the simple
share to local models is a **60–80% cost cut on that share** at equal quality.

**Concrete A777ance fits — route to local Qwen, not Opus:**
- Parsing a booking-form lead into CRM fields (stage 03 → 08).
- Classifying a phone-call note, normalizing an address, dedupe matching on the roster.
- Drafting routine "Handled For You" log lines from structured events.
- Doc-link sanity phrasing checks.

Keep Opus/Sonnet for: statement narrative quality, anything customer-facing and kept, and
genuinely hard reasoning. The dispatcher's privacy lock (sensitive → local-only, no cloud
fallback) is the right guardrail and should stay.

**One efficiency note on the stack itself:** the reasoning ladder is sound (don't run heavy
DeepSeek-R1 on the t630 CPU). For *cost* routing specifically, the cheapest correct default
is: local-fast for trivial, Sonnet 4.6 for most cloud work, Opus 4.8 only for the hardest —
mirroring the capability tiers already in `config.yaml`.

## 4. Batch the non-interactive jobs — 50% off

The **Message Batches API** runs the same requests asynchronously at **half price**, most
finishing within an hour. Anything not waiting on a human qualifies:
- The **monthly statement build** (stage 06) — the canonical batch job: many households, one
  shared system prefix. Combine with caching (§1) on the shared prefix for a double win.
- Bulk classification / enrichment passes over the roster.
- `check-docs` style validation sweeps if they ever call a model.

## 5. Lower-effort levers (do after the above)

- **`effort` parameter.** For mechanical/agentic work, `effort: "high"` is the sweet spot;
  drop to `low` for cheap deterministic sub-tasks. `max` only when correctness > cost.
  Lower effort = fewer tool calls, less preamble, terser output = fewer tokens.
- **Subagents for context isolation.** Fan-out reads/searches run in a separate context and
  return only the conclusion — their transcript never weighs down the main session. Use a
  cheaper model (Haiku/Sonnet) for the subagent. Don't spawn one for a single grep — the
  agent scaffolding has its own overhead.
- **`/compact` and scoped sessions.** End long sessions or compact them rather than letting
  context balloon; start a fresh session per task instead of one mega-session.
- **Context editing / compaction (API).** For our own long-running agent code, clear stale
  tool results (`clear_tool_uses`) or summarize near the window — keeps the transcript lean.
- **MCP deferred tool loading** is already the default in our harness (only tool *names*
  enter context until used) — no action, just don't undo it by force-loading schemas.
- **Code-review before commit** removes "fix the bug I just shipped" round-trips — each of
  those is a whole extra conversation.

## 6. The prompt that triggered this review (the founder asked us to critique it)

The originating prompt was, in effect: *"Find any inefficiency between user and AI; reduce
tokens; better prompting; leverage other AI; hybrid local+cloud; search the web; keep up to
date day by day; ANYTHING that could help."*

It's a good **strategic** ask but an expensive **operational** one, because:
- **Unbounded scope** ("ANYTHING") forces an exhaustive sweep — the most token-intensive
  shape of task. A scoped ask ("rank our top-3 token sinks and fix the #1") gets the same
  decision for a fraction of the spend.
- **No stated target.** Cost, latency, or quality? They trade off. Naming the target lets
  the model stop early instead of covering all three.
- **"Search the web / keep up to date day by day"** is the right instinct but, run literally
  and often, it multiplies tool calls. Best practice is to fetch current data once into a
  cached reference (this doc), then refresh on a *cadence* (monthly), not every run.
- **Withholds cheap context.** We have to *re-derive* our own token surface every time.
  Pasting the current cost/usage snapshot (or pointing at this doc) saves the rediscovery.

**A cheaper version of the same request:**
> "Using `docs/ai-cto/process-efficiency-review.md` as the baseline, has anything changed
> this month that would move our top-3 token sinks? Target: lowest cost at equal statement
> quality. Give me the single highest-ROI action and its rough saving — don't re-survey
> everything."

That reuses prior work, names the target, bounds the output, and refreshes on cadence —
which is itself the meta-lesson: **the cheapest token is the one you don't re-derive.**

---

## Recommended order of execution

1. Prompt caching on the statement generator's shared prefix (§1) + batch the monthly
   build (§4) — biggest, combinable win, touches the actual product.
2. Trim `localDNS/README.md` / lean the always-loaded `CLAUDE.md` index (§2).
3. Wire two or three real simple-tasks through `dispatcher.py` to local models (§3).
4. Adopt the scoped, cadence-based prompt pattern for these reviews (§6); refresh this doc
   monthly rather than re-running an open sweep.

*Sources: Anthropic prompt-caching & batch docs; hybrid local/cloud routing analyses
(sitepoint, mindstudio, buildmvpfast, obviousworks, 2026); Claude Code cost guides
(code.claude.com/docs/costs, firecrawl, kdnuggets, 2026). Live stack:
`localDNS/10-ai-orchestration/{config.yaml,dispatcher.py,ORCHESTRATION-BLUEPRINT.md}`.*
