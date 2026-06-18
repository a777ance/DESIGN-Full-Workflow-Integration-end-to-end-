# Process efficiency — the human ↔ AI loop

*Audit date: 2026-06-18. Owner: NARF (AI CTO). Companion to `tech-debt.md`.*

How we spend tokens, where we waste them, and how to run a cheaper, faster
A777ance AI workflow — Claude Code, the Claude API, and our own local stack
(LiteLLM router / Odin / the reasoning ladder in `localDNS` stage 10).

This is a living doc. Re-check the cited sources quarterly — the Claude Code
cost surface and model line-up change month to month (this audit caught the
Feb-2026 cache-TTL change and the June-2026 model-picker/Fable 5 updates).

---

## 0. TL;DR — the five highest-leverage moves

1. **Trim the always-on context.** Our six `CLAUDE.md` files total **1,040 lines
   / ~58 KB (~15K tokens)** and the longest is **326 lines** (`localDNS`) — every
   one bills on *every turn* of a session in that repo. Anthropic's ceiling is
   **200 lines**. Cutting to ~150 lines each saves ~50% of base context.
2. **Stop force-reading state files at session start.** Five of our `CLAUDE.md`s
   order "read these 4–6 files first" (NARF reads 4, ZORT reads 6). That's a
   guaranteed multi-thousand-token read before any work begins. Convert the
   bulk into **Skills that load on demand**, keep only a one-line pointer in
   `CLAUDE.md`.
3. **Route the cheap work to our own box.** We already own the hard part — the
   LiteLLM gateway + LangGraph Odin + the local reasoning ladder. Most CTO/CFO
   chores (classify, extract, summarize, lint a roster row) don't need Opus.
   Send them to `local-reason` / a Haiku tier and reserve Opus for architecture.
4. **Right-size the model and the thinking budget per task.** Default to Sonnet;
   reserve Opus; set `model: haiku` on mechanical subagents; drop `/effort` for
   non-reasoning tasks (extended thinking bills as output tokens).
5. **Lean on prompt caching deliberately.** Cache hits cost ~10% of input price.
   Work in focused bursts (5-min TTL), keep the cached prefix stable (no
   timestamps / per-run IDs up top), and the routine prompts below benefit most.

Stacking these (caching + routing + tight output + trimmed context) is the
documented path to **20–30% of unoptimized cost** on real workloads.

---

## 1. Findings specific to our setup

| # | Finding | Evidence | Fix |
| - | ------- | -------- | --- |
| F1 | `CLAUDE.md` files are oversized | 1,040 lines total; `localDNS` 326, this repo 295, `MARKETING` 214 — all > the 200-line ceiling | Split folder-specific guidance into **nested `CLAUDE.md`** (loads only when working in that folder) and move workflow detail to Skills |
| F2 | Mandatory session-start reads | NARF: portfolio+roadmap+tech-debt+decisions (4). ZORT: 6 files incl. a cross-repo one. Both repeated in every spoke's `CLAUDE.md` | Replace with a `cto-state` / `cfo-state` **Skill** invoked only when the session is actually doing CTO/CFO work |
| F3 | Same boilerplate duplicated 7× | The House-style block (~25 lines) and the 3-repo table are pasted into every `CLAUDE.md` | Keep the canonical copy once (here / a Skill); leave a one-line link in the others |
| F4 | Scheduled routines re-pay full context each run | This routine reloaded ~15K tokens of `CLAUDE.md` + the task before doing anything | Smaller `CLAUDE.md` (F1) + a tight, cache-friendly routine prompt (§5) compounds across every scheduled run |
| F5 | The local stack is underused for ops | Odin/LiteLLM/ladder exist but our day-to-day AI work runs entirely on the paid API | Wire a routing rule (§4): cheap/bulk → local or Haiku, frontier → Claude |

---

## 2. Claude Code token tactics (the interactive loop)

- **`/clear` between unrelated tasks; `/compact` to continue one.** Stale context
  bills on every subsequent message. `/rename` before clearing, `/resume` to return.
- **Watch the meter.** `/usage` (now attributes spend to skills, subagents,
  plugins, MCP servers) and `/context` show what's eating space. Put context
  usage in the status line.
- **Prefer CLI over MCP servers** where a CLI exists (more context-efficient — no
  per-tool listing). MCP tool defs are deferred by default now; `/mcp` to disable
  unused servers.
- **Offload to hooks.** A `PreToolUse` hook that greps a log for `ERROR` before
  Claude sees it turns a 10K-token file into a few hundred. Same idea for
  `check-docs.py` output and test runs.
- **Delegate verbose ops to subagents** — heavy reads/log processing stay in the
  subagent's context; only the summary returns. Caveat: subagents add startup
  overhead, so don't use them for trivial one-liners.
- **Plan mode (Shift+Tab) before big changes; `/rewind` to recover** — prevents
  paying twice when the first direction was wrong.
- **Specific prompts.** "Add validation to the login fn in auth.ts" reads a
  couple files; "improve the codebase" triggers a broad, expensive scan.

## 3. Prompt caching (for any programmatic Claude API use — bridges, the router)

- Cache hit ≈ **10% of input price**; pays for itself after one read (5-min TTL)
  or two reads (1-hour TTL). 60–90% off the input bill for long stable prefixes.
- **Feb-2026 change to know:** default TTL dropped 60→5 min and caching is now
  **workspace-isolated**, not org-wide — quietly raised many bills 30–60%.
  Use focused bursts or pay for the 1-hour TTL where it earns out.
- **Cache-killers to avoid in the prefix:** embedded timestamps, per-run IDs,
  per-user/per-household names, sloppy whitespace. Move volatile bits into the
  user message; keep the system/prefix byte-identical.
- **Batch API = 50% off** for non-interactive jobs (statement runs, bulk
  classification) that tolerate latency.

## 4. Hybrid: our box + Claude (we already own the hard part)

The market pattern is LiteLLM gateway → Ollama/local tier → Claude tier, with a
router that picks by task complexity / data sensitivity. **We've already built
this** (`localDNS/10-ai-orchestration`: LiteLLM on 4040, Odin/LangGraph, and the
`local-reason` / `cloud-gpu-reason` / `cloud-overflow` ladder). The gap is using
it for our own ops.

- **Task split that works in practice:** ~60–70% of requests are simple
  (classify, extract, format, lint) → local/Haiku; ~20–30% moderate → Sonnet;
  ~10% true frontier reasoning → Opus. Documented hybrid savings: **60–83%**.
- **A777ance candidates for the local/cheap tier:** roster field validation,
  `check-docs.py` triage, "does this statement only cite measured figures"
  pre-checks, draft commit messages, first-pass summaries of long logs.
- **Keep on Claude:** architecture/ADR decisions, anything customer-facing on a
  kept document, security-sensitive review.
- **Routing options if we want it smarter than the current ladder:** RouteLLM
  (LMSYS, ~85% cost cut at 95% quality on MT-Bench) or vLLM Semantic Router
  (Red Hat, ModernBERT classifier) — but our existing LiteLLM model-list +
  Odin rules are probably enough; add a complexity gate before reaching for a
  new dependency. **Privacy invariant:** local tier must honor the same rule as
  our DNS split — sensitive/customer data never leaves the box to a cloud model.

## 5. The prompt that launched this audit — critique

The meta-prompt was effective in *intent* (open-ended, "find anything") but
inefficient in *form*, and worth fixing because **scheduled routines pay for
their prompt on every run**:

- **Too broad → expensive scanning.** "ANYTHING that could help" invites a wide,
  unfocused sweep. Name 2–3 target areas ("context size, model routing, caching")
  to cut exploration tokens.
- **No output contract.** It didn't say *where* the answer should land or how
  long. For a routine, specify: "write findings to `docs/ai-cto/process-efficiency.md`,
  ≤2 pages, notify with the top 3." Without that the result risks living only in
  a transcript nobody reads.
- **Volatile phrasing fights caching.** "Check the news… day by day" is good for
  freshness but, if reused verbatim each run with a date baked in, breaks the
  prefix cache. Keep the standing instruction stable; pass the date as a variable.
- **Redundant emphasis costs tokens.** ALL-CAPS, "Thanks!", and repeated "anything"
  add tokens without adding direction.

**Tighter rewrite for the recurring version:**

> *Audit our AI process for token waste. Focus: (1) always-on context size,
> (2) local-vs-Claude routing, (3) prompt caching. Check current best practices
> on the web (cite sources w/ dates). Append findings newest-first to
> `docs/ai-cto/process-efficiency.md`; notify with the top 3 actions. Skip the
> notification if nothing material changed since the last run.*

---

## 6. Recommended actions (do in this order)

1. **Trim every `CLAUDE.md` to ≤ ~150 lines**; push folder detail into nested
   `CLAUDE.md`, workflow detail into Skills. (F1, F3)
2. **Convert NARF/ZORT session-start reads into on-demand Skills.** (F2)
3. **Add a `/effort` + model discipline note** to the workflow: Sonnet default,
   Opus for architecture, Haiku subagents for mechanical work. (§2)
4. **Add a `PreToolUse` hook** that filters `check-docs.py` / test output to
   failures only. (§2)
5. **Wire one routing rule** in LiteLLM/Odin so bulk classify/extract/lint hits
   the local tier first. (§4)
6. **Adopt the tightened routine prompt** in §5 for any scheduled AI job.
7. **Re-run this audit quarterly**; the cost surface moves monthly.

---

## 7. Sources (verify dates on re-audit)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code — What's new](https://code.claude.com/docs/en/whats-new) · [Releasebot: Claude Code, June 2026](https://releasebot.io/updates/anthropic/claude-code)
- [Claude prompt caching, the 5-min TTL change (DEV, 2026)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Claude cost optimization: Batch API + caching (PE Collective, 2026)](https://pecollective.com/tools/claude-pricing-guide/)
- [Run local AI models with Claude Code to cut costs (MindStudio, 2026)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid cloud-local LLM architecture guide (SitePoint, 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM model routing: cut costs 85% (Burnwise, 2026)](https://www.burnwise.io/blog/llm-model-routing-guide)
- [vLLM Semantic Router (Red Hat, 2026)](https://www.redhat.com/en/blog/bringing-intelligent-efficient-routing-open-source-ai-vllm-semantic-router)
- [23 tips for Claude Code token saving (Analytics Vidhya, 2026)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
