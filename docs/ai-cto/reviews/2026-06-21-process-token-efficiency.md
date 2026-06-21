# NARF — process & token-efficiency review — 2026-06-21

**Question asked:** Where are the inefficiencies in how we (the founder) work with the AI?
Can we cut token use, prompt better, lean on cheaper/local models, and stay current with
fast-moving best practice?

**Scope:** This is a *process* review, not a code review. It measures what every Claude
session pays before any work begins, ranks the fixes by return, and folds in current
(June 2026) best practice from Anthropic's docs and the field. Numbers below are measured
from the live repos (≈4 chars/token).

---

## TL;DR — the five things worth doing

1. **Stop reading 10 state files on every session start.** The DESIGN repo's NARF+ZORT
   instructions pull in **~17,000 tokens of mandatory reads** *on top of* the CLAUDE.md
   files — and you pay a slice of that on **every turn**, all session. Switch from
   "read everything up front" to "read on demand." Biggest single win.
2. **Lean on prompt caching — and stop breaking it.** Cached input costs **10% of normal**
   (a 90% discount). We get this for free *if* the prefix stays stable. Our habit of
   **editing portfolio.md / metrics.md mid-session** and **switching models** is exactly
   what invalidates the cache. Discipline here is nearly free money.
3. **De-duplicate the House-style block.** The identical 304-token typography rule is
   pasted into **all 7 CLAUDE.md files** = **2,126 tokens** re-loaded across a portfolio
   session, and it never changes.
4. **Route by task class to cheaper/local models.** You already built the ladder
   (LiteLLM on :4040, the deepseek-r1 reasoning ladder, Odin/LangGraph). Use it: chores →
   local/Haiku, judgment → Opus/Sonnet. Don't run Opus 4.8 for link-checking.
5. **Mind the June 15, 2026 pricing split** — autonomous usage (Agent SDK, `claude -p`,
   GitHub Actions, **scheduled routines like this one**) now draws from a *separate
   monthly Agent SDK credit*, not your interactive limits. Our automation strategy should
   be planned around that bucket explicitly.

---

## 1. The measured cost of a session before any work happens

| What loads | Tokens | When |
| ---------- | -----: | ---- |
| All 7 CLAUDE.md files (portfolio-wide session) | 14,611 | every session |
| DESIGN: NARF mandatory reads (portfolio/roadmap/tech-debt/decisions) | 5,546 | every DESIGN session |
| DESIGN: ZORT mandatory reads (portfolio/decisions/metrics/runway/budget + MARKETING context) | 11,471 | every DESIGN session |
| **DESIGN session bootstrap total** | **~31,628** | **before the first instruction** |

Single largest offenders:
- `docs/ai-cfo/metrics.md` — **5,642 tokens**, the biggest mandatory file, loaded every
  DESIGN session even when the task has nothing to do with metrics.
- The House-style block — **304 tokens × 7 copies = 2,126 tokens** of pure duplication.
- A cross-repo read baked into the instructions: ZORT is told to read
  `MARKETING/docs/ai-cfo/context.md` (**1,112 tokens**) from inside a DESIGN session.

**Why this is worse than it looks:** with caching, you pay full price for the bootstrap
*once*, then ~10% of it **on every subsequent turn** as a cache read. A ~31k-token
bootstrap is roughly **$0.47 to load** (Opus input ≈ $15/Mtok) and then **~$0.05 per turn**
thereafter. A 100-turn day ≈ **$5 just re-feeding the bootstrap** — multiplied across daily
NARF/ZORT runs. Halving the bootstrap is real, recurring money.

## 2. Fix the bootstrap: read on demand, not on start

The CLAUDE.md "at session start, read files 1–6" pattern is the anti-pattern. Current
Anthropic guidance is explicit: **CLAUDE.md should be a lookup table, not a brain dump**,
and **Explore/Plan subagents deliberately skip CLAUDE.md** to stay cheap. Concrete moves:

- **Demote the mandatory-read lists to a pointer.** Replace "read portfolio, roadmap,
  tech-debt, decisions, metrics, runway, budget, context at start" with: *"The CTO/CFO
  state lives in `docs/ai-cto/` and `docs/ai-cfo/`. Read the specific file the task needs."*
  Claude already reads files when relevant — the blanket up-front load is the waste.
- **Split state into "hot" vs "archive."** Keep a tiny (≤400-token) `state.md` per persona
  with just the live priorities + open decisions; leave the long ledgers
  (`decisions.md`, `metrics.md`) as on-demand references. Today `metrics.md` alone is
  bigger than the entire DESIGN CLAUDE.md.
- **Don't bake cross-repo reads into instructions.** Embed a 3-line MARKETING-context
  *summary* in DESIGN's CLAUDE.md instead of pulling the whole 1,112-token file.
- **Estimated saving:** ~6,000–10,000 tokens off every DESIGN bootstrap, recurring per turn.

## 3. Prompt caching is the highest-leverage lever — protect the prefix

Caching gives a **90% discount** on the cached prefix (cache read = 10% of input price;
breaks even after a single read). It's automatic in Claude Code for the system prompt +
CLAUDE.md + tool schemas. Field reports show **74–84% cache hit rates** are achievable on
stable agent workloads. We are leaving this on the table because we *invalidate* the cache:

- **Editing CLAUDE.md or a read-in state file mid-session** rewrites the prefix → cache
  miss → you re-pay full price for everything after the edit point. Our NARF/ZORT loop
  *reads* state at start and *writes* it at end — if writes happen mid-session, that churns.
  **Rule: do state-file edits in a dedicated short session, or at the very end, in one
  batch.**
- **Switching models mid-session** is the most expensive change — caches are isolated per
  model, so Opus context can't be reused by Sonnet. **Pick the model for the task up front.**
- **Use `/compact` proactively** before context balloons; it produces a shorter, cacheable
  prefix and makes the next turns cheaper.
- **New tools to adopt:** `/context` (v1.0.86+) to *see* what's eating the window;
  `/cd` to move working dir **without rebuilding the cache**; `fallbackModel` (up to 3) so a
  blip doesn't force a costly model switch.
- **Note (Feb 5, 2026):** caches are now isolated per workspace on the Claude API /
  Claude-on-AWS / MS Foundry — relevant if you run automation across accounts.

## 4. De-duplicate and trim (easy wins)

| Win | Action | Saving |
| --- | ------ | -----: |
| House-style block ×7 | Keep the canonical copy in one place; in the other 6 CLAUDE.md files replace it with one line: *"House style: see DESIGN/CLAUDE.md → House style."* | ~1,800 tokens/portfolio session |
| `metrics.md` auto-load | Stop reading it at start; link it. Keep a 5-line KPI snapshot in `ai-cfo/state.md`. | ~5,000 tokens when metrics isn't the task |
| Consolidate NARF's 4 files | Merge portfolio+roadmap+tech-debt into one "state of the union"; keep decisions.md separate (it's an append-only ledger). | ~6,000 tokens |

(Note: a CLAUDE.md only auto-loads for the repo you're working in — so the ×7 House-style
cost lands in full only on **portfolio-wide / multi-repo sessions**, which NARF/ZORT runs
are. Single-repo sessions pay just that repo's copy.)

## 5. Hybrid local + cloud: you already own the rails — now route on them

You have the infrastructure most people are blogging about wanting: LiteLLM gateway on
:4040, the deepseek-r1 reasoning ladder (`local-reason` 1.5b on the t630, `cloud-gpu-reason`
full-R1 on a rented GPU via Tailscale, `cloud-overflow` fallback), Open WebUI, and the
Odin/LangGraph supervisor. The field consensus: **task mix is ~60–70% simple, ~20–30%
moderate, ~10% needs a frontier model**, and routing the cheap majority off Claude cuts
LLM spend **60–80%** with little quality loss. Apply it:

- **Local / Haiku (cheap tier):** classify and extract from logs, format/lint docs,
  first-draft "Handled For You" entries, summarize a stats JSON, the doc-link check
  (`tools/check-docs.py` is deterministic — it shouldn't touch an LLM at all), routine
  roster edits, commit-message drafts.
- **Claude Opus/Sonnet (judgment tier):** architecture & ADR decisions, the
  honesty-of-the-kept-document review, cross-repo reasoning, code review, anything
  customer-facing where the voice rule matters.
- **Reality check on the box:** the t630 is a weak CPU host (1.5b model). It is fine for the
  cheap NL chores above, **not** for coding — local-model-vs-Claude coding benchmarks in
  2026 still favor Claude decisively. Keep code on Claude; push the chores local.
- **Wiring:** Claude Code can point at the LiteLLM gateway via `ANTHROPIC_BASE_URL`, and
  `fallbackModel` can name a Haiku/local fallback so cheap turns don't burn Opus. Batch API
  is **50% cheaper** for any non-interactive bulk job (e.g. regenerating all statements).

## 6. Prompting & process habits

- **One objective per session.** Open-ended "do anything that helps" prompts make the agent
  over-explore (read more, branch more, spend more). Scope each run to a single deliverable;
  start a fresh session per task so the cache prefix and context stay clean.
- **Turn recurring asks into skills / slash-commands**, not re-typed paragraphs. A
  `/narf-review` or `/zort-close` skill (on-demand context) beats fat always-on CLAUDE.md
  instructions — skills load only when invoked.
- **Use subagents for verbose, throwaway work** (searches, audits) so the noise never enters
  the main context — but *not* for trivial one-liners, where startup overhead exceeds the
  saving.
- **Prefer the dedicated tools** (Grep/Glob/Read) over shelling out `cat`/`grep`; they're
  cheaper and cleaner in context.
- **Set output terseness** in CLAUDE.md for heavy workflows ("answer in <N words unless asked
  to expand") — output tokens are billed at the higher rate.

## 7. Timely / news (June 2026 — verify before relying)

- **Autonomous-usage pricing split (June 15, 2026):** interactive Claude Code keeps using
  session/weekly limits; **non-interactive usage — Agent SDK, `claude -p` headless,
  GitHub Actions, scheduled routines — draws from a separate monthly Agent SDK credit.**
  This very review ran as a scheduled routine, so our automation roadmap (the stage-11
  glue, nightly stats, NARF/ZORT routines) should be budgeted against *that* bucket.
- **Subagents can now spawn subagents** (background chains capped at 5 deep) — useful for the
  cross-repo reviews, with the cost caveat above.
- **`--safe-mode`** disables all customizations for troubleshooting a misbehaving config.

## 8. Was the prompt that triggered this review itself efficient?

Honestly, no — and it's a useful example. The request was broad and unbounded ("ANYTHING
that could help… search the web… check the news… anything you could possibly think of").
For a once-off "scan everything" routine that's acceptable, but as a habit it's the
expensive pattern from §6: it licenses the agent to fan out maximally. Tighter versions of
the same ask:

- *"List the top 5 token sinks in our CLAUDE.md/session-start setup with measured numbers,
  and the single highest-ROI fix for each."* (bounded, countable)
- Or split it: one run for *measure our setup*, a separate run for *web best-practices*.
- For the standing version, make it a **scheduled skill** with a fixed output template so
  each run reuses the same cached instructions instead of re-describing the task.

The good parts of the prompt: it named concrete levers (local LLM, hybrid, caching) which
focused the search, and it asked for current sources — correct instinct given how fast this
moves.

---

## Prioritized action checklist

| # | Action | Effort | Recurring saving |
| - | ------ | ------ | ---------------- |
| 1 | Demote NARF/ZORT "read at start" lists to "read on demand"; add tiny `state.md` per persona | M | ~6–10k tok / DESIGN session |
| 2 | Stop auto-loading `metrics.md`; keep a 5-line KPI snapshot, link the full ledger | S | ~5k tok when not the task |
| 3 | De-dupe House-style: canonical copy + one-line pointer in the other 6 repos | S | ~1.8k tok / portfolio session |
| 4 | Cache discipline: edit state files only at session end (batched); fix model per task | S | up to 90% on the prefix per turn |
| 5 | Route chores to local/Haiku via the LiteLLM ladder; keep code + judgment on Claude | M | 60–80% of cheap-task spend |
| 6 | Make `tools/check-docs.py` (and similar deterministic checks) never call an LLM | S | full cost of those runs |
| 7 | Convert recurring NARF/ZORT runs into invokable skills with fixed output templates | M | smaller prefix + cache reuse |
| 8 | Budget automation against the new monthly Agent SDK credit (post-June 15) | — | avoids limit surprises |

## Sources (June 2026)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Claude Code Token-Saving Guide (models, MCP, CLAUDE.md, skills & cache) — knightli.com](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [How to Reduce Claude Code Token Usage: 8 Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Local LLM vs Claude for Coding: GPU Benchmark (2026) — kunalganglani.com](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [LiteLLM (BerriAI) — GitHub](https://github.com/BerriAI/litellm)
- [Anthropic API Pricing 2026: Models, Caching, Batch & Optimization — Finout](https://www.finout.io/blog/anthropic-api-pricing)
