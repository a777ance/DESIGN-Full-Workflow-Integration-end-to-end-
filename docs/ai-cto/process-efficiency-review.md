# Process efficiency review — user ↔ AI workflow

*Prepared 2026-06-27 by NARF (AI CTO routine). Brief: "Locate inefficiencies in our
PROCESS between the user and the AI — reduce token use, better prompting, leverage other
AI, hybrid local/Claude, keep up to date." This is a living doc — the field moves weekly,
so re-run the routine and update the dated findings below.*

> **House-style note:** findings are ranked by impact (biggest lever first), not
> chronologically, because this is a priority list, not a log.

---

## TL;DR — the five biggest levers, ranked

| # | Lever | Est. saving | Effort | Where |
| - | ----- | ----------- | ------ | ----- |
| 1 | **Trim the six CLAUDE.md files** loaded on every run | ~10k tokens **per run**, every run | Half a day | each repo |
| 2 | **Scope each scheduled routine to one repo**, not all seven | ~12k tokens/run on single-repo jobs | Config | routine setup |
| 3 | **Triage with the local LLM first** (you already run LiteLLM on the t630) | 60–80% of "is there anything to do?" runs never hit Claude | 1 day | `localDNS/10-ai-orchestration` |
| 4 | **Tighten the prompts** — narrow scope, define "done", say where output goes | 2–5× fewer exploratory tokens per run | Per-prompt | routine prompts |
| 5 | **Batch the non-urgent routines** through the Batch API (50% off) | Half price on anything that can wait 24h | 1 day | new harness |

The rest of this doc is the detail and the receipts.

---

## 1. The CLAUDE.md tax — the single biggest waste

**Measured today, in this repo:**

| Repo CLAUDE.md | ~Tokens |
| -------------- | ------: |
| `localDNS` | 5,118 |
| `DESIGN-…` (this repo) | 4,496 |
| `MARKETING` | 2,665 |
| `customers` | 1,033 |
| `claude-code-homelab` | 724 |
| `Azure-lab` | 573 |
| **Total injected every run** | **~14,600** |

When a session has multiple repos in scope (as the scheduled routines do), **every repo's
`CLAUDE.md` is injected into the system prompt — on every run, whether or not the task
touches that repo.** A routine that only edits `localDNS` is still paying for the
`MARKETING`, `customers`, and `Azure-lab` briefings it never reads.

Anthropic's own guidance and the 2026 community benchmarks converge on the same number: a
3,847-token CLAUDE.md stripped to "only what Claude can't infer from the code" hit **312
tokens with no quality regression — 91.9% reduction.** Our files are 2–5× larger than the
"before" in that benchmark.

**Why ours are big:** they double as human-facing playbooks (the funnel diagram, the money
flow, the full deploy-path table, the entire known-issues table). That content is valuable —
but it belongs in `README.md` / `network-context.md`, which Claude reads *on demand*, not in
`CLAUDE.md`, which loads *unconditionally*.

**Fix (keeps the house style, just relocates the bulk):**

1. Cut each `CLAUDE.md` to a lean briefing: the handful of rules Claude *cannot* infer
   (push-to-main vs. branch, secrets policy, the one source of truth, where the product
   lives) + a table of contents pointing at the full docs. Target **< 1,500 tokens** each;
   the stubs (`Azure-lab`, `homelab`) can go under 400.
2. Move the rest — funnel diagram, deploy-path table, known-issues, verification blocks —
   into `README.md` (most already duplicate it) and link from `CLAUDE.md`.
3. Adopt **path-scoped rules** (`.claude/rules/*.md` with `paths:` frontmatter). A rule
   with `paths: ["01-unbound/**"]` costs **zero tokens** until Claude actually opens an
   Unbound file. This is the right home for the long per-stage detail. *(New 2026 feature —
   see Anthropic's "Steering Claude Code" post.)*

Expected: ~14.6k → ~4–5k tokens of memory files, recovered on **every run across every
repo**. At the routine cadence implied here, that is the highest-ROI change on the list.

---

## 2. Scheduled-routine structural waste

**Cold cache every run.** Prompt caching has a 5-minute (default) to 1-hour TTL. Scheduled
routines fire far enough apart that each one **re-pays the full prefix at cache-write
price** (writes cost 25% *more* than base input; reads cost ~10%). We get the worst side of
caching — never the cheap reads. Two mitigations:

- **Shrink the prefix** (item 1) so the cold write is small in the first place.
- **Cluster related routines** so a second run lands inside the cache window of the first
  (reads at 10%). E.g. run the CTO and CFO portfolio sweeps back-to-back, not 6 hours apart.

**Scope creep.** Each routine has all seven repos in scope, so it pays for seven repos'
CLAUDE.md + a larger tool/skill surface. If a routine's job is "audit `localDNS`," scope it
to `localDNS` only. One-repo scope ≈ saves ~9–12k tokens of memory files per run plus a
smaller MCP/skill footprint.

**Run-or-skip gate.** Many routines exist to answer "did anything change / is anything
broken?" — and most fire the expensive model only to conclude "all healthy, stay silent."
That triage is exactly what the local LLM is for (item 3).

---

## 3. Hybrid local + Claude — you already own the hard part

`localDNS/10-ai-orchestration` already runs **LiteLLM (port 4040) as a unified gateway**,
Ollama-class local models on the t630 CPU, a reasoning ladder (`local-reason` =
deepseek-r1:1.5b cool on-box, `cloud-gpu-reason` = full R1 on a rented GPU via Tailscale),
and `cloud-overflow` fallback. **This is, almost exactly, the reference hybrid stack the
2026 cost-optimization guides recommend** (LiteLLM gateway + local serving + Claude as the
frontier tier). You built the moat; you're just not routing through it yet.

The published task split that hybrid shops see:

- **60–70% of requests are "simple"** (classify, extract, format, "did the file change?",
  "is the service up?", "does this log have an error?") → **local model, $0/inference.**
- **20–30% moderate** (summarize a diff, draft a changelog entry, lint prose) → local or
  cheap cloud tier.
- **~10% genuinely need frontier reasoning** (architecture, multi-file refactor, the actual
  fix) → **Claude (Opus 4.8 / Sonnet 4.6).**

Documented real-world results from this exact pattern: **60–83% cost reduction**, with one
team going $47k → $8k/mo.

**Concretely for us:**

- Put a **local triage step in front of every monitoring routine.** Local model reads the
  git diff / log / status and answers one question: *"Does this need Claude? yes/no + why."*
  On "no," the routine ends without ever calling the API. On "yes," it hands Claude a tight,
  pre-summarized brief instead of raw files.
- Use the local model for **prose-quality passes** (the "talk like a person" house rule, the
  Z→A ordering check, link-checking) — deterministic, cheap, no frontier model needed.
- Keep **`deepseek-r1:7b`+ off the t630 CPU** — the homelab known-issues table already warns
  it cooks the box; use the rented-GPU rung for heavy local reasoning.
- Reserve **Claude Opus 4.8 for the 10%**: the actual edits, the cross-repo decisions, the
  things that change `main`.

---

## 4. Prompt quality — including the prompt that launched this routine

**The brief that started this run was, candidly, inefficient** — and you asked me to say so.
It was: *"Locate inefficiencies… Is there a better way… Perhaps also better prompting…
Anything you could possibly think of. Leveraging other AI… ANYTHING that could help. Search
the web… Keep UP TO DATE… Check the news."*

What that costs: it's **open-ended ("ANYTHING")**, has **no definition of done**, **no
output target** (where should the answer go? how long?), and **bundles five distinct jobs**
(audit, prompt-coaching, hybrid architecture, news scan, self-critique) into one run. An
unbounded prompt makes the model fan out across the whole repo set and the open web "to be
safe" — which is the exact token burn the prompt is trying to find.

A tighter version of the same intent:

> *"Audit our Claude-Code-on-the-web process for token waste. Focus on the recurring
> scheduled routines. Give me the top 5 fixes ranked by tokens-saved-per-run, each with a
> concrete action. Check current best practices (cite dates). Write it to
> `docs/ai-cto/process-efficiency-review.md` and push. Keep it under ~1,200 words."*

Same outcome, a fraction of the exploration, and a deliverable I can't misjudge the shape of.

**General prompt rules that cut tokens (2026 consensus):**

- **Name the files / line ranges.** "Check lines 45–60 of `auth.ts`" beats "look at the auth
  code" — same answer, a fraction of the reads.
- **State the output contract** (format, length, destination). Vague length → the model
  over-produces.
- **One job per run.** Bundled asks force the model to hold everything in context at once.
- **Say what *not* to do** ("don't refactor," "don't read the other repos") — cheaper than
  letting it explore and back out.
- **Put the stable stuff first, the variable stuff last** so caching covers the big prefix.

---

## 5. Mechanics worth turning on

- **`/context`** — shows exactly where tokens go (system prompt, tools, memory files,
  skills, history). Run it once in an interactive session to see the CLAUDE.md tax for real.
- **`/compact` proactively** — after each discrete sub-task, not at the limit. Shrinks the
  prefix for every subsequent turn.
- **Subagents for fan-out reads** — anything that means reading >3–4 large files. They run
  in a *separate* context and return only a summary, keeping the main window clean. *Caveat:
  not free — the agent harness has startup overhead, so don't spawn one for a `git status`.*
- **Batch API = 50% off** for anything that can wait up to 24h. Most of our routines are not
  real-time ("nightly stats summary," "weekly portfolio sweep"). Route those through Batch.
- **Effort controls on Opus 4.8** (low / high / xhigh / max) — use `low` for mechanical
  passes, save `max` for genuine reasoning. Don't pay xhigh to reformat a table.
- **Model tiering** — Haiku 4.5 / Sonnet 4.6 for the cheap-but-needs-cloud middle; Opus 4.8
  only for the hard 10%.

---

## 6. Current state of the field — June 2026 (dated; re-check on next run)

- **Opus 4.8** (launched 2026-05-28): $5 / $25 per MTok — flagship, same rate as 4.7.
  Adaptive thinking + effort controls (low/high/xhigh/max). **Fast Mode now $10/$50**
  (3× cheaper than 4.7's). 1M-token context at flat rate, no surcharge.
- **Fable 5** is the new generally-available top tier as of June 2026 (Mythos 5 in limited
  preview above it). Worth a look for the frontier 10% if a task out-reasons Opus.
- **Sonnet 4.6 / Haiku 4.5** — the mid and cheap rungs for the hybrid ladder.
- **Prompt caching: ~90% off cached input.** **Batch API: 50% off, all models.** These two
  stack with hybrid routing — they're the cloud-side levers; local-first is the other half.
- Pricing direction in 2026 is **usage-based, optimize-by-feature** — base rates are flat,
  so savings come from *caching + batching + routing + smaller prefixes*, exactly the levers
  above, not from waiting for a price cut.

---

## 7. Action checklist

- [ ] Trim all six `CLAUDE.md` to < 1,500 tokens (stubs < 400); move bulk to README + link.
- [ ] Stand up `.claude/rules/` with `paths:`-scoped rules for the per-stage / per-service detail.
- [ ] Scope each scheduled routine to the single repo it actually works on.
- [ ] Add a local-LLM triage gate (via the LiteLLM router) in front of monitoring routines.
- [ ] Move non-urgent routines (nightly/weekly sweeps) onto the Batch API (50% off).
- [ ] Cluster related routines into one cache window; set effort=low on mechanical passes.
- [ ] Rewrite routine prompts: one job, named files, defined "done", explicit output target.
- [ ] Re-run this review next cycle — the field changes weekly; update the dated section.

---

## Sources (accessed 2026-06-27)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude remembers your project (memory / CLAUDE.md) — Claude Code Docs](https://code.claude.com/docs/en/memory)
- [Steering Claude Code: skills, hooks, rules, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026) — BuildToLaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Anthropic API Pricing 2026: Opus 4.8, Sonnet 4.6, Haiku 4.5 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
