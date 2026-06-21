# Process efficiency review — the user↔AI loop (2026-06-21)

A standing review of *how we work with Claude*, not what we build. Goal: same or better
output for fewer tokens / dollars / minutes. Findings are ranked by **payoff ÷ effort**.
Re-run this review monthly — the tooling moves weekly (see "Keep it current" at the end).

> **Why this matters now:** as of **2026-06-15**, headless Claude Code, the Agent SDK,
> GitHub Actions, and **scheduled routines** (like the one that produced this file) bill on a
> separate monthly credit **at API rates**, no longer against a flat subscription. Every
> unattended run now has a real per-token price tag. Efficiency stopped being academic.

---

## TL;DR — the five highest-leverage moves

| # | Move | Effort | Payoff |
| - | ---- | ------ | ------ |
| 1 | **Scope each session/routine to ONE repo** unless it's genuinely cross-repo | trivial | huge |
| 2 | **Trim & de-duplicate the CLAUDE.md files** (two are 3–4× Anthropic's guidance; the house-style block is copy-pasted into all 7) | low | high |
| 3 | **Default routines to Sonnet/Haiku, escalate to Opus on demand** (this run used Opus 4.8) | trivial | high |
| 4 | **Wire your *existing* local LLM stack into the bulk/private sub-tasks** — you already built the hybrid router; it isn't pointed at the work yet | medium | high |
| 5 | **Push deterministic work out of the model into scripts/CI** (you already do this with `check-docs.py` — extend the pattern) | low | medium |

---

## 1. The CLAUDE.md tax is the biggest recurring sink

Every turn re-sends the project memory. It is never lazy-loaded and never evicted, so a
5,000-token CLAUDE.md costs ~5,000 tokens of *prefix* on every turn of every session.
Anthropic's own guidance is **keep CLAUDE.md under ~200 lines.**

Measured footprint in this portfolio (chars ÷ 4 ≈ tokens):

| Repo | CLAUDE.md size | ≈ tokens | vs. ~200-line guidance |
| ---- | -------------- | -------- | ---------------------- |
| localDNS | 20.5 KB | ~5,100 | **~3× over** |
| DESIGN (this repo) | 18.0 KB | ~4,500 | **~3× over** |
| MARKETING | 10.7 KB | ~2,700 | ~2× over |
| customers | 4.1 KB | ~1,000 | ok |
| claude-code-homelab | 2.9 KB | ~700 | ok |
| Azure-lab | 2.3 KB | ~600 | ok |

**Two compounding problems:**

- **All of them are in context *right now*.** This session has 6 repos in scope, so ~14–15K
  tokens of CLAUDE.md load *before any work begins*. A normal single-repo Claude Code session
  only loads that repo's CLAUDE.md — which is exactly why move #1 (scope to one repo) is the
  single biggest win. Working in localDNS alone? You pay ~5K, not ~15K.
- **The house-style block is duplicated verbatim in all 7 repos.** The identical
  "House style: ordering & typography" section (~375 tokens) is copy-pasted everywhere. That's
  a maintenance hazard *and* dead weight whenever more than one repo is loaded.

**Fixes (in order):**

1. **Scope sessions/routines to a single repo.** Don't add repos to a session's scope "just in
   case." Cross-repo tasks are the exception, not the default.
2. **Split CLAUDE.md into a thin always-on core + lazy detail.** Keep the briefing short and
   replace long reference tables with *pointers*: "When deploying, read `C. Deploy paths`."
   Claude reads the detail on demand instead of paying for it every turn. The localDNS deploy-path
   table and the DESIGN stage map are the obvious candidates to demote to linked sections.
3. **De-duplicate the house style.** Put the shared block in one file (e.g.
   `~/.claude/house-style.md` or a repo file) and pull it in with a CLAUDE.md `@import`
   (`@path/to/house-style.md`) rather than pasting it. One edit updates every repo.
4. Anything that is "nice to know" but not "needed every turn" belongs in README/context docs,
   which Claude opens only when relevant — not in CLAUDE.md.

---

## 2. Session hygiene — stop paying to re-read stale context

Long threads are a silent drain: every new message re-reads the entire conversation, including
superseded instructions and dead code. Cheap habits:

- **`/clear` when switching tasks**, `/compact` when a thread gets long but you want continuity.
  Compaction reuses the cached prefix (system + tools + CLAUDE.md), so it's cheap to do.
- **Batch and scope the ask.** "Refactor the login function in `auth.ts`" beats "refactor the
  auth module" — narrower scope = less context pulled in = fewer tokens and a more focused diff.
- **Cap tool-output size** so a giant log or file dump doesn't blow up the window (set a max
  around 8K for tool results).
- **Fan out exploration to subagents.** A subagent runs in its *own* context window and returns
  only a summary — the verbose file-reading stays out of your main thread. (This review used the
  read-only search pattern for exactly that reason.) New in June 2026: subagents can spawn their
  own subagents, capped 5 deep — useful for big fan-out research like this.

---

## 3. Model tiering — don't run a monitoring routine on Opus

This routine executed on **Opus 4.8**, the most expensive tier. A research/monitoring/lint
routine almost never needs Opus.

- **Default scheduled + headless work to Sonnet 4.6** (the speed/intelligence sweet spot), or
  **Haiku 4.5** for pure mechanical monitoring (does CI pass? did a file change? is the box up?).
  Reserve **Opus** for genuinely hard reasoning or large refactors.
- Use Claude Code's **`fallbackModel`** config (up to three, tried in order) so a busy primary
  degrades gracefully instead of failing the run.
- Interactive rule of thumb: *start on Sonnet, switch up to Opus only when you hit something that
  needs it.*

Concretely: re-point this efficiency routine at Sonnet (it's mostly web research + file reads +
writing). Likely 3–5× cheaper per run for output you wouldn't be able to tell apart.

---

## 4. You already built the hybrid stack — now point it at the work

`localDNS/10-ai-orchestration/` is a genuinely good hybrid setup that most people only *read*
about: LiteLLM front door on `ai.home.lan:4040`, local Ollama tiers (`qwen2.5:3b/7b`,
`deepseek-r1:1.5b`, `nomic-embed-text`) as the privacy-preserving default, a rented-GPU tier for
heavy reasoning over Tailscale, cloud Claude as overflow, **and** a LangGraph supervisor with a
deterministic privacy gate so a `sensitive` task never leaves the box. That's the architecture
the 2026 write-ups (LiteLLM + Ollama hybrid, 60–88% cost cuts) all describe — you have it.

**The gap: it's a separate chat stack (Open WebUI), not wired into the day-to-day Claude Code
loop.** Leverage it:

- **Route bulk, low-stakes, or privacy-sensitive sub-tasks to local tiers** instead of paying
  Claude API rates: drafting boilerplate, summarizing logs/`Handled For You` entries,
  first-pass classification of leads, reformatting, doc-lint pre-checks, embeddings/RAG over your
  own repos. `qwen2.5:7b` on the t630 is free and never leaves the LAN — ideal for the customer
  data in the private `customers` repo where you *don't* want real names crossing the Bifröst.
- **Reserve Claude (Sonnet/Opus) for the frontier work**: architecture, hard diffs, the
  customer-facing voice, anything where quality is the product.
- **Pattern to copy from the literature:** small/local model handles routine sub-steps, frontier
  model drives the main loop and only sees the distilled result. That's the same economics as
  Claude Code subagents — apply it across the *fence* too (local for cheap, cloud for hard).
- Low-effort first step: use the local stack for the throwaway "summarize / draft / classify"
  asks you currently fire at Claude in chat. Keep CC for the repo work.

---

## 5. Push deterministic work out of the model entirely

The cheapest token is the one you never spend. `DESIGN/tools/check-docs.py` is the right
instinct — link/anchor integrity is a *script's* job, not a language model's. Extend it:

- Gate house-style conventions (newest-first ordering, Z→A lists, the font stack) with a linter
  in CI rather than asking Claude to check them by reading files.
- Anything with a deterministic right answer (formatting, schema validation, "does HH-0001 carry
  facts from stages 02/03/05/07") → a script that Claude *runs* and reads the 1-line result of,
  instead of Claude doing it by hand across files.
- Prefer **prompt caching-friendly** structure on the API side: a stable prefix (system + tools +
  CLAUDE.md) is cached and re-billed at ~10% on cache hits. Keep that prefix stable across a
  session; put the volatile stuff late in the message. (Note: scheduled routines start in fresh
  containers, so the cache is cold on the *first* turn of each run — another reason to keep the
  prefix, i.e. CLAUDE.md, small for routines.)

---

## 6. Critique of the prompt that launched this run

The triggering prompt was, paraphrased: *"Locate inefficiencies in our process… reduce token
use… better prompting… leverage other AI… hybrid local+Claude… ANYTHING that could help… search
the web… keep up to date… check the news."*

**What's good:** clear intent, gives permission to use the web, asks for currency.

**What makes it expensive — especially as a *recurring* routine:**

- **Unbounded scope.** "ANYTHING that could help" invites maximal exploration every run. A
  routine should have a *fixed checklist*, so each run does bounded work and you can diff runs.
- **No output contract.** It doesn't say where the answer goes, how long, or what format — so the
  agent has to guess (and tends to over-produce).
- **No cost budget.** No "spend under N searches / minutes / dollars," so the run self-justifies
  more digging.
- **"Check the news" with no source list** → broad open-web searches each run, re-covering known
  ground. Pin the 3–4 sources worth re-checking.
- **Redundancy** ("Anything you could possibly think of" + "ANYTHING that could help") adds
  tokens without adding signal.

**Rewritten as an efficient recurring routine:**

> Monthly process-efficiency check. Read `docs/ai-cto/process-efficiency-review-<prev>.md`,
> then check these sources for changes since that date: Claude Code "What's new", Anthropic
> release notes, and our own `10-ai-orchestration` config. Output: a new dated review file in
> the same folder, **≤2 pages**, listing only what *changed* and any new recommendation, ranked
> by payoff÷effort. Use **Sonnet**. Budget: ≤6 web searches, ≤15 min. If nothing materially
> changed, write one line saying so and **do not** notify me. Notify only on a new actionable
> finding.

That version is scoped, diff-able, capped, and self-silencing on a quiet month — which is the
whole point of a routine.

---

## 7. Keep it current (this list rots fast)

Tooling here changes weekly. Re-check monthly:

- **Claude Code "What's new"** — https://code.claude.com/docs/en/whats-new
- **Best practices** — https://code.claude.com/docs/en/best-practices
- **Prompt caching (CC)** — https://code.claude.com/docs/en/prompt-caching
- **Anthropic release notes / news** — https://www.anthropic.com/news
- Our own `localDNS/10-ai-orchestration/` config + the LiteLLM routing docs.

Recent items worth knowing (June 2026): `/cd` switches the session's working dir without
rebuilding the prompt cache; subagents can spawn subagents (≤5 deep); `--safe-mode` for
troubleshooting; `fallbackModel` (up to 3); auto-mode now blocks destructive git/terraform
unless asked; and the 2026-06-15 billing change that moved headless/SDK/Actions/routines to
metered API-rate credits.

### Sources

- https://code.claude.com/docs/en/best-practices
- https://code.claude.com/docs/en/whats-new
- https://code.claude.com/docs/en/prompt-caching
- https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
- https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage
- https://buildtolaunch.substack.com/p/claude-code-token-optimization
- https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- https://docs.litellm.ai/docs/routing
- https://www.walturn.com/insights/how-prompt-caching-elevates-claude-code-agents
- https://releasebot.io/updates/anthropic/claude-code
- https://www.pravinkumar.co/blog/claude-june-15-billing-change-explained-2026
