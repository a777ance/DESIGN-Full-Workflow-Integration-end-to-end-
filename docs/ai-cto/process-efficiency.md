# Process efficiency — cutting token spend on the user↔AI loop

*Written 2026-06-28. A standing review of how we use Claude (and other AI) across the
A777ance repos, and where the money leaks. Newest findings at the top, per house style.
Figures and API behaviour verified against the Anthropic `claude-api` reference current
as of this date — re-check before acting on anything pricing-sensitive, this moves weekly.*

---

## TL;DR — the five biggest levers, in order

1. **Turn on prompt caching for the CLAUDE.md files.** They're large, stable, and re-sent
   on every single call. Cached reads cost ~10% of full price. This is the single highest-ROI
   change and it's nearly free to do.
2. **Move the daily AI-CTO/CFO reviews to the Batch API.** They're not interactive — nobody
   is waiting on them. Batch is **50% off** every token. ~25 reviews in June × the whole repo
   as context = our largest recurring spend, and it's the easiest half to cut.
3. **Stop spending a frontier model on deterministic work.** `check-docs.py` already proves
   link integrity with zero tokens. Audit the rest of the loop for tasks a script (or the
   local box) should own.
4. **Tier the model to the task.** Haiku/Sonnet for routine, Opus for judgement, `effort: low`
   for mechanical passes. We default to the most expensive option too often.
5. **Route the cheap half through the LiteLLM ladder we already run.** We have local
   `deepseek-r1:1.5b` + a rented-GPU tier. Summarization, extraction, and triage don't need
   Claude. (Fix TD-14 first — see below.)

Realistic blended saving if all five land: **60–80% off the AI line**, in line with what
hybrid setups are reporting publicly this year. Most of it comes from #1 and #2.

---

## 1. The inefficiencies, ranked

### A. The daily review loop re-reads the world every run *(biggest leak)*
`docs/ai-cto/reviews/` has ~25 dated review files for June alone. Each run appears to load
large stable context (the four CLAUDE.md files, portfolio, tech-debt, decisions) and produce
a short delta. That's the textbook caching + batching case:

- **Caching:** the stable prefix (CLAUDE.md × 4 + portfolio + decisions) is byte-identical
  run to run. With a `cache_control` breakpoint it bills at ~0.1× instead of 1×. Cache writes
  cost 1.25× (5-min TTL) or 2× (1-hour); break-even is 2 requests on the 5-min tier, so a
  daily-and-ad-hoc cadence pays off immediately within a working session.
- **Batching:** reviews are asynchronous by definition. The Batch API is a flat **50% discount**
  on all tokens, completes within an hour (usually minutes), and supports caching too. There is
  no quality trade-off — same model, same prompt, half price.
- **Stacked:** cached + batched, the recurring per-review cost on the stable context drops to
  roughly *0.1 × 0.5 = 5%* of today's. That compounds daily.

### B. We default to the most expensive model and full effort
Opus is $5/$25 per Mtok; Sonnet is $3/$15; Haiku is $1/$5. A doc-integrity sweep, a
"summarize what changed", or a roster-field validation does not need Opus. Two free levers:

- **Model tier** — Haiku for triage/extraction/classification, Sonnet for routine drafting,
  Opus only for genuine architecture/judgement calls (the reviews' actual verdicts).
- **`output_config: {effort: "low"|"medium"}`** — lower effort means fewer, terser, more
  consolidated steps. `high` is the default; `low` is right for mechanical passes and cuts
  token spend materially with little quality loss on simple work.

### C. Deterministic work is sometimes handed to an LLM
`check-docs.py` is the model to copy: a script proves the invariant for free. Candidates to
move off the model where they aren't already: link/anchor checks (done), roster-schema
validation, "did this commit touch HH-0001's required fields" spot-checks, JSON well-formedness,
secret-scanning for `CHANGE_ME` leaks. If the answer is a rule, write the rule, not a prompt.

### D. Long interactive sessions carry dead weight
Once a session is deep, old tool outputs and superseded reasoning still re-bill every turn.
Two server-side tools handle this: **context editing** (`clear_tool_uses` / `clear_thinking`
— prunes stale blocks) and **compaction** (summarizes history near the window limit). For our
agentic work in `localDNS`/this repo, turning these on stops the slow context bloat.

### E. The privacy-fallback bug (TD-14) blocks safe local offload
We already run a LiteLLM ladder (`local-reason` → `cloud-gpu-reason` → `cloud-overflow`).
But TD-14 means a `sensitive`-tagged prompt can fail *open* to Claude cloud. Until that fails
*closed* (local-only fallback), we can't confidently push the cheap, sensitive half of the
work to the local box — which is exactly the work we most want off the paid API. **Fixing
TD-14 is a prerequisite for the hybrid-routing saving, not separate from it.**

---

## 2. Hybrid local + Claude — we're already half-built

We are not starting from zero: the t630 runs `deepseek-r1:1.5b` locally and a rented-GPU R1
tier on demand, behind LiteLLM. Public hybrid setups report 60–83% cost cuts by routing the
~60–70% of requests that are simple (classification, extraction, formatting, first-pass
summarization) to local models and reserving the frontier model for the ~10% needing real
reasoning. Our split should be:

| Work | Route to | Why |
| ---- | -------- | --- |
| Summarize a diff / changelog; extract fields; tag/triage | **local** (deepseek) | No judgement; privacy-safe; ~free |
| First-draft a review, then have Claude verify/finalize | **local → Claude** | Local does the bulk tokens; Claude only adjudicates |
| Architecture calls, the Statement honesty checks, money decisions | **Claude (Opus)** | Genuine judgement; correctness > cost |
| Anything `sensitive`-tagged | **local only** | Privacy invariant — **needs TD-14 fixed** |

This reuses infrastructure we already pay for (the box is a sunk cost) and turns the LiteLLM
ladder from a CTO experiment into a cost lever.

---

## 3. Better prompting (cheaper *and* better output)

- **Give the goal and constraints up front, in one well-specified turn.** Opus 4.x is more
  autonomous and reasons more after each user turn; ambiguous, drip-fed instructions across
  many turns *raise* token use and sometimes lower quality. A clear first turn is the single
  best prompting-side economy.
- **Ask for the deliverable, not a survey.** "Give a recommendation, not an exhaustive
  list of options" cuts a lot of output. Our reviews already do this well — keep it.
- **Don't re-state what's in CLAUDE.md.** It's already in context every call; repeating it
  in the user turn is pure waste (and, if it varies, it silently breaks the cache).
- **Keep the cached prefix byte-stable.** No timestamps, UUIDs, or "current date: …" injected
  into CLAUDE.md or the system prompt — one changed byte invalidates the whole cached prefix.
  Inject volatile context *after* the last cache breakpoint (e.g. as a late message).
- **House style already helps:** newest-first logs mean the model reads the relevant delta
  first and can stop early; reverse-chronological reviews are token-efficient by design.

---

## 4. On *this* prompt (you asked)

The prompt that commissioned this report is itself a good teaching case in inefficiency:

> "Locate inefficiencies… Is there a better way… Perhaps also better prompting… Anything you
> could possibly think of. Leveraging other AI… ANYTHING that could help…"

- **It's maximally open-ended.** "ANYTHING you could possibly think of" on a frontier model
  at high effort invites broad, expensive exploration — the model spends tokens deciding what
  you meant. That's the most costly shape of request.
- **No scope, no success criterion.** "A better way" for *what* — the daily reviews? Claude
  Code sessions? The whole guild? Each implies a different (and much shorter) answer.
- **No constraints.** Budget? Time horizon? Are we optimizing the paid API bill, or human
  time, or both? Unstated, so the model hedges across all of them.

A tighter version that gets a sharper answer for a fraction of the tokens:

> *"Audit our recurring Claude spend across the A777ance repos. Rank the top 5 token leaks by
> estimated cost, propose a concrete fix for each (with the API feature or routing change
> named), and flag which need the t630. Recommend, don't survey. Assume I'll act on the top 3."*

Same intent, bounded scope, names the deliverable and the cut-off — cheaper to run and easier
to act on. (The irony: this thorough report is the *expensive* answer to the loose prompt.
The scoped prompt above would have produced the TL;DR and section 1 alone, which is 80% of the
value.)

---

## 5. What I could not measure

I don't have the actual token bills or per-session usage here, so the rankings are by
*structural* leak size (frequency × context size), not measured dollars. To make this
data-driven: log `usage.cache_read_input_tokens` vs `input_tokens` on review runs for a week —
if cache reads are ~0 across identical-prefix runs, a silent invalidator is live and lever #1
isn't actually firing. That one number tells you whether caching is working.

---

## Suggested next actions

1. Add a `cache_control` breakpoint on the stable review context; verify `cache_read_input_tokens`
   is non-zero on the second run. *(lever #1 — do first, near-free)*
2. Re-platform the daily reviews onto the Batch API. *(lever #2 — 50% off, no quality cost)*
3. Fix **TD-14** (fail closed) so sensitive + cheap work can move to the t630. *(unblocks #5)*
4. Tier models per task and set `effort` explicitly on mechanical passes. *(lever #4)*
5. Inventory the loop for deterministic tasks still handled by an LLM; script them. *(lever #3)*

---

## Sources

- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Claude Code with local agents using LiteLLM and Ollama — Medium](https://medium.com/@kamilmatejuk/run-claude-code-with-local-agents-using-litellm-and-ollama-ab88869cbd00)
- [LLM Gateways & Model Routing: Cut AI Costs 2026 — Lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- Anthropic `claude-api` reference (prompt caching, Batch API, effort/thinking, context editing, model pricing) — internal skill, current 2026-06-28.
