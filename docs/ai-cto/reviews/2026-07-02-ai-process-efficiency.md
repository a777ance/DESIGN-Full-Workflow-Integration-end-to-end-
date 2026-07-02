# NARF — AI process & token-efficiency audit — 2026-07-02

**Question posed:** find inefficiencies in the *process between the human and the AI* —
token waste, weak prompting, missed hybrid (local-LLM + Claude) leverage — and keep it
current with 2026 best practice.

**One-line answer:** the biggest waste isn't the models, it's the **session shape**. Every
session opened at `/home/user` loads *all six* `CLAUDE.md` files (~14.6k tokens) before a
single useful token, most of it irrelevant to the repo actually being touched. Fix that and
three other structural things and we cut ~40–60% of per-session overhead with no quality loss.

---

## Findings, ranked by leverage (impact × ease)

### 1. Per-session context bloat: all six CLAUDE.md files load at once — ~14.6k tokens/session

Sessions run from the `/home/user` parent, so Claude Code merges **every** child
`CLAUDE.md`. Measured today:

| Repo | chars | ~tokens |
| ---- | ----- | ------- |
| localDNS | 20,472 | ~5,120 |
| DESIGN | 17,987 | ~4,500 |
| MARKETING | 10,660 | ~2,665 |
| customers | 4,135 | ~1,033 |
| claude-code-homelab | 2,896 | ~724 |
| Azure-lab | 2,294 | ~573 |
| **Total** | **58,444** | **~14,600** |

A task touching only `customers/` still pays for localDNS's Unbound config and MARKETING's
pricing. Because `CLAUDE.md` is **never lazy-loaded or evicted** (it persists the whole
session — [Claude Code docs][cc-best]), that's ~14.6k tokens carried through every message of
every session, uncached whenever any of the six changes.

**Fix (do this first):** open Claude Code with the working directory set to the *specific
repo*, not the parent. Only that repo's `CLAUDE.md` (+ any `~/.claude/CLAUDE.md`) then loads.
Expected saving: ~9–13k tokens/session on single-repo work, which is most work.
For genuinely cross-repo sessions (portfolio reviews), scope to DESIGN and let its links pull
the others on demand.

### 2. The house-style block is duplicated verbatim in all six files — ~1k tokens × 6

The `## House style: ordering & typography` section (reverse-chronological, Z→A lists, reversed
walkthrough blocks, Gill Sans MT) is copy-pasted identically into every repo. It's ~40 lines /
~450 tokens each. Every cross-repo session pays for it six times; every edit to the convention
means six commits.

**Fix:** move it to a single user-level `~/.claude/CLAUDE.md` (loads once, applies everywhere)
**or** one `HOUSE-STYLE.md` linked by a one-line pointer from each repo. Net: one copy instead
of six, one edit instead of six. Saving: ~2.2k tokens on any multi-repo session, plus it kills
a whole class of drift bugs.

### 3. CLAUDE.md files are brain-dumps, not lookup tables

Current best practice is explicit: `CLAUDE.md` "works better as a **lookup table** than a
giant brain dump" — keep out design history and long rationale ([KDnuggets][kd],
[claudefa.st][cf]). But `localDNS/CLAUDE.md` (326 lines) carries full narrative rationale for
the DNS split, the host-resolver root cause, the IPv6 black hole — *all of which already exist*
in `network-context.md`, which the file itself links. We're paying for the same prose twice,
every session, in the copy that can't be evicted.

**Fix:** demote rationale to the linked context files (they already exist); keep `CLAUDE.md`
to the table + the invariant + the pointer. Target: localDNS and DESIGN CLAUDE.md under ~150
lines each. Rough saving: ~3–4k tokens/session on those two repos. This does **not** mean
delete knowledge — it means store it where it's loaded on demand, not always-on.

### 4. Hybrid local↔Claude routing is 80% built and unused for our own workflow

We already run the LLM router (localDNS stage 10: LiteLLM on :4040, Open WebUI, a reasoning
ladder with local `deepseek-r1:1.5b` on the t630 and cloud-GPU overflow). It exists to serve
*customers* — but we don't route **our own** repo chores through it. Industry hybrid setups
report **60–80% cost cuts** by sending routine work local and reserving the frontier model for
hard reasoning ([buildmvpfast][hy], [sitepoint][sp]).

Tasks that should run on the **local** model (they're cheap, high-volume, low-stakes):
- `tools/check-docs.py`-style link/anchor checking and lint
- drafting commit messages and changelog/log entries
- summarizing a diff, classifying an inbound lead, templated statement copy
- the newest-first / Z→A reordering chores the house style demands

Reserve **Claude** for: architecture, code changes, security-sensitive reasoning, anything
touching real customer data (never route PII to the shared cloud-overflow — see the standing
privacy invariant, and note **TD-14**: `local-reason`'s fallback still isn't fail-closed, so
fix that *before* leaning on local routing for anything sensitive).

**Caveat, stated honestly:** the t630's `deepseek-r1:1.5b` is fine for lint/summarize/classify,
not for code. The best local coding model that fits consumer hardware in 2026 is
Qwen2.5-Coder-32B ([kunalganglani][kg]) — but that needs a real GPU, not the Carrizo iGPU. So
route *chores* local now; don't pretend the box can replace Claude for code.

### 5. We're paying Opus 4.8 / 1M-context rates for doc edits

Most work in these repos is markdown editing, not deep reasoning. Best practice: **default to
Sonnet, escalate to Opus only for hard analysis/refactor** ([claudefa.st][cf-usage]); and 1M
context is a premium tier we rarely need for a 150-line CLAUDE.md. Match the model to the task
tier instead of running the biggest model by default.

### 6. Async/batch work is billed at full real-time rates

The **Batch API is 50% off** for anything that can tolerate a <24h turnaround, with no quality
penalty; stacked with prompt caching (cached input reads are **90% off**) the combined ceiling
is ~95% ([Anthropic pricing][fin], [devtoollab][dt]). Two of our workloads are textbook batch
candidates: the **monthly statement generation job** (stage 06) and any bulk doc-lint/CI sweep.
They run on a schedule and nobody's waiting on the response — exactly the batch profile.

**Also protect the cache we already get:** Claude Code auto-caches the system prompt + memory
files. A giant, frequently-edited merged CLAUDE.md *busts that cache* on every change. Findings
1–3 (smaller, per-repo, stable memory files) are also a **cache-hit** win, not just a raw-token
win.

---

## On the prompt that triggered this run — yes, it was inefficient

The request was: *"Locate inefficiencies… Is there a better way… Perhaps also better prompting…
Anything you could possibly think of… ANYTHING that could help… Search the web… Check the
news."* Honest critique, since you asked:

- **No scope boundary.** "ANYTHING that could help" forces the AI to guess how wide to go — it
  will either under-deliver or (more likely, to be safe) fan out expensively across the web and
  the whole repo set. That open-endedness is itself a token cost.
- **No success criterion / output format.** Nothing says "top 5, ranked, with an estimate
  each" vs. "a paragraph." The model has to invent the deliverable shape, and often produces
  more than you wanted.
- **Stacked vague amplifiers.** "Perhaps also…", "Anything…", "ANYTHING…" don't add
  information; they add surface area to cover.
- **"Check the news / keep up to date" on an open-ended routine** is the priciest habit here —
  it triggers broad web search every run for facts that move monthly, not daily.

**A tighter version of the same ask:**

> Audit our human↔AI process for token waste. Output: the top 5 changes ranked by estimated
> token saving, each with (a) the concrete fix and (b) a rough %/token estimate. Focus on
> session structure, CLAUDE.md size, and using our local LLM router for chores. One web search
> max, only for 2026 pricing/caching numbers. Skip anything I can't act on this week.

Same intent, bounded scope, defined deliverable, capped research — cheaper and it gets you a
more useful answer. General rule: **state the goal, the constraints, and what "done" looks
like.** Give the model a target and it stops guessing (and over-producing).

**And the cadence:** run this kind of audit **monthly, not on a tight loop.** Pricing and
model tiers shift on a scale of weeks; a daily "check the news" pass mostly re-buys the same
answer. Schedule structural audits monthly; keep any fast loop for things that actually change
daily (CI, PRs, deploys).

---

## Recommended order of operations

1. **Today, free:** run single-repo sessions (cwd = the repo). Biggest single saving, zero risk.
2. **This week:** de-dupe house style into `~/.claude/CLAUDE.md`; trim localDNS + DESIGN
   CLAUDE.md to lookup-table size (rationale already lives in the linked context files).
3. **This week:** fix **TD-14** (fail-closed local fallback), *then* route repo chores
   (lint, commit msgs, summaries, classification) through the local router.
4. **This month:** default new sessions to Sonnet, escalate to Opus deliberately; move the
   monthly statement job and doc-lint sweeps to the **Batch API** (50% off).
5. **Ongoing:** treat CLAUDE.md as append-rarely (protect the prompt cache); run this audit
   monthly, not on a loop.

Rough combined effect: **~40–60% fewer tokens per typical single-repo session** (mostly from
#1–#3), plus ~50% on the batchable async jobs, with no loss of capability on the work that
actually needs Claude.

---

## Sources

- [Best practices for Claude Code — Claude Code Docs][cc-best]
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets][kd]
- [Claude Code Context Window: Optimize Your Token Usage — claudefa.st][cf]
- [Claude Code Pricing / usage optimization — claudefa.st][cf-usage]
- [Anthropic API Pricing 2026: caching + batch — finout.io][fin]
- [Prompt Caching in 2026 — DevToolLab][dt]
- [Hybrid Cloud-Local AI Workflows — buildmvpfast][hy]
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint][sp]
- [Local LLM vs Claude for Coding benchmark 2026 — kunalganglani][kg]

[cc-best]: https://code.claude.com/docs/en/best-practices
[kd]: https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
[cf]: https://claudefa.st/blog/guide/mechanics/context-management
[cf-usage]: https://claudefa.st/blog/guide/development/usage-optimization
[fin]: https://www.finout.io/blog/anthropic-api-pricing
[dt]: https://devtoollab.com/blog/prompt-caching-guide
[hy]: https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
[sp]: https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
[kg]: https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark
