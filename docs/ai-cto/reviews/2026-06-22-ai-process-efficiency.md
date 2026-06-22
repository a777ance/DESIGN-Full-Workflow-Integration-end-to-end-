# NARF — special review — 2026-06-22 — AI process efficiency & token economics

**Brief from the CEO:** find inefficiencies in *our process* — the loop between the human
and the AI. Where can we cut token use? Better prompting? Leverage other AI? Hybrid
local-LLM + Claude? Anything. Keep it current — checked the news for June 2026.

This is a meta-review (the machine that runs the machine), so it sits beside the daily
portfolio reviews rather than in the funnel docs.

---

## TL;DR — the five moves, ranked by leverage

1. **Trim the `CLAUDE.md` stack.** Our six `CLAUDE.md` files are 5k–7k tokens each and
   load *every turn of every session*. That is the single biggest recurring token bill we
   control. Cut each to a lean index (<1,500 tokens), push detail into linked files read
   on demand, and factor the duplicated House-Style block into one shared file. **~50–70%
   off baseline context cost, every session, zero behavior change.** (TD-16)
2. **Turn on prompt-cache discipline.** Daily routines re-read the same stable prefix
   (CLAUDE.md + portfolio + tech-debt). Cached reads cost ~10% of normal input. Keep the
   cached prefix *byte-stable* (no timestamps/dates inside it) and we get 60–90% off input
   on every repeat run. Combined with batch (below), the docs report up to ~95% off.
3. **Default routines to Sonnet 4.6, not Opus.** Opus 4.8 is 5× Sonnet's price
   ($5/$25 vs $3/$15 per MTok). This routine — web research + synthesis — is Sonnet work.
   Reserve Opus for genuine deep reasoning / hairy refactors. Our *own* router already
   encodes this (`cloud-code` = Sonnet); apply the same rule to the Claude Code routines.
4. **Stop paying Opus for the daily review.** The portfolio review has run daily for ~2
   weeks and produced near-identical "nothing shipped" output (≈5–6 KB each). That is a
   daily frontier-model run re-deriving deterministic state. Compute the state-check with
   a script; only wake the LLM when state actually changed. (TD-15)
5. **Re-tier the router's cloud fallback.** `cloud-overflow` = Opus 4.8 means a snappy
   `local-fast` miss fails over to our most expensive brain. Tier it: fast→Haiku,
   smart→Sonnet, reasoning→Opus. Cheaper *and* faster. (folds into TD-14 work)

---

## Where the tokens actually go (and where they don't)

The 2026 consensus — Anthropic's own context-engineering guidance, GitHub, Glean — is blunt:
**in agentic systems, trimming prompt wording barely moves the needle.** Cost accumulates in
bloated standing context, unmanaged message history, tool-output bloat, and retry loops. So
the wins below are architectural, not "write shorter sentences."

| Driver | Our exposure | Fix |
| ------ | ------------ | --- |
| Standing context loaded every turn | 6× `CLAUDE.md`, 5k–7k tokens each; House-Style block duplicated verbatim in all 6 | Lean index + on-demand links + one shared `HOUSE-STYLE.md` (TD-16) |
| Re-reading stable files each run | portfolio.md, tech-debt.md, decisions.md pulled fresh every routine | Prompt caching on the stable prefix; keep it byte-stable |
| Frontier model on routine work | This Opus session; daily Opus review | Sonnet default; deterministic pre-check (TD-15) |
| Tool-output bloat in context | large file reads, full CLAUDE.md echoed | Read only the needed slice; subagents return *condensed* summaries |
| Expensive failover | `cloud-overflow` = Opus | Per-tier fallback (Haiku/Sonnet/Opus) |

**What is already right** (keep doing): `tools/check-docs.py` does link-integrity with **zero
LLM tokens** — that is exactly the pattern to extend. The LiteLLM router is local-first with a
privacy gate. Embeddings/RAG run local. The reasoning ladder offloads heavy R1 to a rented GPU
instead of cooking the t630. This is a genuinely good hybrid spine.

---

## Hybrid local-LLM + Claude — the honest split

The web's 2026 numbers are real (one fintech cut LLM spend 83% by routing simple work local;
hybrid routing commonly lands 60–80% savings) **but they don't transfer to our hardware for
this kind of work.** The t630 (4-core Carrizo, no GPU offload) tops out at 1.5–7B models — fine
for classification, extraction, embeddings, and privacy-sensitive DNS-adjacent jobs; **too weak
for cross-repo reasoning, code, or research synthesis.** So the split that fits us:

- **Local (t630):** anything *sensitive + simple + high-volume* — embeddings, tagging, the
  privacy-pinned path. Already built.
- **Rented GPU (on-demand):** heavy reasoning bursts, then power it off. Already designed.
- **Claude API:** reasoning, code, synthesis, anything customer-facing in quality. Where the
  routines live. **The gap is that we apply local-first discipline to the router but not to
  the Claude routines** — they default to Opus, don't dedupe, and re-read fat context. Items
  1–5 close that gap.

Do **not** chase "run it all local" — at our scale a $489 GPU offsets a $60–100/mo bill in
5–8 months only if you're running enough volume to saturate it, which we are not. The lever is
spending the Claude budget *well*, not eliminating it.

---

## Prompting — the CEO's brief is the worked example

The brief that triggered this review is a textbook efficiency anti-pattern, so I'll use it as
the teaching case (with respect — open-ended is the right instinct for *discovery*, just
expensive as a *standing* instruction):

> "Locate inefficiencies… Anything you could possibly think of… ANYTHING that could help…
> Search the web… Check the news… If THIS prompt is inefficient then also let me know."

Why it's costly: "anything / everything" forces broad scanning and maximal output;
no scope, no budget, no output target, no done-condition. Per the research, vague asks
("improve this codebase") trigger wide reads; specific asks keep the agent narrow.

A tighter version of the same request:

> *"Audit our AI process for token waste. Scope: the `CLAUDE.md` stack, the daily review
> routine, and the LiteLLM fallback tiers. For each, give the fix and the rough % saved.
> One web search for any June-2026 pricing/feature change. Output: ≤1 page + tech-debt
> entries. Skip anything under ~5% savings."*

Same intent, bounded cost, checkable result. **General rules for our routines:**
- Name the scope and the files. Set an output ceiling ("≤1 page", "≤5 bullets").
- State a done-condition and a floor ("skip anything under X").
- Paste-by-reference: put long inputs in a file and say "read it," never paste into the prompt
  (pasted text is re-processed every subsequent turn).
- One routine = one job. Stack questions = stacked scans.

---

## June 2026 — what's current (so we don't optimize against stale facts)

- **Opus 4.8** (launched 2026-05-28): $5/$25 per MTok; Fast Mode dropped to $10/$50.
  **Sonnet 4.6** $3/$15; **Haiku 4.5** $1/$5. Opus/Sonnet support 1M context at flat rate.
- **Prompt caching:** cached input ≈ **10%** of normal (90% off). Pays off after ~3 reads in
  the 5-min window, ~5 reads in the 1-hr window.
- **Batch API:** **50% off** all models for non-interactive work — relevant when we render
  many statements at once (Stage 06 at scale).
- **Caching + batch stack to ~95% off** input on the right workloads.
- Pitfall confirmed: a timestamp inside a cached prefix busts the cache every call. Keep dates
  out of cached `CLAUDE.md`/portfolio prefixes.

---

## Recommended actions (this is the deliverable)

| # | Action | Owner | Effort | Est. saving |
| - | ------ | ----- | ------ | ----------- |
| 1 | Trim 6× `CLAUDE.md` to lean index; shared `HOUSE-STYLE.md` (TD-16) | NARF | M | 50–70% standing context |
| 2 | Keep cached prefix byte-stable; rely on prompt caching | NARF | S | 60–90% repeat input |
| 3 | Set routine default model = Sonnet 4.6; Opus opt-in | CEO | S | ~40% per routine |
| 4 | Deterministic pre-check for daily review; LLM only on change (TD-15) | NARF | M | ~90% of review runs |
| 5 | Per-tier router fallbacks (folds into TD-14) | NARF | S | overflow cost + latency |
| 6 | Adopt the bounded-prompt template above for all routines | CEO | S | fewer wide scans |

Items 1, 4, 5, 6 need no t630 access — they're edits in these repos. Item 3 is a routine-config
toggle. Item 2 is automatic once item 1 makes the prefix lean and stable.

---

## Sources (June 2026)

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) · [Claude Code — Manage costs](https://code.claude.com/docs/en/costs)
- [Finout — Anthropic API pricing 2026 (caching, batch)](https://www.finout.io/blog/anthropic-api-pricing)
- [KDnuggets — 7 ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) · [Firecrawl — 12 ways to cut token consumption](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Glean — Optimizing token efficiency in agentic systems](https://www.glean.com/perspectives/how-to-optimize-token-efficiency-in-agentic-systems) · [GitHub — Improving token efficiency in agentic workflows](https://github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/)
- [SitePoint — Hybrid cloud-local LLM architecture 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [MindStudio — Local AI with Claude Code](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
