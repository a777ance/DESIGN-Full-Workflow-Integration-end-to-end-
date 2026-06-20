# AI process efficiency review — token spend between us and the model

**Date:** 2026-06-20
**Scope:** How we (the operators) talk to the AI, and where that conversation wastes tokens and money.
Not a code review — a review of *the process itself*. Prompted by the founder's standing question:
"is there a better way, and can we run a hybrid local + Claude setup to cut spend?"

**One-line answer:** Yes. The three biggest levers, in order, are (1) trim the per-session
context baseline, (2) route routine work to cheaper models / the local box, and (3) lean on prompt
caching and batching for the recurring jobs. Most of this builds on infrastructure we already own.

---

## 0. The thing you can see from inside this very session

This review was produced by a scheduled routine. Before it did any work, the session loaded **all
seven repos' `CLAUDE.md` files in full** as project instructions — the DESIGN and localDNS briefings
alone are ~15–16 KB each. That fixed context is paid **every turn, every session**, including
routines that only touch one concern. Industry write-ups put it bluntly: a 5,000-token `CLAUDE.md`
costs 5,000 tokens before you type a word, every turn ([KDnuggets][kd]). We are carrying several
times that, multiplied across daily routines.

That is the cheapest win available and it's entirely in our control.

---

## 1. Findings, highest-ROI first

### F-1 — Trim the per-session context baseline (biggest lever, fully ours)
Our seven `CLAUDE.md` files are loaded as project instructions on every session. Re-sent context is
the single largest line on most agentic bills — one analysis pegs it at ~62% ([Finout][fin]).
- **Do:** keep each `CLAUDE.md` to a tight briefing (target < ~1,500 tokens) and push detail into
  `README.md` / linked files the model reads *on demand*. We already half-do this; the briefings are
  still long.
- **Do:** add `.claudeignore` discipline — one measured report saw an **85.5% context reduction** from
  ignore-rules alone ([Agensi][ag]).
- **Do:** scope routines to the repos they actually touch. This routine loaded all seven; a daily
  doc-review only needs one or two. Use per-session repo scoping / add-on-demand, not all-in.

### F-2 — Route by task to the cheapest adequate model (we own the infra for this)
The 2026 consensus pattern is a routed stack: **Haiku triages, Sonnet builds, Opus reviews**
([MindStudio][ms]). Pricing (per 1M tok): Haiku 4.5 **$1/$5**, Sonnet 4.6 **$3/$15**, Opus 4.8
**$5/$25**. Teams routing ~70% of traffic to the cheap tier report **40–85% bill cuts** with no
visible quality drop ([Truefoundry][tf]).
- This session is running on **Opus 4.8** — correct for a cross-repo analysis, overkill for the
  daily `reviews/` summaries, link-checks, and status rollups. Those should default to **Sonnet**,
  with **Haiku** for pure triage/extraction.
- We already have the routing layer: **localDNS stage 10** (LiteLLM + the `local-reason` /
  `cloud-gpu-reason` / `cloud-overflow` ladder). Extend that same dispatcher to cover these
  operator/routine jobs instead of sending everything to cloud Opus.

### F-3 — Hybrid local + Claude (60–86% savings reported) — but fix TD-14 first
Hybrid cloud-local workflows are reported to cut LLM cost **60–80%**, with one case going $10.5k →
$1.5k/mo (**86%**) by keeping simple/low-sensitivity work on a local model and reserving Claude for
hard queries ([SitePoint][sp], [BuildMVPfast][bm]). We have the t630 + Ollama-class models already.
- **Blocker:** **TD-14** (tech-debt log) — a `sensitive`-tagged task can currently fail *over* from
  `local-reason` to `cloud-overflow` (Claude cloud) if the local model is down. The dispatcher's
  `allow_cloud=False` isn't enforced at the LiteLLM failover layer. **Do not lean harder on hybrid
  routing until this fails closed** (local-only fallback chain). Privacy promise depends on it.

### F-4 — Prompt caching is the highest-ROI lever on the recurring jobs
Anthropic caches a stable prefix at **~10% of input price (≈90% off)**; cache writes cost 1.25×
(5-min TTL) or 2× (1-hour) ([Finout][fin], [AICheckerHub][ach]). Our daily routines run on an almost
identical prefix (the same `CLAUDE.md` baseline + skill docs) — an ideal cache target.
- **Do:** confirm the stable prefix (CLAUDE.md, tool/skill defs) sits *before* any volatile content
  (dates, per-run IDs) so the cache actually hits. A single `date.now()` early in the prompt
  invalidates everything after it.
- **Do:** for back-to-back routines within 5 min, the default TTL already covers it; for the daily
  cadence, either pre-warm or accept a cold write once a day.

### F-5 — Batch the non-interactive routines (50% off, and nobody's watching anyway)
The daily `reviews/` docs and status rollups are scheduled, latency-insensitive, and unattended —
the textbook case for the **Batches API (50% off all tokens)**. Agentic loops burn ~50× the tokens
of a chat ([LeanOps][lo]), so batching the predictable ones compounds with F-2/F-4.

### F-6 — Session hygiene on long routines
Use compaction / context-editing on long agentic loops rather than re-sending the whole transcript
each turn; batch related edits into one pass instead of many small turns ([Firecrawl][fc]). For the
daily reviews specifically, scope tightly ("summarize today's diff in repo X") rather than
"review everything."

---

## 2. About the prompt that triggered this routine

Asked to critique its own instructions: the prompt is **good** in spirit — open-ended, gives the
agent latitude, explicitly asks for current/dated info. Its inefficiencies:
- It runs **cross-repo but loads all seven repos in full** when the analysis mostly needed the
  briefings. Scope the routine to what it reads.
- It's **scattershot** ("ANYTHING that could help") — fine for a one-off brainstorm, expensive as a
  recurring job. A recurring version should pin a concrete success criterion (e.g. "report any
  process change that would cut token spend >10%, else stay silent").
- It doesn't **pin a model tier**. A monthly deep analysis like this earns Opus; if it recurs weekly,
  drop it to Sonnet and only escalate when it finds something.

---

## 3. Recommended sequence (cheapest/safest first)

1. **Now, free:** trim the seven `CLAUDE.md` briefings; add `.claudeignore`; scope each routine to
   the repos it touches. (F-1)
2. **This week:** default routine/review jobs to Sonnet; reserve Opus for genuine cross-repo
   reasoning. (F-2)
3. **This week:** verify prompt-cache prefix ordering on the recurring jobs; move the unattended
   daily jobs onto the Batches API. (F-4, F-5)
4. **Before expanding hybrid routing:** close **TD-14** so sensitive tasks fail closed to local.
   Then extend the stage-10 dispatcher to cover operator/routine jobs. (F-3)

Estimated combined effect, from the cited ranges: context trimming + routing + caching land most
teams in a **40–85% reduction** without visible quality loss. Our hybrid box can push the
low-sensitivity slice further — once TD-14 is fixed.

---

## Sources

- [KDnuggets — 7 ways to reduce Claude Code token usage][kd]
- [Agensi — reduce Claude Code token usage][ag]
- [Firecrawl — 12 ways to cut token consumption][fc]
- [Finout — Anthropic API pricing & caching][fin]
- [AI Checker Hub — Anthropic prompt caching 2026][ach]
- [LeanOps — AI agents burn 50× more tokens][lo]
- [MindStudio — AI model routing: Fable 5 / Opus / Sonnet / Haiku][ms]
- [Truefoundry — cost & quality-aware LLM routing][tf]
- [SitePoint — hybrid cloud-local LLM architecture guide 2026][sp]
- [BuildMVPfast — hybrid cloud-local cost optimization][bm]

[kd]: https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
[ag]: https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage
[fc]: https://www.firecrawl.dev/blog/claude-code-token-efficiency
[fin]: https://www.finout.io/blog/anthropic-api-pricing
[ach]: https://aicheckerhub.com/anthropic-prompt-caching-2026-cost-latency-guide
[lo]: https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/
[ms]: https://www.mindstudio.ai/blog/ai-model-routing-fable-5-opus-sonnet-haiku
[tf]: https://www.truefoundry.com/blog/llm-routing-cost-quality-aware-model-selection
[sp]: https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
[bm]: https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
