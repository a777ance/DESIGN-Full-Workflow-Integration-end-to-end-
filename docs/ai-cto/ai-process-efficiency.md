# AI process efficiency — reducing token use across the A777ance workflow

**Author:** NARF (AI CTO), routine analysis · **Date:** 2026-06-28
**Scope:** the *process* between the operator and the AI — how we drive Claude (and other
models) across the seven repos — not any one feature. Goal: same output, fewer tokens,
better prompts, more local-vs-cloud split.

> Honesty note: token-saving percentages below are vendor/community figures for the
> *technique in isolation* (sources at the bottom). Treat them as direction, not a promise —
> measure our own before/after (see "Instrument first").

---

## TL;DR — the ranked wins

| # | Lever | Effort | Est. saving on our usage | Where |
| - | ----- | ------ | ------------------------ | ----- |
| 1 | **Stop loading 7 giant CLAUDE.md files into every session** | Low | High | this repo + all 6 others |
| 2 | **Turn on prompt caching** on the stable CLAUDE.md/system prefix | Low | 10% read price on the cached prefix (~70–90% of input bill) | LLM router / API |
| 3 | **Right-size the model + context window** — stop defaulting to Opus-1M | Low | 5–12× on the downgraded share | router default |
| 4 | **Route mechanical work to the local t630 model**, reserve Claude for reasoning | Med | 60–80% of *eligible* tasks at ~$0 marginal | stage 10 / LLM router |
| 5 | **Adopt context editing + memory tool** for long Claude Code sessions | Med | up to ~84% on long agent runs | Claude Code / agent runs |
| 6 | **Use Explore/Plan subagents + `/compact`** instead of one bloated session | Low | Med | daily Claude Code habit |
| 7 | **Batch the non-interactive jobs** (monthly statements, doc reformats) | Med | ~50% (Batch API) | stage 06 / 11 |
| 8 | **Tighten our prompts** (this routine's prompt is a worked example) | Low | Med, compounding | every session |

Do 1–3 this week — they are low-effort and compounding. 4–8 are projects.

---

## The biggest token sinks *in our actual setup*

These are specific to us, not generic advice:

1. **Seven near-identical CLAUDE.md files, each large, all loaded on every session in
   their repo.** The ~15-line "House style: ordering & typography" block is **duplicated
   verbatim in all 7 repos.** That block, plus the contents tables and stage maps, is
   re-sent as input on *every* turn of *every* session. This routine alone was handed all
   seven CLAUDE.md files concatenated before it did any work.
   - **Fix:** ruthless diet. A CLAUDE.md should be the *minimum* standing context — a
     pointer file, not a manual. Move the house-style block to one
     `docs/house-style.md` and have each CLAUDE.md link to it in one line ("House style:
     see [house-style.md] — newest-first, Z→A, Gill Sans MT") instead of pasting 15 lines.
     Push the long stage map / contents tables into README (loaded on demand, not every
     turn). Target: each CLAUDE.md under ~40 lines of genuinely always-needed rules.
   - The community consensus is blunt: CLAUDE.md only pays off when output volume is high
     enough to offset its *persistent* per-turn input cost. Ours are encyclopedic.

2. **The "at session start, read these N files" ritual.** NARF says read 4 files; ZORT
   says read 6; the localDNS/MARKETING/etc. briefings each add their own. A session that
   obeys all of it reads ~10 docs *before touching the task.* Most tasks need none of them.
   - **Fix:** make these *conditional* — "read portfolio.md *only when* the task is
     cross-repo planning or a status update." Let the task pull context, don't push it.

3. **Defaulting to `claude-opus-4-8[1m]`.** The 1M-context variant carries a price premium
   above the 200K tier, and Opus is the most expensive model. These repos are docs +
   small configs — Sonnet handles ~80% of it; Haiku handles the mechanical share. We are
   paying Opus-1M rates to reformat a markdown table reverse-chronologically.

4. **One long, do-everything Claude Code session.** Tool output (file reads, `docker ps`,
   logs, `nft list`) accumulates in context — the *whole* output, not a summary — and rides
   along on every subsequent turn. A multi-hour session degrades past ~2/3 context.

5. **Broad scheduled routines on the expensive model.** *This very routine* — "search the
   web, check the news, anything that could help" on Opus-1M — is itself a recurring token
   cost. Scope and model-cap recurring jobs (see "Critique of this prompt").

---

## Lever 2: Prompt caching (the single biggest API lever)

If we hit the Claude API through the LiteLLM router for any repeated-prefix workload, this
is nearly free money:

- Mark the **stable prefix** (system prompt + CLAUDE.md + tool defs) with `cache_control`.
  The next call reusing that exact prefix reads it at **~10% of input price**. For our
  big standing prompts that is most of the input bill.
- **The 5-minute-TTL trap (2026):** the default cache lives 5 minutes. Back-to-back turns
  hit it; a session you walk away from for 6 minutes pays the full write again. For stable
  system prompts hit across a longer window, use the **1-hour extended TTL**.
- **What silently kills cache hits** (so we avoid them): any whitespace change in the
  prefix, **reordered tool definitions**, string-vs-typed-array content mismatch, and —
  most relevant to us — **a timestamp or "current date" in the cached prefix.** Our
  CLAUDE.md injects `currentDate`; if that sits inside the cached block it invalidates the
  cache every day. Keep volatile values *after* the cache breakpoint.
- Up to 4 cache breakpoints per request; cacheable content must come *before* dynamic
  content (prefix match, not substring).
- **Verify** with `cache_read_input_tokens` in the response — don't assume, confirm.

This pairs with Lever 1: a *small, stable* CLAUDE.md is also a *cacheable* one.

---

## Lever 4: Hybrid local + Claude — we're halfway there, finish it

We already run the right architecture: LiteLLM gateway (stage 10) + a local reasoning
ladder (`local-reason` on the t630, `cloud-gpu-reason` on a rented GPU, `cloud-overflow`
to Claude). Two gaps:

1. **We don't route enough to local.** Industry task mix: ~60–70% of requests are simple
   (classify, extract, format), ~20–30% moderate, ~10% need a frontier model. Our
   mechanical chores are perfect local-model work and should *never* touch the Claude API:
   - reverse-chronological / Z→A reformatting per house style
   - `tools/check-docs.py` triage and link fixes
   - commit-message drafting, changelog entries
   - lead/email classification for stage 02/08
   - first-pass extraction from a consult write-up into roster fields (stage 04→08)

   Route these to `local-reason` (t630, cool, ~$0 marginal) or the rented GPU; reserve
   Claude for design, ambiguous reasoning, and customer-facing copy.

2. **TD-14 is still open and it's the blocker to trusting the split.** A `sensitive`-tagged
   task can fail over from `local-reason` to `cloud-overflow` (Claude cloud) because the
   privacy fallback isn't fail-closed. Until that's fixed we can't honestly say "personal
   data stays local," which is exactly the dimension (data sensitivity) that justifies a
   hybrid router. **Fix TD-14 first**, then expand local routing — order matters.

Routing decision = three axes: **data sensitivity** (sensitive → local, fail closed),
**task complexity** (simple → local, hard → Claude), **availability** (local down →
fall over, but only within the allowed tier).

---

## Lever 3 & 5: Right-size model/context, and adopt the new context tools

- **Model default:** set the router default to **Sonnet**, escalate to **Opus** only for
  deep/ambiguous work, drop to **Haiku 4.5** for mechanical work. Stop defaulting to the
  **1M** context variant — only pay the >200K premium when a task genuinely needs it
  (rare for these repos). (Confirm current model IDs/prices via the `claude-api` skill
  before wiring.)
- **Context editing (new, 2026):** automatically clears stale tool calls/results from the
  window as it fills — reported up to **84%** token reduction on long agent runs while
  letting them finish workflows that would otherwise exhaust context. Turn this on for our
  long Claude Code / agent runs.
- **Memory tool (new):** file-based store outside the context window that persists across
  sessions. This is the *right* home for the "read these N files at session start" ritual —
  let the agent keep distilled portfolio/decision state in memory instead of re-reading
  full docs each session.
- **Agent Skills:** package our repeating procedures (build-a-statement, add-a-customer,
  house-style reformat, doc-link check) as Skills that load *on demand* rather than living
  permanently in CLAUDE.md. This is the structural cure for fat CLAUDE.md files.

---

## Lever 6: Daily Claude Code hygiene

- **Use Explore / Plan subagents for search and planning.** They run in their own context
  *and skip CLAUDE.md loading*, so a "where is X / how does Y work" question doesn't drag
  the giant briefing along. Each subagent's context is discarded after — only the
  conclusion returns.
- **`/compact` on long tasks** to summarize-and-continue instead of dragging raw history.
- **Scope tasks tightly:** "reformat the FAQ in 06's README newest-first," not "fix the
  docs." Smaller scope = less context pulled = fewer tokens + better output.
- **Mind tool output:** prefer the dedicated file/search tools and targeted reads over
  dumping whole logs; a 10k-line log stays in context for the rest of the session.
- **Batch related edits** into one session where context is already loaded, rather than
  five cold sessions.

---

## Lever 7: Batch the non-interactive jobs

The monthly statement run (stage 06, "a penny a home") and any bulk doc-reformat are not
interactive — they don't need a live session. The **Message Batches API** gives ~**50%**
off and stacks with caching. Wire the monthly job and bulk housekeeping through it.

---

## Critique of this routine's prompt (a worked example)

The prompt that launched this analysis is a good teaching case, because it's *us*:

> "Locate inefficiencies… Anything you could possibly think of… ANYTHING that could help.
> Search the web… Look for best practices… Keep UP TO DATE… Check the news. … If THIS
> prompt is inefficient then also let me know."

What it does well: clear domain, gives permission to use the web, asks for a self-critique.

Where it burns tokens:
- **Unbounded scope.** "Anything / ANYTHING" invites the model to explore every avenue and
  over-research. Unbounded prompts produce unbounded (expensive) runs.
- **No output contract.** No format, length, or "stop when." The model guesses, often long.
- **Several questions in one.** Token use, prompting, other AI, hybrid local, news — each a
  research thread. Bundling forces one big context to hold all of them.
- **"Check the news / keep up to date" with no cadence** invites broad open-web crawling
  every run. On a *scheduled, unwatched* routine that compounds.
- **Run on Opus-1M.** A research-and-summarize routine is Sonnet-shaped.

A tighter version (same intent, a fraction of the tokens):

```
Review our AI process for token waste. Output: a ranked table of the top 5 fixes
(lever / effort / est. saving / where), each ≤3 sentences, then a 6-item action
checklist. Ground it in our setup (CLAUDE.md sizes, the LiteLLM ladder, default
model). Web-check only these 3 things, ≤1 search each: prompt-caching TTL changes,
context-editing availability, current Opus/Sonnet/Haiku prices. Stop there — don't
expand scope. Model: Sonnet. Cadence: monthly, not on every run.
```

General prompt rules to adopt house-wide:
- **Put the deliverable contract first** (format + length + done-condition).
- **One job per prompt.** Split multi-part asks into separate, cheaper runs.
- **Bound the research** ("≤N searches," "only these sources").
- **Name the model and effort** for the job; don't let it default to the most expensive.
- **State the cadence** for anything scheduled, and cap it to the cheapest model that works.

---

## Keeping up to date — cheaply

"Check the news daily" is itself a cost. Instead:
- A **monthly** (not per-run) low-effort routine on **Sonnet**, restricted to a short
  allow-list of sources (Anthropic release notes / platform changelog, LiteLLM releases),
  that diffs against last month and appends only *new* items here. Newest-first per house
  style.
- Subscribe the human to the Anthropic changelog; let the routine summarize, not discover.

---

## Instrument first (so we measure, not guess)

Before/after, capture from the LiteLLM router: tokens in/out per model, % of calls served
locally vs cloud, and `cache_read_input_tokens` share. Without these we can't tell a real
saving from a vendor's headline number. One dashboard panel in Uptime Kuma or a nightly
log line is enough to start.

---

## Action checklist (in order)

1. [ ] Diet every CLAUDE.md: one-line link to a shared `docs/house-style.md`; move stage
       maps/contents to README; target <40 lines of always-needed rules. **(Lever 1)**
2. [ ] Make session-start "read these files" rituals *conditional*, not mandatory. **(1)**
3. [ ] Enable prompt caching on the stable prefix; move `currentDate`/timestamps *after*
       the cache breakpoint; verify with `cache_read_input_tokens`. **(2)**
4. [ ] Set router default to Sonnet; Haiku for mechanical; Opus only on demand; drop the
       1M default. **(3)**
5. [ ] **Fix TD-14** (fail-closed local fallback), *then* route mechanical chores to the
       local model. **(4)**
6. [ ] Turn on context editing + the memory tool for long runs; pilot the memory tool as
       the home for portfolio/decision state. **(5)**
7. [ ] Default to Explore/Plan subagents for search/plan; `/compact` long sessions. **(6)**
8. [ ] Move the monthly statement run + bulk reformats to the Batch API. **(7)**
9. [ ] Adopt the prompt rules above; re-scope and Sonnet-cap this routine to monthly. **(8)**
10. [ ] Add a token/cache/local-share panel so every change is measured. **(Instrument)**

---

## Sources (2026)

- Anthropic — Managing context on the Developer Platform (context editing, ~84%):
  https://anthropic.com/news/context-management
- Anthropic — Memory tool docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Anthropic — Agent Skills: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Claude — Prompt caching docs: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude — Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- "The 5-Minute TTL Change That's Costing You Money" (caching TTL trap):
  https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363
- KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage:
  https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
- Agensi — How to Reduce Claude Code Token Usage (8 methods):
  https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage
- SitePoint — Hybrid Cloud-Local LLM Architecture Guide (2026):
  https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- BuildMVPfast — Hybrid Cloud-Local AI Workflow Cost Optimization (60–80%):
  https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- Claude Code — Sub-agents docs: https://code.claude.com/docs/en/sub-agents
- Claude Code — Best practices: https://code.claude.com/docs/en/best-practices
