# NARF — review — 2026-06-18 — process & token efficiency

A themed review (not the standard portfolio pass): *where is the user↔AI process
wasting tokens, where can prompting improve, and what's the real hybrid local/cloud
play given our hardware?* Researched against current (June 2026) best practice and
grounded in our actual stack (LiteLLM router, the reasoning ladder, the t630, the
multi-repo CLAUDE.md set). Findings ordered by return-on-effort, biggest first.

---

## TL;DR

Yes — there's real waste, and most of it is in **what we re-send every turn**, not in
how we phrase things. The three highest-ROI fixes are free and need no box access:

1. **Trim & de-duplicate the CLAUDE.md set** — biggest standing token sink.
2. **Give this routine a memory** — it re-researches from zero every run today.
3. **Stop running Opus-1M for triage** — route by task; reserve the big model for code.

The honest hybrid-local finding: our architecture is right, but **the t630 cannot run a
coding-grade local model** — so "do coding locally" is the wrong target. The real
local/cloud win is routing *bulk, non-interactive* jobs to cheap cloud (Batch API +
caching), not asking a Carrizo iGPU to do Claude's job.

---

## 1. CLAUDE.md bloat + duplication — the #1 standing token cost (P1, free to fix)

Our six `CLAUDE.md` files total **~1,040 lines (~9–11k tokens)** that load *before any
work* in a session. In a multi-repo session like this one, several load at once and get
re-sent on **every turn**. Two specific problems:

- **Verbatim duplication.** The entire "House style: ordering & typography" block
  (~30 lines) is byte-identical in all six repos. The "three repos, one business" table
  is repeated in three. We pay for the same paragraphs many times over.
- **Detail that belongs in linked files.** `DESIGN` (295 lines) and `localDNS`
  (326 lines) carry full tables (deploy paths, the nftables checklist, known-issues) in
  the *always-loaded* file. A 5k-token CLAUDE.md costs 5k tokens on turn 1 and on turn 200.

**Fixes (in priority order):**
- Within a repo, factor the house-style block into `docs/house-style.md` and pull it in
  with a CLAUDE.md `@docs/house-style.md` import — Claude Code resolves `@path` imports,
  so the text lives once and loads on demand instead of inline every turn.
- Move the big reference tables (deploy paths, nftables deploy checklist, the full
  known-issues grids) out of CLAUDE.md into the README/INSTALL-NOTES they already
  duplicate, and leave a one-line pointer. CLAUDE.md should be the *briefing*, not the
  manual — target each under ~120 must-load lines.
- Cross-repo we can't import, so the lever there is "trim to a tight read-this-first."

Quantified: trimming ~40% off the always-loaded set saves ~4k tokens **per turn, every
session** — it compounds harder than any one-off prompt tweak.

## 2. This routine has no memory — it re-researches cold every run (P1, free to fix)

Today's run did 5 web searches from scratch and will do so again tomorrow. No
compounding, and notifications fire on a full re-scan rather than on what actually
changed. Anthropic shipped the **memory tool** (persist across sessions) and the broader
**context-management** primitives in 2026 precisely for this.

**Fix — make the committed brief the memory:** each run reads the *previous* review file
first and reports **only deltas** (new model releases, price/feature changes, a config
that drifted). Same pattern the daily NARF review already follows via `portfolio.md`. This
cuts research tokens dramatically and turns notifications into signal-only — ping the
founder only when something genuinely moved, stay silent otherwise.

## 3. Model & effort routing — don't run Opus-1M for triage (P1, free to fix)

This routine (read the news, summarize) and most of the daily portfolio pass do not need
Opus 4.8 / 1M context. Current guidance is consistent: Sonnet handles most work, Haiku
handles bounded triage, Opus is for multi-file reasoning and synthesis.

**Fixes:** in Claude Code use `/model` and `/effort` to drop a research/triage run to
Sonnet (or Haiku for the pure web-scan), and set `model: haiku` on subagents doing simple
fetch/summarize. Escalate to Opus only when a run will actually edit code across files.
Thinking tokens bill as output — for routines that don't need deep reasoning, cap with
`/effort` or `MAX_THINKING_TOKENS`.

## 4. Hybrid local/cloud — the architecture is right; the hardware target is wrong (P2)

We already scaffolded the correct shape: LiteLLM as the gateway (`10-ai-orchestration`),
the reasoning ladder (`local-reason` → `cloud-gpu-reason` on a rented GPU via Tailscale →
`cloud-overflow`), and the Odin/LangGraph supervisor. Good bones. But two honest
corrections to the "do more locally" instinct:

- **The t630 cannot run a coding-grade local model.** 2026 benchmarks ("Qwen2.5-Coder-32B
  handles 70–80% of daily coding") assume a 24 GB GPU (RTX 4090 class). Our box is an AMD
  Carrizo iGPU with 16 GB shared RAM — it runs `deepseek-r1:1.5b` "cool" and nothing near
  coder-32B. And **multi-file repo reasoning — our actual Claude Code workload — is the
  single thing local models are worst at.** So "move coding off Claude onto the t630" is
  not on the table; don't chase it.
- **Where local genuinely fits:** bounded, single-shot, low-stakes — the sensitivity
  routing decision itself, quick Q&A, draft text, classifying a lead, summarizing one
  statement. Keep those local for privacy and to keep the box earning its keep.

**The hybrid win we're actually leaving on the table** is *cheap cloud for bulk*, not
local-for-coding. Route high-volume, non-interactive jobs — statement copy generated "at a
penny a home," lead classification, the `MARKETING` NotebookLM-bridge summarization —
through LiteLLM to a cheap model with **Batch API (–50%)** + **prompt caching (–90% on
repeated context)**. That's where the documented 40–85% routing savings are real for us.
Frontier-quality is wasted on traffic that never needed it.

- **Guardrail:** any routing we build must **fail closed**. This is exactly TD-14 — a
  `sensitive`-tagged task can currently fail *open* to `cloud-overflow` if the local model
  is down. A privacy-routing layer that leaks on failure is worse than none. (See TD-14;
  not re-litigating here.)

## 5. Prefer deterministic tools over LLM calls (P3, ongoing discipline)

The cheapest token is the one we don't spend. `tools/check-docs.py` (now in CI, TD-11) is
the model: a recurring check that *could* have been an LLM review pass is a script
instead. Extend the habit — e.g. a house-style/link linter rather than a review turn.
Prompt caching is automatic in Claude Code; the actionable part is keeping the cached
prefix **stable** (don't reorder CLAUDE.md mid-session) and `/clear`-ing between unrelated
tasks so each starts a clean cache instead of dragging stale context.

---

## 6. On *this* prompt (you asked)

As a one-off message to a human it's fine and friendly. As a **scheduled, unwatched
routine** it's inefficient for reasons worth naming:

- **Unbounded scope** — "ANYTHING that could help / anything you could possibly think of"
  invites maximum fan-out on every run with no stopping criterion. Costly and repetitive.
- **No defined output** — nothing tells the run *where* findings should land, so they'd
  evaporate into a transcript nobody reads. (That's why this brief exists as a file.)
- **No memory directive** — guarantees a cold re-research each run (see §2).
- **Mixed register** — a research task and a "critique yourself" meta-task bundled
  together; cleaner as two narrower routines.
- The two "Thanks!"/politeness tokens are trivial — **not** worth optimizing, and not the
  problem. The scope/output/memory gaps are.

**A tighter version to paste into the routine config:**

> Weekly, on Sonnet. Read the newest file in `docs/ai-cto/reviews/` for what we already
> know. Web-search only for what's *changed since then* in: Claude/Anthropic model
> releases & pricing, Claude Code token features, and local/hybrid-LLM routing. Append a
> dated delta-only brief to `docs/ai-cto/reviews/` (newest-first), commit to the working
> branch. Notify the founder **only if** something actionable changed (new model, price
> drop, a feature that cuts our spend); otherwise finish silently. Keep it to one page.

---

## What I changed / recommend

- **Wrote** this brief to the reviews log (the routine now has a durable output + a seed
  for the memory pattern in §2).
- **Recommend, no box needed, this week:** (1) factor the house-style block into a
  `@`-imported file and trim CLAUDE.md tables out to READMEs; (2) switch this routine to
  delta-only + Sonnet; (3) when we build LiteLLM routing for bulk jobs, fail closed and
  use Batch + caching — and *don't* target the t630 for coding.
- **Cross-refs, not re-litigated:** TD-14 (fail-closed) and TD-11 (deterministic checks).

### Sources (June 2026)
- Anthropic — Prompt caching (–90% reads), Memory tool, Batch API (–50%), context
  management: platform.claude.com/docs, code.claude.com/docs/prompt-caching & /costs
- Claude Code token optimization guides (KDnuggets; buildtolaunch; analyticsvidhya, 2026)
- Hybrid local/cloud routing & RouteLLM (sitepoint; buildmvpfast; digitalapplied, 2026)
- Local-LLM-vs-Claude coding benchmarks (kunalganglani; dev.to; mindstudio, 2026)
