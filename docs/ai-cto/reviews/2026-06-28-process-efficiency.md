# 2026-06-28 — Process efficiency review (user ↔ AI)

**Scope:** where tokens and human time leak in how we work *with* the AI — not the
product. Grounded in this repo set + current (June 2026) best practice. Reviewer: NARF
(AI CTO), scheduled routine.

**Headline:** the *hybrid local/cloud* piece is already done well — `localDNS`'s LiteLLM
router (local Ollama default, privacy gate, reasoning ladder, cloud as overflow) is exactly
what the 2026 "cut cost 10×" guides prescribe. The real, unaddressed leaks are upstream of
that: **context bloat in the `CLAUDE.md` files, cold prompt caches on scheduled runs, model
over-provisioning, and loose prompting.** Fixing those is cheap and compounds on every
session.

---

## The findings, biggest lever first

### 1. `CLAUDE.md` bloat — the #1 recurring cost (P1)

Every session loads the repo's `CLAUDE.md` *before* the task, and it re-loads on context
refresh. Current sizes (≈chars/4):

| Repo | `CLAUDE.md` tokens |
| ---- | ------------------ |
| localDNS | ~5,100 |
| DESIGN (this) | ~4,500 |
| MARKETING | ~2,700 |
| customers | ~1,000 |
| claude-code-homelab | ~720 |
| Azure-lab | ~570 |

A 5k-token brief costs 5k tokens before a word is typed. Worse, the **40-line "House style"
block is duplicated verbatim in all 7 files** (~350 tokens × 7), and `localDNS/CLAUDE.md`
inlines the *entire* deploy-path table (~40 rows), the full known-issues table, and a
verification block — all of which already live in README / nested docs.

**Fix (target <1,500 tokens each):**
- Move the deploy-path table, full known-issues, and verification commands out of
  `localDNS/CLAUDE.md` into the README it already points to; leave a one-line pointer.
  `CLAUDE.md` should be "what you can't infer from the code," not a mirror of the README.
- Collapse the duplicated House-style block to ~6 lines + a link to one canonical copy
  (e.g. `DESIGN/docs/house-style.md`). Claude reads the link on demand.
- Push folder-specific guidance into nested `CLAUDE.md` files in those folders — they load
  only when work touches that folder, not on every session.

Best practice is explicit on this: *"CLAUDE.md loads on every single turn, so keep it
concise, push folder-specific guidance into nested files, and only document what the code
cannot say for itself."*

### 2. Scheduled routines run with a cold cache (P1, and now a *budget* issue)

Anthropic's prompt cache is a 90%-off read but only stays warm **~5 minutes**. Scheduled
routines fire cold, so each run pays **full price** for the big `CLAUDE.md` + system prompt
every time. Two compounding fixes:
- Shrinking `CLAUDE.md` (finding 1) directly cuts the cold-start floor.
- **Batch related routines into one session** where possible so the second task hits a warm
  cache instead of paying the write again.

**News that makes this urgent:** as of **June 15, 2026**, Agent-SDK / headless `claude -p`
invocations (which is what these scheduled routines *are*) **no longer count against the
plan's normal limits — they bill against a separate API-rate credit pool** ($20/mo on Pro,
$100 on Max 5×, $200 on Max 20×). Unattended routines now hit a hard, metered cap, so every
token of cold-cache `CLAUDE.md` is now real money against a small pool.

### 3. Model over-provisioning on routine work (P1)

This very routine ran on **Opus 4.8 (1M ctx)** — the most expensive tier — to do a
scan-and-summarize job that Haiku 4.5 or Sonnet 4.6 would do at a fraction of the cost. The
2026 consensus: *default to Haiku, escalate on demand; reserve Opus for genuinely hard
reasoning.*
- Set cheaper default models on the **scheduled/routine** tasks (doc checks, log scans,
  status summaries, link checking). Keep Opus for architecture/design sessions only.
- Their own `config.yaml` already encodes this discipline for the LiteLLM tiers
  (`cloud-code` = Sonnet, escalate to Opus for the hardest) — extend the same rule to the
  Claude Code routines themselves.

### 4. Subagents: use them to *protect* context, not by reflex (P2)

Subagent-heavy flows add **200–500% token overhead** vs. one agent — *but* a subagent that
reads 30 files and returns a 20-line summary keeps the parent context tiny. Rule of thumb:
spin a subagent when the work would otherwise dump large file contents into the main
session (broad searches, multi-file audits); don't fan out trivial single-file lookups.

### 5. The hybrid local stack — already strong, one efficiency gap (P2)

`localDNS/10-ai-orchestration` already does the expensive-advice part: local-first, privacy
gate, graceful cloud overflow, local embeddings for RAG. Two small adds from current best
practice:
- **Semantic cache in front of LiteLLM** — catches near-duplicate prompts and returns a
  stored answer without hitting any model; cited as 15–30% volume cut on
  classification-heavy work.
- Route the cheap sub-steps of routines (classification, extraction, "is this changed?")
  through the t630's `local-fast`/`local-smart` instead of the Claude API. (Note: this can't
  back the Claude Code agent loop itself today, but it can absorb scripted pre/post steps.)
- *(Already tracked: TD-14 — the `local-reason` cloud fallback breaks the privacy gate. Not
  an efficiency issue but worth fixing in the same pass.)*

### 6. Strip low-signal input before it reaches the model (P3)

Data-prep — dropping redundant fields, trimming verbose formats before sending — cuts input
tokens 40%+ on structured workloads and is free (it's outside billing). Applies to anything
we feed the API from `roster.json`, stats files, or logs: send the slice, not the file.

---

## On the prompt that triggered this routine

The triggering prompt was, candidly, **token-inefficient** — and since the user asked, here
it is plainly:
- *"Anything you could possibly think of… ANYTHING that could help"* is unbounded, so the
  agent explores wide and expensive instead of deep and cheap.
- No output target, no budget, no "stop when" condition.
- Multiple distinct asks (token use, prompting, hybrid LLM, news) bundled into one open
  sweep, so nothing gets a focused, cache-friendly pass.

**A tighter version that gets the same answer for less:**

> Review our AI *process* for token waste. Check (a) `CLAUDE.md` sizes across repos, (b)
> whether scheduled routines run on the cheapest viable model, (c) one current best-practice
> source. Output: top 5 fixes ranked by token-saved, ≤1 page, written to
> `docs/ai-cto/reviews/`. Use Sonnet. Skip anything already done well.

Scoped, names the deliverable, caps the length, picks the model, and tells the agent what to
ignore — that combination is the single biggest prompting lever.

---

## Recommended next actions (ranked by token saved × ease)

1. Trim `localDNS/CLAUDE.md` and `DESIGN/CLAUDE.md` to <1,500 tokens; move tables/known-issues
   to README + nested docs. *(biggest, easy)*
2. De-duplicate the House-style block to one canonical file + links. *(easy)*
3. Set Haiku/Sonnet as the default for scheduled/routine tasks; keep Opus opt-in. *(easy, big)*
4. Batch related routines into one session to ride a warm cache. *(medium)*
5. Add a semantic cache in front of LiteLLM; route routine sub-steps to local tiers. *(medium)*
6. Adopt the scoped-prompt template above for future routines. *(free)*

## Sources (June 2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching Deep Dive — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Your Claude Code Automations Are About to Get a Bill — Medium (May 2026)](https://medium.com/@fukuda.aritomo/your-claude-code-automations-are-about-to-get-a-bill-6a77cf5338f9)
- [What Claude Code Actually Costs in 2026 (two June deadlines) — UsageBox](https://usagebox.com/articles/claude-code-cost-2026-per-token-per-month-june-deadlines)
