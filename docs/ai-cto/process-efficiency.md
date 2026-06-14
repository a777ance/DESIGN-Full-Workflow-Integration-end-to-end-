# Process efficiency — human ↔ AI review log

How we spend tokens and attention working with Claude across the A777ance repos, and
how to spend less for the same or better output. Time-based, **newest-first** (house style).

This is a recurring review. Each entry is dated; the top entry is current. Verified
model/price facts come from the `claude-api` skill (cached 2026-06-04) and the external
sources cited inline — re-check them each run, since they move week to week.

---

## 2026-06-14 — First pass: where the tokens actually go

**TL;DR.** The biggest waste isn't prompt wording — it's *fixed context we re-pay on
every run*. Every scheduled routine loads all seven repos' `CLAUDE.md` (~58 KB ≈ ~15K
tokens) plus the mandatory NARF/ZORT session-start reading ritual, and runs almost
everything on Opus 4.8 (our most expensive widely-available model). We already own a
local LLM router (localDNS stage 10) and aren't using it as a triage layer. Five changes
below cut routine cost an estimated 50–80% with no quality loss on the work that matters.

### The findings, in priority order

**1. The "load everything" tax — our single biggest lever.**
A scheduled run that touches only `localDNS` still carries the `MARKETING`, `customers`,
`DESIGN`, `Azure-lab`, `claude-code-homelab`, and `Chronikomicon` briefings in context
(measured: `wc -c /home/user/*/CLAUDE.md` → 58,444 chars). On top of that, every repo's
CLAUDE.md *instructs* the session to open more files at start — NARF reads
`portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md`; ZORT reads six more
(`portfolio.md`, `decisions.md`, `metrics.md`, `runway.md`, `budget.md`, plus
`MARKETING/.../context.md`). That's easily 25–50K tokens of fixed prefix before the
actual task starts — re-billed on every run because, for jobs spaced more than 5 minutes
apart, the prompt cache has already expired (see #4).
*Fix:* scope each routine to the one repo it works on; make the NARF/ZORT
"read these files at start" ritual **lazy, not mandatory** — read the hub doc only when
the task is actually cross-repo or financial. Context engineering, not shorter prompts,
is where the savings live ([Token Optimize][ctx], [Ortem][cctx]).

**2. One model for everything — tier the work.**
We run Opus 4.8 ($5 / $25 per MTok) on link-checking (`tools/check-docs.py` gating),
roster edits, status-doc updates, and routine "Handled For You" logging. None of that
needs frontier reasoning.
*Fix:* a routing tier table —
| Work | Model | Rate (in/out per MTok) |
| ---- | ----- | ---------------------- |
| Hard reasoning, cross-repo design, money decisions | Opus 4.8 | $5 / $25 |
| Most drafting, doc edits, summaries | Sonnet 4.6 | $3 / $15 |
| Classification, link/lint checks, "is this stale?" triage | Haiku 4.5 | $1 / $5 |
Routing ~70% of volume to the cheapest adequate model is the single biggest cost lever
short of caching; industry reports put hybrid routing savings at 60–80% with negligible
quality impact ([SitePoint][sp], [Cleveroad][cr]). Don't downgrade the *intelligence-
sensitive* work — that's a false economy.

**3. We already have the hybrid local+cloud rig — use it as a pre-filter.**
localDNS stage 10 runs a LiteLLM router + Open WebUI + a reasoning ladder
(`deepseek-r1:1.5b` on the t630 for light work, a rented-GPU tier for heavy). Today it's
a chat toy; it should be the **triage layer** in front of the Claude API: let the local
model do free classification, staleness checks, and first drafts, and escalate only the
hard remainder to Claude. This is exactly the LiteLLM-gateway + Ollama + Claude pattern
the field has standardized on ([Hybrid LLM routing][devto], [MindStudio local][ms-local]),
and we'd be running it on hardware we already pay for. Bonus: sensitive customer data in
`customers/` can be triaged locally and never leave the box.

**4. Caching barely helps our *scheduled* routines — stop counting on it.**
Prompt-cache TTL dropped from 60 min to 5 min in early 2026; for jobs spaced further
apart than that, the cache is cold every run and we pay the ~1.25× *write* premium each
time with zero read benefit ([DEV TTL][devttl]). So caching is **not** the lever for
day-apart routines — reducing the fixed prefix (#1) is. Caching *does* pay off (a) within
a single multi-step run, and (b) for a burst of requests fired in one window, where a
single `max_tokens: 0` warm-up request primes the cache for the rest. Use it there; don't
expect it to rescue a once-a-day job.

**5. Budget alert for the CFO (ZORT): the June 15, 2026 split.**
As of 2026-06-15 Anthropic separates interactive from autonomous usage on subscription
plans — headless `claude -p`, Agent SDK, GitHub Actions, and scheduled/non-interactive
runs draw from a **new monthly Agent SDK credit**, not the interactive session pool
([CloudZero][cz]). Our scheduled routines are non-interactive, so they hit this pool —
ZORT should track it as its own line in `budget.md`. Also: Fast Mode now defaults to Opus
4.8 at $10 / $50 (2× rate for ~2.5× speed) — speed, not intelligence, so only worth it
when latency is the constraint, which it isn't for an overnight routine.

### On *this* prompt (you asked)

The intent is right but it's **unscoped** — "Locate inefficiencies… ANYTHING that could
help… search the web… check the news" forces broad, expensive exploration and, ironically,
this run loaded a ~40K-token reference skill to answer one question. For a *recurring*
routine, a tight, stable prompt is both cheaper and cache-friendlier. Suggested rewrite:

> "Audit token spend in our scheduled Claude routines. Output: (1) a model-routing tier
> table, (2) the three highest-cost fixed-context items and how to trim them, (3) any
> Anthropic pricing/feature news from the last 7 days that changes the above. Skip
> generic advice; assume our localDNS LiteLLM rig exists. Append findings to
> `docs/ai-cto/process-efficiency.md`, newest-first."

That names the deliverable, sets the boundary, gives the reason, and points at where the
output goes — so the routine produces a diff, not an essay nobody reads.

### Recommended next actions

- [ ] **NARF:** make the session-start reading ritual conditional (cross-repo/financial
  only); record as an ADR if it changes the documented process.
- [ ] **NARF:** scope each scheduled routine to its one repo; don't co-clone all seven
  unless the task is genuinely cross-cutting.
- [ ] **NARF:** stand up the localDNS LiteLLM router as a triage tier; route lint/link/
  staleness checks off Opus.
- [ ] **ZORT:** add an "Agent SDK credit" line to `budget.md`; re-baseline routine cost
  after the routing tier lands.
- [ ] Tighten recurring-routine prompts to the scoped form above.

### Sources (re-verify next run — these move fast)

- Context engineering over shorter prompts — [Token Optimize][ctx], [Ortem][cctx]
- Hybrid local+cloud routing & savings — [SitePoint][sp], [Cleveroad][cr], [DEV.to][devto], [MindStudio][ms-local]
- Prompt-cache 5-min TTL impact on scheduled jobs — [DEV.to][devttl]
- Token-efficiency / MCP & tool-schema overhead — [GitHub Blog][gh], [MindStudio MCP][ms-mcp], [LogRocket][lr]
- June 2026 Claude Code billing/feature changes — [CloudZero][cz]

[ctx]: https://www.tokenoptimize.dev/guides/context-engineering-reduce-token-usage
[cctx]: https://ortemtech.com/blog/claude-code-context-window-tax-guide-2026/
[sp]: https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
[cr]: https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/
[devto]: https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b
[ms-local]: https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
[devttl]: https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363
[gh]: https://github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/
[ms-mcp]: https://www.mindstudio.ai/blog/reduce-token-usage-ai-agents-mcp-optimization
[lr]: https://blog.logrocket.com/stop-wasting-ai-tokens-10-ways-to-reduce-usage/
[cz]: https://www.cloudzero.com/blog/claude-code-agents/
