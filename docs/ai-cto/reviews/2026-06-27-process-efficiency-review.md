# NARF — special review — 2026-06-27 — process efficiency (user↔AI)

**Ask:** find inefficiencies in *how we work with the AI* — token use, prompting,
hybrid local/Claude routing, anything. Stay current; check the news.

**Scope note:** this is a meta-review of our *process*, not a code review. It is written
from inside a live session, so the headline finding is one I can measure on myself.

---

## TL;DR — the five levers, biggest first

| # | Lever | Effort | Est. saving | Status |
| - | ----- | ------ | ----------- | ------ |
| 1 | Trim + scope the CLAUDE.md load (14.6K tokens load **every** session) | Low | 30–50% of fixed per-turn cost | Do now |
| 2 | Right-size the model per task (this routine ran on **Opus 4.8 1M**) | Low | 5–10× on routine/research turns | Do now |
| 3 | Push grunt work to the **local LLM router we already own** (LiteLLM/Ollama) | Med | 60–80% on the offloadable slice | Build |
| 4 | Exploit prompt caching deliberately (batch, don't churn CLAUDE.md mid-session) | Low | up to 90% on cached input | Habit |
| 5 | Use subagents *surgically*, not by default (they cost ~7× tokens) | Low | avoids 7× blowups | Habit |

**Timely news (act on this):** Anthropic's **June 15 billing change was PAUSED on June 15**
— Agent SDK / `claude -p` / Claude Code GitHub Actions / *scheduled routines like this one*
still draw from the Max subscription pool, **not** a separate metered credit. Nothing to
claim, limits unchanged. But it is explicitly coming back "with advance notice." Everything
below is how we get ahead of it before it lands.

---

## 1. The CLAUDE.md load is our single largest fixed cost

Measured this session (the whole portfolio is checked out under one working dir, so **all
seven repos' CLAUDE.md files load at once**):

| Repo | ~tokens |
| ---- | ------- |
| localDNS | 5,118 |
| DESIGN (this repo) | 4,496 |
| MARKETING | 2,665 |
| customers | 1,033 |
| claude-code-homelab | 724 |
| Azure-lab | 573 |
| chronikomicon | (none) |
| **Total** | **≈ 14,600 tokens, every turn, never evicted** |

CLAUDE.md is never lazy-loaded — a 14.6K load costs 14.6K on turn 1 and on turn 200. Two
problems:

- **We load all 7 even when working in 1.** A session editing `localDNS` is paying ~9.5K
  tokens for DESIGN+MARKETING+customers+homelab+azure instructions it never uses.
- **The files are prose, not lookup tables.** A published benchmark cut a 3,847-token
  CLAUDE.md to 312 tokens (–91.9%) with no quality regression by stripping anything the
  model can infer from the code. Our two big ones are *bigger* than that starting point.

**Fix (cheap, high-leverage):**
- Run sessions from *inside* the target repo dir, not the portfolio root, so only that
  repo's CLAUDE.md loads. Reserve the portfolio-root view for genuine cross-repo work.
- Cut each CLAUDE.md to a lookup table: keep the non-inferable rules (house style,
  deploy-path table, the DNS-split invariant, secrets rule, branch policy). Move the
  *narrative* (the funnel story, the "why pest-control-not-lawn-care" essays, repeated
  role/money-flow diagrams that already live in README) **out** to README and link to it.
  The voice/why belongs in README; CLAUDE.md should be the briefing, not the book.
- The house-style block is duplicated near-verbatim in all 7 files (~250 tokens each ≈
  1.7K total). Keep it in *one* canonical place and have the others point to it.
- Add/тighten `.claudeignore` per repo. Measured 85% context reduction from ignore
  discipline alone — keep `node_modules`, rendered statement HTML, stats dumps, and the
  `pihole_data`/`open-webui-data` blobs out of any glob the agent walks.

Target: get the per-session fixed load from ~14.6K → ~4–5K without losing a single rule.

## 2. Model right-sizing — this routine is the example

This very run executed on **`claude-opus-4-8[1m]`** — the most expensive model *and* the
1M-context premium tier — to do web research and write a report. That is a Sonnet job (or
even Haiku for the search-and-summarize legs). Opus earns its price on architecture,
gnarly debugging, and the honesty-sensitive statement logic — not on "read 6 articles and
summarize."

**Fix:**
- Default scheduled/research/doc routines to **Sonnet 4.6**; escalate to Opus only inside
  the run when reasoning depth actually demands it.
- Reserve the **1M-context** variant for the rare cross-repo task that truly needs it.
  Loading 1M-context pricing to hold 15K of CLAUDE.md is paying for a moving truck to carry
  a grocery bag.
- This is a one-line change in whatever schedules the routine (model: sonnet).

## 3. We already own a hybrid router — use it for the offloadable slice

`localDNS/10-ai-orchestration` is a *standing LiteLLM gateway* (port 4040) + Ollama + a
cloud-GPU reasoning tier over Tailscale, with the Odin/Heimdall LangGraph supervisor. The
industry pattern (60–80% cost cut) is exactly this: route the ~60–70% of work that is
classify/extract/format/draft to a local model, keep frontier spend for the ~10% that needs
it. We have the rails; we're not running trains on them for *our own* workflow.

Concrete offload candidates that do **not** need Claude:
- `tools/check-docs.py` link/anchor validation — pure script, no LLM at all; just gate CI on it.
- The mechanical house-style chores: reverse-chronological reordering, Z→A list sorting,
  Gill-Sans stack find/replace — a local Qwen/Devstral handles these fine.
- First-draft statement prose, "Handled For You" log entries, commit-message drafts —
  draft local, have Claude *edit*, not author.
- Bulk classification/triage of leads/issues on the master list.

**Caveats, honestly:**
- Claude Code itself can be pointed at a gateway (LLM-gateway support exists), but you don't
  want *interactive* coding on a t630-class local model — quality gap is real. The win is
  **batch/non-interactive** jobs, not replacing the coding agent.
- **Privacy invariant lives here too:** TD-14 in tech-debt is still open — `local-reason`
  fails *open* to `cloud-overflow` at the LiteLLM layer, so a "sensitive" task can leak to
  cloud if the local model is down. Fix that gate before routing any customer data through
  the router. Don't let a cost optimization break the honesty/privacy rule.
- Local hardware reality: keep heavy chain-of-thought (full DeepSeek-R1) on the rented GPU
  tier, not the t630 — the Known-Issues warning about cooking the box still stands.

## 4. Prompt caching — make our habits match how it bills

Cached input reads at ~10% of standard price; Claude Code manages breakpoints automatically.
We don't toggle it, we *earn* it by behaving cache-friendly:
- **Don't edit CLAUDE.md (or other stable context) mid-session** — every edit busts the
  cache and re-bills the whole prefix. Make CLAUDE.md changes their own short session.
- **Batch related asks into one session** so the cached prefix is amortized over many turns,
  instead of paying a cold read for each of five separate small sessions.
- The 5-min cache TTL is why a scheduled routine that wakes, does one thing, and sleeps is
  cache-cold every time. Cluster routine work.

## 5. Subagents and fan-out — surgical, not reflexive

Subagent/multi-agent workflows can burn ~7× the tokens of a single thread. They're worth it
for *isolation* (parallel codebase exploration, keeping a failed-approach spiral out of the
main context) — not as a default. For a survey like this one, a single thread was correct;
a fan-out workflow would have 7×'d the bill for no quality gain. Rule of thumb: fan out only
when the work is genuinely parallel *and* read-heavy, or when you need a clean context to
escape contamination.

---

## On the prompt that triggered this review

The prompt was warm and clear about *intent*, but it is itself a token-efficiency example —
it asks for "ANYTHING that could help… Anything you could possibly think of," which invites
an unbounded, expensive sweep and re-does full research on every run. Suggestions:

- **Bound the scope per run.** "Find the top 3 token inefficiencies and one news item since
  the last review" returns the same value for a fraction of the tokens, and is repeatable.
- **State the output shape.** "Append a dated entry to `docs/ai-cto/reviews/` and notify me"
  removes guesswork (and is what this run did).
- **Make it incremental/stateful.** A recurring "find inefficiencies" prompt should read the
  *previous* review and only report what changed — otherwise every run re-derives the same
  CLAUDE.md and model-choice findings from scratch. Point it at this file as its baseline.
- **Drop the meta-instructions that don't pay rent.** "Search the web if helpful," "look for
  best practices," "check the news" are already implied by the task; spelling them out is
  fine but not free. A tighter version: *"Review our user↔AI process for the top token
  inefficiencies since the last review (docs/ai-cto/reviews/). Include any pricing/feature
  news since then. Append a dated entry and push it; notify me with the headline."*

That tighter prompt is ~40 words vs ~110 and produces the same deliverable on a cheaper model.

---

## Recommended order of operations

1. **Today (minutes):** set scheduled/research routines to Sonnet; stop running them on Opus-1M.
2. **This week (low effort):** trim the two big CLAUDE.md files to lookup-tables, dedupe the
   house-style block, scope sessions to single repos, tighten `.claudeignore`.
3. **Next (build):** close TD-14, then wire the offloadable batch jobs (doc-check, house-style
   chores, draft generation) onto the existing LiteLLM router.
4. **Ongoing (habit):** batch work into sessions, don't churn stable context mid-session, fan
   out to subagents only when isolation/parallelism actually pays.
5. **Watch:** the paused Agent-SDK billing split — when Anthropic re-announces, scheduled
   routines move to metered credit; levers 1–3 are exactly what blunt that bill.

## Sources (June 2026)

- [Anthropic — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code — LLM gateways](https://code.claude.com/docs/en/llm-gateway)
- [Claude credit overhaul / June 15 pause](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Zed — what the Anthropic subscription change means](https://zed.dev/blog/anthropic-subscription-changes)
- [How to reduce Claude Code token usage (CLAUDE.md benchmark)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [7 practical ways to reduce Claude Code token usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid cloud-local LLM architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Best local coding LLMs 2026](https://www.promptquorum.com/local-llms/best-local-llms-for-coding)
- [Best practices for Claude Code subagents — PubNub](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
