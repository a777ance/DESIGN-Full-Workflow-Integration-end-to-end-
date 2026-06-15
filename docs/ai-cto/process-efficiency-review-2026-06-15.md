# Process efficiency review — user ↔ AI workflow

**Date:** 2026-06-15 · **Author:** NARF (AI CTO routine) · **Status:** findings for review

Prompted question: *"Locate inefficiencies in our PROCESS between the user and the AI.
Reduce token use, better prompting, leverage other AI, hybrid local/Claude. Keep it current."*

This is a findings doc, not a decision. Nothing here changes config. Pick the ones worth
doing and I'll wire them up. Token figures are estimates (~1.3 tokens/word).

---

## TL;DR — the one big lever

**Your single largest, fully-controllable waste is the session-start tax, and it is
measurable in your own repos right now.**

- Every web session auto-injects **all six `CLAUDE.md` files** = ~8,030 words ≈ **~10.5k
  tokens before a single instruction is read.** (This very routine paid that.)
- A DESIGN-repo session that *follows its own CLAUDE.md* must then read **9 more docs**
  (AI-CTO portfolio/roadmap/tech-debt/decisions + AI-CFO portfolio/decisions/metrics/
  runway/budget) = ~7,600 words ≈ **~10k more tokens** — and it's told to **re-write
  portfolio.md at session end** too.
- **Net: ~13–20k tokens consumed before any actual work begins, on every session.**

Fix this one thing and you cut more cost than any prompting trick. Everything else below
is secondary.

---

## 1. Cut the session-start tax (biggest win)

| Problem | Fix |
| --- | --- |
| All 6 `CLAUDE.md` load on every web session even when you touch one repo | Trim each `CLAUDE.md` to a **lookup table**, not a full briefing. DESIGN (2,608 w) and localDNS (2,728 w) are 2–3× too long. Move the prose to `README.md`/`network-context.md` (already exist) and leave `CLAUDE.md` as pointers. Industry rule of thumb: CLAUDE.md is an index, not a brain dump. |
| CLAUDE.md mandates reading 9 docs *up front* every session | Make session-start reads **lazy/conditional**: "read the CFO docs **only when the task is financial**." A homelab DNS fix should never load `runway.md`. Replace the "at session start, read 1–6" blocks with "read X **when** the task touches X." |
| Dual-hat (NARF + ZORT) doubles the ritual | Split the start-up reading by hat and trigger by task type, not load both every time. |
| `portfolio.md` rewrite at session end | Make it **append-only and conditional** ("update *only if* a decision/status changed"). A read-only routine like this one shouldn't trigger a full-file rewrite. |

**Estimated saving:** ~8–15k tokens/session. At even a few sessions/day this dwarfs every
other item here.

---

## 2. Exploit prompt caching (you may already get some of this free)

Claude Code caches the system prompt + CLAUDE.md automatically, so the *stable* prefix is
discounted ~90% on cache hits. Two implications:

- **Stability matters more than size for the cached part.** Keep CLAUDE.md byte-stable
  within a work block — don't edit it mid-session, or you bust the cache and re-pay full
  price. (Trimming it once, then leaving it alone, is ideal.)
- **Order content stable→volatile.** Put the unchanging brief first, the task-specific /
  date-stamped bits last. Your house-style "newest-first" ordering on logs is fine for
  humans but means the *top* of every log file changes every entry — if a log is pulled
  into context often, the churn defeats caching. Keep frequently-cached docs append-stable.
- Caches are now **per-workspace isolated** (since 2026-02-05) — fine for you, just be aware
  cross-repo cache sharing won't happen.

---

## 3. Lean on the hybrid stack you already built

You have the rare advantage of **already owning** a local+cloud router: LiteLLM on
`:4040`, Ollama on the t630, the `local-reason` / `cloud-gpu-reason` / `cloud-overflow`
ladder, plus the rented-GPU path. Most teams pay consultants to build what's sitting on
your thin client. Use it deliberately:

- **Route by task class.** Industry split is ~60–70% of requests are simple (classify,
  extract, format, lint, commit-message, rename) — those belong on the **local Ollama
  tier**, not the Claude API. Reserve Opus for genuine reasoning/refactor/architecture.
- **Pre-process locally, finish on Claude.** Use a local model to *summarize/triage* a big
  log or file, then hand only the distilled result to Claude. Cuts input tokens hard.
- **The reasoning ladder is the right pattern** — extend it: add a cheap local "draft +
  self-review" pass before anything hits the paid API.
- **Keep a kill-switch on spend.** LiteLLM can cap spend and add fallbacks as a config
  change ("nginx for LLMs"). Set a monthly budget + alert so a runaway routine (like a
  mis-scheduled loop) can't run up a bill silently.
- **Caveat — don't over-route.** Splitting work across many agents/models has a real
  "telephone game" cost; coordination tokens can exceed the work. Route by *task*, not by
  inventing a committee of agents.

---

## 4. Subagents & context discipline (for me, the AI)

- Multi-agent / subagent-heavy sessions use **~4–7× the tokens** of a single thread (Agent
  Teams ~15×). They're worth it **only** when a subtask produces lots of context that's
  irrelevant to the main thread (e.g. a broad code search). Then the verbose work stays
  isolated and only the conclusion returns.
- Rule I'll follow: **main session = direction + review; subagent = any large read or
  multi-step search.** I should not spin up role-split agents (planner/implementer/tester)
  for routine work — that's where coordination cost balloons.
- **`/clear` between unrelated tasks**, `/compact` or the new `/recap` on resume instead of
  replaying the whole thread. Long threads silently re-read themselves every turn.
- Add a **`.claudeignore`** to each repo (build output, `*.stats.json`, rendered HTML,
  `node_modules`, large generated statements) — reported ~85% context reduction from this
  discipline alone. Your `customers/` rendered statements and `localDNS` generated HTML are
  prime candidates.

---

## 5. Prompting itself (general best practice, 2026)

- **Specific beats polite.** Structured, specific prompts cut the iterative-refinement rate
  from ~38% to ~11% — i.e. fewer expensive back-and-forth rounds. Each avoided round is the
  whole context re-read.
- **Give the minimum context that defines the task** — function signature + error + calling
  context, not the whole file. Reasoning quality starts degrading past ~3k tokens of prompt;
  more context can make answers *worse*, not just costlier.
- **State the output shape and stop conditions up front** (e.g. "commit to branch X, don't
  open a PR, notify only if Y") — you already do this well in the routine harness.
- **Batch related asks** into one turn rather than a sequence of small ones.

---

## 6. Critique of *this* prompt (you asked)

Your prompt was **effective for a human-to-human brainstorm but token-inefficient for an
agent**, for three reasons:

1. **Unbounded scope.** "ANYTHING that could help… search the web… check the news…" invites
   maximal fan-out. I had to *choose* a budget for you. A capped version — *"Find the top 3
   token-waste sources in our actual repos and propose one fix each; ≤6 web searches"* —
   gets you 80% of the value at a fraction of the cost.
2. **No output contract.** It didn't say where to put the answer, how long, or what "done"
   looks like. Unanchored, an agent over-produces. Add: *"Write findings to
   `docs/ai-cto/…`, ≤2 pages, prioritized."*
3. **Open-ended freshness.** "Keep UP TO DATE… day by day" reads as "search exhaustively."
   Better: *"Only flag changes since <date>; assume I know the basics."*

A tighter rewrite that would have cost ~half the tokens:

> *"Audit our repos for the 3 biggest token-waste patterns in how we run Claude sessions.
> For each: the cost (measured from our files), one concrete fix, and the saving. Then 5
> web searches max for any 2026 technique we're missing. Write it to `docs/ai-cto/` as a
> prioritized ≤2-page doc. Notify me with the headline number."*

Note: for a **scheduled routine** the looseness is lower-risk (it runs unattended, results
are cheap to discard) than for interactive work where you're paying per round-trip.

---

## 7. Worth watching (current, will change fast)

- **Nested subagents + smarter model/region handling** shipped in Claude Code (June 2026) —
  relevant to how routines fan out work.
- Anthropic roadmap talk of context windows that "feel infinite" + better multi-agent
  coordination — may make some of §1's manual trimming less necessary later, but not yet.
- **`/recap`** (April 2026) for cheap session resumption.
- LLM-gateway routing (LiteLLM/Olla) maturing fast — your stack is already on the right side
  of this trend.

---

## Recommended order of action

1. **Trim the two big `CLAUDE.md`s** (DESIGN, localDNS) to lookup tables — biggest, easiest win.
2. **Make session-start doc reads conditional on task type** (don't load CFO docs for infra work).
3. **Add `.claudeignore`** to `customers/` and `localDNS/`.
4. **Set a LiteLLM monthly spend cap + alert**; push routine triage to the local tier.
5. **Tighten routine prompts** with an output contract + scope cap (template in §6).

---

### Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM AI Gateway: Route Local + Cloud Models (2026) — Local AI Master](https://localaimaster.com/blog/ai-gateway-litellm)
- [When to use multi-agent systems (and when not to) — Claude](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)
- [Claude Code Sub-Agents Explained: Context, Cost, Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Claude Code Guide 2026: 25 Features — MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [Prompt Engineering Best Practices 2026 — Promptessor](https://promptessor.com/blog/prompt-engineering-best-practices-2026)
- [Cut AI Agent Token Waste 74%: Semantic Prompt Engineering — CostLayer](https://costlayer.ai/blog/semantic-prompt-engineering-reduce-ai-token-waste)
