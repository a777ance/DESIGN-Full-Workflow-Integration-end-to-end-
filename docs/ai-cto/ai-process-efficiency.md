# AI process efficiency — human↔AI token & cost review

NARF memo, 2026-06-19. Scope: how we spend tokens working with Claude across the
portfolio — the automated agents (`tools/ai-cto.py`, `tools/ai-cfo.py`), interactive
Claude Code sessions, and the Odin LLM stack in `localDNS`. Grounded in the actual
code, not generic advice. Findings are ranked by saving-per-effort. Web sources at the
bottom; figures verified against the [Claude pricing](https://www.finout.io/blog/anthropic-api-pricing)
in effect June 2026 (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5 per 1M in/out;
cache read 0.1×, cache write 1.25×; Batch API 50% off).

This file is time-based at the top (newest review first) and reference below.

---

## TL;DR — the five levers, ranked

1. **Tier the model and effort in NARF/ZORT.** Today every mode of `ai-cto.py`/`ai-cfo.py`
   runs `claude-opus-4-8` at default (high) effort. Most modes are summarise-and-log work,
   not architecture reasoning. → biggest saving, one config change.
2. **Route NARF/ZORT through our own Odin router**, not the bare Anthropic client — so the
   dispatcher's tiering, local models, and spend cap actually apply to our two heaviest API
   consumers. (Fix TD‑14 first — privacy fallback gap.)
3. **Stop the cached prefix changing daily.** `Today is {TODAY}` lives inside the cached
   system block, so the cache is cold-written every single run. Move it past the breakpoint.
4. **Instrument cache hits.** We assume caching works; we have zero visibility. After the
   March 2026 caching-inflation incident, log `usage.cache_read_input_tokens` every run.
5. **Trim the append-only re-read payload** (`portfolio.md`/`decisions.md`/`metrics.md`) and
   prune the duplicated governance block in the NARF system prompt.

Everything below is grounded; two things I'd have flagged generically turned out **not** to
be problems here — see "What's already right."

---

## What's already right (don't touch)

- **`ai-cto.py` prompt-caching is correct.** The system array puts the large portfolio-state
  block last with `cache_control: {"type": "ephemeral"}`, so tools + both system blocks cache
  together and the multi-iteration tool loop reads from cache on calls 2..N. Good placement.
- **The `reviews/` logs and the `CLAUDE.md` files are NOT loaded into the agent context.**
  `CONTEXT_FILES` reads the four hub docs + four spoke `context.md` files only. So the growing
  review logs are a disk-hygiene matter, not a token cost, and the big `CLAUDE.md` files only
  cost tokens in *interactive* Claude Code sessions, not the automated agents.
- **`check-docs.py` and the deterministic checks use zero tokens.** Keep pushing mechanical
  work (link checks, schema/roster validation, metric arithmetic) into code, never the model.
- **The deterministic dispatcher** (`localDNS/10-ai-orchestration/dispatcher.py`) routes with a
  rule table and no LLM — the right design. The Odin reasoning ladder + cloud-GPU offload is
  ahead of most homelab setups.

---

## Channel A — the automated agents (NARF / ZORT)

These two scripts are our largest, most predictable API spend. They run on a schedule
(weekly NARF, daily ZORT) and in CI.

### A1 · Tier the model and effort by mode  — **highest saving**
`run_agent()` hard-codes `model="claude-opus-4-8"` and never sets `effort`, for every mode.
But `review` / `priorities` / `end-session` are read-summarise-log work; only `issues` and
genuine architecture/finance calls need Opus-grade reasoning. Industry split is ~60–70% of
agent requests being simple ([hybrid routing data](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).

- Route the routine modes to `claude-sonnet-4-6` (40% cheaper per token) with
  `output_config={"effort": "low"}` or `"medium"` — lower effort means fewer thinking tokens
  and terser output, which is exactly what a daily log pass wants.
- Keep `claude-opus-4-8` at `high` (or `xhigh`) only for `issues` and ad-hoc architecture work.
- Net: the daily ZORT run and weekly NARF review drop to roughly half their current cost with
  no quality loss on the work they actually do.

### A2 · Daily cold cache — move `TODAY` out of the cached prefix
`SYSTEM_PROMPT` interpolates `Today is {TODAY}`. Caching is a prefix byte-match, so the
prefix differs every calendar day → guaranteed cold write each run, and it kills any chance of
a cross-run hit on the multi-pass `NARF_ITER` super-runs the same day. Put the date in the
**user** message (or a post-breakpoint block) and keep the system prefix byte-identical. Then a
`"ttl": "1h"` on the cache block lets same-day re-runs read instead of re-write.

### A3 · Prune the duplicated governance block
`SYSTEM_PROMPT` carries **two** governance sections ("## Governance" then "## Governance — HARD
RULES") that largely restate each other. It's cached so the marginal token cost is small, but
redundant, conflicting-looking instructions measurably dilute instruction-following on Opus
4.8, which follows the prompt literally. Collapse to one. While there: Opus 4.8 does better with
goal+constraints than long enumerated rule-lists — the metamodernism stance is fine, the
double governance is not.

### A4 · Trim the re-read payload
`portfolio.md`, `decisions.md`, and (for ZORT) `metrics.md` are loaded in full every run and
grow append-only — and `metrics.md` repeats the two standing RED blockers verbatim ~10 days
running. These files are **not** cached across runs (daily cadence + the A2 date issue), so
every redundant line is paid for on every run. Collapse "standing blockers" into one
current-state block that gets rewritten in place, and archive resolved `decisions`/old metric
rows to a `…/archive/` file. Smaller payload = fewer input tokens every single run.

### A5 · Instrument cache + spend
Neither script logs `usage`. Add a one-line print of `cache_read_input_tokens` /
`cache_creation_input_tokens` / `input_tokens` per call. This (a) proves caching is live and
(b) is our only defence against a recurrence of the [March 2026 caching-inflation bug](https://buildtolaunch.substack.com/p/claude-code-token-optimization),
where two Anthropic-side bugs silently inflated token use 10–20×.

---

## Channel B — interactive Claude Code (founder in a repo)

This is where the big `CLAUDE.md` files cost tokens — they're read at every session start and
there is no cross-session cache (5-min TTL goes cold between sittings).

- **Split each `CLAUDE.md` into a lean session brief (<100 lines) + a linked full reference**
  read on demand. `localDNS/CLAUDE.md` (≈326 lines) and `DESIGN/CLAUDE.md` (≈295 lines) are
  the worst offenders. Smaller stable prefix = fewer tokens and faster first response.
- Use `/clear` when switching to unrelated work, `/recap` on resume instead of replaying the
  transcript, and scope requests narrowly — all per the
  [Claude Code cost docs](https://code.claude.com/docs/en/costs) and
  [2026 token-reduction guide](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage).

---

## Channel C — leverage our own hybrid stack (Odin)

We built a privacy-first local/cloud router and then bypass it: NARF/ZORT call
`anthropic.Anthropic()` directly. Point them at the Odin LiteLLM front door
(`ai.home.lan:4040`, OpenAI-compatible) and we get, for free: model tiering (A1) enforced
centrally, the option to run the cheap summarise/log passes on local `qwen2.5` on the t630,
and a single spend cap + log (Hoard-Warden). [Hybrid routing routinely cuts cost 60–80%](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
by keeping routine work local and reserving the API for the ~10% that needs frontier reasoning.

> ⚠️ **Blocked on TD‑14.** Before routing financial/customer-touching agents through Odin,
> fix the privacy fallback gap: a `sensitive` task can currently fail over from `local-reason`
> to `cloud-overflow` (Claude cloud). Routing ZORT through Odin while that's open could push
> real revenue figures to the cloud tier. Fail closed first.

## Batch API — partial fit
The Batch API is 50% off and ideal for non-interactive jobs ([Anthropic pricing](https://www.finout.io/blog/anthropic-api-pricing)).
Our agents are non-interactive *but* multi-turn (the `read_file` tool loop), which the batch
endpoint doesn't model. So batch fits the **one-shot** pieces — a single-pass digest, statement
copy generation — not the agentic loop. Worth it for those; don't force the agent loop into it.

---

## Prompting notes (Opus 4.8 specifics)
- 4.8 **narrates more and asks more** by default. For NARF/ZORT add a silence-default and grant
  autonomy on minor choices, or we pay for "Want me to also…?" round-trips.
- 4.8 is **more conservative reaching for tools/subagents** — make `read_file`'s description
  prescriptive about *when* to consult deeper files.
- Set `effort` explicitly (see A1); don't leave everything at the high default.

---

## On the prompt that triggered this routine
The instruction was effective in intent but token-loose for something that *runs on a schedule*:
open-ended "ANYTHING… anything you could possibly think of… search the web… check the news"
forces a broad, expensive fan-out every run. For a recurring routine, tighten to fixed scope +
fixed output + scoped search, e.g.:

> "Review AI token/cost efficiency across the portfolio (agents, interactive sessions, Odin).
> Output: findings ranked by saving-per-effort, each with the file/change and an estimated
> saving. Search the web only for changes **since the last run** in: Claude pricing/caching,
> model tiering, local/cloud routing. Notify only if a finding is actionable."

That cuts input tokens every run and produces a more decision-ready output. (The double
"Thanks!" is harmless — just N× over a routine.)

---

## Sources
- [How to Reduce Claude Code Token Usage (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization / March 2026 caching incident](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [Hybrid Cloud-Local LLM Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Anthropic API Pricing 2026 — caching & batch](https://www.finout.io/blog/anthropic-api-pricing)
