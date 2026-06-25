# AI Process Efficiency — how we work with Claude (and where we waste it)

**Author:** NARF (AI CTO), commissioned by the founder's "find inefficiencies in our PROCESS" routine.
**Date:** 2026-06-25. **Status:** review — recommendations, not yet adopted as policy.
**Scope:** the *process* between the human and the AI across all seven A777ance repos — token
spend, prompting, model choice, and the local↔cloud hybrid we already half-built. This is a
living doc; the AI landscape moves weekly, so [§7](#7-keep-up-to-date-a-standing-watch) defines
what to re-check and when.

> **One-line answer to the founder's question:** *Yes, there's a better way, and most of the
> waste is the context we load before any work happens.* The single biggest lever is trimming
> the always-on context tax (CLAUDE.md + the session-start reading protocol), then routing cheap
> work to the local box we already own instead of to Opus. Realistic, low-risk saving: **40–70%
> of tokens per session** with no loss of quality. The methods below are industry-standard as of
> mid-2026 (sources in [§8](#8-sources)).

---

## Contents

- [1. TL;DR — ranked by return on effort](#1-tldr--ranked-by-return-on-effort)
- [2. The biggest sink: the always-on context tax](#2-the-biggest-sink-the-always-on-context-tax)
- [3. Workflow inefficiencies (session shape & model choice)](#3-workflow-inefficiencies-session-shape--model-choice)
- [4. The hybrid we already built — connect it](#4-the-hybrid-we-already-built--connect-it)
- [5. Prompt-craft: small habits, real savings](#5-prompt-craft-small-habits-real-savings)
- [6. Critique of the prompt that triggered this doc](#6-critique-of-the-prompt-that-triggered-this-doc)
- [7. Keep up to date: a standing watch](#7-keep-up-to-date-a-standing-watch)
- [8. Sources](#8-sources)

---

## 1. TL;DR — ranked by return on effort

Newest thinking first; within this section, ordered by **saving ÷ effort** (best first).

| # | Move | Effort | Est. saving | Where |
| - | ---- | ------ | ----------- | ----- |
| 1 | **Trim the session-start reading protocol** — stop auto-reading 9 CTO/CFO docs (~13k tokens) every session; read only what the task touches. | 1 hr | High | [§2](#2-the-biggest-sink-the-always-on-context-tax) |
| 2 | **Work inside a single repo, not `/home/user`** — the parent dir pulls *all seven* CLAUDE.md files (~15k tokens) into every turn. | 0 (a habit) | High | [§2](#2-the-biggest-sink-the-always-on-context-tax) |
| 3 | **Default to Sonnet; escalate to Opus deliberately** — most doc edits, link checks, and CRM chores don't need the top tier. | 0 (a habit) | High | [§3](#3-workflow-inefficiencies-session-shape--model-choice) |
| 4 | **`/clear` between unrelated tasks, `/compact` mid-task** — don't let one 200-turn session re-read its whole history each turn. | 0 (a habit) | Med–High | [§3](#3-workflow-inefficiencies-session-shape--model-choice) |
| 5 | **Split the big CLAUDE.md files** into a ~150-line core + linked detail; only the core is taxed every turn. | 2–3 hr | Med | [§2](#2-the-biggest-sink-the-always-on-context-tax) |
| 6 | **Point Claude Code's cheap calls at the local box** via the LiteLLM router we already wrote (stage 10) — but deploy + close TD-14 first. | ½ day | Med (and privacy) | [§4](#4-the-hybrid-we-already-built--connect-it) |
| 7 | **Audit MCP servers** — each connected server's tool schemas ride along every turn; drop the ones a given session doesn't use. | 30 min | Med | [§3](#3-workflow-inefficiencies-session-shape--model-choice) |
| 8 | **Tighten prompts** (incl. the founder's own) — scope narrow, state the deliverable, stop apologizing. | 0 (a habit) | Low–Med | [§5](#5-prompt-craft-small-habits-real-savings), [§6](#6-critique-of-the-prompt-that-triggered-this-doc) |

---

## 2. The biggest sink: the always-on context tax

A token spent on context loaded *before the work* is spent whether or not the work needs it.
We carry a large one. Measured today (`wc` on the live files):

**Every-turn tax — the CLAUDE.md files.** Claude Code injects the CLAUDE.md for the working
directory (and every parent/child in scope) into *every single turn*. Working from the
`/home/user` parent — which is where this routine ran — pulls **all seven**:

| File | ~chars | ~tokens |
| ---- | -----: | ------: |
| `localDNS/CLAUDE.md` | 20,500 | ~5,100 |
| `DESIGN-…/CLAUDE.md` | 18,000 | ~4,500 |
| `MARKETING/CLAUDE.md` | 10,700 | ~2,700 |
| `customers/CLAUDE.md` | 4,100 | ~1,000 |
| `claude-code-homelab/CLAUDE.md` | 2,900 | ~700 |
| `Azure-lab/CLAUDE.md` | 2,300 | ~600 |
| `Chronikomicon/CLAUDE.md` | (not measured) | ~500? |
| **Total** | **~58,500+** | **~15,000+** |

That's ~15k tokens of overhead **on every turn** before a word of work — the exact "CLAUDE.md
tax" the 2026 guides warn about (the rule of thumb is *keep it under ~200 lines*; ours run
2,600–2,700 words / well over 300 lines each).

**Per-session tax — the reading protocol.** The DESIGN CLAUDE.md instructs NARF to read 4 docs
and ZORT to read 5 more at session start:

| Persona | Docs auto-read | ~words | ~tokens |
| ------- | -------------- | -----: | ------: |
| NARF (CTO) | portfolio, roadmap, tech-debt, decisions | ~3,300 | ~4,400 |
| ZORT (CFO) | portfolio, decisions, metrics, runway, budget | ~6,800 | ~9,000 |
| **Both** | **9 files** | **~10,100** | **~13,400** |

`docs/ai-cfo/metrics.md` alone is 3,681 words. A session that opens to fix a broken doc-link
pays ~13k tokens to "catch up" on financial KPIs it will never touch.

**So a protocol-following session starts ~28k tokens in the hole** (~15k every-turn CLAUDE.md +
~13k one-time reads) before the user's first sentence.

### Fixes (cheapest first)

1. **Make the reading protocol conditional, not unconditional.** Change the CLAUDE.md wording
   from "read these at session start" to *"read the hub `portfolio.md` first; read CTO or CFO
   spoke docs **only when the task is a CTO or CFO task**."* A doc-link fix needs none of them.
   This is the highest-ROI change in the whole doc and it's a one-paragraph edit.
2. **Adopt a working-directory habit:** `cd` into the one repo you're editing before launching
   Claude. Never run routine work from `/home/user` — that's what loaded all seven CLAUDE.md
   files into this very session.
3. **Split each big CLAUDE.md into core + detail.** Keep a ≤150-line core (the briefing, the
   rules, the stage map) and move the long reference tables (deploy-path tables, the full known-
   issues list) into `README`/`network-context` files that are *read on demand*, not injected
   every turn. The localDNS deploy-path table and the two big known-issues tables are the
   obvious candidates — they're reference material, not per-turn briefing.
4. **Lean on prompt caching (already automatic in Claude Code, but protect it).** Stable
   prefixes — CLAUDE.md, tool schemas — cache at a 90%-cheaper read after the first turn, *as
   long as you don't perturb the prefix*. Practical implication: don't edit CLAUDE.md mid-session
   if you can help it (it busts the cache), and the 5-min TTL means a session left idle >5 min
   re-pays the full prefix on the next turn. Batching your turns close together keeps the cache
   warm. (For API-side work outside Claude Code — e.g. the statement generator if it ever calls
   an LLM — caching needs explicit `cache_control` markers; it is *not* automatic there.)

---

## 3. Workflow inefficiencies (session shape & model choice)

- **Model tiering.** Opus 4.8 is ~$5/Mtok in, ~$25/Mtok out; Sonnet and Haiku are materially
  cheaper. The consensus 2026 default is *start on Sonnet, escalate to Opus only for deep
  reasoning or large refactors.* Most of our actual work — doc edits, link audits, CRM/roster
  chores, README rewrites, the doc-checker — is not Opus-class. A `/fast` Opus session for the
  hard stuff and Sonnet for the rest is the right split. (This routine itself ran on Opus 4.8
  1M; a Sonnet run would have produced a near-identical doc for a fraction of the cost.)
- **Session hygiene.** Every turn re-reads the whole transcript. A 200-turn session sends
  ~200k tokens *per turn*. Use `/clear` when switching tasks (e.g. localDNS deploy → MARKETING
  pricing), `/compact` when a single task's history gets long, and `/recap` (added Apr 2026) to
  resume without replaying everything. The repos' "land one coherent commit" philosophy already
  nudges toward short, scoped sessions — make it explicit.
- **MCP overhead.** Every connected MCP server injects its tool schemas into every turn — the
  GitHub server alone is a large block. Connect only the servers a session needs. For a pure
  localDNS config edit, GitHub MCP is dead weight on every turn.
- **Scheduled routines (like this one) are a recurring spend.** They're valuable as a "standing
  watch," but each run pays the full context tax above. Two cheap wins: (a) point routines at a
  *single* repo dir, not `/home/user`; (b) where a routine just polls for a yes/no state
  ("did CI go red?", "is there a new PR?"), that classification is exactly the kind of task the
  **local box** should answer for free — see [§4](#4-the-hybrid-we-already-built--connect-it).

---

## 4. The hybrid we already built — connect it

The founder asked specifically about "running a hybrid, local LLM and Claude API." **We already
designed it and it's sitting un-deployed.** `localDNS/10-ai-orchestration/` is a LiteLLM router
with local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` qwen2.5:7b, `local-reason`
deepseek-r1:1.5b, `local-embed`) in front of a cloud overflow tier (`cloud-overflow` →
claude-opus-4-8). The 2026 playbook for cutting LLM cost 60–80% is exactly this shape: a routing
layer that sends simple/sensitive work local and hard work to the cloud. We have the parts; we
haven't turned it on.

**What the local box is genuinely good for (offload these off Opus):**

- **Classification / triage** — "is this PR comment actionable?", "which stage does this lead
  belong to?", "sensitive or not?". Cheap, local, private.
- **Embeddings / RAG** — `local-embed` (nomic-embed-text) indexes the repos so a question is
  answered from a retrieved snippet, not by stuffing whole files into Opus's context. This
  directly attacks the [§2](#2-the-biggest-sink-the-always-on-context-tax) tax: retrieve the
  relevant 500 tokens instead of injecting a 5,000-token CLAUDE.md.
- **Reformatting / lint / first-draft** — house-style reorders (the Z→A, newest-first rules),
  link-checking, "make this terse." Mechanical, no judgment.
- **Privacy-sensitive lookups** — anything touching the real `customers` roster should *prefer
  local* on principle, not just cost.

**What still belongs on Claude (don't kid ourselves):** multi-repo reasoning, this kind of
synthesis, code that has to be right the first time, and anything customer-facing where the
"honesty of the kept document" rule applies. The 7B-on-CPU local tiers are real but slow and
limited; route *to fit*, don't force everything local.

**Two blockers before this is safe to lean on — both already tracked:**

1. **TD-14 (P1) — the privacy fallback fails *open*.** `config.yaml` chains
   `local-reason → ["cloud-gpu-reason", "cloud-overflow"]`, so a *sensitive* task silently
   spills to Claude cloud if the local model is down. **A false privacy guarantee is worse than
   none.** Fix is a 3-line edit (local-only fallback) and needs no box access. *Do this before
   advertising the hybrid as private.*
2. **TD-03 (P1) — the whole stage-10 stack is reference code, not deployed.** The router, the
   nftables layer, none of it is live on the t630. This is downstream of the single t630 access
   session the portfolio keeps flagging as the Phase-1 critical path.

**Recommendation:** treat "stand up the local router + close TD-14" as part of the *same* t630
visit that's already the #1 blocker. Once live, wire Claude Code / routines to call the local
tiers for classification and embeddings. Until then, the hybrid is a design, not a saving — be
honest about that (it's the same honesty rule we hold the Statements to).

---

## 5. Prompt-craft: small habits, real savings

These are cheap habits that compound. None require tooling.

- **State the deliverable and where it goes.** "Write X to `path/file.md` on branch Y, commit,
  push" beats "look into X" — it removes a clarification round-trip (each round-trip re-reads the
  whole context).
- **Scope narrow.** "Fix the broken anchor in `README.md §3`" not "audit all our docs." Narrow
  scope = less context pulled = fewer tokens, *and* a more focused answer. Batch related small
  asks into one session; separate unrelated ones with `/clear`.
- **Don't pre-load politeness or hedging.** "Please could you possibly…", double "Thanks!", and
  "ANYTHING that helps" cost tokens and widen scope without improving output. Direct ≠ rude.
- **Ask for terse output when you don't need prose.** "Just the diff" / "bullet list, no
  preamble" cuts output tokens (the expensive half — output is ~5× input price on Opus).
- **Give the model the answer-shape.** A table, a checklist, a number — saying so up front
  avoids a long narrative you then have to ask to be condensed.
- **Reference files by path, don't paste them.** Claude Code can read `file:line`; pasting a
  file into the prompt both duplicates it in context and breaks caching.

---

## 6. Critique of the prompt that triggered this doc

The founder asked us to flag this. Here's the original, honestly assessed:

> *"Locate inefficiencies in our PROCESS. Between the user and the AI. Is there a better way, for
> which we can reduce token use? Perhaps also better prompting can be identified? Anything you
> could possibly think of. Leveraging other AI. Running a hybrid, local LLM and Claude API.
> ANYTHING that could help. Search the web for answers if this is helpful. Look for best
> practices. Keep UP TO DATE, as this will change quickly day by day. Check the news. Thanks!
> If THIS prompt is inefficient (above) then also let me know and come up with suggestions."*

**What's good:** the *intent* is crystal clear, it names the concrete angles worth exploring
(token use, prompting, hybrid local/cloud, currency of advice), and asking for self-critique is
genuinely smart — it's how you improve the tool.

**What costs tokens / output quality:**

1. **Scope is unbounded.** "Anything you could possibly think of" / "ANYTHING that could help"
   tells the model to maximize breadth — which spends tokens generating options you may not
   want. A scoped ask ("top 5 token wastes + a fix each") gets you the 80% for 20% of the spend.
2. **Redundancy.** "Anything you could possibly think of" and "ANYTHING that could help" say the
   same thing twice; "Search the web," "Look for best practices," "Keep UP TO DATE," "Check the
   news" are four phrasings of one instruction. Each adds tokens, none adds information.
3. **No deliverable named.** It doesn't say *where* the answer should land or in *what shape*.
   This routine had to choose (a doc in `docs/ai-cto/`); a one-line "write findings to
   `docs/ai-cto/ai-process-efficiency.md`" would have removed the guess.
4. **Politeness/filler** ("Perhaps also," "Thanks!" ×2, "If THIS prompt…") — harmless in small
   doses, but it's the habit, not the instance, that adds up across thousands of prompts.

**A tighter rewrite that gets the same result for fewer tokens:**

> *"Audit our human↔AI process for token waste. Deliverable: ranked list of the top ~8
> inefficiencies, each with a concrete fix and rough effort/saving, written to
> `DESIGN-…/docs/ai-cto/ai-process-efficiency.md`. Cover: context/CLAUDE.md tax, prompting
> habits, model tiering, and the local-LLM-vs-Claude hybrid. Use current (2026) best practice —
> cite sources. Critique this prompt too."*

Same intent, ~60% fewer tokens, names the deliverable, bounds the scope to ~8 items, and still
asks for the self-critique. **Meta-point:** the prompt being long isn't the real cost here —
it's a one-off. The real lesson is the *habit* it models, repeated across every session, plus the
"maximize breadth" framing that makes the model spend more on every answer.

---

## 7. Keep up to date: a standing watch

The founder is right that this changes "day by day." Don't re-research from scratch each time —
re-check these specific things on a cadence, and update this doc's [§1](#1-tldr--ranked-by-return-on-effort)
when something moves:

- **Anthropic pricing & model lineup** — model IDs and per-token rates drift; the current
  recommended default tier can change. (Note: the June 15 2026 Agent-SDK billing change was
  *paused* — worth confirming it stays paused, as it would have re-priced routines/`claude -p`.)
- **Claude Code features** — *Skills* (on-demand instruction packs, so we stop paying for
  always-on context), *subagents/dynamic workflows* (parallel specialists, each with its own
  cheaper model), and context commands (`/compact`, `/recap`). Each is a lever this doc should
  fold in as it matures. Skills in particular are the *right* long-term answer to the
  [§2](#2-the-biggest-sink-the-always-on-context-tax) CLAUDE.md tax: move per-stage detail into a
  Skill that loads only when that stage is in play.
- **Local model quality** — the local tiers improve fast; a 7B that's "good enough" for more
  tasks shifts the route-local/route-cloud line and grows the saving. Re-benchmark when we pull
  newer Ollama tags.
- **Cadence:** a light monthly re-check is enough; don't burn a routine polling daily for news
  that moves the needle only a few times a year. (This itself is a token-efficiency point.)

---

## 8. Sources

Current as of 2026-06-25. External best-practice references behind the recommendations above:

- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — firecrawl.dev](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing 2026: Models, Caching, Batch & Optimization — finout.io](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Deep Dive: Cut Anthropic API Costs by 90% — agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Implementing LLM Model Routing with Ollama and LiteLLM — Medium/Hannecke](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8)
- [Anthropic pauses the June 15 Agent SDK billing change — digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Claude Code Skills in 2026: Complete Guide (vs Hooks, Subagents, MCP) — Totalum](https://www.totalum.app/blog/claude-code-skills-totalum)

---

*Filed by NARF per the founder's efficiency routine. Tracked as TD-15. Next review when any item
in [§7](#7-keep-up-to-date-a-standing-watch) moves — or when the t630 deploy session lands and
the hybrid in [§4](#4-the-hybrid-we-already-built--connect-it) becomes real instead of designed.*
