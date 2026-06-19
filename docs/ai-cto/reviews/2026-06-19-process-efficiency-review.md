# NARF — process & token-efficiency review — 2026-06-19

Founder asked: where are the inefficiencies in *how we work with the AI* — token use,
prompting, leveraging the local LLM, hybrid local+Claude? What does the current best
practice say (June 2026)? This is that review. It is about the **meta-process**, not the
product. Sources are listed at the bottom.

The headline: the hard part — a hybrid local/cloud router — is **already built** (LiteLLM,
stage 10). The waste is upstream of it, in how Claude Code sessions are *scoped and
prompted*, and in work we hand to an Opus session that a script or a local 3B model should
do. Five concrete levers below, ordered by payback.

---

## The seven biggest levers (cheapest win first)

### 1. CLAUDE.md is ~14.6 KB / ~3,650 tokens **per repo loaded, every turn** — and this routine loads all seven

`cat */CLAUDE.md | wc -c` = **58,444 bytes ≈ 14,600 tokens.** A CLAUDE.md loads in full
before Claude reads a single line of code or the task, on *every* turn of a session (the
current-best-practice sources are blunt about this being the silent baseline drain). The two
big ones are `localDNS` (326 lines) and `DESIGN` (295 lines).

Two specific wastes:

- **The house-style block is duplicated verbatim in all seven repos** (~30 lines ×7 ≈ 210
  lines of identical text). Per-repo it must be self-contained, but it can be *compressed* to
  ~8 lines of rules + a one-line link to the canonical copy here. Saves ~150 lines of repeated
  tokens across the portfolio.
- **This routine opened all seven repos at once** → all seven CLAUDE.md files in context (~14.6k
  tokens of project instructions) plus this 2,300-token open-ended prompt, on Opus 4.8 with a
  1M window, before any work. A process-review routine needs *one* repo (DESIGN), not seven.

**Do:** trim `localDNS` and `DESIGN` CLAUDE.md by ~30–40% (move detail to README, which is only
read on demand); compress the house-style block; **scope each routine to the minimum repos.**
Target: cut steady-state per-session overhead roughly in half.

### 2. We run every routine on Opus 4.8 at high effort — the most expensive tier — including cheap recurring jobs

Opus 4.8 is $5/$25 per MTok (fast mode $10/$50); Haiku 4.5 is $1/$5; Sonnet 4.6 is $3/$15.
That's a **5–25× spread.** Output is 5× input, so verbose review prose is the costly part.

A daily/recurring routine that *checks status* or *summarizes* does not need frontier
reasoning. Best-practice routing (and our own LiteLLM config already encodes this philosophy):
classification / extraction / summarization → Haiku-class; general coding/analysis → Sonnet;
reserve Opus for measurably-hard, multi-step work.

**Do:** set the model **per routine**, not globally. This process review and the daily
portfolio review could run Sonnet 4.6 (escalate to Opus only when a real design decision
surfaces); reserve Opus for actual code/architecture work. Use `/effort` to dial effort down
on light routines. Configure `fallbackModel` (now up to 3) so a rate-limit doesn't fail a run.

### 3. We have a hybrid router (stage 10) but Claude Code isn't using it for the cheap 60–70%

Best-practice hybrid splits are explicit: ~60–70% of requests (classify/extract/format),
~20–30% moderate, ~10% need a frontier model — and pushing the cheap bucket to local models
cuts cost 60–80%. We *built* exactly this (`local-fast` qwen2.5:3b, `local-smart` 7b,
`local-embed` for RAG, cloud as overflow) — but it serves the Open WebUI / supervisor path,
not our Claude Code routines.

Candidates to push down to the local tier (via the LiteLLM front door, `ai.home.lan:4040`)
or off the LLM entirely:
- First-pass summaries, link/anchor checks, "did this file change" diffs, draft commit
  messages, roster sanity checks → `local-fast`/`local-smart`.
- `tools/check-docs.py` already runs deterministically in CI (TD-11 resolved) — **that's the
  pattern.** Deterministic gates belong in hooks/CI/scripts, costing *zero* tokens, not in an
  Opus prompt. Keep finding work that looks like a model call but is really a `grep`.

### 4. The prompt that launched this routine is itself inefficient (founder asked us to say so)

It is open-ended and maximalist — "ANYTHING that could help… Search the web… Check the news…
Keep UP TO DATE day by day." That guarantees an unbounded, expensive run *every* time it
fires, on the most expensive model, with all repos loaded. It mixes a one-off audit with a
standing watch.

**Rewrite it as two things:**
- A **cheap, frequent** watch (weekly, Sonnet/Haiku, DESIGN repo only): "Check the Claude Code
  changelog and Anthropic pricing page since <date>. If anything changes our cost or routing
  posture, note it in one paragraph and notify. Otherwise stay silent." Tight scope, clear
  completion condition (use `/goal`), bounded output.
- A **deep, rare** audit (monthly/quarterly, Opus): the full "find every inefficiency" sweep
  this doc represents.

Prompt hygiene that applies generally: state the deliverable and a completion condition; cap
output length; name the repos in scope; put stable instructions first (preserves prompt cache,
−90% on cached input); don't restate context the CLAUDE.md already carries.

### 5. Preserve the prompt cache; summarize instead of letting context balloon

Caching cuts cached-input cost ~90% and latency ~85%, but only if the stable prefix
(system + CLAUDE.md + tool defs) doesn't change mid-session. Editing a CLAUDE.md mid-session,
or `cd`-ing the old way, busts it. New tools help: **`/cd`** moves a session without rebuilding
the cache; **Rewind → "Summarize up to here"** compresses earlier context; lowering the
auto-compact threshold (~70%) keeps long sessions from dragging a bloated window. Tool output
(not our messages) is the thing that compounds — prune it.

### 6. New capabilities (June 2026) we should adopt deliberately

- **Routines** (what this is): keep them *scoped and budgeted* per §1–§4.
- **`/usage`** breaks down what drives plan limits by skill / subagent / plugin / MCP server —
  run it to find the actual hogs instead of guessing.
- **Sub-agents** isolate context: a fan-out search returns only the conclusion to the parent,
  not the file dumps — cheaper than reading everything inline. (Background chains now nest 5
  deep; "dynamic workflows" orchestrate many.) Good fit for our cross-repo sweeps.
- **`--safe-mode`** / **`enforceAvailableModels`** / version-pinning for reproducible,
  governed routine runs.
- **Batch API** (−50%) and prompt caching for any *programmatic* Claude use we add later.

### 7. Cross-check: the one privacy-cost item already tracked (TD-14)

The hybrid-routing efficiency story has a known hole: a `sensitive`-tagged task pinned to
`local-reason` can **fail *open* to `cloud-overflow` (Claude cloud)** if the local model is
down — `config.yaml`'s fallback chain isn't gated by the dispatcher's `allow_cloud=False`.
Already logged as **TD-14 (P1)**; the one-line fix is a local-only fallback chain. Flagging
here only because "route the cheap stuff local" (§3) makes this path hotter — close TD-14
before leaning on local routing harder.

---

## What's already right (don't "fix" these)

- The LiteLLM hybrid with local-default + cloud-overflow and graceful fallback — this is the
  textbook 2026 architecture; we're ahead of the curve on the hard part.
- Deterministic doc-integrity in CI (TD-11) — the correct "don't pay a model to do a script's
  job" instinct.
- Reasoning-ladder split (light distill local, heavy R1 on rented GPU) — right call; don't run
  a heavy R1 on the t630 CPU.

## Recommended next actions

1. **Trim + scope** (§1): shrink the two large CLAUDE.md files, compress the house-style block,
   scope routines to one repo. *Biggest steady-state saving, lowest effort.*
2. **Re-model the routines** (§2, §4): split this routine into a cheap weekly watch + a rare
   deep audit; set per-routine model and effort.
3. **Run `/usage`** (§6) to measure the real drivers before optimizing further.
4. **Close TD-14** (§7) if we intend to route more through local tiers.
5. **Find one more script-able check** to move from prompt → hook/CI (§3).

---

## Sources (June 2026)

- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude API Pricing 2026: Opus 4.8, Sonnet 4.6, Haiku 4.5 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Anthropic Claude API Pricing 2026 — CloudZero](https://www.cloudzero.com/blog/claude-api-pricing/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Effective harnesses for long-running agents — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Prompt Engineering Best Practices 2026 — Thomas Wiegold](https://thomas-wiegold.com/blog/prompt-engineering-best-practices-2026/)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
