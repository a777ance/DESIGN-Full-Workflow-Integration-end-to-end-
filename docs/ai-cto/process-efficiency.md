# Process efficiency: user ↔ AI token & workflow audit

*Analysis run 2026-06-28 (scheduled routine). Findings ordered most-impactful first.*
*This is a living doc — re-run the audit and update; AI tooling economics move week to week.*

---

## TL;DR — the three biggest wins

1. **Your CLAUDE.md files are a per-turn tax of ~10.7K tokens** in multi-repo sessions,
   paid on *every* message. Trim them and stop pasting the shared house-style block into
   all seven. (~Section 1)
2. **The NARF/ZORT session-start ritual reads ~10.8K words (~14K tokens) before any work
   begins**, every session. `metrics.md` (3.7K words) and the 28 append-only review logs
   are the worst offenders. Read a digest, not the archive. (~Section 2)
3. **You already own the hybrid rails (LiteLLM on the t630) — use them.** Route the
   60–70% of low-reasoning tasks to a local model; reserve Opus for hard reasoning. The
   literature consistently reports **60–80% cost cuts** from this split alone. (~Section 4)

Everything else (prompt caching, batch API, subagent discipline, routine cadence,
tightening this very prompt) is below.

---

## 1. The CLAUDE.md tax (highest-frequency cost)

Every connected repo's `CLAUDE.md` is injected into context **on every single turn**, not
once per session. Measured today:

| Repo | CLAUDE.md words | ~tokens |
| ---- | ---: | ---: |
| localDNS | 2,728 | ~3,630 |
| DESIGN-… | 2,608 | ~3,470 |
| MARKETING | 1,445 | ~1,920 |
| claude-code-homelab | 371 | ~490 |
| Azure-lab | 316 | ~420 |
| customers | 562 | ~750 |
| **Total (multi-repo turn)** | **~8,030** | **~10,700/turn** |

A 50-turn session pays this ~50 times. The guidance the field has converged on: **keep
CLAUDE.md under ~150 lines** — it is an *index*, not an encyclopedia.

**Concrete fixes:**

- **De-duplicate the house-style block.** The ~250-word "House style: ordering &
  typography" section is pasted verbatim into all 7 repos (~1,750 words of pure
  duplication, billed every turn in multi-repo work). Keep the canonical copy in one place
  (e.g. `DESIGN/docs/house-style.md`) and replace the others with a one-line link. CLAUDE.md
  is read by the model every turn; a link costs ~10 tokens, the pasted block costs ~330.
- **Move reference tables out of CLAUDE.md into README and link them.** `localDNS/CLAUDE.md`
  carries the full deploy-paths table *and* the multi-step nftables deploy checklist (Section
  F). Those are run-once procedures, not per-turn briefing — they belong in README. Same for
  the long "Known issues" tables: keep a 5-line pointer, move the detail.
- **Target:** get each CLAUDE.md to ≤150 lines / ≤1,200 words. Realistic saving: **~5–6K
  tokens per turn** in multi-repo sessions — a 50%+ cut to the standing tax.

## 2. The session-start ritual (highest fixed cost per session)

NARF (CTO) is told to read 4 files at session start; ZORT (CFO) reads 6. Measured:

| Persona | Mandated reads | words | ~tokens |
| ------- | -------------- | ---: | ---: |
| NARF | portfolio + roadmap + tech-debt + decisions | 3,300 | ~4,400 |
| ZORT | portfolio + decisions + metrics + runway + budget + MARKETING/context | 7,458 | ~9,900 |
| **Both** | 10 files | **10,758** | **~14,300/session** |

`docs/ai-cfo/metrics.md` alone is **3,681 words** — the single largest forced read, pulled
in whole even when a task touches none of it.

**Concrete fixes:**

- **Read a digest, not the archive.** Maintain one `docs/ai-cto/state.md` and one
  `docs/ai-cfo/state.md` — a ~300-word current-snapshot (open decisions, this-week
  priorities, phase gate, latest KPI line). The routine reads *that*; the full
  portfolio/metrics/decisions files are read **on demand**, only when the task needs them.
  This is the single highest-leverage change for a routine that fires often.
- **Stop mandating history at startup.** `docs/ai-cfo/reviews/` holds **28 files (~45K
  words)**. They are append-only and grow without bound. Roll them up: keep the last 1–2,
  summarize the rest into one quarterly digest, move raw files to `reviews/archive/`, and
  make sure no CLAUDE.md or ritual instruction pulls the whole folder.
- **Scope the ritual to the repo.** A routine working in `Azure-lab` (a 50-line stub) or
  `claude-code-homelab` (a docs guide) does not need the full CFO ritual. Gate the heavy
  ritual to the DESIGN/MARKETING/customers repos where money facts actually live.

## 3. Prompt caching — the biggest free lever for repeated runs

Scheduled routines re-send a near-identical system prompt + CLAUDE.md every time they fire.
That is exactly the shape prompt caching is built for.

- **Cached input reads cost ~10% of normal** (a 90% discount); cache *writes* cost 1.25×.
  Hit rates above ~60% on long-context workloads are the target.
- **Opus 4.8 lowered the minimum cacheable prompt to 1,024 tokens** (was 2,048 on 4.7), so
  even your smaller repos' prompts now cache with no change.
- **Placement is everything:** stable content first (instructions, tool schemas, the
  CLAUDE digest, durable examples), volatile content last (the task, today's data, the
  timestamp). A single changed character before a cache breakpoint invalidates the cache —
  so **never put a date/timestamp near the top** of a routine's prompt.
- Opus 4.8 also lets you inject `system` entries mid-`messages` array, so you can update
  instructions mid-task **without breaking the cache**.
- For Claude-Code-driven sessions caching is largely automatic within a session; the win to
  capture is on the **API-driven NARF/ZORT jobs** you control directly.

**Pair with the Batch API for non-urgent jobs:** the monthly statement build, the metrics
roll-up, and bulk roster operations are not latency-sensitive. The Batch API gives **50%
off input *and* output**, and **stacks with caching**. Monthly statement generation at "a
penny a home" gets cheaper still.

## 4. Hybrid local + Claude — you have the rails, now route on them

`localDNS` already runs **LiteLLM on the t630 (port 4040)**, Open WebUI, a reasoning ladder
(`local-reason` = deepseek-r1:1.5b on CPU; `cloud-gpu-reason` for heavy), and the Odin
LangGraph supervisor. The infrastructure for hybrid routing is *built*. The gap is
**routing policy**: most work still goes to Opus by default.

Industry split of a typical workload: **60–70% simple** (classification, extraction,
formatting), **20–30% moderate**, **~10% genuine frontier reasoning**. Routing the bottom
two-thirds local yields the widely-reported **60–80% cost reduction**.

**What to send local (via LiteLLM) vs. keep on Opus:**

| Send to local / cheap tier | Keep on Claude Opus |
| -------------------------- | ------------------- |
| Reformatting docs to house style (Z→A, newest-first) | Strategy, pricing, unit-economics reasoning |
| Drafting "Handled For You" log entries from a template | Architecture decisions / ADRs |
| Extracting/normalizing roster fields | Non-trivial code changes & reviews |
| Internal link/anchor checking (`check-docs.py` is already code, not a model) | Anything customer-facing & kept ("honesty rule") |
| First-pass classification / triage of issues | Final judgement on money/compliance facts |

- **Point cheap subtasks at your own endpoint.** Claude Code can run against a custom
  model base URL — wire a "cheap" profile at the LiteLLM `:4040` gateway for the
  formatting/extraction class of tasks, with a **Claude cloud fallback** configured (always
  configure the fallback — local models fail).
- **Use local for drafts, Claude for the kept document.** Generate with the local model,
  have Claude review/finalize anything that goes out for money. This matches your own
  "honesty of the kept document" rule.

## 5. Subagent / multi-agent discipline

Multi-agent fan-out is powerful but **expensive**: subagent-heavy workflows run ~**4–7×**
the tokens of a single thread, and a wide multi-agent system can hit **~15×**. The Odin
muster ("3 orders of 5 + Loki" = 16 agents) is only economic on **high-value, divisible**
work — not routine doc edits or single-file changes.

- **Use the built-in `Explore` subagent for read-heavy search.** It keeps the file-dump
  noise out of the main context and returns only the conclusion — that *saves* tokens.
  (This audit used exactly that pattern.)
- **Tier the model per agent, enforced in config.** Orchestrator on Opus; workers on
  Haiku or the local tier. Commit the model choice in subagent YAML so nothing silently
  defaults every worker to Opus.
- **Don't fan out for routine work.** One agent, one focused task is cheaper and usually
  better for anything that isn't genuinely parallel exploration.

## 6. Session & MCP hygiene (low effort, compounding)

- **One task per session; `/clear` between tasks.** Long sessions are geometric: a fresh
  session sends ~20K/turn, a 200-turn session re-sends ~200K/turn because the whole history
  rides along. `/clear` between unrelated tasks cuts per-message cost ~30–50%.
- **`/compact` and `/recap`** instead of letting a session sprawl — recap summarizes where
  you left off without replaying the transcript.
- **Keep MCP servers lean.** Each connected server loads its tool definitions into every
  turn; 5 servers can be ~90K tokens of pure overhead. The **Tool Search** mechanism (this
  session loads GitHub's ~60 tools on demand rather than up front) already mitigates this —
  keep relying on it, and don't connect servers a routine won't use.

## 7. Routine cadence (specific to this 7-repo setup)

Running a scheduled routine per repo, each on its own branch, multiplies the fixed
session-start cost by the number of repos. Reduce the multiplier:

- **Batch related repos into one routine** where the task spans them (most CTO/CFO work
  touches DESIGN + one spoke).
- **Skip or shrink the ritual for stub/guide repos** (Azure-lab, claude-code-homelab,
  chronikomicon) — they have no money facts to load.
- **Notify, don't narrate.** A routine's reply text is discarded (nobody watches the
  session); only the notification and committed files survive. Keep routine *output* terse
  and persist conclusions to a file — which is what this doc does.

---

## 8. On the prompt that triggered this audit

The triggering prompt was, paraphrased: *"Locate inefficiencies in our process between user
and AI. Reduce token use. Better prompting? Leverage other AI, hybrid local + Claude.
ANYTHING. Search the web, keep up to date, check the news. If THIS prompt is inefficient,
tell me."*

**What it does well:** clear goal, grants permission to use web search, names the levers it
cares about, and asks for self-critique — that last part is genuinely good practice.

**Where it's inefficient:**

- **Unbounded scope.** "ANYTHING that could help" with no success criterion or budget
  invites open-ended (token-expensive) work. A research prompt should cap itself.
- **Vague verbs.** "Check the news" / "keep up to date" don't say *which* sources, *how
  recent*, or *how many*. The agent has to guess, often over-searching.
- **No output contract.** It doesn't say *where* the answer should land (file? notification?
  length?). For a routine where the reply is discarded, that matters.

**A tighter rewrite:**

> *Audit our user↔AI process for token waste. Cover: (1) CLAUDE.md / session-start context
> size, (2) prompt caching + batch API, (3) hybrid local-vs-Claude routing on our existing
> LiteLLM box, (4) subagent economics. Do ≤6 web searches for 2026 best practices; cite
> sources. Output a prioritized, costed list to `docs/ai-cto/process-efficiency.md` and
> notify me with the top 3. Cap the run at ~15 minutes of work.*

That version fixes scope (named dimensions), bounds the search (≤6, with citation),
specifies the deliverable and its location, and sets a budget — so the agent stops when
it's answered the question instead of when it runs out of ideas.

---

## Estimated combined impact

| Lever | Effort | Token impact |
| ----- | ------ | ------------ |
| Trim + de-dupe CLAUDE.md | Low (one edit pass) | ~5–6K **per turn** in multi-repo work |
| Digest-not-archive at session start | Low–med | ~10K **per session** |
| Prompt caching on NARF/ZORT API jobs | Med (restructure prompts) | up to **90%** off the cached prefix |
| Batch API for monthly/bulk jobs | Low | **50%** off those jobs (stacks with caching) |
| Hybrid local routing (LiteLLM) | Med (routing policy) | **60–80%** of total spend, on the simple-task share |
| Subagent tiering + `/clear` hygiene | Low | 30–50% on long sessions; avoids 4–15× fan-out waste |

The field reports **40–85% total reductions** when these are stacked. The two lowest-effort,
highest-frequency wins here are **CLAUDE.md trimming** and **digest-based session start** —
do those first.

---

## Sources (2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [5 Claude Code Skills That Cut Token Costs Up to 70%](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [What's new in Claude Opus 4.8 — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8)
- [Anthropic Prompt Caching in 2026: Cost, TTL, Latency](https://aicheckerhub.com/anthropic-prompt-caching-2026-cost-latency-guide)
- [Anthropic API Pricing 2026: Models, Caching, Batch & Optimization](https://www.finout.io/blog/anthropic-api-pricing)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM Gateways & Model Routing: Cut AI Costs 2026](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [Claude Code Agents in 2026: What Parallel Sessions Actually Cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Claude Code Sub-Agents Explained: Context, Cost, Parallel Execution](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
