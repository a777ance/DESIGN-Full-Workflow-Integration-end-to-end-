# Process efficiency: getting more out of the AI for fewer tokens

*Audit date: 2026-06-27. Reviews the user↔AI working process across the seven A777ance
repos and ranks concrete changes by return-on-effort. Newest review leads (house style).*

This is a **process** review, not a code review. The question: where are we spending tokens
(money + latency) on the way Claude is invoked, and where could better prompting, cheaper
models, or local LLMs do the same job for less?

---

## TL;DR — the five wins, ranked by payback

| # | Change | Why it pays | Effort |
| - | ------ | ----------- | ------ |
| 1 | **Trim the mandatory session-start reading** (NARF reads 4 files, ZORT reads 6 — ~13k tokens *before any work*) | That's paid on *every* DESIGN-repo session, cold, before the first useful turn. Replace "read these 9 files" with "read `portfolio.md`; open the others only if the task touches them." | 1 hr |
| 2 | **De-duplicate the house-style block** (copied verbatim into 6 CLAUDE.md files ≈ 2k tokens of hand-maintained copy) | It reloads every turn in every repo and drifts when edited in one place. Put it in one file, link to it. | 1 hr |
| 3 | **Default to Sonnet; reserve Opus for hard reasoning** | Sonnet is ~5× cheaper per token than Opus and handles doc edits, link-checking, roster edits, and statement composition fine. Opus only for architecture/ambiguous design. 30–80% of session cost is model tier. | 0 — just `/model` |
| 4 | **Push verbose work into subagents** (Explore, general-purpose) | A grep across 7 repos or a "find where X lives" dumps thousands of lines into the *main* context that then reload every turn. A subagent returns only the conclusion. | per-task habit |
| 5 | **Protect the prompt cache** — stop putting today's date / volatile state in cached prefixes | The 5-min TTL change (early 2026) already raised effective cost 30–60%; a timestamp in a cached prefix re-bills the whole prefix every call. | ongoing hygiene |

Everything below is the detail behind these.

---

## 1. The biggest leak is our own session-start protocol

Measured today:

- **CLAUDE.md files total ≈ 8,030 words ≈ ~11k tokens.** DESIGN (~3.4k tokens) and localDNS
  (~3.5k tokens) are the heavy two, and a repo's CLAUDE.md is in the system prompt on **every
  turn** of every session in that repo.
- **The NARF (CTO) + ZORT (CFO) "read at session start" lists total ≈ 10,074 words ≈ ~13k
  tokens across 9 files** — read *before the first useful action* in any DESIGN-repo session.

A 5k-token CLAUDE.md costs 5k tokens before you've typed a word, every turn, every session
([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage),
[buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)). Loading
instructions that aren't relevant to the current task is the single biggest hidden cost; the fix
is **load-on-demand**, not load-all-up-front.

**Do this:**

- Change the NARF/ZORT preambles in CLAUDE.md from *"read these 6 files"* to: **"Read
  `portfolio.md`. Open `roadmap.md` / `decisions.md` / `runway.md` / `metrics.md` /
  `budget.md` only when the task touches that area."** Most sessions touch one area.
- Move the deep CLAUDE.md content (the full funnel diagram, the stage map, the nftables deploy
  checklist in localDNS) into **Skills** — a SKILL.md loads its body only when the task matches
  its description, instead of sitting in the system prompt every turn
  ([Claude Code skills docs](https://code.claude.com/docs/en/skills),
  [MindStudio benchmark: ~70% cut](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked)).
  Keep CLAUDE.md to the one-screen briefing + pointers. localDNS's "F. nftables volume layer
  deploy checklist" is a textbook skill candidate: needed rarely, costs tokens always.
- Use `/context` to see what's actually eating the window, and `/clear` between unrelated tasks
  rather than letting one session accrete ([Claude Code cost docs](https://code.claude.com/docs/en/costs)).

## 2. Kill the duplicated house-style block

The house-style/typography block (reverse-chronological, Z→A lists, Gill Sans MT, reverse-the-
blocks) is **copied verbatim into 6 of 7 CLAUDE.md files**. That's ~2k tokens of identical text
that (a) reloads on every turn in every repo and (b) has to be edited in six places to change
once — exactly the drift risk that "one source of truth" is supposed to prevent.

**Do this:** keep the full block in *one* canonical file (it already reads like a shared
standard — put it in the DESIGN repo, e.g. `docs/house-style.md`), and in each repo's CLAUDE.md
replace the block with a two-line summary + a link. The per-repo CLAUDE.md still tells Claude
the rules exist; the detail loads only if a task needs it.

## 3. Model selection — the zero-effort 5× lever

Start sessions on **Sonnet**; switch to **Opus only for deep analysis or genuinely hard
refactors/design** ([claudefa.st](https://claudefa.st/blog/guide/development/usage-optimization),
[agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)). For this
portfolio specifically, Sonnet comfortably handles: doc edits, `check-docs.py` link fixes,
roster.json edits, statement composition, CLAUDE.md upkeep, commit/push mechanics. Save Opus for
ADR-level design calls, the contractor-classification reasoning, pricing-model work, and
cross-repo architecture. Combined model + context discipline is where the cited
30–80% reductions come from.

## 4. Push verbose work into subagents

Every file read, shell output, and MCP response is appended to context **in full, not
summarized**, and then rides along on every later turn
([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)).
A cross-repo "where does X live?" or a big log dump can balloon the window for the rest of the
session. Subagents have **their own context window** and hand back only the answer
([Anthropic: steering Claude Code](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)),
so the noisy part never touches the main thread. Use the **Explore** agent for "find/locate"
sweeps and **general-purpose** for multi-step research. This routine itself used a subagent-style
web sweep rather than reading ten pages into the main context.

## 5. Prompt-cache hygiene (this is now a real cost line)

Claude Code already caches the system prompt + CLAUDE.md automatically — but the cache is matched
as a **prefix**, so anything volatile near the top invalidates everything after it
([Claude prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[aimagicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)).
Two changes in early 2026 raised the stakes: TTL dropped from 60 min → **5 min**
([dev.to](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)),
and caches went **workspace-isolated** (2026-02-05). Practical rules:

- **Keep `currentDate` / "today is…" / live KPI snapshots out of cached prefixes.** A date in the
  system prompt re-bills the whole prefix every request. Put volatile state in the *user* turn or
  a file Claude reads, not in CLAUDE.md.
- Order CLAUDE.md **stable-first, volatile-last** so the durable prefix keeps hitting cache.
- The 5-min TTL means **batching a repo's work into one focused session beats many short ones** —
  scattered one-off prompts each pay a cold cache write (1.25× input) and then expire.

## 6. Hybrid local + Claude routing — you already own the rails

You already run the LiteLLM router on the t630 (`10-ai-orchestration`) with a reasoning ladder
(`local-reason` deepseek-r1:1.5b on CPU → `cloud-gpu-reason` → `cloud-overflow`). That is exactly
the architecture the 2026 guides recommend: a routing layer that sends ~60–70% simple work
(classification, extraction, formatting, "is this link dead", "summarize this log") to a **local
model**, ~20–30% moderate work to mid-tier, and only the ~10% frontier-reasoning work to Claude —
typically **60–80% cost reduction**
([sitepoint hybrid guide](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).

**Where it pays here, today, without new infra:**

- Route **pre-processing** through the local model before Claude sees it: summarize a long Kuma
  log, pre-classify a batch of leads, draft first-pass "Handled For You" entries, sanity-check
  reverse-chron ordering — then hand Claude the distilled result. Cheap local tokens replace
  expensive context.
- Keep **privacy-sensitive** customer-data passes (roster.json, household stats) on the local
  model where feasible — the `customers` repo is private precisely because this data shouldn't
  leave the box; local inference is the natural fit and the hybrid guides flag data-sensitivity
  as a primary routing signal.
- Claude Code can itself be pointed at non-Anthropic/local models for the cheap legs
  ([techsy: OpenRouter+Ollama](https://techsy.io/en/blog/claude-code-use-different-models)),
  but keep the frontier work (this kind of cross-repo reasoning, ADRs, design) on Claude — that's
  where it earns its price.

Caveat: don't run heavy chain-of-thought models (deepseek-r1:7b+) on the t630/laptop CPU — your
own localDNS Known-Issues already documents that it cooks the box. The ladder is the right shape;
just push more of the *routine* legs onto the cool local tier.

## 7. Prompting habits that cut rework (rework is the silent token sink)

- **Be specific.** "Make this better" forces Claude to read everything and guess; "in
  `08-client-list-and-crm/schema.md`, add a `paid_through` date field after `setup_paid` and
  update the three stages that read it" is cheap and right the first time
  ([agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)).
- **Plan before expensive edits** (Shift+Tab twice → plan mode). Catching a wrong approach in a
  plan costs a few hundred tokens; catching it after a multi-file edit costs thousands.
- **One task per session; `/clear` between them.** Don't let a finished statement-build session
  carry its context into an unrelated CFO edit.
- **State the done-condition.** "…and `python3 tools/check-docs.py` exits 0" lets Claude
  self-verify instead of you round-tripping.

---

## On the prompt that triggered this review

The triggering prompt was, paraphrased: *"Locate inefficiencies in our process… reduce token
use… better prompting… leverage other AI… hybrid local LLM + Claude… ANYTHING that could help…
search the web… keep up to date… check the news… and critique this prompt too."*

**What it did well:** it set a clear goal (reduce token cost), named concrete avenues (prompting,
hybrid local, web research), and asked for a self-critique — that openness is genuinely useful for
an exploratory audit and is why this review could range widely.

**Where it spent tokens it didn't need to:**

1. **Unbounded scope.** "ANYTHING that could help" + "search the web" + "check the news" invites a
   broad, expensive sweep. For a *recurring* routine that's costly every run. Better: name the 2–3
   levers you most want checked, and let the routine go deep there.
2. **No success criterion or budget.** Without "find the top 3 by ROI" or "keep it under N
   sources," the model over-collects. Adding a target focuses the spend.
3. **"Keep up to date day by day" implies high frequency.** Best practices here move in weeks, not
   days. A daily run mostly re-discovers the same advice at full cost. **Monthly** is the right
   cadence for a best-practices scan; keep a cheap daily/weekly check only for things that truly
   change fast (your own token spend, a model-pricing change).

**A tighter template for the recurring version:**

> "Monthly process-efficiency check. Re-read `docs/ai-cto/process-efficiency.md`. In ≤5 web
> searches, find anything *new since last run* on Claude Code cost/token reduction, prompt
> caching, or local/Claude hybrid routing. Output only: (a) what changed, (b) the single
> highest-ROI action for us this month, (c) anything in our doc now outdated. Skip the rest. Use
> Sonnet."

That version is bounded (≤5 searches), incremental (only what's new), has a clear output shape,
self-references this doc so it doesn't re-derive context, and names the cheaper model — i.e. it
practices what it audits.

---

## Keeping current (without paying full price every day)

- Run this audit **monthly** on Sonnet, incrementally (template above), not daily.
- Watch the primary sources, which move fastest:
  [Claude Code release notes](https://releasebot.io/updates/anthropic/claude-code),
  [cost docs](https://code.claude.com/docs/en/costs),
  [prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
- Track **our own** numbers, not just the blogs: `/context` per session and the LiteLLM router's
  cost log tell you where tokens actually go here — more reliable than generic "cut 90%" posts.

### Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude Code Token Optimization (2026) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [How to Reduce Claude Code Token Usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [5 Claude Code Skills That Cut Token Costs ~70% — MindStudio](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked)
- [Claude Code Pricing & Usage Optimization — claudefa.st](https://claudefa.st/blog/guide/development/usage-optimization)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching cost optimization 2026 — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [The 5-Minute TTL Change — dev.to](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflow Cost Optimization — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Use Claude Code with OpenRouter & Ollama — TECHSY](https://techsy.io/en/blog/claude-code-use-different-models)
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Claude Code Updates June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
