# Process Efficiency — Claude usage audit

How we (the founder) and the AI (Claude / the homelab LLMs) work together, and where that
process wastes tokens, money, or attention. Findings are prioritized P1→P3 like `tech-debt.md`;
within a priority they read newest-first per house style. This file is the **diff target** for
the recurring efficiency routine — a future run should report only what changed against it.

**Last run:** 2026-06-20 (first pass — model `claude-opus-4-8`, scheduled routine).
**Headline:** the biggest waste is observable in every session — standing context (the six
`CLAUDE.md` files + the mandatory session-start reading lists) is loaded in full before any work
starts. Trimming it and making the reads conditional is the single highest-leverage fix.

---

## The numbers (measured this run)

- **6 `CLAUDE.md` files total ~8,030 words ≈ ~10.7k tokens.** This routine had all six in scope,
  so it paid the whole bill at once. Per-file: DESIGN 2,608 w · localDNS 2,728 w · MARKETING
  1,445 w · customers 562 w · homelab 371 w · azure 316 w.
- **The "House style: ordering & typography" block (~250 w) is copy-pasted verbatim into 6
  files** — ~1,500 words of pure duplication that every multi-repo session re-loads.
- **Session-start protocols force-read more on top:** NARF reads 4 files (portfolio 9.1 KB,
  decisions 8.2 KB, tech-debt 2.6 KB, roadmap 2.2 KB); ZORT reads 6. A single DESIGN session can
  load **~18–25k tokens of standing context before doing one useful thing** — every session.

---

## Findings

### P1 — Standing-context bloat (CLAUDE.md + forced session reads)  ·  effort: M
**Problem.** Every session pays ~10–25k input tokens of always-on context, much of it
irrelevant to the task at hand, and the house-style block is duplicated 6×. Best practice is the
opposite: keep `CLAUDE.md` lean; it loads before the code, so every word is a tax.
**Fix.**
1. Trim each `CLAUDE.md` to a lean core (what/rules/where-to-look-next); push detail into
   `README`/context files that are read **on demand**, not at boot. Target ~40% smaller.
2. De-duplicate house style: keep it in **one** canonical file (e.g. `localDNS` or this hub) and
   have the others link to it, or shrink to a 5-bullet stub + link.
3. Make session-start reads **conditional**: "read `portfolio.md`; read the spoke/CFO files only
   if the task touches that area" instead of "always read all 6."
**Saving.** ~8–15k input tokens/session, every session, across both NARF and ZORT.

### P1 — Privacy hole in the existing hybrid router intersects "leverage other AI"  ·  see TD-14
**Problem.** You already run the hybrid you're asking about (LiteLLM reasoning ladder:
`local-reason` deepseek-r1:1.5b on the t630 → `cloud-gpu-reason` → `cloud-overflow` = Claude
cloud). But **TD-14**: a `sensitive`-tagged task can fail over from local to cloud if the local
model is down — it does not fail closed. Any *expansion* of hybrid routing must fix this first,
or "use more local AI for privacy" actively backfires.
**Fix.** Give `local-reason` a local-only fallback chain; enforce `allow_cloud=False` at the
LiteLLM failover layer. (Already tracked as TD-14, P1.)

### P2 — Wrong model tier for routines (Opus doing scan work)  ·  effort: S
**Problem.** This very routine — "keep up to date / check the news" — ran on **Opus 4.8** ($5/$25
per 1M). First-pass scanning and triage is a Haiku/local job; Opus/Fable should be reserved for
synthesis and code. Haiku 4.5 (~$1/1M in) is ~5× cheaper and fine for search/extract/classify.
**Fix.** Tier explicitly: route classify/extract/summarize-the-news to **local-reason or Haiku**,
escalate only architecture/code/final-synthesis to Opus. Extend the t630 ladder's philosophy to
the dev/CTO workflow, not just the homelab chat UI.
**Note on Fable 5.** Released 2026-06-09; $10/$50 (2× Opus). Free on Pro/Max/Team plans only
through **2026-06-22**, then billed at API rates and it already burns plan allowance ~2× faster.
Do **not** default any routine to Fable — reserve it for the genuinely hardest reasoning.

### P2 — Prompt caching may be unused on our own API calls  ·  effort: S
**Problem.** Cached input is **~90% cheaper** (and lower latency). Our repeated session-start
prefix (CLAUDE.md + portfolio docs) is the textbook cacheable block — especially for a *daily
scheduled routine* that re-reads the same large context. 1-hour TTL is now available on Opus 4.8
/ Sonnet 4.5 / Haiku 4.5 (since Jan 2026).
**Fix.** For any script we write against the Claude API (and in the LiteLLM/Open WebUI configs),
set a cache breakpoint on the stable system prompt + standing docs. Claude Code does some of this
automatically; our own tooling likely does not.

### P2 — Deterministic rules spent as model tokens instead of hooks/CI  ·  effort: M
**Problem.** Several standing rules are deterministic and don't need the model to re-read and
re-reason them every session: "run `check-docs.py` before commit" (already CI, TD-11 ✓), "no
secrets in git", "newest-first / Z→A ordering". Hooks execute code that can't hallucinate and
cost no model tokens.
**Fix.** Encode the mechanical ones as hooks/pre-commit (e.g. a secret-scan hook, a docs-link
gate). Leave the judgement-heavy ones (voice, house-style nuance) as prose. Don't over-rotate —
full ordering lint is hard.

### P3 — Subagents + output caps for research fan-out  ·  effort: S
**Problem / fix.** Research that sweeps many files/sources should run in **subagents** (separate
context, optionally on Haiku) so the main thread stays lean — exactly how this run did its web
search. Cap tool output sizes so command/file dumps don't flood context. New `/recap` (Apr 2026)
summarizes a resumed session instead of replaying it.

### P3 — Drop "think step by step" scaffolding from any of our prompts  ·  effort: S
**Problem.** 2026 reasoning models (Opus 4.6+) think internally; the hand-written
"let's think step by step" trick now often **hurts** output. If any skill/prompt still injects
chain-of-thought scaffolding, remove it.

---

## Critique of the request that triggered this run

The founder asked whether the *prompt itself* was inefficient. Honest answer: good intent,
loose construction.

**Strengths.** Clear goal; explicitly invites currency ("keep up to date, check the news");
gives permission to range.

**Weaknesses (per 2026 practice: structure beats length; write success criteria + an output
contract).**
- **No success criteria / output contract.** "ANYTHING that could help… anything you could
  possibly think of" is unbounded — it invites token-expensive open-ended exploration with no
  defined "done."
- **Many sub-questions in one breath**, so they get answered unevenly.
- **Redundancy.** "Anything you could possibly think of." and "ANYTHING that could help." restate
  the same instruction.
- **Routine-blind.** As a *scheduled, unwatched* run it doesn't say where output should go, or the
  bar for pinging a phone. A daily "keep up to date" task should **diff against the last run** and
  surface only what's new — otherwise it re-reports the same advice and re-spends the tokens.

**Tightened template (drop-in):**
> Audit our Claude usage for cost/efficiency. Output **≤8 findings**, prioritized, each as:
> *Problem · Fix · Est. token/$ saving · Effort (S/M/L)*. Cover (1) standing context load,
> (2) prompt caching, (3) model tiering & local/cloud split, (4) prompt quality. Use web search
> only for what changed since **{last run date}**; report only what's **new** vs
> `docs/ai-cto/process-efficiency.md`. Write results there; notify me only on a P1.

That last clause (diff + notify-on-P1-only) is itself the biggest recurring-cost saver: it turns
a re-run from "redo the whole audit" into "report the delta."

---

## Sources (2026-06-20)

- Anthropic — [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Best practices for prompt engineering](https://claude.com/blog/best-practices-for-prompt-engineering)
- Claude Code — [Best practices](https://code.claude.com/docs/en/best-practices) · [KDnuggets: 7 ways to reduce token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) · [Analytics Vidhya: 23 token-saving tips](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- Hybrid local/cloud — [SitePoint: hybrid cloud-local LLM architecture (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [DigitalApplied: LLM model routing 2026](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- Pricing/news — [Finout: Anthropic API pricing 2026](https://www.finout.io/blog/anthropic-api-pricing) · [TechCrunch: Claude Fable 5 release](https://techcrunch.com/2026/06/09/anthropic-released-claude-fable-5-its-most-powerful-model-publicly-days-after-warning-ai-is-getting-too-dangerous/) · [Amnic: Opus 4.8 pricing](https://amnic.com/blogs/anthropic-api-pricing)
