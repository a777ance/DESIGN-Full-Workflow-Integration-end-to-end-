# AI Working-Process Efficiency — token cost & prompting review

**Prepared by:** NARF (AI CTO), scheduled routine · **Date:** 2026-06-20
**Question asked:** Where is the human↔AI process inefficient? How do we cut token use,
prompt better, and lean on local LLMs / a hybrid stack? Keep it current.

This is a review of *how we work with Claude*, not of the product. It reads newest-first
per house style; the **TL;DR** and **Do-this-week** list are at the top.

---

## TL;DR — the five levers, biggest first

1. **Re-sent context is ~62% of an agentic bill.** The single largest cost in
   Claude-Code-style work is not your prompt — it's the session dragging earlier
   messages, file reads, tool dumps, and the `CLAUDE.md` files along every turn. Fix
   the context discipline and most of the bill goes with it.
2. **Our `CLAUDE.md` files are our biggest self-inflicted cost.** They load *in full,
   every turn*. Ours are long, narrative, and lore-heavy (Norse roster, reverse-chron
   rules, prose rationale). Beautiful — and expensive on every single round. **Slim them
   to hard rules; move the prose to `README`/`network-context` that load only on demand.**
3. **Prompt caching is free money we're not taking.** A stable system prefix (the
   `CLAUDE.md` + tool defs) cached cuts that cached input by ~90%. Teams report 59–70%
   total LLM-cost cuts from caching alone. It needs a *stable* prefix — which is exactly
   what slimming `CLAUDE.md` also buys.
4. **We built a hybrid router and aren't using it for our own coding.** The stage-10
   LiteLLM stack (`local-fast`/`local-smart` Ollama on the t630 → cloud failover) is
   designed for exactly this. Local models now handle ~80% of *daily* coding (boilerplate,
   well-specified features, refactors, tests) at zero per-token cost. We pay Claude for
   100% of it. Route the bulk locally; reserve Claude for hard reasoning.
5. **Tier the cloud calls.** Haiku for grunt work, Sonnet for code, Opus only for the
   hard reasoning. We default to Opus (this session is Opus 4.8) for everything.

## Do this week (cheap, high-leverage)

- [ ] **Cut each `CLAUDE.md` to hard rules only** (commands, invariants, "don't touch"
      paths, the deploy table). Target < ~150 lines. Push prose to `README`/context docs.
      *This helps token cost AND caching AND model focus at once.*
- [ ] **Adopt a `/clear`-between-tasks habit**, and `/recap` on resume (new Apr-2026).
      Every unrelated task starts fresh — don't carry one task's reads into the next.
- [ ] **Scope prompts to a file/function, not a module.** "Refactor the login function in
      `auth.ts`" not "refactor auth." Less context pulled, fewer tokens, tighter output.
- [ ] **Set `fallbackModel`** (now supports up to 3, tried in order) so a rate-limit or
      outage degrades gracefully instead of failing the run.
- [ ] **Verify prompt caching is on** for the API tiers (5-min TTL default; 1-hr for
      work that pauses and revisits the same prefix within the hour).

---

## 1. What we're already doing right

We are ahead of most of the field on architecture:

- **The hybrid router exists** (`localDNS/10-ai-orchestration/`): LiteLLM front door,
  local Ollama tiers as default, cloud as *overflow*, capability-named tiers, a
  deterministic privacy gate. This is the textbook 2026 hybrid pattern — sensitivity +
  complexity + availability routing — and we designed it before the blog posts caught up.
- **"Route, don't shard"** is the correct invariant.
- **Capability-named tiers** (`cloud-explore`/`cloud-code`/`cloud-vision`) mean a backend
  swaps without touching callers — exactly right.

**The gap is execution, not design:** per the CTO context, the gateway is *"config in
repo, not deployed."* Until Ollama is pulled and LiteLLM is up on the t630, every "local"
saving is theoretical and we pay Claude for 100% of work. **Standing up stage 10 is the
highest-ROI infra task for cost** — it's already P3 in the localDNS open items; this
review argues it should jump the queue.

## 2. The context-cost problem (the 62%)

Agentic AI burns ~50× the tokens of a chat because every turn re-sends accumulated
context. The four levers that actually move the bill:

| Lever | What it does | Our status |
| ----- | ------------ | ---------- |
| Prompt caching of the system prefix | ~90% off cached input; 59–70% total savings reported | **Not exploited** — and our long `CLAUDE.md` makes the cacheable prefix big *and* worth caching |
| Model-tier routing | Haiku grunt / Sonnet code / Opus hard | **Not doing** — Opus default |
| Aggressive context pruning | `/clear`, scoped tasks, subagents for big reads | **Ad hoc** |
| Per-user / per-session budget caps | Hard ceiling on runaway loops | Hoard-Warden (spend cap) is *designed* in Odin, not live |

### Subagents — use with judgement, not reflexively

Subagents run in an isolated context window; only their *summary* returns to the main
thread. That's a real win when a task would otherwise force Claude to read **>3–4 large
files** — the verbose searching/log-dumping stays off the main bill. But they are **not
automatically cheaper**: for small shell/git actions the startup overhead (their own
prompt, tool defs, extra round-trips) can cost *more*. Rule: subagent when the
main-context clutter saved outweighs the startup overhead.

## 3. The `CLAUDE.md` problem (specific to us)

This is worth its own section because it's our most concrete, fixable inefficiency.

> *"The `CLAUDE.md` file is fully loaded in every conversation turn. If this file is too
> bloated, the base cost of every round will rise significantly. Keep only hard rules."*
> — KDnuggets, 7 ways to reduce Claude Code token usage

Our `CLAUDE.md` files are the opposite of this: multi-hundred-line narrative briefings
with funnel diagrams, money-flow ASCII, role tables, lore, and full house-style essays.
A reader loves them; **the model re-reads all of it every turn, and so does the meter.**

**Recommendation — split each `CLAUDE.md` into two layers:**

- **`CLAUDE.md` (always loaded):** hard rules only — deploy/path tables, invariants
  ("push to `main`, no branches"; "never add sensitive domains to the forward-path";
  "honesty rule"), verification commands, "don't touch" paths. Terse. ~1 screen.
- **`README.md` / `*-context.md` (loaded on demand):** the funnel diagrams, the
  rationale, the lore, the role/money tables. Claude pulls these only when a task needs
  them — and that pull is cacheable and scoped.

This single change compounds across **all seven repos** and every session in each.

> Note: the house-style "reverse-chronological / Z→A / reversed walkthrough blocks" rules
> are charming but add reasoning overhead on every doc the model writes or edits. They're
> a brand choice, not a cost emergency — keep them, but be aware they're a small
> per-edit tax, and don't let them creep into the slimmed `CLAUDE.md`.

## 4. Hybrid local + cloud — turn the design on for *our* work

We have the stack. The 2026 consensus on what to route where:

| Send to **local** (t630 Ollama / `local-*`) | Keep on **Claude (cloud)** |
| --- | --- |
| Boilerplate, well-specified features | Architecture-level design, new system boundaries |
| Refactors of existing code | Unfamiliar frameworks, subtle concurrency/debugging |
| Writing tests | The hard reasoning, the 1M-context exploration |
| Codebase explanation, summaries | Anything touching real customer data *off-box* (privacy gate) |
| **Anything sensitive** (privacy: stays in the walls) | (sensitive never routes to cloud — the gate guarantees it) |

**Tooling note:** Cline and Roo Code support *per-task* routing today — default to Ollama,
escalate to Anthropic above a complexity threshold. That's the practical bridge between
"we have a LiteLLM gateway" and "our daily coding actually hits it." Worth a spike once
stage 10 is live. The t630 is CPU-only (4-core Carrizo), so `local-fast`/`local-smart`
(qwen2.5 3b/7b) are the realistic local tiers; heavy reasoning still offloads (rented GPU
or cloud) — that's already in `config.yaml`.

**Caveat to keep us honest:** on a CPU-only t630, local inference is *slow*. The win is
**cost and privacy on bulk/low-urgency work**, not latency. Don't route interactive,
"I'm-waiting-on-it" coding to a 7B-on-CPU and call it an upgrade — that's a worse
experience. Route async/bulk/sensitive work local; keep interactive hard work on Claude.

## 5. Critique of the request that triggered this review

The founder asked me to critique the prompt itself — so, candidly:

**What was inefficient about it:**
- **Unbounded scope.** "ANYTHING that could help… Search the web… check the news…
  best practices… Thanks!" invites maximal fan-out. An open mandate makes the agent
  read widely and write long — the most expensive possible shape of request. It worked
  here because it's a scheduled routine with a research budget, but as a *habit* it's the
  costly pattern this very document warns about.
- **Two questions in one** (process audit + meta prompt-critique) — fine, but each would
  cache/scope better alone.
- **No deliverable spec.** "Let me know" leaves format open, so the agent guesses
  (I chose: a committed doc + a notification). Specifying the artifact up front saves a
  round-trip and a wrong guess.

**A tighter version of the same ask:**

> *"Audit how we use Claude across the A777ance repos for token cost. Cover: (1) `CLAUDE.md`
> size, (2) prompt caching, (3) using our stage-10 local router for daily coding, (4)
> model-tier routing. Use current (2026) best practices — cite sources. Output a committed
> markdown doc under `docs/ai-cto/` with a prioritized action list. Skip anything already
> covered in ORCHESTRATION-BLUEPRINT.md."*

Same intent, but scoped, sourced, and with a named deliverable — cheaper to run and
easier to act on. **General principle for prompting this team's agents: name the scope,
name the deliverable, name what to skip.** That trims the context the agent has to pull
and the output it has to produce — the two things you pay for.

---

## Sources (2026)

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya (May 2026)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Anthropic API Pricing in 2026: Caching, Batch & Optimization — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Anthropic Prompt Caching in 2026: Cost, TTL, Latency — AI Checker Hub](https://aicheckerhub.com/anthropic-prompt-caching-2026-cost-latency-guide)
- [How We Cut LLM Costs by 59% With Prompt Caching — ProjectDiscovery](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching)
- [AI Agents Burn 50x More Tokens Than Chats — LeanOps](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Local LLM vs Claude for Daily Coding: Real Data 2026 — DEV](https://dev.to/kunal_d6a8fea2309e1571ee7/local-llm-vs-claude-for-daily-coding-real-data-2026-1nke)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Claude Code Updates — June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
