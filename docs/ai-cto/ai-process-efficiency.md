# AI process efficiency — the user↔AI loop

How we spend tokens and attention working *with* Claude across the seven repos, and where
that spend is wasteful. Scoped to the **process** (how a session is shaped, what it loads,
which model runs it), not to any one feature. Findings are ranked by impact ÷ effort.
Figures verified against the live repos on 2026-06-27.

The discipline we already apply to the customer's network — *make it dull, measure the quiet,
never pay for what the box didn't measure* — we do **not** yet apply to our own AI spend.
This doc closes that gap.

---

## TL;DR — the five that matter

1. **Every session pays a fixed "boot tax" before any work happens** — up to ~10 mandatory
   doc reads (NARF's 4 + ZORT's 6) plus a 295-line CLAUDE.md, whether the task is a one-line
   fix or a refactor. This is the single biggest, most-repeated waste. **(P1, low effort)**
2. **The house-style block is copy-pasted verbatim into 6 of 7 CLAUDE.md files.** One edit =
   six edits, and the model re-reads it on every repo switch. Factor it to one canonical file.
   **(P1, low effort)**
3. **We own a hybrid local/cloud LLM router and barely use it for our own work.** The t630
   reasoning ladder (stage 10) can absorb the mechanical 80% — link-checking, commit-message
   drafting, lead classification — at ~zero marginal cost. *Blocked on TD-14 (fail-open privacy
   bug) for anything sensitive.* **(P1, medium effort)**
4. **The statement pipeline is a textbook Batch-API job and runs at full price.** Non-interactive,
   high-volume, deadline-tolerant → 50% off. "A penny a home" becomes half a penny. **(P2, low effort)**
5. **The scheduled "find inefficiencies" routine is itself inefficient** — it loads all 7
   project CLAUDE.md files + a very large skill on every fire. Scope each fire to one repo or
   one dimension. **(P2, low effort)**

---

## 1. The session boot tax (P1)

**What it costs.** Two standing instructions fire on *every* session:

- NARF (CTO): read `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md` — 4 files.
- ZORT (CFO): read `portfolio.md`, `decisions.md`, `metrics.md`, `runway.md`, `budget.md`,
  plus `MARKETING/docs/ai-cfo/context.md` — 6 files.

That is up to **10 file reads + a 295-line / ~2,600-word CLAUDE.md** loaded *before the first
useful token*, regardless of task. A one-line typo fix pays the same boot tax as a migration.
Anthropic's own guidance is to keep `CLAUDE.md` under ~200 lines; ours is 295 and growing.

**Fix (cheap, high-leverage):**
- Make the session-start reads **conditional, not unconditional**: "Read the ZORT docs *when the
  task touches money*; read the NARF docs *when the task touches architecture or cross-repo
  status.*" Most sessions touch neither.
- Trim `CLAUDE.md` toward the 200-line target. The stage map, funnel diagram, and verification
  walkthrough are reference material — move the long-form parts into the files they already link
  to (`README.md`, `workflow-context.md`) and leave CLAUDE.md as the index it claims to be.
- This is pure win: the same information stays one hop away, but it loads *on demand* instead of
  *on every turn*.

## 2. Duplicated house-style block (P1)

The "House style: ordering & typography" block (~30 lines: reverse-chron, Z→A, reversed-blocks,
Gill Sans MT) is present **verbatim in 6 of 7 CLAUDE.md files** (all but Chronikomicon, which has
none). Costs:
- **Maintenance:** one rule change = six synchronized edits (and a seventh when Chronikomicon gets
  a CLAUDE.md). Drift is inevitable.
- **Tokens:** the model re-reads the identical block every time it switches repos.

**Fix:** keep one canonical copy (it already conceptually lives here, in the portfolio hub) and
have each repo's CLAUDE.md carry a one-line pointer — "House style: see
`DESIGN-…/docs/house-style.md`" — instead of the full block. `tools/check-docs.py` already
validates cross-file links, so the pointer is safe.

## 3. Use the hybrid router we already built (P1, medium)

We have what most teams pay consultants to design: LiteLLM (stage 10) with a local Ollama
reasoning ladder on the t630 and a rented cloud GPU on demand. External benchmarks put hybrid
local/cloud routing at **53–80% cost reduction** by running the cheap 80% locally and reserving
Claude for the hard 20%. We are not yet applying this to *our own* AI work.

Tasks that should route to the local model (deterministic, low-sensitivity, low-judgment):
- Running and parsing `tools/check-docs.py` output
- Drafting commit messages from a diff
- Lead/household classification (stage 02/08), tagging, dedup
- First-pass doc linting (house-style conformance checks)
- nftables stats summarization (stage 06 collect)

Reserve Claude (Opus for hard reasoning, **Sonnet for most coding, Haiku for classification** —
right-size, don't default to Opus) for architecture, customer-facing copy, and anything needing
real judgment.

> ⚠️ **Gate:** TD-14 is open — `local-reason` has a cloud fallback that can leak a `sensitive`-tagged
> prompt to `cloud-overflow` (Claude cloud) if the local model is down. **Do not route real customer
> data through the local path until TD-14 is fixed (fail closed).** Mechanical, non-sensitive tasks
> (link-checking, commit drafting on non-secret diffs) are safe to route today.

## 4. Batch API for the statement pipeline (P2)

The monthly statement run (stage 06) and any bulk classification (leads, households) are the ideal
Batch API profile: **non-interactive, high-volume, tolerant of up to ~24h latency.** The Batch API
is **50% off** every model, and it stacks with prompt caching (shared system prompt across all
households) for **>90% combined** savings on the cacheable portion. "About a penny a home" becomes
roughly **half a penny a home** — and statements are already a batch job in spirit (one nightly cron).
This is a code change in the generator, not a process change, but it belongs on the roadmap.

## 5. Prompt-caching hygiene (P2)

Claude Code caches automatically, but our cross-repo workflow fights it:
- **Switching repos** swaps the CLAUDE.md → invalidates the system-prompt cache every switch.
  Batching work by repo (finish in localDNS, *then* move to DESIGN) keeps the cache warm.
- **Never interpolate volatile data** (dates, run IDs) into CLAUDE.md or session-start docs — one
  byte change invalidates the whole downstream prefix. Today's CLAUDE.md files are static; keep them
  that way. (Cache read ≈ 10% of base input; a 5-min-cache write ≈ 1.25×, so the break-even is two
  reads — trivially met within a single session.)
- For long bursty sessions with gaps, the 1-hour cache TTL (2× write, but survives the gap) pays off.

## 6. Subagents and session compaction (P2)

- **Use a subagent for exploration** (broad file searches, log dumps, cross-repo sweeps) so the
  verbose output stays in the subagent's context and only the conclusion returns to the main thread.
  Our repos are doc-heavy — this is a good fit.
- **Don't** subagent trivial shell/git ops — the prompt + tool-definition overhead exceeds the
  saving.
- **Compact after exploration:** once the relevant files are identified, compact away the false
  leads before continuing. Scope prompts narrowly ("fix the login function in `auth.ts`", not
  "refactor auth").

## 7. The house style imposes a real, ongoing tax (P3 — decision, not a bug)

Reverse-chronological logs, Z→A alphabetization, and reversed walkthrough blocks are a deliberate
brand choice, and that's legitimate for customer-facing surfaces. But they cut against the grain of
how the model (and a human skimmer) naturally reads, and *every* doc edit now carries a re-sort step.
For the **internal docs the AI reads constantly** (ai-cto/ai-cfo logs, tech-debt, decisions), the
brand value is zero and the friction is real.

**Suggestion (record as an ADR either way):** consider exempting machine-read internal logs from the
reversed conventions, or at minimum acknowledge the cost so it's a chosen trade rather than an
unexamined default. Not urgent; flagging for honesty.

---

## On the prompt that triggered this routine

The triggering prompt is **good** — it scopes the target (the user↔AI process), explicitly grants
web search, asks for current best practice, and even asks the AI to critique the prompt itself. Keep
all of that. Two weaknesses worth fixing so this routine earns its keep:

1. **"ANYTHING that could help… Check the news"** is unbounded. Every fire then re-derives the whole
   landscape from scratch and re-loads all seven CLAUDE.md files plus a large skill (this run did
   exactly that — the inefficiency-hunting routine is one of the most token-heavy sessions we run).
   **Fix:** scope each fire to **one repo or one dimension** ("this week: caching hygiene in
   localDNS") and have it read *this doc* first, so it builds on prior findings instead of restarting.
2. **No success metric.** "Find inefficiencies" has no finish line. **Fix:** track one number —
   e.g. tokens/session or cache-read ratio — in `docs/ai-cfo/metrics.md`, and let the routine report
   the delta. Then "all quiet" is a real, legible state and the routine can stay silent on a good week
   (which is the point of a routine).

A tighter prompt: *"Once a week, pick one repo. Read `docs/ai-cto/ai-process-efficiency.md`, then
check that repo's CLAUDE.md and session-start load against it. Report only new waste or regressions,
with the token estimate. If nothing changed, stay silent."*

---

## Sources

External best practice, current as of 2026-06:
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Anthropic prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid AI Strategy Guide — 50% Cost Reduction (2026) — Oflight](https://www.oflight.co.jp/en/columns/hybrid-ai-cloud-local-llm-cost-reduction-2026)
- [Run Claude Code with local agents using LiteLLM and Ollama — Medium](https://medium.com/@kamilmatejuk/run-claude-code-with-local-agents-using-litellm-and-ollama-ab88869cbd00)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Deep Dive — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)

API facts (caching economics, batch 50%, model tiers) verified against the bundled `claude-api`
reference; current model tier is Opus 4.8 ($5/$25 per MTok), Sonnet 4.6 ($3/$15), Haiku 4.5 ($1/$5).
