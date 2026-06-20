# Process & Token-Efficiency Review — User ⇄ AI workflow

**Date:** 2026-06-20 · **Author:** NARF (AI CTO routine) · **Scope:** how we run Claude
across the seven A777ance repos — token cost, prompting, and where a local model should
carry the load. Sources are linked at the bottom; pricing/feature facts are from the
in-harness Anthropic `claude-api` reference (cached 2026-06-04) and current web sources.

> TL;DR — The single biggest, cheapest win is **~20K tokens of mandatory boilerplate read
> at the start of every DESIGN session** (CLAUDE.md + the NARF/ZORT "read these 6–10 files"
> ritual). Trim and lazy-load it. Then: **tier the model** (most routine work is Haiku- or
> local-grade, not Opus), **exploit prompt caching for back-to-back routines**, and **push
> triage/first-draft work onto the t630 LiteLLM ladder we already run.** Realistic blended
> saving: **50–70%** on routine spend with no loss of quality on the work that matters.

---

## 1. What we actually do today (the process)

- Claude Code runs **interactively and as scheduled routines** across 7 repos, each on its
  own feature branch, with the GitHub MCP server attached.
- Every repo ships a `CLAUDE.md` that is auto-loaded into **every request** in that repo.
- The DESIGN repo additionally instructs every session to **read NARF state** (portfolio,
  roadmap, tech-debt, decisions) **and ZORT state** (portfolio, decisions, metrics, runway,
  budget, + MARKETING context) at session start.
- We default to **Opus 4.8** (the most capable, most expensive tier) for everything.
- We already run a **hybrid LLM stack** on the t630 — LiteLLM router (`:4040`) with a
  reasoning ladder (`local-reason` = deepseek-r1:1.5b on the t630 CPU; `cloud-gpu-reason` =
  full R1 on a rented GPU; `cloud-overflow`) plus Open WebUI — but it's wired for *chat*,
  not for offloading agent/routine work.

## 2. The measured inefficiency: fixed boilerplate per session

Real token counts from the repo today (≈ chars/4):

| Loaded every DESIGN session | ~tokens |
| --- | ---: |
| `CLAUDE.md` (auto-injected every request) | 4,500 |
| NARF: portfolio + roadmap + tech-debt + decisions | 5,540 |
| ZORT: portfolio + decisions + **metrics (5,100 alone)** + runway + budget | 9,820 |
| **Fixed read before any real work** | **≈ 20,000** |

(localDNS `CLAUDE.md` is even bigger at ~5,100 tokens.) That ~20K is paid **on top of** the
system prompt, tool schemas, and the actual task — and for a *scheduled* routine the 5-minute
prompt cache is almost always cold, so it's paid at **full input price every run**
(~$0.10/session on Opus 4.8 just to "wake up and read the manuals"; ~10× that across a busy
day of routines × repos). Most of those 10 files are irrelevant to any given task.

## 3. Recommendations, in priority order

### A. Quick wins (do this week)

1. **Lazy-load NARF/ZORT state.** Replace "read all 6–10 files at session start" with "read
   the 1-page `portfolio.md` index; open roadmap/decisions/metrics **only if the task touches
   them**." `metrics.md` alone is 5,100 tokens and is rarely needed to, say, fix a broken
   link. Estimated cut: **10–14K tokens off the typical session.**
2. **Slim the `CLAUDE.md` files.** They carry full funnel diagrams, ASCII art, and long
   tables that belong in `README.md`. Keep `CLAUDE.md` to the briefing + links; everything
   loaded every request should earn its place. Target ~1,500–2,000 tokens each (from
   4,500–5,100). This is pure margin — `CLAUDE.md` is in the cached prefix, so trimming it
   helps *both* cold-cache cost and every cache-read.
3. **Tier the model.** Stop defaulting routines to Opus 4.8 ($5/$25 per 1M). Use **Haiku 4.5
   ($1/$5 — 5× cheaper in, 5× out)** for doc-integrity (`check-docs.py` gating), link checks,
   log/changelog appends, reformatting, and reverse-chronological housekeeping. Keep Opus for
   genuine reasoning/architecture. Set per-routine model, or per-subagent overrides; use the
   Haiku-backed Explore subagent for searches. *Fable 5 finishes some agentic tasks in fewer
   turns, so its 2× sticker price can net out close to Opus on the right hard task — but it's
   not the routine default.*
4. **Let routines stay quiet.** A routine that finds nothing should send **no notification**
   and do **no write** — attention and tokens both cost. (This review only exists because the
   run found something.)

### B. Prompt caching for routines (structural, high leverage)

- Caching is a **prefix match**: cache reads cost **~0.1×** input, writes cost **1.25×** (5-min
  TTL) or **2×** (1-h TTL). Break-even is 2 requests (5-min) / ~3 (1-h).
- Our routines run minutes-to-hours apart, so the **default 5-min cache is always cold** — we
  pay full price every run and never read the cache. Two fixes:
  - **Batch the 7-repo housekeeping into one back-to-back session** instead of 7 cold starts,
    so the second…nth repo reads the shared cached prefix.
  - For bursts, set **`ttl: "1h"`** on the stable prefix (CLAUDE.md + state) so a follow-up
    run within the hour reads at 0.1×.
- **Keep the prefix byte-stable**: no `datetime.now()`, run-IDs, or per-run strings in
  `CLAUDE.md` or the system prompt, and don't change the MCP tool set mid-stream — any of these
  silently invalidates the whole cache. Verify with `usage.cache_read_input_tokens` (zero across
  identical-prefix runs = a silent invalidator).

### C. Use the Batch API for bulk, non-interactive jobs

- **50% off all tokens**, results within ~1h. This is the right home for **monthly statement
  generation** (the "penny a home" job), bulk content drafting, and any fan-out over the
  master list that doesn't need a human in the loop. Combine with a cached shared system
  prefix for compounding savings.

### D. Trim the tool surface (per-request cost)

- Every attached MCP tool's schema is sent **on every request**. The GitHub MCP server alone
  exposes ~50+ tools. Attach the GitHub MCP only to sessions that touch GitHub, and prefer
  **deferred tool loading / ToolSearch** (load a tool's schema only when needed) so idle tool
  definitions don't ride along in every prompt.

### E. Lean harder on the hybrid stack we already own

We're paying Anthropic for work the t630 could do for free. 2026 best practice is a **router
in front of every call** (LiteLLM — which we already run) that decides local-vs-cloud on:

- **Sensitivity** — anything with real customer data (the `customers` repo) stays local by
  default; never send PII to a cloud resolver of any kind.
- **Complexity** — route classification, triage, "is this lead hot?", first-draft "Handled
  For You" copy, log summarization, and link/format checks to **`local-reason`**; escalate
  only the hard reasoning to the Claude API.
- **Pattern**: local model drafts → Claude reviews/polishes the few that matter.

Published hybrid results land at **30–50% cost reduction** (conservative split) up to **60–80%**
(aggressive: simple tasks local, complex to Claude). We have the rails; we just need to point
routine triage at `:4040` instead of the API. Re-run this cost split every ~6 months — hardware
and API rate cards move fast.

### F. Other compounding levers (lower effort-to-payoff, still worth it)

- **Semantic caching** for repeated/near-duplicate queries (FAQ, repeated triage prompts):
  eliminates 15–30% of calls outright.
- **Prompt compression** (e.g. LLMLingua) for long RAG-style contexts — 5–20× on the retrieved
  context with minimal quality loss; relevant if/when we feed big docs to a model.
- **`/compact` + context editing** on long agent sessions instead of letting context balloon;
  clear stale tool results rather than carrying them.

## 4. House-style note (a real process cost, not just tokens)

The "**reverse-chronological / Z→A / reverse-the-blocks**" convention makes docs measurably
harder for both a human reader and the model to parse, and raises edit-error risk (it's easy
to append in the wrong place). It buys little and taxes every read and write. Worth revisiting
whether the cost is paying for itself — at minimum, don't extend it to machine-read state files
(`portfolio.md`, `metrics.md`), where ordering should serve the parser.

## 5. Critique of the routine prompt that generated this review

The standing prompt ("locate inefficiencies… token use… better prompting… leveraging other
AI… hybrid… **ANYTHING** that could help… search the web… check the news") is itself a mild
anti-pattern, and the user explicitly asked to be told so:

- **Unbounded scope** ("anything", "everything") makes the agent fan out expensively and
  optimizes for breadth over a decision. A scoped prompt is cheaper and more actionable.
- **No success criterion** — nothing tells the routine when it's *done* or what "good" output
  is, so it over-explores.
- **Re-runs from scratch** — as a recurring routine it re-derives the same landscape each time
  with no memory of prior findings.

Suggested rewrite (tighter, cheaper, repeatable):

> *"Weekly: check Anthropic release notes and our last review for anything that changes our
> token cost or model choice. If something changed, propose the one or two highest-ROI process
> changes with an estimated saving and which repos/routines they touch. If nothing material
> changed since the last review, send no notification. Keep total output under ~600 words."*

That version has a bound, a done-condition, a memory anchor (last review), and a silence rule —
all of which cut tokens and raise signal.

## 6. Time-sensitive news (2026-06)

- **June 15 billing change — *paused*.** Anthropic's planned move of Agent SDK / `claude -p` /
  Claude Code GitHub Actions / third-party-agent usage onto a separate full-rate monthly credit
  (no rollover) was announced, then **confirmed as not happening** for now. **Action: none, but
  watch** — if revived, our scheduled routines and GitHub-Actions usage would meter at full API
  rates outside the subscription, which makes recommendations A–E above materially more valuable.
- Reference points: Anthropic's own March-2026 data has the median Claude Code dev at **~$6/day**,
  90% under $12/day — a useful yardstick for whether our routine spend is in band.
- Current rates (per 1M in/out): **Haiku 4.5 $1/$5 · Sonnet 4.6 $3/$15 · Opus 4.8 $5/$25 ·
  Fable 5 $10/$50**; cache reads ~0.1× input; Batch API −50%.

## 7. Suggested next actions (owner: NARF/ZORT)

1. Trim the four `CLAUDE.md` files and convert the NARF/ZORT session-start ritual to lazy-load
   (A1, A2). *Biggest, cheapest win.*
2. Add a model-tier policy to the routine definitions: Haiku/local for housekeeping, Opus for
   reasoning (A3).
3. Point routine triage/first-draft at the t630 `local-reason` model via LiteLLM (E).
4. Move statement generation + bulk drafting to the Batch API (C).
5. Adopt the scoped routine-prompt template (§5) and have each review read the previous one.

---

## Appendix — Claude Code knobs that implement the above

Concrete settings (verify against our installed `claude --version`; defaults move fast):

- **Cheaper subagents in one line:** `CLAUDE_CODE_SUBAGENT_MODEL=haiku` makes every subagent
  use Haiku by default — directly implements §3 without per-agent frontmatter. Per-agent
  override via `model: haiku` in the agent's frontmatter.
- **Default model per project:** `"model": "sonnet"` (or `haiku`) in `settings.json`, or
  `ANTHROPIC_MODEL` — stops routines defaulting to Opus (§A3). **Pick model/effort at session
  start, never mid-task** — a mid-session `/model` switch invalidates the whole cache.
- **MCP tool search / deferred loading is automatic on Claude Code ≥ 2.1.7** for Opus/Sonnet
  (not Haiku) — reportedly **85–95%** reduction in tool-definition tokens. Confirms §D: just
  stay current and don't attach servers you won't use. `/context` and `/mcp` show what's loaded.
- **1-hour cache for headless/API-key runs:** `ENABLE_PROMPT_CACHING_1H=1` keeps the prefix
  warm across scheduled runs within the hour (implements §B; on subscription plans Claude Code
  already requests 1h automatically).
- **Path-scoped rules instead of one giant CLAUDE.md:** move conditional guidance into
  `.claude/rules/*.md` with `paths:` frontmatter so it loads **only** when relevant files are
  open; move multi-step procedures into **skills** (loaded on demand). Implements §A2 — target
  each `CLAUDE.md` well under ~150 lines.
- **Effort control:** `/effort low` (or `CLAUDE_CODE_EFFORT_LEVEL`) for housekeeping; thinking
  tokens bill as output, so low effort on routine work is a direct saving.
- **Context hygiene:** `/compact` at task boundaries, `/usage` to read session cost, `/context`
  to find bloat. Note subagents always use the 5-min cache TTL even on subscription plans.

(Source: in-session `claude-code-guide` research against `code.claude.com/docs` — treat
version-specific env-var names as "verify before relying on.")

---

### Sources

- In-harness Anthropic `claude-api` reference (pricing, prompt caching economics, Batch API,
  model tiers, tool-search/deferred loading) — cached 2026-06-04.
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Local LLMs vs Cloud APIs: 2026 TCO — SitePoint](https://www.sitepoint.com/local-llms-vs-cloud-api-cost-analysis-2026/)
- [Hybrid Cloud-Local AI Workflow Cost Optimization — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LLM Cost Optimization: 8 Strategies (80%) — PremAI](https://blog.premai.io/llm-cost-optimization-8-strategies-that-cut-api-spend-by-80-2026-guide/)
- [LLM Token Optimization — Redis](https://redis.io/blog/llm-token-optimization-speed-up-apps/)
- [Token optimization 2026 (up to 80%) — Obvious Works](https://www.obviousworks.ch/en/token-optimization-saves-up-to-80-percent-llm-costs/)
- [Anthropic June 15 2026 billing change — Codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [Claude credit overhaul paused — Digital Applied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [What Claude Code actually costs in 2026 — UsageBox](https://usagebox.com/articles/claude-code-cost-2026-per-token-per-month-june-deadlines)
