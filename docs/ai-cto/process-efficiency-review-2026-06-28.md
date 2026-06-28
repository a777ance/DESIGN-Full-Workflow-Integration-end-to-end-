# Process efficiency review — user ↔ AI workflow

**Date:** 2026-06-28 · **Author:** NARF (AI CTO), scheduled review · **Scope:** how we work *with*
Claude across the seven repos — token cost, prompting, model/tooling choices, and where our own
local-LLM stack should be doing more of the work.

This is a findings doc, not a decision. Nothing here changes a config until it's adopted. Numbers
are measured from this repo on the review date; web best-practice claims are cited at the bottom.

---

## TL;DR — the five things worth doing first

| # | Move | Effort | Est. saving | Where |
| - | ---- | ------ | ----------- | ----- |
| 1 | Trim the two big `CLAUDE.md` files and lazy-load detail via skills | M | ~50–80% of a fixed per-session tax that's currently ~10–12K tokens *every turn* | `localDNS`, `DESIGN` |
| 2 | Stop reading all 9 AI-CTO/CFO state files at every session start; load on demand | S | ~800 lines (~9–11K tokens) off session-start cost | `DESIGN` |
| 3 | Route more of our own work through the existing LiteLLM ladder (local first, Claude for the hard 10%) | M | 60–80% on the routable share | t630 router |
| 4 | Default to Sonnet/Haiku for mechanical work; reserve Opus for reasoning | S | 2.5–5× on every downgraded call | all |
| 5 | One task per session + `/compact`/`/clear` discipline; point at files, not "the repo" | S | 40–85% reported by teams doing only this | all |

The single biggest lever is **#1 + #2 together**: we pay a large fixed token cost on *every single
turn* before any actual work happens, and it's almost entirely self-inflicted.

---

## 1. The fixed per-session tax (biggest lever)

Every Claude Code turn re-sends the project `CLAUDE.md`. Today:

| File | Lines | Bytes | ~Tokens (≈bytes/4) |
| ---- | ----- | ----- | ------------------ |
| `localDNS/CLAUDE.md` | 326 | 20.5 KB | ~5,100 |
| `DESIGN/CLAUDE.md` | 295 | 18.0 KB | ~4,500 |
| `MARKETING/CLAUDE.md` | 214 | 10.7 KB | ~2,700 |

A 5,000-token `CLAUDE.md` is a **5,000-token tax on every turn of every session in that repo** —
it doesn't get cheaper the longer you work; it compounds. Industry guidance now is to keep
`CLAUDE.md` **under ~200 lines** and push domain detail into *skills* that load only when the task
needs them; one writeup measured ~15K tokens/session recovered (~82%) by moving from
"everything in CLAUDE.md" to on-demand skills.

Our two flagship files are ~50–60% over that line. They're excellent *documents* — but a lot of
their content (the full Unbound deploy-path table, the nftables checklist, the funnel ASCII art) is
reference that a session needs maybe 1 turn in 20.

**Recommendation:** split each big `CLAUDE.md` into a lean core (the briefing, the invariants, the
house-style rules, the "read this on session start" pointers) plus skill/reference files the core
*points to*. Keep the voice rules and the honesty rules in the core — those genuinely apply every
turn. Move the deploy-path and checklist tables out.

## 2. Session-start state-file loading (`DESIGN` hub)

`DESIGN/CLAUDE.md` instructs reading, at every session start: 4 AI-CTO files + 6 AI-CFO files +
the MARKETING spoke context. Measured here:

```
ai-cto:  decisions 131 + portfolio 155 + roadmap 64 + tech-debt 23   = 373 lines
ai-cfo:  portfolio 168 + decisions 69 + metrics 67 + runway 64 + budget 64 = 432 lines
                                                            total ≈ 805 lines (~9–11K tokens)
```

That's loaded *before the user has asked for anything*, on a CFO question and a CTO question alike.
A pure-CTO session pays the full CFO load and vice-versa.

**Recommendation:** make session-start reading **conditional and minimal** — read `portfolio.md`
for the relevant hat only, and load `decisions/metrics/runway/budget` *when a decision or number is
actually in play*. The CLAUDE.md can say "on a finance task, read §6 files; on an architecture
task, read §5 files" instead of "read all of these every time." This is the cheapest big win on
the list — pure instruction edit, no infra.

## 3. Use the LLM router we already built (hybrid local + cloud)

We are unusually well-positioned here: `localDNS/10-ai-orchestration` already runs **LiteLLM +
Open WebUI + a privacy-aware dispatcher** with a reasoning ladder — `local-reason`
(deepseek-r1:1.5b on the t630, cool/cheap) → `cloud-gpu-reason` (full R1 on a rented GPU) →
`cloud-overflow`. The hybrid architecture the whole industry is converging on in 2026, we have a
first draft of on the thin client.

The 2026 consensus: **route by task complexity** — ~60–70% of real workloads are simple
(classify, extract, format), ~20–30% moderate, and only ~10% truly need a frontier model. Teams
report **60–80% cost cuts** routing the simple/moderate share to local models and reserving
Claude's API for the hard tail.

What we're under-using: the router exists, but most of our day-to-day still goes straight to Claude.
Candidate work to push onto `local-reason` / Open WebUI:
- Drafting boilerplate (Handled-For-You log entries, statement copy first drafts, commit-message
  drafts) — then Claude polishes only if needed.
- Classification/extraction over the roster and call notes.
- "Rubber-duck" and summarization passes that don't need Opus-grade reasoning.

**Caveat — fix TD-14 first.** The dispatcher's privacy guarantee has a known hole: a
`sensitive`-tagged task can fail over from `local-reason` to `cloud-overflow` (Claude cloud)
because `allow_cloud=False` isn't enforced at the LiteLLM failover layer. Routing *more* private
data through the ladder makes that gap more dangerous. Close it (local-only fallback, fail closed)
before we lean on local routing for anything touching real customer data in `customers/`.

## 4. Model selection — stop paying Opus rates for mechanical work

Default everywhere right now is effectively top-tier. Current API pricing (per 1M tokens):

| Model | Input | Output | Use for |
| ----- | ----- | ------ | ------- |
| Opus 4.8 | $5 | $25 | Real reasoning, architecture, the hard 10% |
| Sonnet 4.6 | $3 | $15 | Most coding & doc work — the default workhorse |
| Haiku 4.5 | $1 | $5 | Classification, formatting, short mechanical edits |

Haiku is **5× cheaper on output than Opus**; Sonnet is ~1.7×. For doc-link checking, reformatting
to house style, Z→A re-sorting, and link-fix passes, Haiku or Sonnet is plenty. Reserve Opus for
the genuinely hard calls (architecture decisions, the statement-honesty judgment calls, debugging
the DNS split). This is per-call and free to adopt — just pick the model.

## 5. Prompt caching — make the fixed cost cheap when we can't remove it

Whatever fixed context survives #1/#2, **prompt caching** can serve at ~0.1× input price on repeat
turns (write costs 1.25× for the 5-min TTL; break-even is ~2 requests). Claude Code does much of
this automatically, but it only works if the cached *prefix is byte-stable*. Our enemy here is any
per-turn-varying content early in context (timestamps, "current date", IDs). Keep the volatile bits
*late*; keep `CLAUDE.md` and the state files frozen within a session.

**Caution flag from the news:** the **March 2026 prompt-caching incident** caused 10–20× token
inflation from two Anthropic caching bugs, silently. Worth a periodic sanity check on
`cache_read_input_tokens` / billing so we'd catch a recurrence early rather than after a surprise
bill.

## 6. Context hygiene (cheap habits, large aggregate)

Straight from current Claude Code cost guidance — teams report **40–85%** reductions from these
alone:
- **One task per session.** Unrelated work in one long chat drags stale context into every turn.
- **`/compact` before a session gets long; `/clear` when switching topics.** Tool output (file
  reads, command dumps, MCP responses) is the biggest silent drain — it appends in full and
  compounds.
- **Point at specific files, not "the whole project."** Especially in `localDNS` and `DESIGN`.
- **Subagents for heavy context** — let a subagent accumulate the big reads and return a
  conclusion, keeping the main session lean. (Our `tools/check-docs.py` style work is a good
  subagent candidate.)

## 7. Scheduled-routine specifics (this run is one)

Routines like this run unattended, so the only thing that reaches a human is a notification. Two
efficiency notes for our own routines:
- **Don't over-load context for a watch task.** A "did anything break?" routine doesn't need all 9
  state files — it needs the one signal it's watching. Same lesson as #2.
- **Pick the model to the job.** A routine that just checks CI or diffs a file should run on Haiku;
  only escalate to Opus when it actually finds something worth reasoning about.

---

## Critique of the prompt that triggered this review

The triggering prompt was, paraphrased: *"Locate inefficiencies in our PROCESS… reduce token use…
better prompting… leverage other AI… hybrid local + Claude… anything… search the web… keep up to
date… check the news… and tell me if THIS prompt is inefficient."*

It's a **good** prompt for an open-ended research task — it states the goal, the constraints
(token cost, hybrid, currency), grants tool latitude (web search), and even asks for
self-critique. For *that* job, breadth is a feature. But measured purely on tokens-per-answer it
has three soft spots, and since you asked:

1. **No scope or success criterion.** "Anything you could possibly think of" maximizes output
   length — the model has no stopping signal, so it errs long (this very document is longer than a
   tightly-scoped prompt would have produced). If the goal is *the top 5 changes to make this
   quarter*, say so; you'll get a shorter, more decisive answer for fewer tokens.
2. **Several distinct asks bundled into one turn** (audit + prompting advice + hybrid strategy +
   news + prompt-critique). Each is answerable, but bundling forces one giant context-gathering
   pass. For recurring versions of this, splitting into scoped sub-tasks (each on the right model)
   is cheaper than one Opus mega-turn.
3. **"Check the news / keep up to date" with no anchor.** Open-ended currency requests trigger
   broad web fan-out. Naming what you care about ("Claude Code pricing/feature changes since last
   month; any caching incidents") gets the same signal for far fewer search calls.

A leaner phrasing that keeps the intent: *"Give me the top 5 token-reduction changes for our
repos this quarter, ranked by impact/effort, using our existing LiteLLM router where it fits.
Check for any Claude pricing or caching news since 2026-05. Flag if this prompt itself is
wasteful."* Same answer, smaller bill, clearer stopping point.

And the meta-point: **routing matters for prompts too.** A broad survey like this is Opus-worthy.
A "re-sort this list Z→A" request is not — sending it to Opus is the prompt-level version of the
model-selection waste in §4.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 Tips for Smart Claude Code Token Saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Reduce Claude Code token usage by 90% — Medium](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [Token Economics in 2026: No More Cheap Claude](https://age-of-product.com/token-economics-2026/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM Gateways & Model Routing: Cut AI Costs 2026 — Lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [Context Engineering Guide 2026 — The AI Corner](https://www.the-ai-corner.com/p/context-engineering-guide-2026)
- [Context Engineering vs Prompt Engineering for AI Agents — Firecrawl](https://www.firecrawl.dev/blog/context-engineering)

Model pricing (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5 per 1M tokens) and
prompt-caching economics (~0.1× read, 1.25×/2× write) are from the Anthropic API reference current
as of this date.
