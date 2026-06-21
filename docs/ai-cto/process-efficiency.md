# Process Efficiency — Human ↔ AI Workflow Review

NARF (AI CTO) review of how we *use* Claude — token efficiency, prompting, and the
local/cloud split. Requested by the founder, 2026-06-21. Findings lead newest-first per
house style; the numbered findings are ranked by impact, not by date.

> **Honest framing first.** Per `docs/ai-cfo/budget.md`, Anthropic API is **~$5–15/mo**
> against a **<$30/mo** burn target — we are not bleeding money today. So this is about
> *habits that scale* (the bill that matters is the one at 50 customers and 2 operators,
> not this month's) and about *getting more done per session*, not emergency cost-cutting.
> The single biggest lever below (CLAUDE.md trimming) also makes Claude **faster and
> sharper**, which matters more than the dollars at our size.

---

## TL;DR — the five things worth doing

1. **Trim the CLAUDE.md files.** `localDNS` (326 lines) and this repo (295 lines) are well
   over the ~200-line guidance; every session pays for them whether relevant or not. Move
   workflow-specific prose into **Skills** (load on demand). **Biggest single win.**
2. **Stop defaulting to Opus + max thinking.** Match model and `/effort` to the task. This
   very routine ran on Opus 4.8 (1M) — a Sonnet job. ~5× cost difference, Opus vs Haiku.
3. **De-duplicate the house-style block.** The same ~15-line block is copy-pasted into all
   7 repos' CLAUDE.md. It's the one thing every session in every repo re-pays for.
4. **Use the Batch API for the non-urgent jobs** (monthly statements, these scheduled
   routines): 50% off, and it *stacks* with prompt caching (cached batch ≈ 5% of list).
5. **Adopt Anthropic's new context-editing + memory tools** in the LangGraph supervisor —
   reported +39% on long multi-step agent runs, and they fit our `langgraph-router/` exactly.

---

## 1. CLAUDE.md context bloat — the recurring tax (biggest lever)

**What's happening.** Every Claude Code session loads that repo's CLAUDE.md into context on
the first turn, on every prompt thereafter (cached, but still counted). Current sizes:

| Repo | Lines | Words | Note |
| ---- | ----- | ----- | ---- |
| localDNS | 326 | 2,728 | **Over budget** — full topology tables, deploy-path table, every known issue |
| DESIGN (this) | 295 | 2,608 | **Over budget** — funnel diagram, stage map, two AI-state sections |
| MARKETING | 214 | 1,445 | Slightly over |
| customers | 80 | 562 | Fine |
| claude-code-homelab | 75 | 371 | Fine |
| Azure-lab | 50 | 316 | Fine (stub) |

Industry guidance in 2026 converged on **keep CLAUDE.md under ~200 lines / essentials only**;
"loading every workflow into CLAUDE.md bloats the main context and slows the model down."

**Why it matters beyond tokens.** A 2,700-word always-on preamble dilutes attention — the
model spends budget re-reading the deploy-path table when you asked it to fix one Unbound
line. Leaner context = faster *and* more accurate, not just cheaper.

**The fix — split "always-on" from "on-demand":**
- **Keep in CLAUDE.md:** the invariants and rules a session must never violate — "push to
  `main`, no branches," the honesty rule, the privacy invariant, secrets policy, where the
  source of truth lives. These are genuinely always-on.
- **Move to Skills** (`.claude/skills/`, load only when triggered): the deploy-path table,
  the nftables deploy checklist (Section F), the full Unbound drop-in walkthrough, the
  statement-build procedure, the verification command blocks. Skill *descriptions* stay in
  context so Claude knows they exist; the *body* loads only when the task needs it. Target a
  skill body under ~500 tokens with deeper detail in linked reference files.
- **Net effect:** CLAUDE.md drops toward ~120–150 lines of pure invariants; the procedural
  bulk is one `Skill` call away when actually needed.

## 2. De-duplicate the house-style block across repos

The identical "House style: ordering & typography" block (~15 lines, ~250 words) is pasted
verbatim into **all 7** CLAUDE.md files. It's correct content, but it's the single most
redundant thing in the whole portfolio — re-paid on every session in every repo, and it
drifts the day someone edits one copy.

**Options (pick one):**
- Collapse each copy to a one-line pointer + the 3 rules that actually bite, linking the
  canonical copy (it already lives in full in this repo).
- Or treat it as a shared Skill / a generated include so there's one source of truth.

Low effort, portfolio-wide, and it ends the drift risk.

## 3. Model + effort discipline (don't run Opus on a doc edit)

Current list pricing (per 1M tokens, June 2026): **Opus 4.8 $5 / $25**, **Sonnet 4.6 $3 /
$15**, **Haiku 4.5 $1 / $5**. Opus is ~5× Haiku. Extended thinking bills as *output* tokens
and the default budget can be tens of thousands of tokens per request.

The most expensive default habit in 2026 is "run the biggest model on everything."
Right-size instead:
- **Haiku / `local-fast`:** routine edits, renames, lint fixes, commit messages, doc tweaks,
  link-checking, classification — most of what these repos need.
- **Sonnet:** normal coding, diffs, structured builds, this kind of research/advisory write-up.
- **Opus + thinking:** genuinely hard reasoning, cross-repo architecture, the gnarly debug.
- In Claude Code: `/model` to pick, `/effort` to dial thinking down (or
  `MAX_THINKING_TOKENS=8000` / disable thinking in `/config`) for simple work. `/clear`
  between unrelated tasks so stale context isn't re-billed every turn.

We already encode exactly this philosophy in `10-ai-orchestration/config.yaml` (local-fast →
local-smart → cloud tiers). The gap is applying the same discipline to **how we drive Claude
Code itself**, where Opus-by-default is easy to leave on.

## 4. Prompt caching hygiene

Claude Code caches the static prefix (system prompt, tool schemas, CLAUDE.md) automatically;
cache *reads* bill at ~10% of input. We don't configure it, but we can avoid breaking it:
- **Don't edit CLAUDE.md mid-session** — it invalidates the cached prefix and the next turn
  pays full price to re-cache. Batch CLAUDE.md edits at the start or end of a session.
- Keep the big static stuff *stable and up front*; keep the volatile stuff late in context.
- This is a free win once #1 makes the cached prefix small in the first place.

## 5. Batch API for the non-urgent jobs

The **Batch API is 50% off input and output**, async within 24h, and **stacks with prompt
caching** (a cached batch request can land near ~5% of a standard call). Candidates we
already run on a schedule, none of which need to be interactive:
- The **monthly statement generation** (Stage 06 / `localDNS` generator — "about a penny a
  home"). At scale this is the obvious batch workload.
- **These scheduled routines themselves** (like this one) — anything cron-driven and
  unwatched should prefer batch + a cheaper model over interactive Opus.

## 6. Adopt the new context-management tools in the supervisor

Anthropic shipped (and as of mid-2026 these are GA/beta on the platform) two features that
map directly onto our `10-ai-orchestration/langgraph-router/` (Odin/Heimdall) supervisor:
- **Context editing** — automatically trims stale tool calls/results as the window fills
  (reported +29% alone on long agent runs).
- **Memory tool** — file-based store/retrieve outside the context window; **together with
  context editing, +39%** on complex multi-step tasks. Server-side compaction is now
  recommended over client-side.

Our supervisor is exactly the kind of long-running, multi-tool agent these were built for.
Worth a Phase-2 spike in `ORCHESTRATION-BLUEPRINT.md`.

## 7. Hybrid local/cloud router — already strong, two notes

Credit where due: the LiteLLM router with a deterministic **privacy gate**, a **reasoning
ladder** (local distill → rented-GPU R1 → cloud overflow), local embeddings for RAG, and
capability-named tiers is genuinely best-practice — it's the architecture the 2026 guides
*recommend*, and we already have it. Two refinements:

- **Push more cheap work local.** The literature puts ~60–70% of real traffic in the
  "simple" bucket (classify / extract / format / short summarize) that a 3–7B local model
  handles fine. Make sure the *callers* (dispatcher, supervisor, any scripts) actually send
  that bucket to `local-fast`/`local-smart` rather than reflexively to a cloud tier.
- **Privacy fallback is still open (TD-14).** `local-reason` falls back to `cloud-overflow`,
  so a `sensitive` task can leak to cloud if the local model is down. Until that's fixed
  (fail *closed* to a local-only chain), the "sensitive never leaves the walls" guarantee
  isn't real. This is a correctness bug, not just efficiency — flagged P1 in tech-debt.

## 8. Keep the main session lean with subagents

For anything that means reading a lot of files or a multi-step sweep, spawn a subagent
(Explore / general-purpose) and let *it* hold the heavy context; the main session keeps only
the conclusion. This run used that pattern (web research + targeted file reads) instead of
dragging all 7 repos' full contents into one window.

---

## On the prompt that triggered this run

The founder asked me to critique the request itself. Fairly: it worked — it got a useful
result. But it was **maximally broad** ("ANYTHING that could help… Anything you could
possibly think of"), which pushes the model toward wide, expensive exploration and toward
the most powerful model + high thinking "to be safe." For a recurring routine that's the
costly default.

A tighter version that would cost less and return something more actionable:

> *"Review how we use Claude across the A777ance repos for token efficiency. Focus on: (1)
> CLAUDE.md size, (2) model/effort selection, (3) the local/cloud split in
> 10-ai-orchestration. Skip anything we already do well. Output: a ranked, actionable list
> with rough effort/impact for each, written to docs/ai-cto/process-efficiency.md. Use
> current (2026) sources. Run on Sonnet unless a finding needs deeper reasoning."*

Why it's cheaper/better: a **named scope** stops the model fan-out; an **explicit
deliverable + location** avoids a second clarifying round; "**skip what we do well**" avoids
paying to re-derive the router we already built; **naming the model** keeps a routine off
Opus. General prompting hygiene that applies to all our sessions: state the deliverable and
where it goes, give the model an explicit "don't bother with X," and set the model/effort to
the job.

**Meta-point for routines:** an unwatched scheduled run on Opus 4.8 (1M context) with all 7
CLAUDE.md loaded is about the most expensive way to ask a question. Pin scheduled routines to
Sonnet/Haiku + batch where the task allows, and scope them to the one or two repos they need.

---

## Suggested next actions (effort → impact)

| Action | Effort | Impact |
| ------ | ------ | ------ |
| Trim `localDNS` + this repo's CLAUDE.md to invariants; move procedures to Skills | M | High |
| Collapse duplicated house-style block to a pointer (all 7 repos) | S | Med |
| Make model/effort discipline a written rule (and pin routines to Sonnet/Haiku) | S | High |
| Route the monthly statement job through the Batch API | S | Med (scales) |
| Phase-2 spike: context-editing + memory tool in the LangGraph supervisor | M | High (at scale) |
| Close TD-14 (privacy fail-closed) — correctness, not just efficiency | S | High |

---

## Sources (current as of 2026-06-21)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Context editing — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Managing context on the Claude Developer Platform](https://www.anthropic.com/news/context-management)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
