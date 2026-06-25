# NARF — AI Process Efficiency Review — 2026-06-25

**Question asked (scheduled routine):** Locate inefficiencies in the *process* between the user
and the AI. Where can we cut token use? Better prompting? Leverage other AI / hybrid local-LLM +
Claude? Keep it current with mid-2026 best practice.

**Scope:** This is about the *human↔AI workflow* (Claude Code sessions, the LiteLLM/Odin router,
the scheduled routines), not the product. Findings are ranked by leverage. Numbers are grounded in
this repo set; web sources dated June 2026 are listed at the bottom.

---

## Bottom line

The hybrid architecture is already good — **deterministic (zero-token) routing, local-first
reasoning ladder, spend cap, local RAG, privacy gate.** That's ahead of most 2026 write-ups. The
inefficiency is **not** in the router design; it's in three cheaper places:

1. **Context weight** — the `CLAUDE.md` files are 3–4× the recommended size and the house-style
   block is duplicated 6×. This is paid on (nearly) every turn.
2. **Unused free discounts** — prompt caching and the Batch API are 90% / 50% off respectively and
   stack to ~95%. The scheduled routines (like this one) and statement generation are textbook
   Batch-API workloads and are almost certainly running at full synchronous price.
3. **Model tier defaulting** — interactive dev work defaulting to Opus 4.8 where Sonnet/Haiku would
   do, and subagent fan-out with no parallelism cap.

Top 5 actions, in order of $/effort:

| # | Action | Effort | Saving |
|---|--------|--------|--------|
| 1 | Trim `CLAUDE.md` to <200 lines each; factor the shared house-style block into one file | 1 hr | Every-turn context tax + sharper attention |
| 2 | Route scheduled routines + statement batch jobs through the **Batch API** | code in router | 50% off those jobs |
| 3 | Confirm **prompt caching** is on for the Claude tier in LiteLLM and long Claude Code sessions | config check | up to 90% off repeated input |
| 4 | Default Claude Code to **Sonnet 4.6**; escalate to Opus only for hard tasks; cap subagents | habit + 1 CLAUDE.md line | ~3–5× on routine edits |
| 5 | Move repeatable procedures (doc-check, statement build) from prose into **Skills** | incremental | smaller context, dynamic load |

---

## 1. Context weight — the biggest everyday lever

`CLAUDE.md` sits in the context window for the *entire* session; a 5,000-token file costs ~5,000
tokens every turn. Anthropic's own guidance is to keep it **under ~200 lines.** Current state:

```
localDNS/CLAUDE.md      2,728 words  ≈ 3,650 tokens
DESIGN/CLAUDE.md        2,608 words  ≈ 3,500 tokens
MARKETING/CLAUDE.md     1,445 words  ≈ 1,900 tokens
customers, homelab, Azure-lab        ≈ 1,650 tokens combined
TOTAL across 6 repos    8,030 words  ≈ 10,700 tokens
```

- A **single-repo** session loads one of these — localDNS or DESIGN alone is already ~2× the lean
  target.
- A **multi-repo routine** (this session) loaded **all six ≈ 10.7K tokens of project instructions
  before the task even starts.**
- The **house-style typography block is duplicated verbatim in all 6 files** (~450 tokens × 6 ≈
  2,700 tokens of pure repetition per multi-repo turn).

**Two costs, not one.** Prompt caching cushions the *dollar* cost inside a warm session (cache hits
are ~10% of input price), but: (a) cache is per-session and expires, so new sessions and the daily
routines pay full freight on the cache *write*, and (b) the bigger issue is **attention dilution** —
10K tokens of standing instructions crowd the window and bury the parts that matter. Smaller
CLAUDE.md = cheaper *and* better-followed.

**Fixes:**
- Cut each `CLAUDE.md` to the briefing essentials (<200 lines); push detail into README/context
  files that load *on demand*, not every turn. The DESIGN and localDNS files have grown into mini
  manuals — that content belongs in `README.md`, which Claude reads only when needed.
- **De-duplicate the house-style block.** Keep the canonical copy in one place (e.g.
  `DESIGN/docs/house-style.md`) and have each repo's CLAUDE.md link to it in one line rather than
  inlining all four bullets. Same rule, ~1/6th the tokens.
- Keep the per-repo "Known issues" tables — those are high-value — but consider that they're really
  tech-debt tracking and could live in `tech-debt.md` (loaded when relevant) rather than the
  always-on briefing.

## 2. Free discounts you're probably leaving on the table

Per Anthropic's June-2026 pricing:

- **Prompt caching: cache-hit input costs 10% of standard** (90% off). Claude Code applies this
  automatically to the system prompt + CLAUDE.md within a session — *confirm long sessions aren't
  being `/clear`ed so often that the cache never warms.* For the **LiteLLM Claude tier**, verify
  `cache_control` breakpoints are set on the stable system prompt (Frigg's instructions, the router
  system message) — LiteLLM supports Anthropic caching but it is **not on by default.**
- **Batch API: flat 50% off, async within 24h, no quality difference.** This is the single biggest
  miss. Workloads that are *not* interactive should go through Batch:
  - **The scheduled routines themselves** (this efficiency review, any cron-driven analysis) — they
    have no human waiting, so the 24h window is free money.
  - **Statement generation** (`compose.py`/`generate_client.py` LLM steps, if any), monthly and
    bulk — perfect batch shape.
  - Any **classification/extraction** the router does in bulk.
  - Stacked with caching, effective spend on these can drop **95%+.**
- **Opus 4.8 is 61% cheaper per token on multimodal than 4.7, and tool-calling uses fewer steps.**
  If any config still pins 4.7 for vision, move it to 4.8. Also: **requests over 200K tokens no
  longer carry the long-context premium** — relevant since this box runs Opus 4.8 `[1m]`; large
  context is now priced linearly, but that's a reason to not *fear* big context, not to be sloppy
  with it.

## 3. Model tiering in the dev loop

The router's cloud tiers are sensibly split (Sonnet 4.6 for `cloud-code`, Opus for
explore/overflow/vision). The gap is the **interactive Claude Code sessions**, which default to
Opus 4.8:

- **Default to Sonnet 4.6 for routine edits/docs** (this repo set is mostly Markdown + small Python).
  Opus 4.8 is $5/$25 per MTok vs Sonnet $3/$15 — and most CLAUDE.md edits, link fixes, and roster
  tweaks don't need Opus. Escalate to Opus only for cross-repo reasoning, architecture, or hard bugs.
- **Cap subagent parallelism.** 2026 field reports are brutal: a 3-agent team ≈ **7× tokens**; one
  unattended 49-subagent run was estimated **$8–15K**; another team burned **$47K in three days** of
  unattended fan-out. Your portfolio already says "no agent loop for routing" — extend that
  discipline to dev work: add one line to CLAUDE.md capping concurrent subagents (e.g. ≤3) and
  **never leave subagent chains running unattended.** (This routine used exactly one subagent, by
  design.)

## 4. Push local-first one notch further

You already capture the 60–80% hybrid saving. Two extensions:

- **More dev-side pre-filtering local.** Doc-link checking (`check-docs.py`) is already pure Python
  (zero tokens) — good pattern, keep extending it. Tasks like "summarize what changed in this diff"
  or "draft a commit message" can hit `local-smart` (qwen2.5:7b) first via the router, with Claude
  as overflow only when the local draft is rejected.
- **Fix TD-14 while you're in there.** The `local-reason` fallback chain still includes
  `cloud-gpu-reason`/`cloud-overflow`, which can leak a *sensitive* task to the cloud if local is
  down. Make sensitive tiers **fail closed (local-only).** This is a privacy fix that *also* removes
  an unbudgeted cloud-spend path — it belongs in this review, not just the security one.

## 5. Skills over standing context

June-2026 Agent Skills load instructions/scripts **dynamically and only when invoked** — a script
can read a PDF and return fields without ever loading the script or PDF into context. Repeatable
A777ance procedures are good candidates to move from always-on prose into on-demand Skills:

- "Build a statement" (the `make statement` pipeline)
- "Add a customer" (roster + sidecar scaffold)
- "Run the doc-integrity check before commit"

Each becomes a small Skill the model loads when needed, instead of paragraphs every repo's CLAUDE.md
carries forever.

---

## 6. The meta-question: was *this* prompt efficient?

Honest answer: **no — and you asked, so here it is.** The prompt was warm and clear in intent but
expensive in shape:

- **Unbounded scope.** "Anything you could possibly think of… ANYTHING" tells the model to explore
  in every direction with no stop condition. That maximizes tokens and invites a sprawling answer.
- **No target output.** No format, length, or destination specified, so the model has to guess
  (this review picked "ranked, written to the AI-CTO reviews folder" — but that was inference).
- **"Search the web… check the news"** with no bound runs many open-ended searches. Useful here, but
  it should be *scoped* (which topics) and *cadenced* (it changes daily — so make it a cheap weekly
  routine, not a deep dive each run).
- **Repetition** ("Thanks!" ×2, restated asks) is minor but real.

A leaner version that gets the same result for fewer tokens:

> *Weekly routine. Review our AI workflow (Claude Code + the LiteLLM/Odin router) for token-cost and
> prompting inefficiencies. Use last week's review as the baseline — report only what changed or is
> newly worth doing. Run ≤4 web searches on current Claude/LLM cost best practice. Output: a ranked
> table of ≤5 actions (effort + saving), appended to `docs/ai-cto/reviews/`. Notify only if there's a
> high-leverage change. ≤600 words.*

Why it's cheaper and better: bounded search count, a hard output spec, a delta-only instruction (so
it doesn't re-derive findings every week), and an explicit notify threshold. **Run it on the Batch
API** (no human is waiting on a scheduled routine) for another 50% off.

General prompting habits that save tokens across all sessions: state the **target file and format**
up front; scope to the **smallest unit** ("fix the X in `file.py`", not "refactor the module");
**batch related asks** into one message so the model reads context once; and `/clear` between
unrelated tasks so stale context isn't re-billed each turn.

---

## What I'm explicitly NOT recommending

- **No new orchestration framework.** The Odin/LangGraph + LiteLLM stack is fine; the wins above are
  config and habit, not a rebuild. "Liquidity before app, trust before tech" applies to the tooling
  too — don't spend engineering on the router when the savings are in CLAUDE.md size and Batch/cache
  flags.
- **No bigger local hardware yet.** The t630 is memory-bandwidth bound and that's an accepted
  constraint; the cloud-overflow tier is the right pressure valve. Renting a GPU full-time would cost
  more than the Claude spend it displaces at current volume.

## Sources (June 2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing) (caching 90%, batch 50%, stack 95%+)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8) (61% cheaper multimodal; no >200K premium)
- [Equipping agents with Agent Skills — Anthropic](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Code Agents 2026: what parallel sessions actually cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/) (3-agent ≈ 7×; $47K/3-day example)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) (60–80% saving; PII-first routing)
- [LLM Model Routing 2026 — DigitalApplied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
