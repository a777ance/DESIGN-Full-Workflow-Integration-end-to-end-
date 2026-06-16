# Process efficiency — how we work with the AI

**Audit date:** 2026-06-16 · **Author:** NARF (AI CTO routine) · **Scope:** the
user↔AI loop across all A777ance repos — token cost, prompting, and the
local/cloud hybrid we already own.

This is a standing audit, not a one-off. The LLM-cost landscape moves weekly;
re-run this routine and update the table when the numbers or the tooling shift.

---

## TL;DR — the five changes ranked by money saved

| # | Change | Effort | Est. saving | Status |
| - | ------ | ------ | ----------- | ------ |
| 1 | **Finish & deploy the deterministic dispatcher** so 60–70% of simple work runs on local Ollama / cloud Haiku, not Opus | M (it's already specced + `dispatcher.py` exists) | **60–80% of API spend** | dispatcher designed, not deployed (TD-15) |
| 2 | **Stop loading every repo's full `CLAUDE.md` into every session** — trim to a thin "always-load" core, push detail to on-demand files | S | ~10–20k input tokens **per session start** | open |
| 3 | **De-duplicate the House-style block** (copy-pasted verbatim into 6 `CLAUDE.md` files) | S | smaller, but pure waste; helps cache | open |
| 4 | **Right-size the model to the task** — routines/monitors on Haiku/Sonnet, Opus only for hard reasoning (this very routine ran on Opus 4.8) | S | 5–15× on autonomous runs | open |
| 5 | **Turn on prompt caching + use subagents for file-heavy reads** | S | 50–90% off repeated context | partially in use |

Everything below is the detail behind that table.

---

## 1. The biggest lever is already half-built: the dispatcher

We already run a hybrid stack — LiteLLM front door on the t630, local `qwen2.5`
tiers, a rented-GPU reasoning tier, and `cloud-overflow` → Claude. The
[ORCHESTRATION-BLUEPRINT](https://github.com/a777ance/localDNS/blob/main/10-ai-orchestration/ORCHESTRATION-BLUEPRINT.md)
specs a **deterministic Python dispatcher** that classifies each request and
routes it to the cheapest backend that can do the job, and `dispatcher.py`
already exists as a runnable starting point. **It is not deployed.**

Industry numbers for 2026 say a typical workload is **~60–70% simple** requests
(classification, extraction, formatting, drafting), ~20–30% moderate, and only
~10% needing a frontier model. Routing that bottom 60–70% to local models or to
Haiku instead of Opus is the single biggest cost reducer — published hybrid
setups report **60–80% savings with minimal quality loss**, and routing
background tasks to a cheap model (DeepSeek is ~50× cheaper than Opus) is the
headline win.

**Action:** finish Phases 3–4 of the blueprint (the rule table + dispatch).
Caveat first: close **TD-14** — `local-reason` currently fails over to
`cloud-overflow`, so a `sensitive` task can leak to Claude cloud if the local
model is down. Fail closed before routing more volume through this path.

## 2. We pay to re-read the same docs every session

Look at how this very session started: the full `CLAUDE.md` of **7 repos** was
injected as context, plus `localDNS/CLAUDE.md` a **second** time as a file read —
before a single word of the task. The DESIGN `CLAUDE.md` alone is 295 lines;
localDNS is ~250. That is easily **10–20k input tokens loaded before any work**,
every session, most of which is irrelevant to any given task.

Best-practice guidance is blunt about this: Claude Code cost "usually comes from
bloated context, not long prompts," and reasoning quality itself degrades past
~3k tokens of instruction. Our `CLAUDE.md` files are reference manuals, not
briefings.

**Action:**
- Cut each `CLAUDE.md` to the ~40–60 lines that are true *every* session (what
  the repo is, the hard rules, where to look). Move the deploy-path tables, full
  known-issues lists, and verification scripts to README/linked files that the
  AI reads **on demand** — it already follows links.
- Make the NARF/ZORT "read these 4–6 files at session start" blocks
  **conditional** ("when doing CTO/CFO planning, read…") instead of an
  unconditional every-session read of `portfolio.md` + `roadmap.md` +
  `tech-debt.md` + `decisions.md` + the 6 CFO files.
- Scope sessions to the repo(s) a task actually touches. Loading 7 repos to edit
  one is 6 repos of waste.

## 3. The House-style block is duplicated 6 times

The identical ~18-line "ordering & typography" block is pasted verbatim into 6
`CLAUDE.md` files. When several repos are in context it's loaded several times.
It also hurts prompt caching (see §5): cached prefixes want to be *shared and
stable*, not N near-copies.

**Action:** keep the canonical block in one place (the hub, or a
`docs/house-style.md`) and have the other repos link to it in one line. House
style is a convention, not something the AI must re-read in full per repo.

## 4. Match the model to the job — especially for autonomous runs

This audit routine ran on **Opus 4.8 [1m]**, the most expensive tier, to do work
that is mostly reading and summarising. Prompt-cache is also **per-model**, so
switching Opus↔Sonnet mid-flow throws away the cache.

**Action:**
- Default scheduled routines and monitors (PR-watching, doc-integrity, status
  sweeps) to **Haiku or Sonnet**; escalate to Opus only when a step genuinely
  needs deep reasoning. The hybrid router already makes this a one-line change.
- Pick one model per session and stay on it so the cache survives.
- Reserve Opus for the ~10%: hard architecture, ambiguous refactors, the
  Statement-honesty judgement calls.

## 5. Caching + subagents (mostly free, partly already on)

- **Prompt caching:** stable content (a trimmed `CLAUDE.md`, tool definitions)
  should sit at the **front** of the prompt and never change, so it caches.
  Volatile content (today's date, "current status") belongs at the **end** — a
  date at the top of a cached file busts the whole prefix. Enable the 1-hour
  cache (`ENABLE_PROMPT_CACHING` / extended TTL) for long sessions: 50–90% off
  repeated input.
- **Subagents:** anything that needs reading more than ~3–4 large files is a
  subagent candidate — the subagent's context stays out of the main session and
  only its conclusion returns. (This audit used that pattern.) Claude Code in
  2026 also auto-**compacts** long context and has a **memory** layer; lean on
  them instead of manually re-pasting.

---

## Critique of the prompt that launched this audit

The request was, paraphrased: *"Locate inefficiencies in our process… Is there a
better way to reduce token use?… Anything you could possibly think of… ANYTHING
that could help… Search the web… Check the news… Keep up to date. If THIS prompt
is inefficient, tell me too."*

**What worked:** stating the goal (reduce token cost), naming the hybrid-LLM
angle, asking for web/recency, and — smartly — asking the model to critique the
prompt itself. That last move is genuinely good practice.

**What cost tokens unnecessarily:**
- **Open-ended maximalism.** "Anything… ANYTHING… anything you could think of"
  tells the model to fan out maximally — more searches, longer output, no
  priority. 2026 prompting guidance: treat a prompt like a *contract* — state the
  goal, the constraints, the inputs it may use, and **the exact shape of the
  output**. That single change turns a sprawling survey into a ranked, bounded
  answer.
- **No constraints or context given.** It didn't mention that a hybrid router
  already exists, which repos matter, or any budget figure — so the model spends
  tokens rediscovering our own setup.
- **No output spec.** "Let me know" leaves length and format open, so the model
  errs long.

**A tighter rewrite (≈90 words, drop-in):**

> Audit our Claude/AI usage for cost and friction. Context: 7 A777ance repos; a
> LiteLLM hybrid router (local Ollama + Claude cloud) already exists but the
> dispatcher isn't deployed; large per-repo `CLAUDE.md` files. Find the top 5
> changes that cut token/$ spend or back-and-forth, **ranked by money saved**,
> each with an effort estimate (S/M/L) and a one-line action. Use 2026 sources;
> flag anything that changed in the last ~30 days. Keep it to one page. Then
> critique this prompt.

Same answer, a fraction of the tokens, and the priority ordering is forced by the
spec instead of left to chance. **Rule of thumb for us:** every recurring ask
(especially routines) should name its context, its constraints, and its output
shape — write the prompt once, well, and stop paying for the model to guess.

---

## Sources (2026)

- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Compaction — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Context engineering: memory, compaction, tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Best practices for prompt engineering — Claude](https://claude.com/blog/best-practices-for-prompt-engineering)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Claude Code Token-Saving Guide: Models, MCP, CLAUDE.md, Skills & Cache — knightli.com](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM smart routing — Markaicode](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Claude Code Guide 2026: 25 Features — MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [Prompt engineering best practices 2026 — Thomas Wiegold](https://thomas-wiegold.com/blog/prompt-engineering-best-practices-2026/)
