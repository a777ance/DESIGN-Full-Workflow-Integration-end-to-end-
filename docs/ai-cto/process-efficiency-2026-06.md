# Process efficiency audit — user↔AI workflow & token spend (2026-06-14)

A standing review of how we work *with* the AI: where tokens leak, where prompting can be
tighter, and where the local-LLM/Claude hybrid we already own is under-used. Findings are
ranked by **$ saved ÷ effort**. Web sources dated to mid-June 2026 are linked at the bottom;
this field moves weekly, so treat anything here older than ~30 days as needing a re-check.

## TL;DR — the five highest-leverage fixes

1. **Trim & de-duplicate the CLAUDE.md files** (biggest, cheapest win). They load on *every*
   turn of *every* session.
2. **Make the session-start reading ritual conditional**, not mandatory.
3. **Push more volume to the local LLM** — but fix the privacy-failover bug (TD-14) first.
4. **Batch the scheduled LLM work** (50% off, stacks with caching → 95%+).
5. **Right-size the model and effort** per task; Opus-by-default is overkill for doc edits.

---

## 1. CLAUDE.md bloat — the per-turn tax (P1, trivial effort)

Measured today:

| Repo | CLAUDE.md | ≈ tokens (loaded every turn) |
| ---- | --------- | ---------------------------- |
| localDNS | 20.5 KB | ~5,100 |
| DESIGN | 18.0 KB | ~4,500 |
| MARKETING | 10.7 KB | ~2,700 |
| customers | 4.1 KB | ~1,000 |
| claude-code-homelab | 2.9 KB | ~700 |
| Azure-lab | 2.3 KB | ~600 |
| **All seven** | **58 KB** | **~14,600** |

Anthropic's own guidance: **keep CLAUDE.md under ~200 lines / lean**; a 5K-token CLAUDE.md
costs 5K tokens on every single turn whether the conversation is 2 messages or 200. Two
concrete problems:

- **The "House style: ordering & typography" block is duplicated verbatim across all 7 repos**
  — ~1 KB each, ~7 KB / ~1,750 tokens of pure duplication, *and* a maintenance hazard (any
  edit means touching 7 files; they already drift). It's identical text; it should live once.
- **Reference tables that only matter mid-task are always-on.** localDNS's full *Deploy paths*
  table (~40 rows) and the nftables deploy checklist only matter when actually deploying.
  DESIGN's stage map + verification walkthrough only matter when verifying. Right now they're
  resident context on a one-line typo fix.

**Fix (do this first):**
- Move the deep tables, known-issues lists, and deploy checklists into **on-demand Skills** or
  a referenced `DEPLOY.md` / `ARCHITECTURE.md`. Skills load only when invoked; CLAUDE.md stays
  the lean "read this first" briefing it claims to be. Anthropic explicitly recommends "move
  instructions from CLAUDE.md to skills."
- Replace the duplicated house-style block with a one-line pointer to a single canonical file
  (e.g. a `house-style.md` referenced from each repo), or accept it lives once in DESIGN and
  the others link to it.
- Target: each CLAUDE.md back under ~200 lines. Realistic saving: **~8–10K tokens of resident
  context per session**, every session, across the portfolio.

## 2. Session-start reading ritual is unconditional (P1, trivial effort)

NARF (CTO) is told to read 4 files at session start; ZORT (CFO) 6 files. That's **up to 10
file reads before any work begins, every session** — on top of the ~14.6K of CLAUDE.md. Most
sessions (a doc fix, a config tweak) never touch CFO state at all.

**Fix:** gate them — "*when doing CTO/CFO work*, read X," or fold the state-load into a
`/cto-start` / `/cfo-start` skill the operator invokes deliberately. Don't pay for the CFO
portfolio + decisions + metrics + runway + budget + context (6 files) to fix a broken link.

## 3. The reverse-ordering house style is a quiet token + error tax (P2, judgment call)

Newest-first logs are fine and conventional. But two of the house rules actively fight the
model's training distribution:

- **"Alphabetical lists run Z→A."**
- **"Walkthroughs: reverse the blocks, keep the steps."**

Every time the AI writes or edits one of these, it has to consciously invert the natural order,
which raises the chance of an error — and each correction/re-read is *more* tokens, not fewer.
This is a real cost paid on every walkthrough and list edit, for an aesthetic preference.

**Fix:** consider dropping Z→A and reversed-walkthrough-blocks (keep newest-first for genuinely
time-based logs, which is standard and cheap). This is a founder taste call, not a mandate —
flagging the cost so it's a *chosen* cost.

## 4. Hybrid local/cloud — exploit the architecture you already built (P1, medium effort)

You already run the right stack: **LiteLLM gateway + Ollama + a reasoning ladder**
(`local-reason` → `cloud-gpu-reason` → `cloud-overflow`) on the t630. Industry data (2026):
roughly **60–70% of LLM requests are "simple"** (classification, extraction, formatting),
20–30% moderate, ~10% need a frontier model. Hybrid setups report **60–90% cost reduction**
keeping the same quality ceiling.

**The opportunity:** route more of the simple/moderate work (tagging roster fields, drafting
boilerplate copy, summarizing logs, extraction) to the small local models, and reserve the
Claude API for genuine frontier reasoning and customer-facing prose.

**Blocker — fix before increasing volume:** **TD-14 is a live privacy bug** — a
`sensitive`-tagged task can fail over from `local-reason` to `cloud-overflow` (Claude cloud)
because `allow_cloud=False` isn't enforced at the LiteLLM failover layer. Pushing more volume
through the router *amplifies* that leak. Fix TD-14 (fail closed to a local-only chain) first,
then turn up the local routing.

## 5. Batch the scheduled LLM work (P2, low effort, only if/when those jobs use an LLM)

The **Batch API takes 50% off input *and* output**, and **stacks with prompt caching** for
95%+ effective savings. Anything that runs on a schedule and isn't latency-sensitive is a
batch candidate: the monthly statement run (stage 06), nightly stats summaries, any
recruiting/marketing copy generation.

Caveat: statement *rendering* is templated Python (`compose.py` / `generate_client.py`) at "a
penny a home" and may use no LLM at all — confirm before optimizing. The rule applies the
moment any LLM summarization/judgement is added to a scheduled job: send it as a batch, not
synchronously.

## 6. Use Claude Code's own 2026 cost levers (P2, low effort)

Authoritative tactics from the Claude Code cost docs + June-2026 release notes:

- **Prompt caching is automatic**, ~90% off cache reads; effectiveness depends on a *stable
  prefix*. Trimming CLAUDE.md (item 1) and not thrashing between repos mid-session both raise
  hit rate. Real, achievable hit rates on stable agent workloads: 74–84%.
- **Model + effort right-sizing.** Opus 4.8 is the default here. Anthropic's own line: *Sonnet
  handles most coding/doc tasks and costs less; reserve Opus for architecture/multi-step
  reasoning.* Use `/effort` to lower reasoning on simple edits; `MAX_THINKING_TOKENS` on fixed-
  budget models. Fast mode is now cheaper, too.
- **Subagents for verbose ops.** Delegate test runs, log scans, and doc fetches to subagents so
  the verbose output stays in *their* context and only a summary returns. Use `model: haiku`
  for simple subagents. (Note: Agent *teams* use ~7× tokens — keep those small and rare.)
- **Hooks to pre-filter.** A PreToolUse hook can grep a 10K-line log down to the ERROR lines
  before Claude ever sees it. Good fit for wiring `check-docs.py` output and test output.
- **MCP tool-search deferral** is already on (tool schemas load on demand this session) — keep
  it; prefer CLI over MCP servers where a CLI exists (more context-efficient).
- **"Dreaming" / memory curation** (new) reviews past sessions and curates memory so agents
  improve between runs — worth enabling for the recurring CTO/CFO routines.
- **Routines** (scheduled cloud agents) — already in use (this audit is one). Good pattern;
  see the prompt note below.

## 7. Track a baseline (P1, trivial — do this so the above is measurable)

We are optimizing blind. Run `/usage` (and the Console Usage page) to capture cost/active-day
and the skills/subagents/MCP breakdown, and log `cache_read_input_tokens` vs `input_tokens` to
get a cache-hit ratio. Without a baseline we can't tell which of the above actually moved the
needle. Enterprise reference points: ~$13/dev/active-day, $150–250/dev/month.

---

## On the prompt that asked for this (you asked — here's the candid read)

The triggering request was, itself, an example of the most expensive prompt pattern:

- **Unbounded scope** — "ANYTHING that could help," "Anything you could possibly think of."
  Anthropic's cost guidance singles this out: vague requests ("improve this codebase") trigger
  broad scanning; specific requests ("add validation to the login function in auth.ts") let the
  model work with minimal reads. An open-ended "find all inefficiencies everywhere" maximizes
  exploration tokens — the opposite of the goal.
- **No baseline, no decision, no output format.** It didn't say what the current spend is, what
  actually hurts, what decision it should inform, or what shape the answer should take. The AI
  has to guess all of that, expensively.
- **"Keep UP TO DATE… day by day. Check the news"** can't be satisfied by a one-shot run — a
  single invocation is a snapshot. That's a *recurring* need, which is exactly what a **weekly
  Routine** is for; stating it in a one-off prompt just adds tokens it can't honor.

A tighter version of the same ask, by example:

> *"Our Claude Code + LiteLLM spend is ~\$X/mo (baseline from `/usage` attached). Audit our
> seven CLAUDE.md files and the LiteLLM routing config for token waste. Output: the top 5 fixes
> ranked by \$ saved vs. effort, as a tech-debt entry. Don't change code — recommend only."*

That is bounded, measurable, names the artifacts, fixes the output format, and is cheap to run
weekly. The meta-point, said plainly: a prompt asking how to save tokens shouldn't itself be
unbounded. Lead by example, and let a scheduled Routine carry the "stay current" part.

---

## Sources (mid-June 2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Cache Pricing 2026 — TokenMix](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM AI Gateway: Route Local + Cloud — Local AI Master](https://localaimaster.com/blog/ai-gateway-litellm)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code News June 2026 — blog.mean.ceo](https://blog.mean.ceo/claude-code-news-june-2026/)
