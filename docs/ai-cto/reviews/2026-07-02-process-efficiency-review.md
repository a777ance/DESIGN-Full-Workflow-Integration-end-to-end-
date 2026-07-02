# NARF — process-efficiency review — 2026-07-02

**Question from the CEO:** find inefficiencies in *our process* — the loop between the human
and the AI. Where can we cut tokens? Better prompting? Leverage other AI / a local-LLM +
Claude hybrid? Keep it current.

Scope note: this is a **meta-review of how we use Claude**, not a portfolio/tech-debt review.
Numbers below are measured against the live repos today; web claims are cited and dated (all
current as of 2026-07). Bottom line up front: **the single biggest lever costs nothing to pull
and is under our control — the context we load on every turn.**

---

## What's actually true right now (measured)

- **We load ~14.6k tokens of `CLAUDE.md` into every session before any work happens.**
  Measured across the six repos rooted at `/home/user`:

  | File | Lines | Chars | ≈ tokens |
  | ---- | ----: | ----: | -------: |
  | `localDNS/CLAUDE.md` | 326 | 20,472 | ~5,100 |
  | `DESIGN-…/CLAUDE.md` | 295 | 17,987 | ~4,500 |
  | `MARKETING/CLAUDE.md` | 214 | 10,660 | ~2,700 |
  | `customers/CLAUDE.md` | 80 | 4,135 | ~1,000 |
  | `claude-code-homelab/CLAUDE.md` | 75 | 2,896 | ~700 |
  | `Azure-lab/CLAUDE.md` | 50 | 2,294 | ~600 |
  | **total** | **1,040** | **58,444** | **~14,600** |

  Anthropic's own guidance is **keep `CLAUDE.md` under ~200 lines**
  ([Claude Code costs docs](https://code.claude.com/docs/en/costs)). Two of our files
  (`localDNS` 326, `DESIGN` 295) are well over. When a session is rooted at `/home/user`
  (as scheduled routines are), **all six load at once** — the whole 14.6k — even for a task
  that touches one repo.

- **Prompt caching softens this but does not erase it.** Claude Code caches the stable prefix
  automatically; cached reads run at **~10% of input price**, writes at 1.25× — savings up to
  ~90% on the repeated part ([Anthropic prompt caching](https://claude.com/blog/prompt-caching)).
  But the cache has a **5-minute TTL** and is re-written on every new session. Our pattern —
  **many short scheduled runs** (daily NARF + ZORT, plus this one) — is the worst case: each
  run pays the *write* cost of 14.6k, rarely amortizes it, and never hits a warm cache from the
  previous day's run.

- **The daily routines re-derive stable facts every run.** The 2026-07-01 review literally says
  TD-14 was *"confirmed a third time against the live config."* Re-verifying an unchanged fact
  daily is real, repeated token spend for zero new information.

- **We already own a local-LLM + Claude hybrid — and it currently fails *open* to cloud.**
  `localDNS/10-ai-orchestration` runs LiteLLM with a local reasoning ladder (deepseek-r1:1.5b on
  the t630) + Claude cloud tiers. TD-14 (open, flagged three reviews running): a task pinned to
  `local-reason` falls back to `cloud-gpu-reason → cloud-overflow → claude-opus`. So today the
  "local/cheap" path silently spends **cloud** tokens whenever the local model is down or cooled
  out — which is its normal state. **Our hybrid isn't saving what we think it's saving.**

---

## Top actionable items (highest leverage first)

**1. Stop rooting sessions at `/home/user`; root them in the one repo the task touches.**
This is the biggest single cut and it's free. Rooted in `localDNS`, a session loads ~5.1k of
`CLAUDE.md`, not 14.6k — a **~65% cut** in fixed per-session context. For the scheduled
routines, `cd` into the target repo (or pass the repo path) instead of the portfolio root.
Only the portfolio-hub routine that genuinely spans repos needs more than one file.

**2. Trim the two oversized `CLAUDE.md` files under 200 lines.** `localDNS` (326) and `DESIGN`
(295) carry full tables (deploy-path map, Unbound drop-in table, the entire nftables deploy
checklist) that belong in README / context files loaded **on demand**, not on every turn.
`CLAUDE.md` should be the *briefing* — stable rules + pointers; the detail lives one link away.
Target ~180 lines each. Est. saving ~3–4k tokens/session on top of item 1. (The files even say
"README.md is the full guide" — so move the reference material there and keep the promise.)

**3. Fix the hybrid before scaling it — close TD-14, then push bulk work to local.** Two steps,
in order: (a) re-point `local-reason` fallback to local tiers only so cheap/sensitive work
**fails closed** (already the #1 P1 in the 2026-07-01 review — this review is a second, cost-based
reason to do it). (b) Then route genuinely cheap, non-sensitive, high-volume work — classification,
draft summarization, first-pass doc checks — to the local model via the router we already run.
Industry reports **60–80% cost reduction** on hybrid local+cloud when simple tasks stay local and
only hard reasoning hits Claude
([hybrid architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)).
Caveat we must respect: the honesty/privacy invariant — never route a sensitive lookup to a path
that can leak. Fixing TD-14 is the precondition, not an optional nicety.

**4. Tier models inside Claude Code itself — pin cheap subagents to Haiku, reserve Opus.**
Per-agent model selection lets grunt work (search, `check-docs.py`-style link verification,
syntax passes, roster lookups) run on **Haiku 4.5** while architecture/decisions stay on Opus.
Reported **~51% saving** for 3-tier routing vs. uniform Opus, and 60–80% vs. Opus-for-everything
([subagent cost guide](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)). Concretely:
a Haiku subagent does the first-pass sweep, only flagged items escalate to Opus.

**5. Make the daily routines cheaper by not re-deriving what hasn't changed.** Give
`tech-debt.md` a `last-verified: YYYY-MM-DD` field per item; the daily run re-verifies only items
touched since last run (git-diff-driven) + a full weekly sweep, instead of re-confirming every
claim daily. And run the routines from a **lean context**: root in the hub, load `portfolio.md` +
`tech-debt.md`, pull the others only when an item points there — not all six `CLAUDE.md` + every
CFO doc every night.

**6. Session hygiene, standing habits** (each cited, all in the 2026 cost docs):
   - **Plan mode before expensive edits** — review the plan, cut dead ends, *then* execute;
     kills the trial-and-error token sink.
   - **`/clear` between unrelated tasks; `/compact` and `/recap` on long/resumed sessions** —
     don't drag stale context turn to turn ([costs docs](https://code.claude.com/docs/en/costs)).
   - **Batch related work into one longer session** so caching amortizes, rather than many
     cold-start short ones.
   - **Scope prompts tight** — "refactor the login function in `auth.ts`", not "refactor auth";
     vague scope makes the model open files and reconstruct context we could have handed it.

---

## On the prompt that triggered this (the CEO asked me to critique it)

The prompt is warm and gets a broad answer — but breadth is exactly what makes it expensive, and
it's set to run on a schedule, which compounds the cost. Three concrete fixes:

- **"ANYTHING that could help" makes me explore wide and spend tokens on the survey.** A tighter
  target — e.g. *"cut token spend on the daily NARF/ZORT routines"* or *"audit our CLAUDE.md
  weight"* — gets a sharper answer for a fraction of the tokens. Broad is fine for a **one-off**;
  it's costly as a **recurring** job.
- **"Check the news / keep up to date, day by day" every run is wasteful.** This space does not
  move enough daily to justify fresh web searches each time. Pin it: **re-research weekly**, cache
  the findings, and have the daily run diff against the cache. (Today's searches confirm the
  landscape is stable since our last look — caching, model-tiering, hybrid routing; no new lever.)
- **Say what output you want and whether to commit.** "Let me know" left it to me to decide to
  write this file. Stating *"reply only"* vs *"commit a doc under docs/ai-cto"* + a rough length
  cap removes a guess and trims the run.

A tightened version: *"Weekly: audit our Claude token spend. Measure CLAUDE.md weight and the
routines' fixed context; check for any new cost lever since last week (skip if none); write
findings to docs/ai-cto/reviews as a dated file, ≤150 lines. Don't re-run the web search if the
last one was <7 days ago."*

---

## What this could save (rough, directional)

| Lever | Effort | Est. per-session token cut |
| ----- | ------ | -------------------------- |
| Root sessions in one repo (item 1) | none | ~65% of `CLAUDE.md` load (~9.5k) |
| Trim two big `CLAUDE.md` (item 2) | ~1 hr | ~3–4k more |
| Haiku subagents for grunt work (item 4) | config | ~50% on delegated volume |
| Local-first hybrid, post-TD-14 (item 3) | fix + config | 60–80% on non-sensitive bulk |
| Weekly (not daily) re-verify + news (items 5, prompt) | process | most of the routines' recurring spend |

The first two are free and immediate. The rest need the TD-14 fix landed first (privacy before
savings) and a config pass. None of them touch the honesty invariant — cheaper, not looser.

---

## Sources (current as of 2026-07)

- [Manage costs effectively — Claude Code docs](https://code.claude.com/docs/en/costs)
- [Prompt caching with Claude — Anthropic](https://claude.com/blog/prompt-caching)
- [Create custom subagents — Claude Code docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code sub-agents: context, cost, parallel execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Hybrid cloud-local LLM architecture guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Context editing / compaction / memory tool — Claude Platform docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
