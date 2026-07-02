# Process-efficiency review — user ↔ AI loop — 2026-07-02

*Task: find inefficiencies in how we (human + Claude) actually work, cut token spend,
improve prompting, and evaluate a hybrid local-LLM + Claude-API setup. Grounded in this
portfolio's real files and current (July 2026) best practice — sources at the bottom.*

**TL;DR — the three that matter, ranked by tokens saved per dollar of effort:**

1. **Gate the daily NARF/ZORT review; stop paying Opus to re-derive an unchanged answer.**
   The single biggest leak, and it's in our own logs.
2. **Trim the always-loaded context** (7 × CLAUDE.md + mandatory session-start reads).
   We pay for ~55–90k tokens of boilerplate on *every* session before any work starts.
3. **Route by tier** — we already own the LiteLLM router; use it. Cheap/bulk/private work
   → local or Haiku; only real reasoning → Opus. Industry data: 60–70% cost cut, no
   meaningful quality loss.

Everything below expands these plus smaller wins, and closes with a critique of the prompt
that launched this review.

---

## 1. The daily review is the biggest leak (P1)

**Evidence, from our own files.** The latest review (`reviews/2026-07-01-review-1.md`)
opens by re-verifying TD-14 **"a third time"** and notes **"nothing has shipped in ~three
weeks … four review cycles with no real Statement."** The `reviews/` folder holds ~21 daily
files, most 5–8 KB, each re-reading the same context and re-reaching the same conclusions.
One outlier — `2026-06-22-review-1.md` at 838 bytes — is the *correct* shape for a
no-change day; the rest are not.

**What each daily run actually costs (input tokens, before any real work):**

| Loaded every review | ~bytes | ~tokens |
| --- | ---: | ---: |
| CLAUDE.md files pulled into context (DESIGN 18K, localDNS 20K, + others) | ~40–60K | ~10–15K |
| NARF mandatory reads: portfolio + roadmap + tech-debt + decisions | ~22K | ~5.5K |
| ZORT mandatory reads: portfolio + decisions + **metrics.md (24.7K!)** + runway + budget + MARKETING ctx | ~44K | ~11K |
| "Verify the claim" reads (live config.yaml, READMEs, roster) | varies | ~5–15K |
| **Per-run input floor** | | **~30–45K, spiking to 90K** |

On Opus, run daily, that's a standing bill for output that's ~90% identical to yesterday's.
The review even says so itself.

**Fix (do all three):**

- **Change-gate it.** Before spending a single reasoning token, diff the inputs:
  `git log --since="last review" --oneline` across the repos + a hash of the roster/config.
  **No change → emit the 838-byte "no delta since <date>" line and stop.** Only a real diff
  triggers a full review.
- **Run the gate cheap.** The "did anything change, and does it matter?" check is a
  Haiku-class (or local) job, not an Opus job. Escalate to Opus *only* when the gate fires
  on something substantive.
- **Verify-once, not verify-daily.** TD-14 was confirmed three times. Mark a finding
  `verified: <date>` and don't re-verify for N days unless its source file changed. A
  standing finding doesn't need a fresh Opus proof every morning.

**Estimated effect:** on a portfolio where most days have no material change, this alone
should remove the large majority of the routine's spend — the same category of win Branch8
reported (a 72% monthly drop after caching + session focus).

---

## 2. Trim the always-loaded context (P1)

Anthropic's own guidance for 2026: *"Keep your project instructions short — if your
instructions have grown into thousands of words, trim aggressively; the cost of carrying
that weight is paid on every single prompt."* We are carrying a lot of weight:

- **CLAUDE.md sizes:** localDNS **20 KB**, DESIGN **18 KB**, MARKETING **11 KB** — each is
  a small essay, re-sent (as a cached prefix, but still written and still occupying the
  window) every session.
- **Mandatory session-start reads.** DESIGN §5 (NARF) forces 4 files and §6 (ZORT) forces
  **6 more** at the top of *every* session — including `metrics.md` at **24.7 KB** — whether
  or not the task touches finance. That's ~16K tokens of forced reading before the user's
  actual request is even considered.

**Fix:**

- **Split "always" from "on-demand."** CLAUDE.md should be the *minimum* a session needs to
  not do something dangerous (the rules, the invariants, where to look). Everything
  explanatory moves to README/context files that are read *only when the task needs them*.
  Target: get each CLAUDE.md under ~6 KB.
- **Make session-start reads conditional, not mandatory.** Replace "at session start, read
  these 10 files" with "for a CTO task, read X; for a finance task, read Y." A doc-linting
  session should never load `metrics.md`.
- **This protects prompt caching, not just window size.** Claude Code caches the stable
  prefix (90% discount on cache reads). A smaller, more stable prefix = cheaper cache
  writes and fewer invalidations. Reserve the big cache write for content that's actually
  reused.

---

## 3. Route by tier — we already own the router (P1)

`localDNS/10-ai-orchestration/` runs LiteLLM (:4040) + a local reasoning ladder
(deepseek-r1 1.5b local → rented-GPU R1) + Open WebUI. The infrastructure for hybrid
routing **already exists** — the gap is that heavyweight work (this review; the daily NARF
run) defaults to Opus regardless of difficulty.

**The 2026 consensus split** (sources below):
- **Local model / Haiku:** classification, "did anything change?", link/anchor lint,
  commit-message drafts, roster extraction, first-pass summaries, the change-gate in §1.
  Roughly 60–70% of requests are this shape.
- **Sonnet:** the daily driver — most drafting, edits, medium analysis.
- **Opus:** the 10–15% that need real reasoning — architecture calls, strategy, the
  metamodern-tension synthesis, final-quality customer-facing copy.

**Two extra reasons this fits us specifically:**
- **Privacy.** Roster names/figures and anything customer-facing can be drafted on the
  *local* model and never leave the box — the same fail-closed instinct TD-14 is about.
  (Note: TD-14 shows the router currently fails *open* to cloud; fix that before trusting
  "local-only" for sensitive data — the two efforts reinforce each other.)
- **Bulk/scheduled = Batch API.** Any non-interactive bulk job (regenerating all
  statements, a full-repo doc sweep) should use the Message Batches API for a **50%**
  discount, not an interactive session.

Point Claude Code at the router with `ANTHROPIC_BASE_URL`, or keep Claude Code on Anthropic
and move the *routine/agentic* jobs onto LiteLLM aliases. Reported savings for this pattern:
**60–80%** on the routable slice.

---

## 4. Smaller wins

- **One task per session; `/compact` before it sprawls.** Session focus alone cut costs to
  ~33% of open-ended sessions in the field data. Don't let a review, a code edit, and a
  finance update share one runaway context.
- **Subagents for file-heavy reads.** "Read all 7 repos and summarize" should be a subagent
  that returns only the summary — the 60 KB of CLAUDE.md never enters the main window.
  **Caveat with teeth:** unattended fan-out is how people post $8K–$47K sessions. Any
  subagent/dynamic-workflow use needs a token budget and a stop condition. For *our* volume,
  the gate-and-trim wins above matter far more than fan-out.
- **Reconsider the house-style ordering rules as an AI-loop tax.** Reverse-chronological
  logs, Z→A alphabetical, and "reverse the blocks but keep steps forward, never renumber"
  all cut *against* how the model is trained (forward, A→Z). Every time the model orders it
  the natural way and gets corrected, that's a wasted round-trip — tokens *and* a human
  turn. Two options: (a) keep the style but **make it mechanical** — extend `tools/check-docs.py`
  to lint ordering so it's a deterministic check, not a per-edit judgment call the model
  keeps missing; (b) drop the rules that don't earn their friction. Recommendation: (a) at
  minimum. A lint rule pays for itself in one avoided correction.
- **Stop re-stating unchanged findings in prose.** The reviews re-explain TD-14 in full
  every time. A findings *table* with `status`/`last-verified` columns, updated in place,
  conveys the same state in a fraction of the tokens and reads faster for the human too.

---

## 5. The prompt that launched this review — critique + rewrite

The launching prompt was, honestly, **inefficient in exactly the ways worth naming:**

- **Unbounded scope.** "ANYTHING that could help… anything you could possibly think of"
  invites maximal exploration and maximal spend, with no way to know when it's *done*.
- **No success criteria, no output format, no budget.** The model has to guess how deep, how
  long, and what shape the answer should be — which is itself a source of wasted tokens and
  re-work.
- **Two unrelated asks in one turn** (analyze the process *and* critique this prompt),
  which is fine here but generally splits focus.

It did two things *right*: it named the concrete levers (tokens, prompting, hybrid/local),
and it asked for current/dated info — which correctly triggered web search instead of
stale-memory answers.

**A tighter version of the same request:**

> Review our user↔AI process for cost/efficiency. Scope: the daily NARF/ZORT review
> routine and the always-loaded context (CLAUDE.md + session-start reads). Output: a ranked
> list of ≤7 fixes, each with the est. token/cost impact and effort. Use 2026 best practice
> (search the web; cite sources). Budget ~40k output tokens. Skip anything already tracked
> in tech-debt.md.

That version is answerable, has a finish line, caps spend, and avoids re-deriving known
tech-debt — while still getting the same substance.

**General prompting habits that cut the loop (2026 guidance):** be explicit about the
output schema; give 1–3 examples of the format you want (examples beat paragraphs of
description); state constraints as "don't do X"; wrap source material in tags; set a scope
and a budget. Every one of these reduces the clarify → retry → correct cycles that quietly
dominate token spend.

---

## 6. Suggested next actions (small, ordered)

1. Add a **change-gate** to the review routine and move its "did anything change?" step off
   Opus (§1). *Biggest single win.*
2. **Trim** the three big CLAUDE.md files and make session-start reads **conditional** (§2).
3. Add an **ordering lint** to `tools/check-docs.py` so house style stops costing round-trips (§4).
4. Move **bulk/private/classification** jobs onto the existing LiteLLM router; reserve Opus
   for reasoning; fix TD-14 first so "local-only" is trustworthy (§3).
5. Run *this* meta-review **monthly, not daily**, and on a cheaper tier unless it finds a
   real delta.

None of these touch the product or the honesty rule; they only make the machine cheaper to
run — which is exactly the DESIGN-repo philosophy ("every change should make it cheaper or
more reliable to earn, produce, deliver, or get paid for a Statement").

---

## Sources (July 2026)

- Anthropic — Prompt caching (90% cached-read discount; 1,024-token min):
  https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude Code — How Claude Code uses prompt caching:
  https://code.claude.com/docs/en/prompt-caching
- Anthropic — Prompting best practices (be explicit, examples, constraints, tags):
  https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Claude Code — Create custom subagents (isolated context, cost containment):
  https://code.claude.com/docs/en/sub-agents
- "Reduce Claude Code Costs 60% With Four Habits": https://systemprompt.io/guides/claude-code-cost-optimisation
- "Token Economics in 2026" (Branch8 72% drop; keep instructions short): https://age-of-product.com/token-economics-2026/
- Hybrid Cloud-Local LLM architecture guide (2026; 60–80% savings): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- MindStudio — Run local models with Claude Code to cut costs: https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- LiteLLM — Auto routing: https://docs.litellm.ai/docs/proxy/auto_routing
- Model tiering (Haiku router / Sonnet bulk / Opus hard; 60–70% cut): https://valueaddvc.com/blog/claude-opus-vs-sonnet-vs-haiku-which-model-to-use-and-when-in-2026
- Anthropic — Pricing (Batch API 50% off; cache tiers): https://platform.claude.com/docs/en/about-claude/pricing
