# Process efficiency review — user↔AI workflow & token spend (2026-06-21)

NARF (AI CTO) review, prompted by the founder: *"Find inefficiencies in our process
between the user and the AI. Reduce token use. Better prompting. Hybrid local LLM +
Claude. Keep up to date — check the news."*

Scope: how we *work with* the models (Claude Code + the Odin/LiteLLM router), not the
network stack. Findings are ordered by leverage (biggest token/$ win first).

---

## TL;DR — the five moves that matter

1. **Trim & de-duplicate the `CLAUDE.md` files.** They are loaded *in full, every
   session*. DESIGN (295 lines, ~3.5k tok) and localDNS (326 lines, ~3.6k tok) are over
   the ~200-line best-practice ceiling, and the ~40-line house-style block is copy-pasted
   into all six repos. **Est. ~10.7k tokens load before a single useful instruction.**
2. **Scope routines/sessions to one repo.** This very routine injected *all six*
   `CLAUDE.md` files (~10.7k tok) plus the note "this context may or may not be relevant."
   Cross-repo work needs that; single-repo work pays for five repos it never touches.
3. **Right-size the model per task.** This analysis routine is running on **Opus 4.8
   [1M]** — our most expensive model — to read web pages and write Markdown. Sonnet (or
   Haiku for the fan-out) would do it at a fraction of the cost.
4. **Verify prompt caching is actually on** for our own router/agent calls (Claude Code
   already caches; our LiteLLM-mediated NARF/ZORT calls may not). Correctly structured,
   caching cuts the repeated-prefix cost by **~90%**.
5. **Tighten the prompts.** Open-ended "find ANYTHING that could help" prompts invite
   long, expensive answers. A scoped prompt with an output budget is cheaper *and* better.
   (Critique of today's prompt is in the last section.)

---

## 1. `CLAUDE.md` bloat & duplication — biggest, easiest win

**What's happening:** Claude Code loads the repo's `CLAUDE.md` into context at session
start. Skills, by contrast, load *on demand* only when their description matches the task.
Anything in `CLAUDE.md` is paid for on every turn, even unrelated work.

**Measured today:**

| Repo | Lines | ~Tokens |
| ---- | ----- | ------- |
| localDNS | 326 | 3,637 |
| DESIGN | 295 | 3,477 |
| MARKETING | 214 | 1,926 |
| customers | 80 | 749 |
| claude-code-homelab | 75 | 494 |
| Azure-lab | 50 | 421 |
| **Total** | **1,040** | **~10,700** |

**Fixes:**
- The identical ~40-line **house-style block** lives in all six files. Keep the canonical
  copy in DESIGN; in the others replace it with a one-line pointer + a `SessionStart` hook
  (or a `house-style` skill) that loads it *only when a doc is being edited*. Saves
  ~200 lines (~2k tok) of pure repetition across the portfolio.
- localDNS and DESIGN: move the **deploy-path tables, verification command blocks, and the
  nftables checklist** out of `CLAUDE.md` into linked reference files (`DEPLOY.md`,
  `VERIFY.md`) or skills. The model rarely needs the full deploy table just to answer a
  question — let it `Read` the file when it does.
- Target: each `CLAUDE.md` ≤ ~150 lines of *true* always-on essentials (what the repo is,
  the hard rules, where to look next). Everything else becomes on-demand.

**Why it's safe:** content isn't deleted, it's relocated to files the model can open when
relevant. Net effect: smaller per-turn base context, same knowledge available.

## 2. Scope context to the work — don't pay for six repos to touch one

The routine harness concatenated every repo's `CLAUDE.md` here, flagged "may or may not be
relevant." That's correct for a *cross-repo* review like this one, but most work is
single-repo. Recommendations:
- Run single-repo routines/sessions pointed at one working directory so only that repo's
  `CLAUDE.md` loads.
- For genuinely cross-repo routines (the daily review, this one), lean on **prompt caching
  with a 1-hour TTL** so the stable multi-repo prefix is written once and re-read at ~10%
  cost for the rest of the run (see §4).

## 3. Model right-sizing & subagents

Industry data this week is consistent: ~60–70% of agent requests are "simple" (search,
extract, format), ~20–30% moderate, ~10% need a frontier model. Mapping that onto us:
- **Routines that read and summarize** (this one, the daily review) can default to
  **Sonnet 4.6**, escalating to Opus only when a task is genuinely deep. Reserve Opus 4.8
  for hard refactors/analysis.
- **Use Haiku exploration subagents + Sonnet for the write-up.** Reported ~40–50% cost cut
  vs. Sonnet-for-everything. A subagent reads 20 files and returns only a summary — its
  verbose output never lands in (or re-bills against) the main context. Our daily-review
  cadence is a natural fit: fan out per-repo Haiku scans, synthesize once.
- **Disable/lower extended thinking** for mechanical tasks; thinking tokens bill as
  output. Keep it on only for planning/reasoning-heavy work.

## 4. Prompt caching — make sure we're getting it

Claude Code applies caching automatically. Our **own** programmatic calls (NARF/ZORT via
LiteLLM → Anthropic) are the risk: caching only helps if the request is structured for it.
- **Structure stable-first:** system prompt + repo context + tool defs first (cached),
  the changing task last. A 30k-token prefix drops from ~$0.09 to ~$0.009 per call on a hit.
- **Mind the breakpoints:** changing the tool list between calls *breaks* the cache at that
  point — keep tool definitions stable across a routine's run.
- **TTL math:** 5-min cache pays off at 3+ reads; 1-hour cache at 5+ reads. The daily
  cross-repo review and multi-step routines clear that bar easily.
- **Action:** add a cache-hit-rate line to the LiteLLM/router metrics so we can *see*
  whether caching is firing, not assume it.

## 5. Hybrid local + Claude — we already have this; tighten it

We're ahead here: the Odin/LiteLLM reasoning ladder already routes light work to
`local-reason` (deepseek-r1:1.5b on the t630) and heavy work to `cloud-gpu-reason` /
`cloud-overflow`. Refinements:
- **Push more of the 60–70% "simple" tier local.** Classification, extraction, short
  summarization, and template fills run fine on a quantized 7–13B local model; only
  multi-step reasoning, long-context synthesis, and hard code-gen need Claude. A routing
  rule keyed on task type (not just "reason vs not") captures more savings.
- **Fix the privacy fallback first (TD-14).** A `sensitive`-tagged task can currently fail
  over from `local-reason` to `cloud-overflow` (Claude cloud) when the local model is
  down — `allow_cloud=False` isn't enforced at the LiteLLM failover layer. Give
  `local-reason` a **local-only** fallback so it fails *closed*. No hybrid-privacy claim
  holds until this is fixed.

## 6. Skills & hooks over prose instructions (zero-context enforcement)

- **Hooks cost zero context** unless they emit messages. Move deterministic rules there:
  `python3 tools/check-docs.py` should run as a pre-commit/`Stop` hook (TD-11 wired it into
  CI — also wire it locally so the model isn't reminded to run it in prose).
- **Skills load on demand.** Specialized, occasional workflows (build-a-statement,
  add-a-customer, house-style application) belong in skills, not in always-on `CLAUDE.md`.
- Rule of thumb from this week's guidance: *behavioral constraint → hook; reusable
  workflow → skill; broad always-true context → `CLAUDE.md` (kept lean).*

## 7. Session hygiene

- Watch the context meter; **restart at ~80%** rather than letting quality degrade.
- `/compact` between phases of long sessions to keep decisions without every intermediate
  step.
- One task per session where practical — long mixed sessions carry stale context forward.

---

## News this week that changes our planning (checked 2026-06-21)

- **Fable 5 & Mythos 5 suspended (June 12) by a US export-control directive.** If any
  roadmap item assumed Fable 5's 1M-context / always-on adaptive thinking, **re-plan on
  Opus 4.8** (1M context by default on the API/Bedrock/Vertex; 200k on MS Foundry).
- **`response_inclusion` / result-trimming for agentic tool use** is now exposed on the
  Developer Platform — lets an agent drop already-consumed tool result blocks from context.
  Directly useful for the Odin multi-agent loop (Heimdall→Odin→host) to stop tool output
  accumulating across steps.
- **Code-execution tool now exposes the 90s/cell limit** for long-running cells — relevant
  if we move any collect/stats jobs into tool-driven runs.
- **Workload Identity Federation (WIF)** replaces static API keys with short-lived scoped
  credentials. Worth adopting for the router's `ANTHROPIC_API_KEY` (today a `.env` secret)
  — fewer long-lived keys to rotate/leak.
- **Web-search tool returns richer cited SEC data** — minor for us; could ground any ZORT
  market/benchmark research in primary sources instead of placeholders.

---

## Critique of the prompt that triggered this review

The founder asked: *"Locate inefficiencies… Is there a better way… Perhaps better
prompting… Anything you could possibly think of… ANYTHING that could help. Search the web…
Keep UP TO DATE… Check the news. If THIS prompt is inefficient then also let me know."*

It's a *good* exploratory prompt — clear intent, explicitly invites web research and
self-critique. But it is **token-expensive by construction**, and that's the irony worth
naming:

- **"Anything / ANYTHING" has no stopping condition.** An unbounded ask invites an
  unbounded (expensive) answer. Add a scope and an output budget: *"Top 5 levers, ≤2
  pages, ranked by $ saved."*
- **No output target.** Say where the answer should land (this file) and in what form
  (table / ranked list) so the model doesn't hedge with a survey of options.
- **Mixed asks in one prompt** (process audit + prompt critique + news scan). Fine here,
  but for routine work, one prompt = one task caches and reruns better.
- **It ran on Opus 4.8 [1M].** A research-and-summarize routine like this should default to
  **Sonnet**; reserve Opus for the deep refactors.

**A tighter reusable version:**

> "Audit our user↔AI workflow for token waste. Output the **top 5 fixes ranked by tokens/$
> saved**, each with a one-line action, into `docs/ai-cto/reviews/<date>-process.md`. Use
> web search only for anything that changed in the last 30 days. ≤2 pages. Run on Sonnet."

That keeps the open-ended discovery you want while bounding cost and giving the model a
clear finish line.

---

## Suggested follow-ups (for tech-debt / roadmap)

- TD: Trim & de-duplicate the six `CLAUDE.md` files; relocate deploy/verify tables to
  linked refs or skills (P2 — recurring token cost on every session).
- TD: Add cache-hit-rate + per-tier routing-share metrics to the LiteLLM router (P2 —
  can't optimize what we don't measure).
- TD-14 (existing): enforce local-only fallback for `sensitive` tasks — fail closed (P1).
- Default analysis/review routines to Sonnet; adopt Haiku exploration subagents for the
  daily cross-repo review (P2).
- Evaluate WIF for the router's Anthropic credential (P3).

## Sources

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude API Prompt Caching & Token Efficiency Guide — hidekazu-konishi](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid LLM Routing: Ollama + Claude API — DEV](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code: Skills, Subagents, Hooks, Plugins — boringbot](https://boringbot.substack.com/p/claude-code-skills-subagents-hooks)
- [Claude Updates by Anthropic — June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude)
- [Claude Developer Platform Updates — June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-developer-platform)
