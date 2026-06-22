# AI process efficiency audit — token spend & the human↔AI loop (2026-06-22)

Scope: how A777ance actually spends Claude tokens — the scheduled agents (NARF/ZORT),
the Claude Code sessions, and the prompts that drive them. Findings are ordered by
**ROI (biggest saving, least effort first)**. Pricing checked against current rates
(June 2026): Opus 4.8 `$5/$25`, Sonnet 4.6 `$3/$15`, Haiku 4.5 `$1/$5` per MTok;
Batch API −50%; prompt-cache hit −90% (write +25%). Sources at the bottom.

> **TL;DR.** We run our two most expensive things — NARF and ZORT — on the most
> expensive model, every day, whether or not anything changed, while a local-LLM
> routing gateway we already built (`localDNS/10-ai-orchestration/`) sits unused for
> our own agents, and our prompt-cache markers *cost* money on single-pass daily runs
> instead of saving it. Fixing the top five items below cuts agent token spend an
> estimated **70–85%** with no loss of quality, mostly in a single afternoon.

---

## The big five (do these)

### 1. Right-size the model per mode — stop paying Opus for note-taking
`tools/ai-cto.py` and `tools/ai-cfo.py` both hardcode `model="claude-opus-4-8"` for
**every** mode. But most modes are routine: `metrics`, `priorities`, `review` (the
daily default), and `end-session` are read-summarize-update work, not deep
architecture. Industry data is consistent: **60–80% of agent turns run identically on
a cheap model**, and right-sizing cuts per-run token spend **40–70%**.

| Mode | Today | Proposed | Why |
| ---- | ----- | -------- | --- |
| `review` (daily default) | Opus 4.8 | **Sonnet 4.6** | Summarize + update; Sonnet is plenty, −40% |
| `metrics` / `end-session` | Opus 4.8 | **Haiku 4.5** | Mechanical read/write, −80% |
| `priorities` | Opus 4.8 | **Sonnet 4.6** | Ranking with rationale |
| `forecast` / `issues` / multi-pass super-runs | Opus 4.8 | **Opus 4.8** (keep) | Genuine reasoning earns the price |

Make `model` a per-mode lookup (a dict keyed by mode), overridable by an env var.
~10 lines in each tool. **Single highest-ROI change in this repo.**

### 2. Don't run the agent when nothing changed
Both workflows fire on `cron` daily, unconditionally — ~730 Opus sessions/year that
often review repos with **zero new commits since the last pass**. Gate the run: if
`git log --since="last run"` across hub + spokes is empty, exit before the API call
(post a one-line "no change" to the step summary). On a slow week that alone removes
most of the spend. Keep a weekly "review even if quiet" floor so nothing rots silently.

### 3. Route through our own gateway — we built it and don't use it
`localDNS/10-ai-orchestration/` runs **LiteLLM + a reasoning ladder** (local
`deepseek-r1:1.5b` on the t630 for light work → cloud GPU/Opus for heavy). NARF and
ZORT bypass it entirely and call `anthropic.Anthropic()` direct. Point them at the
LiteLLM endpoint and the "did anything material change / classify this diff" triage
step runs **local at ~$0**, escalating to Opus only for real decisions. This is
exactly the hybrid pattern the industry now recommends (60–80% cost cut) — and we
already own the infrastructure. *Caveat: keep money/PII context (ZORT) on the Claude
API or the on-box model only; never route customer data to a third-party gateway.*

### 4. Use the Batch API for the scheduled runs
NARF/ZORT are not latency-sensitive — nobody is watching at 04:00 ET. The **Batch API
is a flat −50% on every token** with a 24h SLA we never need. Submit the daily review
as a batch job. Stacks with #1 (Sonnet-via-batch ≈ Haiku list price).

### 5. Fix the prompt-cache — right now it *loses* money
Both tools mark the portfolio block `cache_control: {"type": "ephemeral"}` (5-min TTL).
A **single daily pass never gets a cache hit** (the cache is long gone 24h later), so
we pay the **+25% write premium** on that block every day for **zero** −90% hits. Cache
only pays off across calls *close in time*. Fix:
- **Single-pass runs:** drop `cache_control` — stop paying the write premium for nothing.
- **Multi-iteration super-runs** (`iterations > 1`): keep caching — the within-session
  tool-use loop and successive passes *do* hit it. Consider the 1-hour cache there.

---

## Context bloat (helps every Claude Code session, not just the agents)

Every Claude Code web session loads the repo's `CLAUDE.md` up front. Ours are large
and partly redundant — this is paid on *every* session before any work begins.

- **`CLAUDE.md` sizes:** localDNS ~20 KB (~5k tok), DESIGN ~18 KB (~4.5k tok),
  MARKETING ~11 KB. Combined across repos ≈ **8,000 words / ~10k+ tokens** of standing
  instructions.
- **The house-style block is duplicated verbatim in 6 files** (already flagged in
  `RECOMMENDED-CHANGES.md` #1). localDNS `CLAUDE.md`↔`README.md` repeat the
  services/ports/peers/DNS-split tables (flagged #2). Every duplicated line is re-read
  every session. **Nominate one canonical copy; cross-reference the rest.**
- **Giant docs pulled into context on demand:** localDNS `README.md` is **67 KB**,
  `network-context.md` **46 KB**, `INSTALL-NOTES.md` **26 KB**. Fine as references, but
  a vague ask ("improve the docs") makes Claude scan them. Keep `CLAUDE.md` as a thin
  router that *points* at these rather than restating them.
- **NARF and ZORT load overlapping context** (both read localDNS + MARKETING context
  files). If they ever share a process, load the common block once.

**Action:** trim each `CLAUDE.md` toward "map, not manual" — the DESIGN one is already
close. Target: keep standing instructions under ~3k tokens/repo; push detail into
linked files that load only when relevant.

---

## Prompting — the human↔AI loop

- **Specific beats broad.** "Improve the codebase" / "anything that could help"
  triggers wide file scanning (expensive); "add input validation to `auth.ts`" lets
  Claude work with minimal reads. Reported savings on focused tasks: **40–70%**.
- **Start sessions on Sonnet, escalate to Opus only when a task is genuinely hard.**
  The same right-sizing logic as the agents, applied by hand at the CLI (`/model`).
- **Delegate verbose work to subagents** (running tests, fetching docs, grepping logs)
  so the noisy output stays out of the main thread and only a summary returns — but
  only when the saved clutter beats the subagent's startup cost.
- **Lean on `/context` and `/compact`** to watch and reclaim the window instead of
  letting it auto-compact mid-task.

### On *this* request's own prompt
Asked directly, so: **the prompt that launched this audit is itself an example of the
broad-scan anti-pattern.** "Locate inefficiencies… Anything you could possibly
think of… ANYTHING that could help… Search the web… Check the news" is open-ended on
several axes at once, which maximizes tokens (wide repo scan + open-ended web research)
for a deliverable that's hard to bound. It worked here because the surface is small,
but as a *recurring* routine it will get expensive and drifty. Tighter versions that
keep the value:

> *"Once a month, re-check our agent model/caching/batch choices in `tools/*.py`
> against current Claude pricing; flag only what changed since last audit and the
> single highest-ROI fix."*

That scopes the web search to one thing (pricing deltas), scopes the repo read to two
files, and produces a diff-shaped answer instead of an essay. Run it **monthly, not
daily**, and run the audit agent itself on Sonnet.

---

## What's already good (keep)

- `cache_control` is *present* (the instinct is right — just mistuned for daily cadence).
- `max_tokens=4096` is a sane cap, not unbounded.
- The reasoning-ladder infra in localDNS is exactly the right architecture — it just
  needs to be *pointed at our own agents*.
- `check-docs.py` runs in plain Python in CI (no tokens) — the right tool for a
  deterministic check. Don't "AI-ify" things a script already does.

---

## Suggested order of work

1. Per-mode model map in `ai-cto.py` / `ai-cfo.py` (#1) — biggest cut, ~1 afternoon.
2. Drop `cache_control` on single-pass; keep on super-runs (#5) — trivial, stops a leak.
3. Skip-if-unchanged git gate in both workflows (#2).
4. Batch API submission for scheduled modes (#4).
5. Route triage through LiteLLM, money/PII staying on-box/Claude only (#3).
6. Dedupe house-style + localDNS tables (`RECOMMENDED-CHANGES.md` #1–2); slim CLAUDE.md.
7. Re-scope this audit as a tight monthly routine on Sonnet (see above).

Estimated combined effect on agent token spend: **−70 to −85%**, no quality loss on the
decisions that matter (those still go to Opus).

---

## Sources (June 2026)

- [Claude API pricing — Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [Prompt Caching Deep Dive: cut Anthropic costs by 90% — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Anthropic API Pricing 2026: caching, batch & optimization — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Hybrid Cloud-Local LLM architecture guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM auto-routing docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- [7 ways to reduce Claude Code token usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code token optimization (2026 guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
