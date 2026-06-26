# Process efficiency review — user ↔ AI workflow (2026-06-26)

**Author:** NARF (AI CTO), scheduled routine
**Question (founder):** Find inefficiencies in our *process* between the user and the AI.
Reduce token use. Better prompting. Leverage other AI / hybrid local + Claude. Keep up to date.

**TL;DR — the single biggest lever:** every Claude Code session in this hub repo starts
~**21,000 tokens in the hole** before any work happens — ~4.5k from a bloated `CLAUDE.md` and
~16.4k from the mandatory NARF+ZORT session-start reading list. That boilerplate is re-paid on
every new session. Fix that first; it dwarfs everything else.

---

## 1. Measured cost of the current setup

| Source | Cost | Notes |
| ------ | ---- | ----- |
| `localDNS/CLAUDE.md` | ~5,100 tok | Loaded every turn of every localDNS session |
| `DESIGN/CLAUDE.md` | ~4,500 tok | Loaded every turn of every DESIGN session |
| `MARKETING/CLAUDE.md` | ~2,700 tok | |
| **Mandatory NARF+ZORT session-start reads (DESIGN)** | **~16,400 tok** | 4 CTO docs + 6 CFO docs, ~805 lines, read *before* any task |
| House-style block, duplicated verbatim | ~300 tok × **6 repos** | Identical text in all six `CLAUDE.md`s |

A DESIGN session therefore opens ~21k tokens deep. At ~30 sessions/month that is ~630k tokens
of pure boilerplate re-reading per month, on top of actual work — and the heaviest reads
(portfolio, decisions, CFO docs) are needed in maybe 1 session in 5.

---

## 2. Fixes, ranked by payback

### A. Make session-start reading *lazy*, not mandatory (biggest win)
The CLAUDE.md rule "At session start, read portfolio.md, roadmap.md, tech-debt.md,
decisions.md" + 6 CFO files forces ~16k tokens up front regardless of task. Most sessions
(a doc fix, a link check, one stage edit) never touch them.

- **Change the instruction to conditional:** "Read the portfolio hub *only when the task is
  cross-repo, financial, or a decision/roadmap change.*" Keep a 5–10 line *digest* of current
  priorities and the phase gate inline in CLAUDE.md so the common case needs no file reads.
- Expected saving: ~12–15k tokens on the ~80% of sessions that are narrow.

### B. Trim every CLAUDE.md to < 200 lines / < 2k tokens
Community + Anthropic guidance converges on "a 5,000-token CLAUDE.md costs 5,000 tokens on
*every* turn." `localDNS` (5.1k) and `DESIGN` (4.5k) are 2–2.5× over. They read like full
manuals — but the manual is already `README.md`. CLAUDE.md should be the *pointer*, not the doc.

- Move the deploy-path table, the full Unbound drop-in table, the nftables checklist, and the
  long known-issues tables into README / dedicated files; leave a one-line "see X" in CLAUDE.md.
- Keep only: how to build/verify, the hard invariants, the push-to-main rule, and links.

### C. De-duplicate the house-style block
The identical ~300-token typography/ordering block is pasted into all 6 `CLAUDE.md`s. It will
drift. Put it once in a shared `STYLE.md` (or in DESIGN as the canonical copy) and have each
CLAUDE.md link to it: "House style: see DESIGN/STYLE.md." Saves duplication *and* keeps it from
forking across repos.

### D. Keep sessions warm — prompt caching is 5-min TTL
Claude Code caches the conversation prefix, but the cache expires after ~5 minutes idle. Two
behavioural changes:
- **Batch related work into one continuous session** rather than many cold starts — a cold
  start re-reads CLAUDE.md + any session-start files uncached.
- `/clear` between *unrelated* tasks (drops stale context); `/compact` after a long work phase
  rather than letting a session sprawl. One task per chat.

### E. Output discipline
Add to each CLAUDE.md: *"Unless asked, give implementations without lengthy explanation; prefer
concise responses; don't re-read files you just edited to verify."* Reported 40–60% output-token
reduction. This repo's work is mostly doc edits where long prose narration is pure waste.

---

## 3. Leverage the local LLM you already own (hybrid)

You already run the hard part: LiteLLM router (`:4040`), Open WebUI (`:3000`), and a reasoning
ladder (`local-reason` deepseek-r1:1.5b on the t630, `cloud-gpu-reason` on a rented GPU) per
`localDNS/10-ai-orchestration`. Two ways to cash that in:

1. **Route the cheap tasks off Claude entirely.** Classification, triage, first-draft prose,
   "summarize this log", "is this link dead", commit-message drafting → the local model via
   Open WebUI / LiteLLM. Reserve the Claude API for code, cross-repo reasoning, and the
   honesty-critical Statement numbers. Industry reports put 60–70% of requests in the "simple"
   bucket — that is the bucket the t630 can serve at ~zero marginal cost.
2. **Tier *within* Claude.** Most of this repo's work does not need Opus. A Haiku/Sonnet/Opus
   **70/20/10** split (Haiku for triage + simple edits, Sonnet for most work, Opus only for the
   hardest reasoning) is widely reported to cut Claude spend by >50% at near-equal quality.
   *This very routine is running on Opus-1M — overkill for a doc review; Sonnet would do.*
3. **Optional, advanced:** point Claude Code at a local proxy via `ANTHROPIC_BASE_URL` so a
   router decides per-request whether to answer locally or forward to Anthropic. Higher setup
   cost; only worth it once the local model is genuinely handling volume. Don't build this
   before the simpler routing above is in daily use ("liquidity before app" applies to your own
   tooling too).

**Caveat (from your own CLAUDE.md):** don't run deepseek-r1:7b+ on the t630/laptop CPU — it
overheats. Keep heavy reasoning on the rented GPU pod or on Claude; the local box is for light,
parallel, low-stakes work.

---

## 4. Better prompting

- **Point at files, don't say "look around the repo."** Vague scope is the #1 token sink — the
  agent opens many files and explores dead ends. "Fix the broken anchor in `06-.../README.md`"
  beats "check the docs for problems."
- **State the stop condition.** "Change X, run `check-docs.py`, commit" terminates cleanly;
  open-ended asks don't.
- **Use subagents for parallel cheap fan-out** (e.g. "check every repo's links") so the main
  Opus/Sonnet loop's context and budget stay intact — each subagent runs its own small-model
  context.
- **Run `tools/check-docs.py` yourself before asking the AI to "review docs"** — let the cheap
  deterministic check find broken links; spend tokens only on what it flags.

---

## 5. Your prompt, reviewed (you asked)

The prompt that triggered this run is itself a good example of the #1 inefficiency: it is
maximally open-ended — *"ANYTHING that could help… anything you could possibly think of… search
the web… check the news."* That invites broad, expensive exploration with no stop condition, and
makes the result hard to act on. It worked here because the answer space happened to be
well-bounded, but as a habit it's costly.

**Tighter version:**

> "Review our user↔AI process for token waste. Focus on: (1) CLAUDE.md / session-start size,
> (2) where the local LLM stack could replace Claude calls. Give me the top 5 fixes ranked by
> token saved, with rough numbers. Skip background I already know. One web search max if a 2026
> best-practice would change your answer."

That scopes the work, caps the web research, names the deliverable shape, and gives a stop
condition — same answer, a fraction of the tokens.

---

## 6. Recommended next actions (cheapest first)

1. [ ] Convert the NARF+ZORT "read at session start" mandate to *conditional*; inline a 10-line
   priorities digest. **(~12–15k tok/session saved — do this first.)**
2. [ ] Add the output-discipline line to all CLAUDE.md files.
3. [ ] Trim `localDNS` and `DESIGN` CLAUDE.md under 2k tokens; move detail to README.
4. [ ] Hoist the house-style block to one shared file; link from the rest.
5. [ ] Start routing triage/draft/summarize tasks to Open WebUI; reserve Claude for code + the
   Statement.
6. [ ] Default everyday Claude Code work to Sonnet; escalate to Opus only when stuck.

Items 1–4 are doc edits I can do on request. Items 5–6 are habit/config changes for the founder.

---

## Sources (2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local AI Workflows — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LLM API Pricing Comparison 2026 — CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/)
