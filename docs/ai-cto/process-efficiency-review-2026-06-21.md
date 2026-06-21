# Process efficiency review — user ↔ AI workflow (2026-06-21)

A standing-routine review of how we *use* Claude (and other AI) across the A777ance
repos: where tokens leak, where prompting can be tighter, and where the hybrid
local-LLM + Claude-API setup we already built can do more of the work. Findings are
ranked by return-on-effort. Newest review at top per house style.

> **One-line takeaway:** the single biggest lever is *fixed context cost paid on every
> routine run* (CLAUDE.md bloat × broad repo scope), and as of **June 15 2026** that cost
> is now real money, not subscription quota — see Finding 0.

---

## 0. ⚠️ NEWS — the billing change that reframes all of this (June 15 2026)

Anthropic moved the **Claude Agent SDK, `claude -p`, Claude Code GitHub Actions, and
third-party agents off the Claude subscription limit** onto a separate metered monthly
credit ($20 Pro / $100 Max 5× / $200 Max 20×), **billed at full API rates, no rollover**.

Our **scheduled routines run on exactly this agent infrastructure.** Until now token
waste in a routine was hidden inside a flat subscription; now every wasted token in a
scheduled run is metered. **Token efficiency just changed from "good hygiene" to a line
item.** Everything below now has a dollar value attached.

Action: confirm which plan/credit pool the routines bill against, and set a monthly cap.

Sources: [Anthropic billing change June 15 2026](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/) ·
[Claude Code what's new](https://code.claude.com/docs/en/whats-new)

---

## 1. Highest ROI — fixed cost paid on *every* run

### 1a. CLAUDE.md files are encyclopedias, not lookup tables
Combined, our briefing files are ~1,040 lines (localDNS 326, DESIGN 295, MARKETING 214,
customers 80, claude-code-homelab 75, Azure-lab 50). A routine scoped to all seven repos
loads **all** of them into context before it reads a single line of the actual task —
every run, forever. This very review's session did exactly that.

Best practice (consistent across every 2026 token-cost guide): **CLAUDE.md should read
like a lookup table, not a brain dump.** It is never lazy-loaded or evicted, so every byte
is paid for on every turn of every session.

- **Keep:** the stage map, deploy-path tables, invariants, "don't do X" rules — the facts
  Claude can't infer.
- **Move out (link, don't inline):** rationale, history, long prose. The *why* belongs in
  `network-context.md` / `workflow-context.md` (we already have these) — link to them; don't
  duplicate their content in CLAUDE.md.
- Target: each CLAUDE.md ≤ ~120 lines of dense reference. localDNS and DESIGN are the
  obvious trim candidates.

### 1b. Scope each routine to the repos it actually touches
A routine listing all seven repos pays the full CLAUDE.md tax even when it only edits one.
**Scope each routine (and its branch list) to the 1–2 repos it works in.** A "check the
network box" routine has no reason to load MARKETING + customers + Azure-lab.

---

## 2. Model selection — stop defaulting to Opus

This routine ran on **Opus 4.8 [1m]** — the most expensive tier, with the priced-up 1M
context window — to do what is essentially research + summarization. Opus is ~5× Haiku per
token; published task-routing case studies show **75–83 % cost cuts** purely from matching
model to task.

| Routine type | Right model |
| --- | --- |
| Triage, classification, summarize logs, news-skim, doc-link checks | **Haiku 4.5** |
| Feature work, bug fixes, standard refactor, code review, this kind of analysis | **Sonnet 4.6** |
| Multi-file refactor, architecture calls, unfamiliar-codebase debugging | **Opus** (only here) |

Set the *default* routine model to Sonnet (or Haiku for pure monitoring) and escalate to
Opus explicitly. Don't pay Opus rates on a daily summarizer.

Sources: [Choosing a model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model) ·
[task-based cost guide](https://kansei-link.com/en/insights/claude-model-cost-guide-2026.html)

---

## 3. Prompt caching on our *own* API paths (90 % off cached input)

Claude Code routines already auto-cache. But our **own** LLM calls — the LangGraph
supervisor (Odin/Huginn), NARF/ZORT automations, anything hitting the LiteLLM
`cloud-*` tiers — should mark the stable prefix (system prompt, tool schemas, the repo
context we resend) with `cache_control`. Cached input is **~90 % cheaper**; reused
prefixes ≥ 1,024 tokens qualify. LiteLLM passes `cache_control` through to Anthropic.
Watch `cache_read_input_tokens` to confirm hits.

Sources: [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) ·
[Anthropic pricing/caching 2026](https://www.finout.io/blog/anthropic-api-pricing)

---

## 4. Use the hybrid router we already built — and mind its one seam

`10-ai-orchestration` already does the textbook-correct thing: local Ollama tiers on the
t630 as default, Claude as failover/overflow, a deterministic privacy gate, graceful
fallbacks. The 2026 hybrid-architecture literature confirms this pattern cuts LLM cost
**60–80 %** by serving the ~60–70 % of "simple" requests (classify / extract / format /
summarize) locally and reserving the frontier model for the ~10 % that needs it.

**Do more of it where it's free to:** route drafting, log summarization, classification,
and RAG-grounded lookups to `local-fast`/`local-smart`/`local-embed`; reserve Claude for
synthesis and the hard 10 %.

**The seam to name honestly:** Claude Code **web/scheduled routines run in Anthropic's
cloud**, and the t630 router lives behind WireGuard on the LAN — the routines **cannot
reach the local box.** So the local router pays off for *interactive* work (Open WebUI,
the console, the LangGraph supervisor) but **not** for the web routines. Two ways to close
it if we want routines on local inference: (a) expose the router via a Tailscale node the
routine can reach (same trick as `cloud-gpu-reason`), or (b) keep heavy local work in
interactive sessions and keep routines lean + cheap (Findings 1–2). Recommend (b) for now —
it's the liquidity-before-app instinct applied to our own tooling.

Sources: [hybrid cloud-local architecture 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
[local models with Claude Code](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)

---

## 5. Batch API (50 % off) for anything non-interactive

Scheduled routines are non-interactive by definition. For our own bulk LLM jobs that
aren't time-critical (bulk classification, any statement-adjacent LLM pass, backfills),
the **Anthropic Batch API is ~50 % cheaper** and stacks with caching. Not every routine
fits (some need a same-minute answer), but the recurring bulk ones do.

---

## 6. Subagents & context isolation for research-heavy routines

When a routine fans out across files or the web (like this one), spawn **subagents**
(Explore / deep-research): their verbose output — search dumps, file reads — stays in the
subagent's context and only the summary returns. Keeps the main context (the expensive one)
small. Also: `/clear` or compact between unrelated phases; parallelize independent searches
(this review ran its web searches in one batch).

Source: [reduce Claude Code token usage](https://www.firecrawl.dev/blog/claude-code-token-efficiency)

---

## 7. Cadence — don't deep-research daily

The "keep up to date, it changes day by day" instinct is right about the *field* but wrong
about the *spend*. A full web sweep + Opus synthesis every day re-discovers a landscape
that barely moves in 24h. Better split:
- **Daily (Haiku, cheap):** a 3-bullet news skim — only escalates/notifies on a real change
  (a billing change, a new model, a deprecation).
- **Monthly (Sonnet):** this kind of deeper review.

---

## 8. The prompt itself — yes, it's inefficient, and here's the fix

The triggering prompt was effective at signalling intent but expensive to run as a
*recurring* routine, because it is unbounded: "ANYTHING that could help," "Search the web,"
"Check the news," "keep UP TO DATE… day by day." An open mandate with no scope, no budget,
and no output target invites maximal exploration on every run — the most expensive shape a
recurring routine can take.

Concrete fixes:
- **Scope it.** Name the target ("the scheduled-routine workflow and LiteLLM config"), not
  "our PROCESS."
- **Bound it.** "≤ N web searches, prefer subagents for fan-out, Sonnet not Opus."
- **Target the output.** "Write findings to `docs/ai-cto/process-efficiency-review-<date>.md`;
  notify only if something changed since last run." (Avoids re-deriving the same report.)
- **Set cadence in the prompt.** Daily skim vs. monthly deep — see Finding 7.

A tighter rewrite:

> *Monthly, on Sonnet: review how we use AI across the routines + `10-ai-orchestration`.
> Use subagents for any web/file fan-out; cap at ~6 searches. Append findings (newest-first)
> to `docs/ai-cto/process-efficiency-review.md` as a dated section. Notify only if a finding
> is new or actionable since the last entry — otherwise stay silent.*

---

## Do-now checklist (ranked)
1. Confirm routine billing pool + set a monthly cap (Finding 0).
2. Trim localDNS + DESIGN CLAUDE.md toward lookup-table density; push prose to the
   `*-context.md` files (1a).
3. Scope each routine + branch list to the repos it touches (1b).
4. Default routines to Sonnet/Haiku; reserve Opus explicitly (2).
5. Add `cache_control` to stable prefixes on our own LiteLLM/API calls (3).
6. Split this review into a cheap daily skim + monthly deep pass (7); tighten the routine
   prompt (8).
