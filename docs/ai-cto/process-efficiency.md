# Process Efficiency — User ↔ AI token & workflow review

**Author:** NARF (AI CTO) · **Date:** 2026-06-25 · **Status:** review, not yet actioned

A standing review of *how we drive Claude* across the seven A777ance repos — where tokens
(and money, and wall-clock) leak, and the cheaper way to get the same answer. Newest review
at the top, per house style. Re-run this review monthly; the model market moves weekly.

> **One-line finding:** the biggest waste is not the model tier — it's that **every session
> re-reads ~1,200 lines of CLAUDE.md plus a 4–6-file "session-start ritual," most of it
> unchanged**, and we already *built* a local-offload router (`localDNS` stage 10) that we
> have **not deployed**. Fix the context bloat first (free, this week), deploy the router
> second (cuts the price of routine drafting ~90%).

---

## A. Priority fixes (highest leverage first)

| # | Fix | Effort | Saves | Where |
| - | --- | ------ | ----- | ----- |
| 1 | **Trim every `CLAUDE.md` to < 200 lines**; push detail into `README`/skills that load on demand | 2h | Loads on *every* turn — biggest fixed cost | all repos |
| 2 | **Collapse the session-start ritual** — one cached "context" file per hub, not 4–6 reads | 2h | 4–6 file reads/session → 1 | NARF & ZORT hubs |
| 3 | **Default to Haiku, escalate to Sonnet, reserve Opus**; set `fallbackModel`; use `/effort low` for mechanical work | 30m | Opus input ≈ 5× Sonnet ≈ Haiku is cheapest; most edits don't need Opus | global settings |
| 4 | **Deploy the LiteLLM router** (it exists, undeployed) and point routine drafting/classification/RAG at local Ollama | 1 box session | ~60–90% on non-sensitive bulk text | `localDNS/10` |
| 5 | **Use subagents for verbose fan-out** (multi-repo search, audits) so the main thread stays small | per task | Keeps the expensive main context lean | global |
| 6 | **Scope prompts** (see §D) — open-ended "anything that helps" invites unbounded, costly exploration | per prompt | Bounds the search; fewer wasted tool calls | human side |
| 7 | **Close TD-14 before any local→cloud routing carries real data** | 3-line edit | Prevents a privacy leak, not tokens | `localDNS/10/config.yaml` |

---

## B. Where our tokens actually go (the diagnosis)

### B1. Context bloat — the dominant, fixable cost
Prompt-caching makes a repeated prefix cheap to *re-read* (cache hits cost ~10% of full
input), **but only if it is stable and sits at the front.** Two habits defeat that here:

- **Oversized memory files.** Current line counts: `localDNS` **326**, `DESIGN` **295**,
  `MARKETING` **214**. Anthropic's own guidance is to keep `CLAUDE.md` near **200 lines** and
  move specialised detail into skills that load only when invoked. Every line over budget is
  paid on every single turn of every session.
- **The session-start ritual.** NARF asks for 4 files at start (`portfolio`, `roadmap`,
  `tech-debt`, `decisions`); ZORT asks for **6** (+ the MARKETING spoke). When we work across
  the portfolio, the harness also injects **all seven `CLAUDE.md` files at once** (you can see
  it in this very session). That's the right design for cross-repo work but it means a "quick"
  cross-repo question starts with tens of thousands of tokens of preamble.

**Fix:** (a) trim each `CLAUDE.md` to a true one-screen briefing; (b) replace the multi-file
ritual with a single, stable `docs/ai-cto/context.md` per hub that the others *link* to, so
the cached prefix is one file, not six; (c) keep the volatile parts (today's focus, last
review date) in **one** place at the *bottom* so edits don't bust the cache for everything
above them. Anthropic's cache is strictly prefix-based — a change in the middle invalidates
everything after it.

### B2. Model tier — we likely over-use the top model
Rough current API rates: **Opus ≈ $5 in / $25 out** per MTok, **Sonnet ≈ $3 in / $15 out**,
**Haiku ≈ $1 in / $5 out** (cache-read is ~10% of input on all three). The community
consensus pattern that cut one team's bill **~72%**: run structure/logic checks on **Haiku**,
move the refined approach to **Sonnet** for daily work, and reserve **Opus** only when Sonnet
visibly fails. Most of our work here is docs, config, and small edits — Sonnet/Haiku territory.

**Fix:** set a `fallbackModel` chain, default the everyday model to Sonnet, and use
`/effort low` (or `MAX_THINKING_TOKENS`) for mechanical tasks where extended thinking is wasted.

### B3. Session hygiene
- `/clear` between unrelated tasks (don't drag a 50-message tail into a one-line fix).
- Work in **short, single-feature sprints** — focused 5–10 message sessions cost a fraction of
  open-ended ones.
- Use the new **`/context`** command and the VS Code **usage-attribution** panel (cache
  misses, long-context, subagents, per-skill/MCP breakdown over 24h/7d) to *see* where tokens
  go instead of guessing.
- Trim **MCP servers** to what a repo needs. Each connected server's tool schemas load into
  context. `DESIGN`/`MARKETING`/`localDNS` each mount the Notion MCP — keep it only where a
  session actually uses it.

---

## C. The hybrid local/cloud angle — we're further along than we think

We **already designed** the right architecture (`localDNS/10-ai-orchestration`): a LiteLLM
front door over local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-embed`
nomic-embed) with Claude as overflow/escalation, plus a deterministic privacy gate. The
industry's 2026 "hybrid cloud-local" pattern *is* this exact stack — LiteLLM gateway, Ollama
local serving, Claude cloud tier, failover routing. Reported savings for routing simple tasks
local: **60–80%**.

**What's missing is deployment, plus two refinements:**

1. **Deploy it** (it's reference code today — see portfolio "not yet deployed"). Until it runs
   on the t630, none of the savings are real.
2. **Best local-offload wins, in order:** (a) **embeddings/RAG** — called constantly, needs no
   frontier intelligence, clearest win; (b) **classification/extraction** (lead triage, tagging
   roster fields); (c) **first-draft** boilerplate (statement prose, email copy) that a human
   or Claude then polishes. Keep **reasoning-heavy** and **customer-facing-final** on Claude.
3. **Point Claude Code itself at the router for cheap turns** — Claude Code honours
   `ANTHROPIC_BASE_URL` / custom model endpoints, so a local model can serve the *trivial*
   turns (rote edits, log summaries) while real work stays on the API. Treat this as an
   experiment, not the default; local 7B on the t630 CPU is slow and not Claude-quality.

**Guardrail (do this first):** **TD-14** — the live `config.yaml` lets a `sensitive` task fail
*open* to Claude cloud if the local model is down (`local-reason → cloud-gpu-reason →
cloud-overflow`). The privacy guarantee lives only in the un-deployed LangGraph gate. Before
any real customer data flows through local→cloud routing, chain sensitive tiers **local-only**.
A false privacy claim is worse than none.

---

## D. The prompt that triggered this review — critique

The triggering prompt was, paraphrased: *"Locate inefficiencies in our process… reduce token
use… better prompting… leverage other AI… hybrid local+Claude… ANYTHING that could help.
Search the web… keep up to date… check the news. If THIS prompt is inefficient, tell me too."*

**It asked the right question but in the most expensive possible shape.** Why it costs more
than it needs to:

- **Unbounded scope** ("ANYTHING… anything you could possibly think of") removes every stopping
  criterion, so the agent explores wide and runs more tool calls than a decision needs.
- **No output target** — no "give me the top 5," no format, no length. The model defaults to
  long.
- **Stacked, open sub-asks** ("also news, also web, also critique this prompt") each pull in
  more searches.

**A cheaper prompt that gets the same value:**

> "Audit our Claude-Code process for token waste. Give me the **top 5** fixes ranked by
> $-saved-per-hour-of-effort, each with the concrete change and where. Check for any pricing/
> feature changes **since [last review date]** — skip what hasn't changed. **≤1 page.** Don't
> re-derive what's already in `process-efficiency.md`."

That version bounds the search (top 5), names the format (≤1 page), makes the web check
*incremental* (since last date), and prevents re-work (points at this file). Same insight,
a fraction of the tokens.

**General prompting levers for us:** be specific and bounded; state the format and length up
front; give the relevant file paths so the agent doesn't go hunting; for recurring reviews,
point at the prior artifact and ask only for the delta.

---

## E. Don't over-optimise — what to leave alone
- **This isn't where the business is stuck.** Per the portfolio, the blocker is t630-access
  cadence and pending human decisions, not token spend. Spend the saved effort on shipping the
  first real Statement, not shaving pennies.
- **Keep the honest, cached documents** (CLAUDE.md as constitution) — trimming ≠ deleting the
  conventions that keep output consistent.
- **Local models are a tool, not a religion.** The t630 is a 4-core CPU box; local inference is
  slow and weaker. Route *appropriate* work there, keep quality-critical work on Claude.

---

## Sources (checked 2026-06-25)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [How We Cut Claude Code Costs 70% — branch8](https://branch8.com/posts/claude-code-token-limits-cost-optimization-apac-teams)
- [Prompt Caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code June 2026: 10 New Features — SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
- [Claude Code Guide 2026: 25 Features — MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
