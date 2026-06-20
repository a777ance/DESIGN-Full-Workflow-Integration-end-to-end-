# Process efficiency review — user ↔ AI workflow (2026-06-20)

Scope: where tokens (and money) leak in how we work with Claude across the A777ance repos,
and what to change. Findings are ordered **highest-leverage first**. Every figure is
approximate (token ≈ chars ÷ 4) and meant for direction, not accounting.

Most numbers below were measured against this repo set on 2026-06-20; the best-practice
figures are sourced (links at the bottom) and will drift — recheck quarterly.

---

## TL;DR — the five moves, ranked by payback

1. **Trim the `CLAUDE.md` files.** They're the single biggest fixed cost: they load *before
   a word is typed*, on *every* turn of *every* session. Ours run 573–5,118 tokens each;
   best practice is **under ~500**. localDNS and DESIGN alone burn ~9,600 tokens of
   context before any work starts.
2. **Turn on prompt caching for the LiteLLM-routed calls.** Claude Code already caches; our
   own `langgraph-router` / Open WebUI calls likely don't. A stable system prefix cached
   reads at **10% of base price** — a 60–90% input-cost cut on repeated calls.
3. **Route more work to the local model we already run** — but fix the privacy fail-open
   first (TD-14). deepseek-r1:1.5b on the t630 can do classify/extract/summarize at ~zero
   marginal cost; reserve the Claude API for reasoning. Industry reports 60–80% savings.
4. **Downshift the model by task.** Opus is ~5× Sonnet per token. Routine doc edits,
   house-style fixes, link-checking → Sonnet 4.6 or Haiku 4.5. Reserve Opus 4.8 for
   ambiguous / architectural work. (This very routine ran on Opus 4.8.)
5. **Scope each prompt and each routine.** Open-ended "look at anything that could help"
   maximizes exploration cost. A scoped ask with an explicit deliverable and output path is
   often 3–5× cheaper for the same result.

---

## 1. `CLAUDE.md` bloat — the biggest concrete win

Measured 2026-06-20:

| Repo | ~Tokens loaded every turn |
| ---- | ------------------------- |
| localDNS | ~5,118 |
| DESIGN (this repo) | ~4,496 |
| MARKETING | ~2,665 |
| customers | ~1,033 |
| claude-code-homelab | ~724 |
| Azure-lab | ~573 |

Best practice in 2026 is a `CLAUDE.md` **under ~500 tokens** — a pointer file, not a manual.
Ours are 1–10× over. A 5,000-token `CLAUDE.md` costs 5,000 tokens of context on turn one and
again on every compaction.

**Why it matters here:** when this routine fired, the harness injected *all six* `CLAUDE.md`
files (~14.6K tokens) as project instructions before the task even began. Even a normal
single-repo session pays the localDNS or DESIGN figure on every message.

**Fix — keep the contract, move the reference:**
- Cut each `CLAUDE.md` to: the one-paragraph "what this repo is," the hard rules (secrets,
  push-to-main vs. branch, honesty rule), and a **table of pointers** to the deep files.
- Move the ASCII funnel diagram, the full stage map, the money-flow box, and the
  verification command blocks into `README.md` / `network-context.md` and let Claude read
  them **on demand** for tasks that need them. They're reference, not per-turn context.
- The "at session start, read these 4–6 files" blocks (NARF §5, ZORT §6) force reading
  `portfolio.md` + `roadmap.md` + `tech-debt.md` + `decisions.md` + six CFO files at the top
  of *every* session regardless of task. Make that **conditional**: "if the task is
  CTO/CFO-shaped, read …" Otherwise a one-line doc edit drags in the whole portfolio.
- The full **house-style block is duplicated verbatim in all seven `CLAUDE.md` files.** That's
  the same ~250 tokens copy-pasted everywhere. Put it in one file (e.g. `HOUSE-STYLE.md` in a
  shared spot or the public localDNS) and link to it; keep only a one-line reminder inline.

Target: every `CLAUDE.md` under ~600 tokens. Estimated saving: ~4,500 tokens/turn on
localDNS sessions, compounding across a long session and every `/compact`.

## 2. Prompt caching — near-free repeated prefixes

We're on the API (LiteLLM router + `ANTHROPIC_API_KEY`, stage 10). Prompt caching cuts
**cached input to 10% of base price** (90% off). After the first call a stable system prefix
is essentially free for the TTL window.

- **Claude Code** caches automatically — no action, but it's *defeated* by a bloated,
  churning `CLAUDE.md`. Fixing §1 also raises the cache-hit rate.
- **Our own routed calls** (`langgraph-router`, Open WebUI → LiteLLM → Anthropic) need an
  explicit `cache_control` breakpoint on the stable system prefix to benefit. Verify they
  set one; today they probably don't.
- **TTL gotcha (2026):** default cache TTL dropped from 60 min to **5 min**. For stable agent
  workloads, request the **1-hour TTL** so the prefix survives between calls. Watch for cache
  breakage from whitespace changes, reordered tool definitions, or a system/content-type
  mismatch — any of these silently drops the hit rate to zero.

## 3. Hybrid local + cloud — we already built it, now use it

Stage 10's ladder already exists: `local-reason` (deepseek-r1:1.5b, t630 CPU, cool),
`cloud-gpu-reason` (full R1 on rented GPU via Tailscale), `cloud-overflow` (Claude). The
opportunity is to push **more high-volume, low-sensitivity work to the local tier**:
classification, extraction, summarizing logs, first-draft "Handled For You" lines,
link-checking triage. Reported savings for this pattern are **60–80%**.

**Blocker — do this first:** TD-14. A `sensitive`-tagged task routes to `local-reason`, but
`local-reason`'s fallback chain includes `cloud-overflow` (Claude cloud). If the local model
is down, a sensitive prompt **fails *open* to the cloud.** The dispatcher's `allow_cloud=False`
isn't enforced at the LiteLLM failover layer. Give `local-reason` a **local-only** fallback
(fail closed) before routing any more sensitive work locally. This is a privacy invariant,
same spirit as the Unbound DNS split — don't hand a third party the private lookups.

## 4. Model choice by task

Opus ≈ 5× Sonnet per token; on subscription it also drains the quota window ~5× faster.
A simple ladder:
- **Haiku 4.5 / Sonnet 4.6** — house-style fixes, link/anchor checks, doc edits, commit
  messages, roster edits, schema-following work.
- **Opus 4.8** — architecture, ambiguous specs, cross-repo reasoning, anything where a wrong
  call is expensive.

`/model` switches mid-session. This efficiency review is borderline Opus-worthy; a daily
"is the funnel still wired / any broken links" routine is Haiku work.

## 5. Cheap habits that add up

- **`/compact`** to compress a long session into a summary instead of carrying raw history;
  **`/recap`** (new April 2026) to resume without replaying the whole transcript.
- **Cap tool output** — large command/file dumps flood context. Read the slice you need
  (`offset`/`limit`), not the whole file; our verification blocks dump a lot.
- **Prefer CLI tools** (`gh`, `stripe`, etc.) over chatty MCP calls when both work — CLI is
  the most context-efficient way to touch an external service. (Note: in *this* remote
  environment GitHub is MCP-only, so that's a local-workstation habit.)
- **Subagents: use for fan-out, not by default.** They isolate context (a big search returns
  the conclusion, not 20 files) — good. But subagent-heavy runs can cost ~7× a single thread,
  and as of June 2026 subagents can nest **5 levels deep**, so cost can blow up fast. Use one
  for a broad search; don't spawn a swarm for a one-file task.
- **Scope routines tightly.** A scheduled routine that re-reads ten portfolio files every run
  is expensive whether or not anything changed. Give each routine a narrow check and an early
  exit when nothing's actionable.

## 6. Relevant platform news (June 2026)

- **Opus 4.8** is current; **rate limits doubled** this month.
- **Auto mode** on Bedrock/Vertex/Foundry replaces permission prompts with background safety
  checks (relevant if we ever route Claude Code through a cloud provider).
- **Destructive-command guards** added: `git reset --hard`, `git clean -fd`, `terraform
  destroy`, etc. are blocked unless explicitly requested — a free safety net for these repos'
  "push to main" habit.
- Claude Code now **prompts before writing executable files even in acceptEdits mode.**

---

## On the prompt that triggered this review (meta)

The request was friendly and broad: "locate inefficiencies … anything you could possibly
think of … search the web if helpful … check the news." That openness is itself a cost
driver — it invites unbounded exploration, and an agent will spend tokens proving it looked
everywhere. A tighter version gets the same answer for less:

> "Review our Claude usage for token waste. Focus on: (1) CLAUDE.md size, (2) prompt caching
> on the LiteLLM router, (3) local-vs-cloud routing. Skip anything that needs my input.
> Web-search only to confirm current best-practice numbers. Write findings to
> `docs/ai-cto/process-efficiency-<date>.md` and notify me with the top 3."

What made it efficient: a **named focus set**, an explicit **skip** boundary, a bounded reason
to search the web, and a **fixed output location**. The general pattern for any AI ask:
*goal · scope/skip · deliverable · where it lands.*

---

## Sources

- [Anthropic — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code — Changelog](https://code.claude.com/docs/en/changelog)
- [KDnuggets — 7 ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [buildtolaunch — Claude Code token optimization (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Tembo — Claude Code subagents 2026 guide](https://www.tembo.io/blog/claude-code-subagents)
- [SitePoint — Hybrid cloud-local LLM architecture (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [DEV — Claude prompt caching 5-minute TTL change (2026)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [jangwook.net — Claude Code June 2026 update](https://jangwook.net/en/blog/en/claude-code-june-2026-new-features-changelog-developer-guide/)
