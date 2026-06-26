# Process efficiency review — user ↔ AI token economics

*Prepared 2026-06-26 by NARF (AI CTO), in response to the founder's "find inefficiencies in
our PROCESS" brief. Grounded in measurements of this repo set + current (June 2026) Anthropic
docs and third-party benchmarks. Re-check the dated claims quarterly — this space moves weekly.*

---

## TL;DR — the one number that matters

**A normal session pays ~33,000 tokens of mandatory reading before it does anything useful.**
That is the single biggest lever. It is paid on every cold start, it is mostly *not* solving
the task, and a large share of it is avoidable. Fix the session-start bloat first; everything
else below is secondary.

| # | Lever | Effort | Est. saving | Owner |
| - | ----- | ------ | ----------- | ----- |
| 1 | Trim session-start mandatory reads (CLAUDE.md + AI-CTO/CFO docs) | M | **~50–70% of cold-start tokens** | NARF |
| 2 | Route cheap work off Opus → Haiku/local (you already own the router) | M | **5–25× on routed tasks** | NARF |
| 3 | Lean on prompt caching deliberately (stable prefixes, batch cold runs) | S | up to **90%** on repeat input | NARF/ZORT |
| 4 | Use Batch API for non-interactive scheduled jobs | S | **50%** flat | ZORT |
| 5 | Calmer, terser prompt style (drop CAPS/NEVER/IMPORTANT) | S | quality + a little output | all |
| 6 | Subagents for verbose research — but watch the 4–15× multiplier | S | context hygiene | all |
| 7 | Context editing + memory tool for long agent runs | M | up to **84%** on long runs | NARF |

---

## 1. Session-start bloat is the headline cost (Lever 1)

Measured today, by file:

**CLAUDE.md files loaded in a multi-repo session** (chars ÷ 4 ≈ tokens):

| File | Bytes | ≈ tokens |
| ---- | ----: | -------: |
| localDNS/CLAUDE.md | 20,472 | ~5,100 |
| DESIGN/CLAUDE.md | 17,987 | ~4,500 |
| MARKETING/CLAUDE.md | 10,660 | ~2,665 |
| customers/CLAUDE.md | 4,135 | ~1,030 |
| claude-code-homelab/CLAUDE.md | 2,896 | ~725 |
| Azure-lab/CLAUDE.md | 2,294 | ~575 |
| **Subtotal** | | **~14,600** |

**AI-CTO / AI-CFO docs the CLAUDE.md files *order* every session to read:**

| Hat | Files | ≈ tokens |
| --- | ----- | -------: |
| NARF (CTO) | portfolio + roadmap + tech-debt + decisions | ~5,500 |
| ZORT (CFO) | portfolio + decisions + **metrics (24.7 KB!)** + runway + budget + MARKETING context | ~11,000+ |

A dual-hat session that touches a couple of repos therefore pays **~31–33K tokens of reading
before the first real action** — and `metrics.md` alone is ~6,200 of those tokens.

**Why this is the right thing to fix:** per the Anthropic context-engineering guidance, the
memory file "loads before Claude reads your code, before it reads your task, before anything…
a constant baseline you carry at all times." It is paid on every cold start, and output
tokens (the expensive side) get squeezed into whatever's left.

**Concrete fixes**

- **Split each CLAUDE.md into "always" vs "on-demand."** Keep ~30–60 lines that every session
  truly needs (the rules, the one-line map, the verification command). Move the rest into
  linked files Claude reads *only when the task touches them*. The house-style block is
  duplicated verbatim across all 7 repos (~40 lines each) — factor it to one
  `docs/house-style.md` and link to it; don't reprint it in every memory file.
- **Make the NARF/ZORT session-start reads conditional, not mandatory.** "Read all 9 docs at
  start" should become "read `portfolio.md`; read the others *when the task needs them*."
  `metrics.md` (24.7 KB) should never be a cold-start read — it's a lookup, load on demand.
- **The house-style ordering rules cost tokens twice:** once to store, and again every time
  Claude has to reason about "reverse the blocks but keep the steps, newest-first within
  sections, Z→A lists." That's real working-memory overhead on every edit. Keep the font rule
  and reverse-chronological logs (cheap, high value); reconsider whether reversed walkthrough
  blocks + Z→A alphabetical lists earn their ongoing cost.
- **This very session loaded six CLAUDE.md files** because it spans repos. When a task is
  single-repo, run it from that repo so only its memory loads.

---

## 2. You already own a hybrid router — use it (Lever 2)

`localDNS` stage 10 already runs **LiteLLM + Open WebUI on the t630**, with a reasoning ladder
(`local-reason` deepseek-r1:1.5b on CPU, `cloud-gpu-reason` full R1 on a rented GPU,
`cloud-overflow` fallback). The hybrid infrastructure the industry is writing 2026 blog posts
about is *already deployed here.* It is just not in the loop for day-to-day A777ance work.

Current API ladder (per 1M tokens, June 2026): **Haiku 4.5 $1/$5 · Sonnet 4.6 $3/$15 ·
Opus 4.8 $5/$25 · Fable 5 $10/$50.** Opus output is **5× Haiku** and recursion-heavy agent
runs spend mostly output.

Route by difficulty, not by habit:

| Task class | Send to | Why |
| ---------- | ------- | --- |
| Link/anchor checks (`check-docs.py`), file moves, renames, lint | local (Qwen2.5-Coder / deepseek) or Haiku | deterministic, no reasoning |
| Metrics roll-ups, classification, extraction, summarizing a log | Haiku 4.5 / local | cheap, high-volume |
| Statement composition from a data file | Haiku/Sonnet + template | structured, ~penny/home already |
| Drafting copy, routine edits | Sonnet 4.6 | good enough, 1.7× cheaper than Opus |
| Architecture, ADRs, cross-repo reasoning, this review | Opus 4.8 | actually needs the frontier |

Industry data point: hybrid setups report **60–83% cost cuts** by keeping the 70–80% of
routine prompts off the frontier model. You don't need new hardware — the t630 router exists.

---

## 3. Prompt caching — make the baseline cheap when you can't make it small (Lever 3)

Cache reads cost **10% of input price**; a cache write is 1.25× (5-min TTL) or 2× (1-hr TTL).
So the big static prefix (system prompt + CLAUDE.md + the AI-CTO/CFO docs) is cheap to *re-read*
inside a warm window, but full price on every cold start.

- Keep the prefix **byte-stable and in a fixed order** so it caches — don't interleave volatile
  content (dates, metrics) into the cached region; put volatile content last.
- **Scheduled routines** (this run is one) typically fire >5 min apart, so the 5-min cache has
  expired and they pay full freight every time. For a routine that re-reads the same big
  context, the 1-hour cache TTL or **batching several checks into one warm session** recovers
  most of it.
- This interacts with Lever 1: a smaller baseline is cheaper *and* caches faster.

---

## 4. Batch API for everything non-interactive (Lever 4)

Anything that doesn't need an answer *this second* — monthly statement generation, metrics
aggregation, doc-integrity sweeps, the nightly `collect_stats.py`-adjacent work — can go through
the **Batch API at a flat 50% off both input and output**, stackable with caching. ZORT should
treat batch as the default for scheduled financial/reporting jobs.

---

## 5. Prompting style (Lever 5)

Current 2026 guidance for Claude 4.x, against what the repos do today:

- **Aggressive language hurts 4.x.** "CRITICAL!", "YOU MUST", "NEVER EVER", ALL-CAPS — these
  over-trigger and *worsen* results. The CLAUDE.md files lean on `IMPORTANT`, `NEVER`,
  `**Never**`, caps. Swap for calm, direct statements ("X overrides defaults" → "Follow X.").
- **XML tags structure better than Markdown** for instruction-following. Where a section is a
  hard contract (the rules block, the honesty rule), `<rules>…</rules>` beats a bulleted list.
- **Sweet spot 150–300 words per instruction; structure beats length.** Several of these
  memory files are essays where a contract would do.
- **Ask for terse output explicitly** when you want it — 4.x follows instructions literally, so
  "answer in ≤5 bullets, no preamble" reliably cuts output tokens (the expensive side).

---

## 6. Subagents & long-run tooling (Levers 6–7)

- **Subagents keep the main context clean** (verbose exploration stays in the child; only a
  summary returns) — but multi-agent runs cost **4–7× tokens, Agent Teams ~15×.** There are
  real 2026 horror stories ($8–15K single sessions; $47K over three days from unattended
  agents). Use them for genuine fan-out (this review used a few searches, not a fleet); never
  leave a multi-agent job running unattended without a token ceiling.
- **Context editing + the memory tool** (server-side compaction) auto-clear stale tool results
  near the limit — Anthropic's 100-turn eval showed **84% fewer tokens** and runs that
  otherwise fail on context exhaustion. Worth enabling for any long NARF/ZORT agent run.
- Operationally: glance at **`/context`** before a big task, **`/compact`** between phases,
  **`/clear`** between unrelated tasks. Reported 40–70% savings from discipline alone.

---

## 7. Feedback on the brief itself (you asked)

The prompt that triggered this review was effective at *intent* but inefficient at *execution*:

- **Strong:** clear goal (reduce token use), permission to use the web, "keep up to date."
- **Costly:** open-ended scope — "ANYTHING that could help," "Perhaps also…," "Anything you
  could possibly think of." That invites maximal fan-out (the expensive path) when a scoped
  ask would do. It also lacks a success definition and an output format, so the model has to
  guess how deep to go.
- **A tighter version:**
  > "Audit our token spend. Measure the session-start context cost across the repos, rank the
  > top 5 fixes by saving-vs-effort, and write the findings to `docs/ai-cto/…`. Use the web
  > for current pricing/best-practices. Keep it to one page. Flag if this prompt is wasteful."

  Same outcome, bounded depth, named deliverable, explicit length cap — fewer tokens, more
  predictable result.
- **Standing tip:** put recurring asks like this in a **slash command / skill** so the scope,
  output path, and length cap are fixed once instead of re-specified (and re-tokenised) each run.

---

## Recommended order of work

1. **Lever 1** — split CLAUDE.md (always vs on-demand), de-duplicate the house-style block,
   make the AI-CTO/CFO reads conditional, move `metrics.md` off cold start. Biggest, cheapest win.
2. **Lever 2** — wire the existing t630 LiteLLM router into routine A777ance tasks; reserve Opus
   for reasoning.
3. **Levers 3–4** — caching discipline + Batch API for scheduled jobs.
4. **Levers 5–7** — prompt-style pass on the memory files; adopt subagent/compaction hygiene.

## Sources (June 2026)

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic — Managing context (context editing + memory tool)](https://anthropic.com/news/context-management)
- [Claude Platform — Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Claude Platform — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Platform — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Platform — Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices) · [Manage costs](https://code.claude.com/docs/en/costs)
- [MindStudio — Run local AI with Claude Code (10× cost cut)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [SitePoint — Hybrid cloud/local LLM architecture (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [CloudZero — Claude Code agents: what parallel sessions cost](https://www.cloudzero.com/blog/claude-code-agents/)
- [claudefa.st — Context window / token optimization](https://claudefa.st/blog/guide/mechanics/context-management)
