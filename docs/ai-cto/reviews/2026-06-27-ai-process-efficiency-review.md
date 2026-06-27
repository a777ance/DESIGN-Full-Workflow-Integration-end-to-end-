# AI Process-Efficiency Review — User ⇄ AI loop

**Date:** 2026-06-27 · **Author:** NARF (AI CTO), scheduled routine · **Scope:** how we
spend tokens and attention across all A777ance repos, and where a local model or better
prompting beats paying Claude for it.

This is advisory — nothing here is deployed. Findings are ranked by payoff for *our actual
usage pattern* (Claude Code sessions across 7 repos + the t630 LiteLLM hybrid router), not
generic tips. Sources at the bottom; the field moves weekly, so re-check before acting.

---

## TL;DR — the five levers, ranked

1. **Trim every `CLAUDE.md`.** Two of ours are ~60% over the recommended budget and that
   tax is paid on *every single turn* of *every* session. Biggest, cheapest win. (§1)
2. **One task per session + `/compact`.** Long sessions are "geometric cost machines" —
   message 50 re-sends messages 1–49. We are doing portfolio-wide work in long sessions. (§2)
3. **Default to Sonnet; reserve Opus.** Opus is ~5× Sonnet/token. Start on the cheap brain,
   escalate only for genuinely hard reasoning. (§3)
4. **Lean on prompt caching — and stop breaking the cache.** 90% cheaper on the cached
   prefix; the 5-min TTL means our reverse-chron "newest at top" edits to long files can
   *invalidate the cache every turn*. Worth measuring. (§4)
5. **Push routine work onto the t630 — but fix TD-14 first.** Our hybrid router already
   exists; the privacy fail-open is the blocker, not the capability. (§5)

---

## 1. The `CLAUDE.md` tax (P1, do this week)

Guidance across the 2026 write-ups converges on **keep `CLAUDE.md` under ~200 lines / ~5K
tokens** — it's injected into context on every request, so a fat one is a flat tax on every
turn, in every repo, forever. Measured today:

| Repo | Lines | ~Words | Verdict |
| ---- | ----- | ------ | ------- |
| `localDNS` | 326 | 2,728 | **~60% over** — trim |
| `DESIGN-…` | 295 | 2,608 | **~45% over** — trim |
| `MARKETING` | 214 | 1,445 | slightly over |
| `customers` | 80 | 562 | good |

**Fix:** move the reference tables that aren't needed *every* turn (the full Deploy-paths
matrix in `localDNS`, the per-stage tool map in `DESIGN`) into the README and leave a one-line
pointer. `CLAUDE.md` should be the briefing Claude needs *before reading anything else*, not
the encyclopedia. Target: each under 200 lines. Rough saving: ~1,500–2,000 tokens *per turn*
on our two busiest repos.

## 2. Session hygiene

A fresh session sends ~20K tokens/turn; a 200-turn session sends ~200K/turn because the whole
transcript re-ships each turn. Two habits:

- **One task per chat.** Don't run "review the portfolio + fix DNS + draft marketing" in one
  session. Separate sessions keep each context small.
- **`/compact` at natural breakpoints** instead of letting a session sprawl. Anthropic also
  ships server-side *context compaction* (beta `compact-2026-01-12`) that condenses history
  near the window limit — but proactively scoping beats relying on it.
- **Point at files, not "the project."** "Edit `08-client-list-and-crm/schema.md`" reads one
  file; "fix the CRM" makes Claude crawl the tree.

## 3. Model tiering

Opus ≈ 5× Sonnet per token. The pattern that wins: **start on Sonnet, escalate to Opus only
for deep analysis** (architecture calls, gnarly debugging, the FIN/ADR decisions). Most of our
work — doc edits, link-checks, statement composition, house-style passes — is Sonnet-grade or
below. (This routine itself runs on Opus 1M-context; for a recurring "is anything broken"
sweep, a cheaper tier would do most of it — see §6.)

## 4. Prompt caching — and our self-inflicted cache misses

Caching makes a repeated prefix ~90% cheaper to read (cache *writes* cost ~25% more; you break
even on the 2nd hit). Cache hits require a **byte-identical prefix** up to the cache breakpoint,
TTL 5 min, refreshed on each read.

**A house-style footgun:** our "newest-first / Z→A / reverse the blocks" rules mean we edit the
*top* of long logs and docs. If a cached prefix includes those files, **every prepend busts the
cache** for everything after it. This is worth a deliberate check — when working a long log,
append-then-reorder, or keep the volatile file out of the cached prefix. Net: the ordering
convention is a readability choice with a real token cost; know which you're paying.

## 5. The hybrid angle — capability is built, the gate is broken

We already have the thing every 2026 "cut costs 10×" article recommends: a **LiteLLM front
door** (`ai.home.lan:4040`) with local Ollama as default and Claude as overflow. The
literature says offloading routine work to local models cuts AI cost **8–10×** with no quality
loss on the *right* tasks: embeddings, classification, intent detection, simple summarization,
first-draft text. Our RAG embeddings already run local (`local-embed`). Good candidates to
move local next: house-style/lint passes, commit-message drafts, "summarize this log,"
triage/routing of which-model-should-handle-this.

**But the blocker is our own TD-14 (P1, open since 2026-06-07):** `config.yaml` still gives
`local-reason` a `["cloud-gpu-reason", "cloud-overflow"]` fallback, so a `sensitive`-tagged
prompt can **fail *open* to Claude cloud** if the local model is down — violating the repo's
own "sensitive never leaves the box" invariant. **Do not widen local→cloud offload until
`local-reason` (and any tier that can carry sensitive data) has a local-only, fail-*closed*
fallback chain.** The privacy guarantee, not the token saving, is the gating constraint.

Reality check from the same sources: local 7B-on-CPU is *not* a Claude substitute for hard
coding/agentic work — and our t630 is a 4-core Carrizo with no usable GPU offload. So this is
"skim the cheap 60–80% of volume off Claude," not "replace Claude." The reasoning ladder
already encodes this; just don't over-promise the local tier.

## 6. Make *this routine* cheaper

This very job is a candidate for its own advice:
- Run the recurring "anything broken / anything new" sweep on **Sonnet**, not Opus 1M; escalate
  to Opus only when a finding needs deep analysis.
- It re-reads all 7 `CLAUDE.md` files via the system prompt each run — §1's trimming pays here too.
- Consider a **local-model pre-filter**: the t630 does a cheap "did anything change since last
  run?" pass and only wakes a Claude session when the answer is yes. Don't pay a frontier model
  to confirm "all quiet."

---

## 7. On the prompt that triggered this (the user asked)

The triggering prompt was effective at *intent* but expensive to execute as written. Honest critique:

- **It's a broad sweep** ("ANYTHING that could help… search the web… check the news"). Broad =
  many tool calls = many tokens. That's fine for a *scheduled* deep-dive like this one; it would
  be wasteful as a daily driver.
- **It bundles 5+ distinct questions** (token use, prompting, other AI, hybrid local/cloud, news)
  into one turn. Per §2, separate asks → smaller contexts. For recurring use, split into named
  prompts: "audit CLAUDE.md sizes," "check Claude Code release notes," etc.
- **No output contract.** "Let me know" leaves format/length open, so the model defaults to long.
  Adding "≤1 page, ranked by ROI, cite sources" would cut output tokens and improve usefulness.
- **Politeness padding** ("Thanks!", "Anything you could possibly think of") is a few tokens —
  negligible; *not* worth optimizing. Don't let anyone tell you to strip courtesy to save money;
  the real cost is scope and context size, not manners.

**A tighter re-write for recurring use:**
> "Weekly: audit our Claude-Code token spend. Check (a) CLAUDE.md sizes vs the 200-line budget,
> (b) any new Claude Code cost features since last run. Output ≤1 page, ranked by $ saved, with
> sources. Flag only what changed."

That swaps an open-ended essay for a bounded diff — cheaper to run and easier to act on.

---

## Sources (re-verify; this moves weekly)

- [Manage costs — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [How to Reduce Claude Code Token Usage: 8 Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Run Local AI Models with Claude Code to Cut Costs 10× — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Prompt Caching Deep Dive — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
