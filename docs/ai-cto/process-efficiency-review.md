# Process efficiency review — the user↔AI loop

*Review run 2026-06-28 by NARF (AI CTO) as a scheduled routine. Findings ordered
newest/highest-impact first, per house style. This is an architecture-and-practice
review, not a billing audit — I can't see the real token meter from here, so treat
the savings figures as the ranges the 2026 sources report, not measured A777ance
numbers. The honesty rule applies: where a number is illustrative I say so.*

The brief: find inefficiencies in how we (founder + AI) actually work — token waste,
weak prompting, where local LLMs should carry load instead of the Claude API, and any
other lever. Plus a critique of the prompt that launched this review.

---

## TL;DR — the five levers, biggest first

1. **The multi-repo context tax is the #1 cost.** Every session in this checkout
   injects all six repos' `CLAUDE.md` (~1,040 lines ≈ ~12K tokens) *before a word of
   work* — and this very run injected `localDNS/CLAUDE.md` **twice** (~660 lines
   duplicated). That tax is paid on every turn, every session, forever. Fix: one repo
   per session + trim each `CLAUDE.md` toward ~200 lines. (TD-15)
2. **Scope each scheduled routine to one repo and one question.** A routine that wakes
   with the whole portfolio loaded pays the full tax on every fire, unattended.
3. **The launching prompt was under-scoped** ("ANYTHING that could help"), which forces
   wide, expensive exploration. A 6-line template fixes it (below).
4. **We already built the hybrid (Odin/LiteLLM) — but it isn't wired to *our* daily
   loop.** Grunt tokens (commit messages, log triage, classification, first-draft
   summaries) should hit local Ollama; Claude API should be reserved for reasoning.
5. **Protect the prompt cache.** Claude Code caches automatically, but our context
   bloat + autocompact cascades on long sessions throw the 90% cache discount away.
   Short, single-repo, single-task sessions keep the cache warm.

---

## 1. The multi-repo context tax (P1 — TD-15)

**What I observed this run**, not theory: the system context carried the full
`CLAUDE.md` of DESIGN (295 lines), localDNS (326), MARKETING (214), customers (80),
claude-code-homelab (75) and Azure-lab (50) — and localDNS's 326-line file appeared a
**second time** after a tool-search reminder. That is ~1,040 lines of always-on
instructions plus a ~660-line duplicate, injected ahead of any task.

Why it matters (2026 cost math): "a 5,000-token `CLAUDE.md` is a 5,000-token tax per
turn," and agent cost is super-linear because *each turn re-sends everything before it*
— 50 turns at +4K/turn ≈ 5.1M cumulative input tokens. Our standing prefix is ~2–3×
that 5K example before we add file reads.

**Fixes, in order of payoff:**
- **One repo per session.** Open Claude Code *inside* the repo you're working in, not at
  `/home/user` where all six load. This alone removes ~80% of the standing prefix for
  most tasks.
- **Trim every `CLAUDE.md` toward ~200 lines** (the 2026 rule of thumb). Ours run
  50–326. Move the deep tables (deploy-path maps, full known-issues logs) into the
  `README`/`network-context` files they already point at, and let `CLAUDE.md` link to
  them. The agent reads them *on demand* instead of *always*.
- **Use modular memory / `@import`** so a repo pulls only the house-style block it needs
  rather than restating it in full in all six files (the typography rules are
  copy-pasted verbatim across every repo today — that's ~25 duplicated lines × 6).
- **Add a `.claudeignore`** in any repo that has build/vendor dirs so indexing never
  burns tokens on `node_modules`/`dist`/binaries.

## 2. Scope scheduled routines tightly

This routine is the cautionary example: it fired with the entire portfolio loaded and
an open-ended brief. For recurring/unattended runs the fixed cost compounds with no
human to cut it short. Guidance:
- Point each routine at **one repo** and **one decision** ("check localDNS CI", "draft
  this month's CFO metrics row"), so its standing prefix is one `CLAUDE.md`, not six.
- Prefer a **cheaper model tier** for routine monitoring (see §4) and only escalate to
  Opus when the routine actually finds something worth reasoning about.
- Have the routine **notify on signal, stay silent on "all clear"** — which keeps the
  output (and any follow-on tokens) down too.

## 3. Prompting — make the ask cheap to answer well

The launching prompt was warm and clear in *intent* but expensive in *shape*:
"Locate inefficiencies… Anything you could possibly think of… ANYTHING that could
help… Search the web… Check the news." Open-ended superlatives ("anything", "anything")
push the agent to fan out across many searches and files to be safe — exactly the
"subagent fan-out / context resubmission" pattern the cost guides flag.

It worked, but a scoped version gets the same answer for a fraction of the tokens. A
reusable template:

```
Goal:      <the one outcome you want>
Scope:     <which repo(s) / which part of the loop>
Constraints: <budget, must-not-touch, privacy>
Output:    <format + length — e.g. "≤1 page + a tech-debt entry">
Freshness: <"web-check only X" vs "no web needed">
Done when: <the test that says stop>
```

Other prompting wins that map to real token levers:
- **Say the format and length up front.** "≤1 page, then stop" prevents over-production.
- **Scope the web/news ask.** "Check only for Claude Code releases since 2026-06-01"
  beats "check the news" — the latter invites unbounded searching.
- **Use plan-mode for anything multi-step** and approve the plan before execution —
  catches a wrong direction before it spends tokens on it.
- **New task → new session.** Don't continue a long thread into an unrelated job; the
  whole history re-sends every turn. Start fresh (or `/clear`).

## 4. Wire the hybrid we already own (Odin/LiteLLM) into the daily loop

We've done the hard part — `localDNS/10-ai-orchestration/` already routes local Ollama
tiers first and falls over to the Claude API. The gap is that this rig serves the chat
UI, not our *working* loop. The 2026 split that pays off: ~60–70% of agent calls are
simple (classify, extract, format, summarize) and a local model clears them at
acceptable quality; reserving the cloud for the ~10% that need frontier reasoning is a
reported 60–80% cost cut. Concrete moves:

- **Offload grunt tokens to `local-fast`/`local-smart`:** draft commit messages, triage
  Uptime-Kuma/CI logs, first-pass summaries of long docs, tagging/classification. These
  don't need Opus and (bonus) **stay on our network** — a privacy win for anything
  touching the private `customers` repo.
- **Tier the Claude side deliberately inside Claude Code.** Sonnet handles ~80% of
  coding; switch to Opus only for hard reasoning (~60% reported saving vs Opus-always).
  Use the new **`fallbackModel`** config so a tier outage degrades instead of failing.
- **Turn extended thinking down/off for trivial tasks** — the reserved reasoning budget
  is billed even when unused; disable it for mechanical edits.
- **Mind the known privacy gap (TD-14)** before routing anything sensitive locally: a
  `sensitive` task can still fail over from `local-reason` → `cloud-overflow` (Claude)
  because the fail-closed chain isn't enforced at the LiteLLM layer. Fix TD-14 first if
  we start sending real customer data through the local tiers.

## 5. Protect the prompt cache (it's free money we're leaking)

Claude Code applies prompt caching automatically: after the 1.25× write, cached reads
are **0.1× input price — a 90% discount** on the stable prefix. Two of our habits throw
it away:
- **Context bloat + autocompact cascades.** Autocompact fires ~187K tokens and each
  compaction can itself cost 100–200K tokens. Long, multi-repo, multi-topic sessions
  trigger it; short single-repo sessions rarely do.
- **An unstable prefix.** Caching only helps when `system prompt → CLAUDE.md → file
  context` sits in a stable prefix. Trimming and de-duplicating `CLAUDE.md` (§1) makes
  the cached prefix both smaller *and* more stable.

Practical: keep sessions short and on one task; `/clear` between tasks; let the small,
stable `CLAUDE.md` be the cached prefix.

---

## Quick-win checklist (do these first)

- [ ] Open Claude Code inside the target repo, not at `/home/user` (kills ~80% of the prefix).
- [ ] Trim each `CLAUDE.md` toward ~200 lines; push deep tables into linked READMEs.
- [ ] De-duplicate the house-style block across the six files via a shared import.
- [ ] Add `.claudeignore` where build/vendor dirs exist.
- [ ] Scope scheduled routines to one repo + one question; cheap tier by default.
- [ ] Adopt the 6-line prompt template; always state output length + freshness scope.
- [ ] Point grunt-work calls at `local-fast`/`local-smart`; reserve Opus for hard reasoning.
- [ ] Set `fallbackModel`; turn extended thinking off for trivial edits.
- [ ] Fix TD-14 before sending sensitive data through local tiers.
- [ ] `/clear` between unrelated tasks to keep the cache warm and dodge autocompact.

## On *this* review's own efficiency

Owning the irony: this run paid the full six-repo tax (twice for localDNS) to tell you
the tax is the problem. A scoped re-run — "review the user↔AI loop, DESIGN repo only,
≤1 page" launched from inside the DESIGN checkout — would reach the same finding for a
fraction of the tokens. That's the recommendation, demonstrated.

## Sources (2026, current as of this run)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [AI Agents Burn 50x More Tokens Than Chats — LeanOps](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code — Prompt Cache Routing — LiteLLM docs](https://docs.litellm.ai/docs/tutorials/claude_code_prompt_cache_routing)
- [Claude Code June 2026: 10 New Features — SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
