# AI Process Efficiency Review — how we use Claude (the user↔AI loop)

**Date:** 2026-06-23 · **Author:** NARF (AI CTO) routine · **Status:** findings + recommendations
**Scope:** token spend and prompting across our Claude Code / Claude API usage, and how to lean
on the hybrid router we already run. Newest-first per house style.

---

## TL;DR — the levers, ranked by payoff

| # | Lever | Effort | Est. saving | Where it bites today |
| - | ----- | ------ | ----------- | -------------------- |
| 1 | **Route Claude Code through a model tier, not always Opus** | low | 50–90% on routine work | This very routine runs on `claude-opus-4-8[1m]`; most of it is read-and-summarize that Haiku/Sonnet do fine |
| 2 | **Trim the CLAUDE.md prefix; stop loading 7 repos at once** | low | big, every turn | All 7 `CLAUDE.md` (~15k+ tokens) inject into a multi-repo session; the house-style block is duplicated verbatim 7× |
| 3 | **Prompt-cache discipline** | low | up to ~90% input | Mid-session model swaps / MCP toggles / prepending to in-context files silently bust the cache |
| 4 | **Use Explore/Plan subagents for research** | low | avoids CLAUDE.md reload | They skip CLAUDE.md + git status by design — the cheapest way to fan out |
| 5 | **Batch API for non-interactive routines** | medium | 50% flat | Scheduled jobs like this one don't need real-time latency |
| 6 | **Point Claude Code at our own LiteLLM front door** | medium | 60–80% blended | We built the hybrid router (stage 10) and aren't aiming Claude Code at it |
| 7 | **Tighten the prompts themselves** | low | variable | Open-ended "do ANYTHING" prompts (see §7) maximise exploration cost |

---

## 1. The single biggest miss: we don't tier the model

This routine is executing on **`claude-opus-4-8` with the 1M-context beta** — the most
expensive configuration we can buy — to do what is largely *read files, search the web,
summarize*. Opus input/output runs roughly **$5 / $25 per Mtok**, and the 1M-context beta
**surcharges tokens above the 200k mark** on top of that. Sonnet 4.6 (~$3/$15) handles
code; Haiku 4.5 is ~**25× cheaper per token than Opus** and is the right tool for
classification, extraction, formatting, link-checking, and log-scan routines.

**Do this:**
- Set per-task model floors. Run scheduled/cron routines (doc-link checks, metrics
  scrapes, "scan for X") on **Haiku**; reserve Opus for genuine hard reasoning.
- In Claude Code, codify model limits in subagent YAML and commit them so no agent
  silently defaults to the priciest model: *"code review on Sonnet, linting on Haiku,
  enforced by configuration, not willpower."*
- For Claude Code subscription sessions, `/model` down to Sonnet/Haiku for routine edits;
  escalate to Opus only when a task is actually reasoning-bound.

## 2. The context prefix is bloated and over-loaded

Our `CLAUDE.md` files are excellent documentation but **heavy**: this multi-repo session
loaded all seven of them — well over 15k tokens — before a single instruction was read,
and the entire **house-style block (~400 words) is duplicated verbatim in every one**.
That prefix is re-sent (cached, but still counted on writes and on every cache miss) on
each session, and it pushes long sessions toward the 200k 1M-context surcharge.

**Do this:**
- Keep `CLAUDE.md` to the *durable, must-know-every-session* facts; push the long deploy
  tables and verification blocks into `README.md` and link them. Explore/Plan subagents
  skip CLAUDE.md anyway, so detail there is wasted on research turns.
- Factor the shared house-style block into **one canonical file** and have each repo's
  CLAUDE.md link to it instead of repeating it. (Single source of truth — our own rule.)
- Scope sessions to **one repo** unless a task is genuinely cross-repo. Loading the whole
  portfolio "just in case" is the costliest default we have.

## 3. Prompt-cache discipline (cheap, easy to lose)

Prompt caching cuts repeated-context input cost by up to ~90% (cache reads ≈ **10%** of
base input; cache writes cost **+25%**; default TTL **5 min**, extendable to 1 hr at 2×
write). The catch is that the cached **prefix must stay byte-stable**:

- **Don't switch models mid-session**, don't install/toggle MCP servers or Skills
  halfway through, and don't use CLAUDE.md as a scratchpad — each invalidates the prefix
  and re-bills the whole thing as a write.
- Note our **newest-first house style**: prepending to a log/changelog that's *currently
  in context* moves the prefix and busts the cache from that point. Fine for files we
  don't hold in context; worth knowing for ones we do.
- Use `/compact` on long sessions to shrink the prefix before it balloons.
- Heads-up from the field: a **March 2026 Anthropic caching bug caused 10–20× token
  inflation** silently. Watch the token counter; if a session's usage looks wrong, it
  might not be us.

## 4. Subagents — power and price

Subagent-heavy workflows can burn **~7× the tokens** of a single thread (each subagent
carries its own context); 10 parallel agents drain quota 10× faster. They're worth it for
true parallel fan-out, but:

- **Explore** and **Plan** subagents *skip CLAUDE.md and the parent git status* to stay
  cheap — prefer them for "go find/where is X" research instead of doing it in the main
  thread (which carries the full prefix).
- Commit `.claude/agents/` definitions with model caps so fan-out can't quietly run on
  Opus.
- New in June 2026: agent-teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), a better
  subagent panel, and ctrl+b backgrounding that no longer restarts the agent. Useful, but
  every parallel session is real token spend — reach for teams only when one specialist
  genuinely isn't enough.

## 5. Batch API for non-interactive routines

Anything that doesn't need a human waiting — like this scheduled review, metrics rollups,
nightly summaries — qualifies for the **Batch API at a flat 50% discount**. Restructure
recurring jobs that tolerate minutes-to-hours latency to run as batches rather than live
Claude Code sessions on Opus.

## 6. Aim Claude Code at the router we already built

We have the whole hybrid substrate standing (stage 10: LiteLLM front door at
`ai.home.lan:4040`, local Qwen tiers on the t630, rented-GPU DeepSeek, `cloud-overflow` →
Claude, plus the deterministic `dispatcher.py` privacy gate). **We just aren't pointing
Claude Code at it.** The 2026 ecosystem move is a proxy like **Claude Code Router** (or our
own LiteLLM endpoint) sitting between Claude Code and the API, classifying each request and
sending simple ones local/Haiku and hard ones to Opus — reported **50–99% API savings**;
the common "60–70% of requests are simple, ~10% need a frontier model" distribution is
exactly the shape of our work.

Two cautions specific to us:
- **Privacy gate still applies.** Our `dispatcher.py` invariant — sensitive tasks pin
  local, no cloud fallback — must hold for any Claude-Code-through-router path too. Real
  customer data (the `customers` repo) must not leak to a cloud tier.
- **Don't over-build.** Per our own "liquidity before app" philosophy: Claude Code Router
  is an off-the-shelf proxy, not a project. Use it; don't build one.

## 7. The prompt that triggered this run — critique

The instigating prompt was, paraphrased: *"Locate inefficiencies in our process… Is there
a better way to reduce token use?… better prompting?… Anything you could possibly think
of. Leveraging other AI. Hybrid local LLM and Claude. ANYTHING that could help. Search the
web… Keep UP TO DATE… Check the news. Thanks!"*

It's a **good intent, expensively framed.** What makes it costly:

- **Unbounded scope** ("ANYTHING," "anything you could possibly think of") invites maximal
  fan-out — many web searches, broad reading — with no stop condition. That is the single
  biggest token driver in the prompt.
- **No named deliverable or destination** — the model has to guess whether you want a chat
  reply, a file, a commit, or a PR (it produced this doc).
- **No budget / depth cap** — "keep up to date, check the news, day by day" reads as
  *open-ended recurring research*, which is the most expensive mode.
- **Mixed registers** — strategy ("better way?"), tactics ("token use"), and infra
  ("hybrid local LLM") in one breath, so the model has to cover all three.

**A tighter rewrite (drop-in):**

> *"Audit our Claude usage for token waste. Deliverable: a ranked list of the top 5 levers
> with rough % savings, written to `docs/ai-cto/reviews/`. Cover: model tiering, CLAUDE.md
> size, prompt caching, and routing Claude Code through our LiteLLM. Do at most 4 web
> searches for 2026-current best practices; cite them. Run on Sonnet, not Opus. Stop at
> the ranked list — don't implement. ~20 min budget."*

That version fixes scope (top 5, stop condition), names the artifact and location, caps
search depth, sets the model, and separates audit from implementation. Same answer, a
fraction of the tokens.

**Meta-fix:** make this an inexpensive **recurring** routine (Haiku/Sonnet, capped
searches, append-to-this-file) rather than an open-ended Opus run, so "keep up to date"
costs little per cycle.

## 8. Keeping current (cadence, not constant)

The field moves weekly; "check daily" is itself wasteful. Suggested rhythm:
- **Monthly**, watch the Claude Code release notes (`code.claude.com/docs/en/whats-new`)
  and Anthropic release notes — Haiku on Haiku, 5 searches max, append a dated bullet here.
- Track three numbers as our own KPIs: **blended $/session**, **% of turns served by a
  non-Opus tier**, and **cache-hit ratio**. If we can't see them, we can't cut them.

---

## Sources
- Claude API — Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude Code — How Claude Code uses prompt caching: https://code.claude.com/docs/en/prompt-caching
- Claude Code token optimization (2026): https://buildtolaunch.substack.com/p/claude-code-token-optimization
- Token-saving guide — models, MCP, CLAUDE.md, Skills & cache: https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/
- Run local models with Claude Code to cut costs 10×: https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- Claude Code Router guide (2026): https://www.getaiperks.com/en/ai/claude-code-router-guide
- Hybrid cloud-local LLM architecture (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Subagents — context, cost, parallel execution: https://www.mindstudio.ai/blog/claude-code-sub-agents-explained
- Claude Code agents 2026 — what parallel sessions cost: https://www.cloudzero.com/blog/claude-code-agents/
- Create custom subagents (docs): https://code.claude.com/docs/en/sub-agents
- Claude Code — what's new: https://code.claude.com/docs/en/whats-new
- LLM API pricing 2026 comparison: https://www.aimagicx.com/blog/llm-api-pricing-comparison-2026
