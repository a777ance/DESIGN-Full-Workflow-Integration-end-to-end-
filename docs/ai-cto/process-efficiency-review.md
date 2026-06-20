# Process efficiency review — user ↔ AI workflow & token spend

*Prepared 2026-06-20 by NARF (AI CTO), in response to a standing request to hunt for
inefficiencies in how we work with Claude and where token spend can be cut. Web-sourced
best practices are dated; this field moves weekly, so re-run this review quarterly.*

> **TL;DR — the three biggest wins, in order of effort-to-payoff:**
> 1. **Dedupe & trim the CLAUDE.md files.** Cross-repo sessions load ~14.6K tokens of
>    project instructions *every turn*; ~1.8K of that is the House-style block pasted
>    verbatim into 6 files. One-time edit, pays on every prompt forever.
> 2. **Use the Batch API (–50%) for everything that can wait a few hours** — the monthly
>    statement run, nightly reports, NotebookLM bridge syncs, eval passes. No quality loss.
> 3. **Actually route through the t630 LLM ladder we already built.** Stage 10 already has
>    LiteLLM + Ollama local models + a cloud fallback. Cheap/routine work shouldn't touch
>    the Claude API at all.

---

## 1. The single most concrete inefficiency: our own context files

Measured today across the six repos:

| File | ~Tokens |
| ---- | ------- |
| `localDNS/CLAUDE.md` | ~5,100 |
| `DESIGN-…/CLAUDE.md` | ~4,500 |
| `MARKETING/CLAUDE.md` | ~2,700 |
| `customers/CLAUDE.md` | ~1,000 |
| `claude-code-homelab/CLAUDE.md` | ~720 |
| `Azure-lab/CLAUDE.md` | ~570 |
| **Total** | **~14,600** |

A 5,000-token CLAUDE.md costs 5,000 tokens *on every single turn* of a session, because it
sits in the context window the whole time. In a normal single-repo session only that repo's
file loads — but any **portfolio / cross-repo session** (like this one, run from `/home/user`)
loads **all of them**: ~14.6K tokens carried on every turn before we've read a line of code.

Two fixes, both one-time:

- **Dedupe the House-style block.** It is pasted *verbatim* into all 6 files (~1,215 chars ≈
  300 tokens each → ~1,800 tokens of pure duplication). Move it to a single
  `HOUSE-STYLE.md` (in DESIGN, the portfolio hub) and replace the inline copy in each repo
  with a one-line link: *"House style → DESIGN-…/HOUSE-STYLE.md."* Claude reads the link only
  when a task actually needs the typography rules.
- **Trim each CLAUDE.md to stable, high-value facts.** Anthropic's own guidance: keep project
  instructions short — how to run tests, deploy paths, hard invariants, "do not touch" rules.
  The long prose ("why pest control not lawn care", full money-flow diagrams) belongs in
  README/workflow-context, loaded on demand, not in the always-on briefing. `localDNS` and
  `DESIGN` are the two worth pruning first; target ~40–50% smaller.

Estimated saving on a typical portfolio session: **~2K tokens/turn from dedup alone**, more
from trimming — multiplied by every turn, every session.

---

## 2. Levers we are not yet pulling (ranked by payoff)

**a. Prompt caching — the easiest big win.** Cached input bills at ~10% of normal input
(a 90% cut on the cached portion). The stable prefix — CLAUDE.md + schema + the statement
template — is identical across many calls, so it should be cached. Rule of thumb: worth it
at 3+ reads inside the 5-min TTL, or 5–7+ reads for the 1-hour TTL. Claude Code applies this
automatically to its system prompt; for **our own scripts that call the Claude API** (the
statement composer, any batch jobs) we should mark the stable prefix as a cache breakpoint.

**b. Batch API — 50% off, no quality difference.** Anything that tolerates a few hours of
latency should go through Message Batches: the **monthly statement generation run (stage 06)**,
nightly stat rollups, the NotebookLM "Rainbow Bridge" syncs, and any eval/QA passes. This is
free money for our scheduled, non-interactive work — which is most of it.

**c. Hybrid local routing — we already own the hardware.** `10-ai-orchestration` on the t630
already runs LiteLLM + Ollama with a reasoning ladder (`local-reason` on CPU, cloud fallback).
Industry data: routing routine traffic to a local/cheap model cuts LLM cost 60–80%; the trick
is *not* sending long-context (>3K tokens), strict-format, or multi-step-reasoning work to a
small local model — those degrade. Good local-tier candidates for us: classifying inbound
leads, drafting "Handled For You" log lines, first-pass summaries, commit-message drafts.
Reserve Claude (Opus/Sonnet) for the kept document and anything customer-facing.

**d. Right-size the model per task.** June 2026 rates: Haiku 4.5 $1/$5, Sonnet 4.6 $3/$15,
Opus 4.8 $5/$25 per 1M (in/out). Most CRM/roster bookkeeping and extraction is Haiku/Sonnet
work; Opus only where reasoning quality changes the outcome. Adaptive thinking (Sonnet 4.6 /
Opus 4.6+) already skips deep reasoning on simple asks — prefer those models for mixed
workloads. Note: 1M-context models carry **no long-context surcharge** now, so big-context
calls are cheaper than they used to be — but that's a reason to cache, not to be careless.

**e. In-session hygiene (Claude Code).** `/clear` between unrelated tasks instead of letting
one session accumulate; `/recap` to resume without replaying the whole transcript; cap bash
output length so long logs don't flood context; make **incremental** requests ("refactor the
booking handler") not sweeping ones ("refactor all of stage 03").

**f. Subagents for fan-out, not for everything.** When a task means reading many files
(codebase research, cross-repo audits), delegate to a subagent: it burns its own context
window and returns only a summary, keeping the main window lean. Use a *skill* when there's
reusable domain logic; a *subagent* for isolated/parallel work. Don't spin them up for simple
one-file lookups — the overhead isn't worth it.

---

## 3. On the prompt that triggered this review

The request was effectively *"find any inefficiency anywhere, search the web if useful, look
at everything."* That open-endedness is itself the inefficiency it's asking about: an
unbounded scope forces broad, expensive exploration and a sprawling answer, and there's no
defined "done." Better-shaped versions of the same ask:

- **Scope it:** *"Audit token spend on our scheduled routines this month and name the top 3
  fixes by $ saved."* — bounded, measurable, one clear deliverable.
- **Constrain output:** add *"≤1 page, bullets, no preamble"* — output tokens are the
  expensive half ($25/1M out vs $5/1M in on Opus).
- **Separate the two jobs:** "research best practices" and "audit our setup" are different
  tasks. Run them separately (or as parallel subagents) so each stays focused.
- **Cache the standing context:** a recurring routine like this should pin a short, stable
  brief ("here's our stack: t630 + LiteLLM ladder + 3 repos; here's last quarter's review")
  so each run starts from a cached prefix instead of rediscovering the setup.

General prompting rules that save the most: say what *not* to do and how long the answer
should be; give the one example you want matched rather than describing it; ask for the
answer first and the reasoning only if needed.

---

## Sources (2026, verify freshness on next review)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Best practices for Claude Code — Docs](https://code.claude.com/docs/en/best-practices)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Anthropic Message Batches API: 50% Off — Respan](https://www.respan.ai/articles/anthropic-message-batches-api)
- [Claude Prompt Caching: 90% Cost Reduction Guide — Respan](https://www.respan.ai/articles/claude-prompt-caching)
- [Hybrid LLM Routing: Ollama + Claude API — DEV](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Sub-Agents Explained — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Anthropic million-token pricing change — The New Stack](https://thenewstack.io/claude-million-token-pricing/)
