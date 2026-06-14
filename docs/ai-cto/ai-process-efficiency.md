# AI process efficiency — token & workflow audit

How we (the founder) and the AI (Claude Code / API) work together, and where that
process wastes tokens, money, or time. Reviewed against current best practice and the
June 2026 pricing landscape. **Newest review at the top** (house style).

This is a NARF (AI CTO) / ZORT (AI CFO) shared concern: NARF owns the workflow design,
ZORT owns the dollar impact. Findings here that need a decision graduate to an ADR
(architecture) or FIN (money) entry.

---

## Review log

### 2026-06-14 — first audit

**TL;DR:** The single biggest, free win is that our `CLAUDE.md` files are ~4× too large
and load on every session; the single biggest *unrealized* win is that we already built
an LLM router (LiteLLM + local Ollama on the t630) and aren't using it to keep cheap work
off the Claude API. Plus we're running automated routines on Opus, the priciest model.

#### A. What's costing us now (ranked by leverage)

1. **`CLAUDE.md` bloat — ~15K tokens loaded every single session.** The seven repo
   `CLAUDE.md` files total ~58 KB (localDNS 20 KB, DESIGN 18 KB, MARKETING 11 KB). The
   official guidance is **under 200 lines / an index under 50 lines** — ours are several
   times that. Everything in `CLAUDE.md` is in context *before the first word of the
   task*, even when irrelevant. In a multi-repo session like this audit, **all seven load
   at once.** Worse for caching: every time we edit a `CLAUDE.md` we bust the prompt cache
   for that repo (see #5).
   - **Fix:** Trim each `CLAUDE.md` to an index — what the repo is, the 5–8 rules that
     actually change behavior, and links. Move the reference tables (localDNS deploy-path
     table, full Known-issues tables, Verification command blocks; DESIGN stage map +
     verification walkthrough) into the docs they summarize or into **Skills** that load
     on demand. Target: each `CLAUDE.md` under ~120 lines.
   - **Est. impact:** ~60–70% off the per-session base context; compounds across every
     session and every subagent (subagents inherit `CLAUDE.md` too).

2. **We own a model router and route nothing to it.** `localDNS/10-ai-orchestration`
   runs LiteLLM (`:4040`) + Open WebUI + local Ollama (`local-reason` = deepseek-r1:1.5b
   on the t630) + an on-demand rented GPU (`cloud-gpu-reason`). Hybrid local/cloud routing
   is the biggest cost lever in 2026 — routing the ~70% of low-stakes work to a cheap/local
   model cuts spend 60–80% with little quality loss. We have the infra and don't point our
   bulk work at it.
   - **Candidates for local/cheap routing:** doc-link checks, draft summaries, classifying
     leads, first-pass copy drafts, commit-message drafting, log triage, "is this worth
     escalating" gating. Reserve Claude API for architecture, customer-facing copy, and
     anything touching the honesty rule.
   - **How:** `claude-code-router` (open-source proxy) lets Claude Code route per-request
     to Ollama/DeepSeek/Gemini with no workflow change (`ccr code` instead of `claude`).
     Or call LiteLLM directly from scripts for non-interactive jobs.
   - ⚠️ **Privacy gate:** this collides with **TD-14** — `local-reason` currently fails
     over to `cloud-overflow` (Claude cloud). Fix TD-14 (fail closed, local-only chain)
     *before* routing any `sensitive`-tagged customer data locally.

3. **Automated routines run on Opus 4.8 — 5× Sonnet, 25× Haiku.** Opus is $15/$75 per
   Mtok; Sonnet $3/$15; Haiku-class and Gemini-Flash-class are cents. A scheduled
   doc-audit / monitor routine (like the one that produced this) almost never needs Opus.
   - **Fix:** default scheduled/headless routines and verbose subagents to **Sonnet**, and
     **Haiku** for mechanical subagent work (`model: haiku` in subagent config). Reserve
     Opus for architecture and multi-step reasoning we start by hand. Start interactive
     sessions on Sonnet, escalate with `/model` only when needed.

4. **Verbose operations run in the main context instead of subagents.** Running tests,
   fetching docs, sweeping many files — the raw output lands in the main window and stays
   there for the rest of the session. Delegating to a subagent keeps the verbose output in
   the subagent and returns only a summary.
   - **Fix:** Use the Explore/general-purpose subagents for fan-out searches and log
     triage; add a `PreToolUse` hook to filter test/log output to just failures before
     Claude sees it (turns a 10K-line log into a few hundred tokens).

5. **Prompt-cache hygiene.** Anthropic dropped the cache TTL from 60 min to **5 min** in
   early 2026 — resuming a session after a short break, or editing `CLAUDE.md`/early
   context mid-session, re-pays full input price. Caching is the highest-leverage API
   optimization (60–90% off input cost) when context is kept *stable*.
   - **Fix:** keep `CLAUDE.md` stable (don't tweak it mid-task), batch related work into
     one continuous session, and don't interleave unrelated repos in one session if it can
     be avoided.

6. **Session hygiene we're probably skipping.** `/clear` between unrelated tasks (stale
   context is re-billed every message); `/compact <focus>` near 70% context; `/recap`
   (new Apr 2026) to resume without replaying the whole thread; `/context` and `/usage`
   to see what's actually eating the window.

#### B. The prompt that triggered this audit — critique

The request was, paraphrased: *"Locate inefficiencies in our process… reduce token use…
better prompting… leverage other AI… hybrid local LLM and Claude… ANYTHING that could
help… search the web… keep up to date… check the news."*

It's a warm, high-trust brief — but it's the textbook **vague prompt** that the cost docs
warn triggers broad scanning ("improve this codebase" → expensive). Specifically:

- **No scope or success criteria.** "ANYTHING that could help" has no stopping point, so
  the agent must guess how deep to go — and tends to go maximal (most expensive path).
- **No deliverable named.** A chat reply? A doc? A PR? Unstated, so the agent picks — and
  in a scheduled, unwatched routine a chat reply would have been *lost* (nobody's reading
  the transcript; only a notification or a committed file survives).
- **No budget signal.** Nothing says "spend 5 minutes" vs "deep dive," so the agent can't
  right-size effort or model.
- **Open-ended web research** ("search… look for best practices… check the news") with no
  freshness bound or topic list invites unbounded fan-out searching.

**Better version of the same ask:**

> "Audit our Claude usage for token/cost waste. Deliverable: a doc committed to
> `docs/ai-cto/ai-process-efficiency.md` with findings ranked by leverage and a 3-item
> action list. Cover: CLAUDE.md size, model choice for routines, using our LiteLLM
> router for cheap work, and prompt-caching. Use ≤5 web searches for 2026 best
> practice; cite them. Keep it under ~2 pages. Don't change any CLAUDE.md yet — propose
> first."

That version names the deliverable (survives an unwatched run), bounds scope and research,
sets a length, and adds a safety rail (propose before editing). Same intent, a fraction of
the tokens, and a result that lands somewhere durable.

**General prompting rules for us going forward:** name the deliverable and where it lands;
give a concrete target/scope; state a rough effort/length budget; for scheduled routines,
say "commit the result + notify, don't just reply"; cap web research; and for risky edits,
"propose before applying."

#### C. Billing/news worth knowing (June 2026)

- **June 15, 2026:** Agent SDK usage and headless `claude -p` invocations stop counting
  against the Claude plan and bill against a **separate API-rate credit pool (~$20/mo)**.
  Directly relevant — our scheduled routines are headless. ZORT should track this as a new
  line item and watch the pool, not the plan bars.
- **Fable 5** now ships **1M context by default** (and always uses extended thinking — no
  way to disable, so don't pick it for cheap mechanical work).
- **Nested sub-agents** and **MCP tool-search/deferral** are live — our GitHub MCP tools
  are already deferred (names only until used), which is correct; keep MCP servers we
  aren't using disabled (`/mcp`) and prefer CLI tools where they exist.

#### D. Recommended next actions (small, reversible)

1. **Trim the CLAUDE.md files to indexes** (biggest free win) — propose diffs per repo,
   move reference tables to linked docs/Skills. *(NARF; gated on founder OK since CLAUDE.md
   is behavior-defining.)*
2. **Fix TD-14, then pilot router offload** — point one bulk job (doc-link checks or commit
   drafting) at LiteLLM/local, measure quality, expand. *(NARF + ZORT.)*
3. **Set Sonnet as the default for scheduled routines and Haiku for mechanical subagents;**
   record the model policy. *(NARF; ZORT tracks the saving.)*

Items 1 and 3 are pure config and reversible. Item 2 is gated on the TD-14 privacy fix.

#### Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Claude Prompt Caching in 2026: the 5-minute TTL change — DEV](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Claude Code Router: Route Claude Code to Any Model — MorphLLM](https://www.morphllm.com/claude-code-router)
- [LLM API Pricing 2026 — AI Magicx](https://www.aimagicx.com/blog/llm-api-pricing-comparison-2026)
- [Claude Code Pricing June 2026 — Bind AI](https://blog.getbind.co/claude-code-pricing-changes-june-15-what-youll-actually-pay-2026/)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
