# Process-efficiency audit — user↔AI loop & token use (2026-06-25)

**Scope:** the *process* between the operator and Claude across the A777ance repos —
where tokens get spent for no benefit, where prompting can be tighter, and where work
should be pushed off the Claude API onto the local LLM stack you already run. Findings
are ordered **highest-leverage first**. Estimated savings are rough but directional.

A companion to `RECOMMENDED-CHANGES.md` — that file audits doc *drift*; this one audits
doc/process *cost*. Where they overlap (the house-style duplication) it's flagged.

---

## TL;DR — the five moves that matter

| # | Move | Effort | Est. token saving |
| - | ---- | ------ | ----------------- |
| 1 | Trim the two big CLAUDE.md files under ~200 lines; move detail to README/context files | 1 hr | ~30–40% of every session's base load |
| 2 | Stop the mandatory "read 4–6 files at session start" — make it on-demand | 30 min | ~5–15k tokens *per session*, every session |
| 3 | Route cheap/bulk work to the local LiteLLM ladder you already run (`localDNS` stage 10) | already built | 60–80% on the offloaded slice |
| 4 | Session hygiene as a habit: `/clear` between repos, `/compact` mid-task, scope by folder | free | biggest *real-world* lever — long threads re-bill the whole transcript every turn |
| 5 | De-duplicate the house-style block via a single sourced file (6 verbatim copies today) | 30 min | small tokens, large drift-prevention |

---

## 1. The base load: CLAUDE.md is doing too much

Every session silently loads the active repo's full `CLAUDE.md` **before** the task —
it's the first thing in context and it's re-billed on cache misses. Current sizes:

| Repo | CLAUDE.md lines | Anthropic guidance |
| ---- | --------------- | ------------------ |
| `localDNS` | **326** | "keep under ~200 lines" |
| `DESIGN-…` | **295** | over |
| `MARKETING` | 214 | slightly over |
| `customers` | 80 | fine |
| `claude-code-homelab` | 75 | fine |
| `Azure-lab` | 50 | fine |
| **Total across repos** | **~1,040** | — |

`localDNS/CLAUDE.md` and its `README.md` carry the **same** service table, port list,
WireGuard peers, hardware specs and DNS-split narrative twice (already flagged as
recommendation #2 in `RECOMMENDED-CHANGES.md`). CLAUDE.md is loaded automatically;
README is only read when needed — so the duplicated detail is paying the automatic-load
tax for no reason.

**Fix.** CLAUDE.md should be the *index and the invariants*, not the manual. Keep:
the one-line "what this repo is," the house-style pointer, the deploy-path table (it's
load-bearing and unique), and the known-issues table. Push the long prose (the Unbound
DNS-split essay, the nftables deploy checklist, the verification command dumps) into
`README.md` / `network-context.md` and leave a one-line pointer. Target: both big files
under 200 lines. Expect ~30–40% off the base context load every session.

## 2. Mandatory session-start reads are a per-session tax

`DESIGN-…/CLAUDE.md` instructs, at *every* session start:

- **NARF (CTO):** read `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md`
- **ZORT (CFO):** read `portfolio.md`, `decisions.md`, `metrics.md`, `runway.md`,
  `budget.md`, **plus** `MARKETING/docs/ai-cfo/context.md`

That's up to **10 files pulled into context before the task is even known** — whether the
session is a one-line typo fix or a financial review. The other repos do the same with
their `docs/ai-cto/context.md`.

**Fix.** Change the instruction from "read these now" to "these exist; read the one(s)
relevant to this task." A CTO doc-tweak doesn't need the runway model; a Stripe question
doesn't need the roadmap. Front-loading them is convenient once and expensive forever.
Net: 5–15k tokens saved on the majority of sessions that don't touch them.

## 3. You already own the hybrid local-LLM offload — use it as the *first* tier

`localDNS` stage 10 is a full LiteLLM gateway + Ollama-class models + a reasoning ladder
(`local-reason` on the t630, `cloud-gpu-reason` on a rented GPU, `cloud-overflow`
fallback). The industry pattern in 2026 is exactly this: **60–70% of LLM requests are
simple** (classify, extract, format, summarize) and a 7B-class local model clears them at
acceptable quality; route only the ~10% that need frontier reasoning to Claude. Reported
savings: **60–80%** on the offloaded slice.

Concrete A777ance candidates to route *local* (no Claude tokens):
- Drafting/lint of "Handled For You" log lines and statement copy from a template
- Roster field extraction / normalization, sidecar.json scaffolding
- First-pass summaries of CI logs, `check-docs.py` output, diffs
- Classifying inbound leads, deduping the master list

Keep Claude for: cross-repo reasoning, the honesty-rule judgment calls, architecture/ADRs,
anything touching real money or customer data. **LiteLLM already gives you one endpoint
with automatic cloud fallback** — so a local miss silently escalates to Claude rather than
failing. This is the single biggest structural lever and the infrastructure is built.

## 4. Session hygiene — the lever that pays every day

The dominant real-world token drain isn't the prompt, it's **long threads**: every new
message re-bills the entire conversation, including stale instructions and superseded code.
Habits that help more than any config:

- **`/clear` when switching repos or tasks.** You work across 7 repos — a thread that
  drifts from `localDNS` to `MARKETING` is carrying dead `localDNS` context the whole way.
- **`/compact` mid-task** when Claude starts losing the thread, instead of re-explaining.
- **`/recap`** (new, Apr 2026) to resume without replaying the whole transcript.
- **Scope the ask to a folder.** "Fix the booking-form copy in `03-funnels-and-capture/`"
  reads one stage; "review the funnel" reads the repo.
- **Batch related edits into one prompt** instead of "change this… now that… also this."

## 5. De-duplicate the house-style block (and stop the drift)

The ~38-line house-style block is **byte-identical in 6 places** (5 CLAUDE.md files +
the homelab template). `RECOMMENDED-CHANGES.md` #1 already flags the drift risk; the
process angle is that it's also redundant load. CLAUDE.md supports `@path` imports —
make `docs/house-style.md` canonical and replace each copy with a single
`@<relative>/house-style.md` line (or, minimally, a "edited? update all 6" stamp). Fixes
the drift and the duplication in one move.

## 6. Prompt-caching hygiene (matters most if/when you call the API directly)

For Claude Code the harness manages caching, but if any of your automations (stage 11,
the langgraph-router, statement generation) call the Claude API directly, the 2026 rules:

- Cache reads cost ~**10%** of normal input; a stable cached prefix cuts input cost 60–90%.
- **Don't put volatile content in the cached prefix** — timestamps, "Last updated:
  YYYY-MM-DD" lines, per-customer names. Those cause a cache miss *every* call. Keep
  per-household data in the *user* turn, the template/system instructions in the cached prefix.
- TTL dropped to **5 min** in early 2026; for a batch job (e.g. rendering many statements
  back-to-back) the 1-hour cache option can be cheaper despite the higher write cost.

This directly serves the honesty/template split: statement *boilerplate* = cached prefix,
*measured figures* = per-call user content.

## 7. Tactical settings

- **Cap tool output** (e.g. `MAX_MCP_OUTPUT_TOKENS` / output limits ~8k) so a runaway
  `nft list` or log dump doesn't flood context. None of your repos set this today (only
  `Chronikomicon` has a `.claude/settings.json` at all).
- **Default to Sonnet, escalate to Opus deliberately.** Opus is ~5× Sonnet per token /
  drains a subscription window faster. Most doc edits and roster work are Sonnet-grade;
  reserve Opus for cross-repo reasoning and the hard calls.
- **Use subagents for fan-out research/audits** (like this one): they run in their own
  context and return only a summary, keeping the main thread clean. The cross-repo
  consistency audits you already do are the textbook use case.

---

## 8. About *this* prompt (you asked)

The prompt that triggered this audit was effective at intent but **inefficient by its own
yardstick** — it's the "change this… also… anything… ANYTHING" shape that maximizes
scope and therefore tokens. Specific issues:

- **Unbounded scope.** "Anything you could possibly think of," "ANYTHING that could
  help" invites the model to explore exhaustively and read widely. Open-endedness is the
  most expensive instruction you can give.
- **Two tasks in one** (audit the process *and* critique the prompt) — fine, but undeclared
  priority means the model guesses how to weight them.
- **No output contract.** No target length, format, or destination, so the model has to
  pick — and tends to over-produce.
- **Strong recency demand** ("keep UP TO DATE, check the news, day by day") triggers
  multiple web searches; worth it here, but it's a token multiplier to invoke knowingly.

A tighter version of the same request:

> *Audit our Claude-usage process for token waste across the repos. Prioritize: (1)
> CLAUDE.md / session-start load, (2) offloading work to the local LiteLLM stack, (3)
> session habits. Check 2026 best practices on the web. Output a ranked table of fixes
> with rough savings and effort — top 5 only. ~1 page.*

That version names the buckets, sets priority, caps output, and still licenses the web
check — same answer, a fraction of the wandering. **General rule for the loop:** state the
goal, the constraints, and the shape of the answer you want; scope to a folder when you
can; start a fresh thread per task. The prompt is cheap to write and expensive to leave vague.

---

## Sources (2026)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Steering Claude Code: skills, hooks, subagents — Claude](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Prompt Caching in 2026: the 5-minute TTL change — DEV](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Code June 2026: 10 New Features — SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
