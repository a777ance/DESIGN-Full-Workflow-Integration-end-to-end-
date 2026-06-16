# Process efficiency — user ↔ AI review

NARF's running review of how we spend tokens and attention working with Claude across the
A777ance repos. Newest review first (house style). Each finding has a concrete fix and a rough
impact band. This is advisory — nothing here changes a workflow until it's adopted as an ADR or
a tech-debt item.

---

## 2026-06-16 — first pass

**TL;DR.** The biggest, most concrete win is **picking the right model/effort per routine and
moving bulk, non-interactive LLM work onto the Batches API (flat 50% off)** — not squeezing
prompts. We already own a local-LLM stack (Odin/LiteLLM + the reasoning ladder) that is
underused for cost offload, gated by one open privacy bug (TD-14). `CLAUDE.md` is healthy in
size but the house-style block is duplicated 6× — a drift hazard more than a token sink. The
prompt that launched this routine is itself under-scoped; a tightened version is at the bottom.

### 1. Match the model and effort to the job — don't default everything to Opus  ·  impact: HIGH
The scheduled routines and most day-to-day edits run on Opus 4.8 ($5 / $25 per Mtok). Most of
our recurring work — link checks, status-file updates, triage, doc tidying, the CFO/CTO
state refreshes — is not Opus-class.

- Run **maintenance-class routines on Sonnet 4.6** ($3 / $15 — ~40% cheaper both ways) or
  **Haiku 4.5** ($1 / $5 — ~80% cheaper). Reserve Opus 4.8 (or Fable 5) for the *kept document*
  — customer-facing Statement copy, pricing/economics reasoning, anything where a wrong number
  is expensive.
- Set **effort** to match: `low`/`medium` for routine routines; `high`/`xhigh` only where
  correctness beats cost. Lower effort also means fewer tool calls and less preamble.
- Per-routine model selection is the single highest-leverage knob and costs nothing but a config
  line.

### 2. Use the Batches API for everything that isn't interactive  ·  impact: HIGH
Scheduled routines and the statement pipeline are, by definition, **not latency-sensitive** —
which is exactly what the Batches API is for: a flat **50% discount** on all tokens, same
features (caching, tools, vision). This applies to the *programmatic* calls in `tools/` and the
statement-generation tool, not to interactive Claude Code itself.

- Route bulk statement generation, lead classification, and any nightly LLM step through
  `POST /v1/messages/batches`.
- Stacks with prompt caching (shared system prefix across the batch) for further savings.

### 3. Put the local stack to work — it's built, it's idle  ·  impact: MEDIUM-HIGH
`localDNS` already runs LiteLLM (Odin) + Open WebUI + a reasoning ladder (local
`deepseek-r1:1.5b` → rented GPU R1 → `cloud-overflow`). Two uses that cut Claude spend:

- **Draft/summarize low-stakes internal content locally**, escalate to Claude only for the kept
  document and customer-facing copy. The honesty rule still governs what ships.
- **Prefer deterministic tools over LLM calls** wherever the task is mechanical.
  `tools/check-docs.py` is the model to copy — link/anchor validation is a *script*, not a
  prompt. The cheapest token is the one never spent. Candidates: roster schema validation,
  stats-file shape checks, statement honesty-gate (does the data file actually carry the figure
  the template prints?).
- ⚠️ **Blocked by TD-14:** a `sensitive`-tagged task can currently fail over from `local-reason`
  to `cloud-overflow` (Claude cloud). Fix the fail-closed gap **before** routing anything
  private to the local ladder, or we leak the lookups we promised to keep local.

### 4. `CLAUDE.md`: not bloated, but duplicated  ·  impact: MEDIUM (drift), LOW (tokens)
Measured: DESIGN ~3.5k tok, localDNS ~3.6k, MARKETING ~1.9k, customers ~0.7k, homelab ~0.5k,
azure-lab ~0.4k — all under the ~200-line guidance. In normal single-repo Claude Code use only
the current repo's file loads, so this is **not** a per-turn tax. But:

- The ~40-line **House style** block is byte-for-byte duplicated in 6 files. Cost is
  *maintenance and drift* (change the convention once → edit 6 files), plus a real token cost in
  multi-repo routines like this one (all files load at once).
- Fix: factor the shared block into one canonical `docs/house-style.md` and have each repo's
  `CLAUDE.md` link to it instead of inlining it. Keep each repo's *own* core inline (the
  self-contained-repo benefit is worth keeping for the repo-specific part).
- Make the **NARF/ZORT session-start reading lists conditional** — "read these only if the task
  touches CTO/CFO state." A doc-link routine shouldn't pull 4–6 portfolio files into context.

### 5. Caching reality for *scheduled* routines  ·  impact: LOW-MEDIUM
Prompt caching saves ~90% on the cached prefix but the TTL is 5 min (1 h with the beta). Daily
routines run far enough apart that the cache is **cold every run** — don't budget for cross-run
cache. It still helps *within* a long session. To keep within-session caching working: front-load
the stable prefix (CLAUDE.md, tool list), keep it frozen, and never interpolate a timestamp or
run-ID into anything before the last cache breakpoint.

### 6. Claude Code session hygiene (current best practice)  ·  impact: MEDIUM
Teams report 40–85% token reductions from: one task per session; `/compact` and `/recap` instead
of letting threads run long; narrowly-scoped requests ("refactor the booking form" not "the
whole funnel"); capping bash output length so a long test log doesn't drain context; and
spawning **Haiku subagents for fan-out search** (read-many-files exploration) while the main loop
stays on the better model.

### 7. The launching prompt is under-scoped  ·  impact: MEDIUM (this routine)
The prompt that triggered this review ("locate inefficiencies … ANYTHING that could help …
search the web if helpful") is open-ended with no definition of done, no output target, and no
budget. For an *unattended, recurring* routine that's costly: open-endedness → broad exploration
→ more tokens and less deterministic output, and "notify me" without a threshold means it can't
tell a real finding from noise. Tightened version for the schedule:

> Review our Claude usage for cost/efficiency regressions since the last run (see
> `docs/ai-cto/process-efficiency.md`). Scope: model/effort settings, the local-LLM offload, and
> any new high-token patterns. Append a dated section to that file with concrete fixes and impact
> bands. Use Sonnet at medium effort. **Notify only if** you find a new HIGH-impact item or a
> regression against a prior finding; otherwise update the file silently. Do up to ~2 web
> searches for material changes in Anthropic pricing/features; skip if nothing's changed.

That gives it a scope, an output target, a model/effort budget, and a notify-only-if rule —
turning a wide-open research task into a cheap, repeatable diff.

### Sources
- Claude Code token optimization (2026): analyticsvidhya.com, agensi.io, buildtolaunch.substack.com, mindstudio.ai
- Hybrid local/cloud routing (2026): sitepoint.com, dev.to (local router −60%), buildmvpfast.com, morphllm.com (Claude Code Router)
- Caching / context editing: platform.claude.com prompt-caching & compaction docs; mager.co
- Prompt/context engineering (2026): promptessor.com, tokenoptimize.dev, redis.io, costlayer.ai
- Pricing/models: Anthropic claude-api skill (cached 2026-06-04) — Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5; Batches API −50%.
