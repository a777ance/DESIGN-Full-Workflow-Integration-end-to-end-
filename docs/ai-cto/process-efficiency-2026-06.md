# Process efficiency review — user ↔ AI workflow (2026-06-22)

NARF (AI CTO) review, requested by the founder: *"Locate inefficiencies in our PROCESS
between the user and the AI. Reduce token use. Better prompting. Leverage other AI. Run a
hybrid local LLM + Claude API. Keep up to date — check the news."*

This is a findings log; lead item is newest (house style). The recommendations are ordered
**by impact-per-effort**, biggest lever first.

---

## TL;DR — the five levers, ranked

| # | Lever | Effort | Est. saving | Status today |
| - | ----- | ------ | ----------- | ------------ |
| 1 | **Trim the seven `CLAUDE.md` files** (1,040 lines, loaded every session) | Low | up to ~90% of the *fixed* per-session context | Not done — files are dense narrative |
| 2 | **Route routine work to the local LLM** you already run (LiteLLM on the t630) | Low–Med | 60–80% on the 60–70% of tasks that are "simple" | Router exists; not used as a router |
| 3 | **Right-size the model per job** — stop running Opus 4.8 for monitoring sweeps | Low | 5× (Opus→Haiku) / 1.6× (Opus→Sonnet) on routine runs | Everything is on Opus 4.8 |
| 4 | **Prompt caching + Batch API** for the repeated/async paths (statements, link-checks) | Med | 90% on cached prefix, 50% on batched jobs | Not used |
| 5 | **Re-scope the recurring prompts** (incl. the one that spawned this) | Low | Stops paying full price on "nothing changed" runs | This prompt is open-ended |

---

## 1. The `CLAUDE.md` files are the single biggest fixed cost

Every Claude Code session in a repo loads that repo's entire `CLAUDE.md` **before** it reads
a line of code, and keeps it resident for the whole session. Current sizes:

```
326  localDNS/CLAUDE.md
295  DESIGN-…/CLAUDE.md
214  MARKETING/CLAUDE.md
 80  customers/CLAUDE.md
 75  claude-code-homelab/CLAUDE.md
 50  Azure-lab/CLAUDE.md   (a stub — fine)
1040  total
```

A widely-cited 2026 benchmark stripped a 3,847-token `CLAUDE.md` to 312 tokens and measured
**91.9% context reduction with no quality regression**
([agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)). The rule:
*if Claude could infer it from reading the codebase, or a senior dev could figure it out in
20 minutes, cut it.*

Our files violate this heavily — they are excellent **onboarding prose** but most of it is
narrative the model doesn't need re-fed every turn:

- The "why behind the funnel," the role/money-flow diagrams, the pest-control metaphor, the
  long known-issues tables → these belong in `README.md` / `workflow-context.md` (where much
  of it already lives) and should be **linked, not inlined**.
- Keep `CLAUDE.md` to: house-style rules, the stage→tool map, the "one master list" rule, the
  honesty rule, and pointers. Target **<400 tokens each**.
- The **house-style block is duplicated verbatim in all 7 repos**. Within a repo that's
  unavoidable; but it's ~20 lines × 7. Consider a terse canonical version.

Pair this with **`.claudeignore` discipline** — measured **85.5% context reduction** from
that alone ([firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)) — and
session hygiene: `/clear` between unrelated tasks, and lower the compaction threshold (set the
override to ~70% instead of waiting for the ~95% auto-trigger)
([analyticsvidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)).

## 2. We already run the hybrid stack — we're just not routing to it

`localDNS` stage 10 runs **LiteLLM (port 4040) + Open WebUI**, with a reasoning ladder:
`local-reason` (deepseek-r1:1.5b on the t630, cool) and `cloud-gpu-reason` (full R1 on a
rented GPU) falling over to `cloud-overflow`. The hybrid plumbing exists. What's missing is
**using it as the cost-routing layer it's built to be.**

Industry data for 2026: hybrid local/cloud workflows cut LLM cost **60–80% with minimal
quality impact**; one fintech went from $47k→$8k/mo (83%)
([buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026),
[mindstudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)).
The reason it works: **~60–70% of requests are "simple"** (classification, extraction,
formatting), 20–30% moderate, only ~10% need a frontier model
([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)).

Route to the **local model** the work that doesn't need Opus:
- Drafting "Handled For You" log entries from structured event data.
- First-pass triage of Uptime Kuma / packet-loss alerts (is this worth a human?).
- Summarizing logs, classifying leads, normalizing CRM fields, tagging.
- The `tools/check-docs.py` link check is already plain Python — keep it that way; don't spend
  a model on what a script does.

Reserve **Claude (API/Code)** for: statement-honesty review, architecture/ADR reasoning,
multi-repo refactors, and anything customer-facing where the "kept document" must be right.
Route on the three standard dimensions: **data sensitivity, task complexity, availability**.

## 3. Stop using Opus 4.8 as the default for routine runs

Current per-MTok pricing (from the Claude API reference, cached 2026-06-04):

| Model | Input | Output | Use it for |
| ----- | ----- | ------ | ---------- |
| Opus 4.8 | $5 | $25 | Hard reasoning, refactors, statement review |
| Sonnet 4.6 | $3 | $15 | Most "real work" — the default workhorse |
| Haiku 4.5 | $1 | $5 | Monitoring sweeps, classification, triage |

This very routine — a *monitoring/analysis sweep* — is running on **Opus 4.8 [1m]**. That is
5× the input / 5× the output cost of Haiku for a task that mostly fans out web searches and
summarizes. **Recurring routines should default to Haiku or Sonnet and escalate to Opus only
when a candidate finding warrants deep analysis.** In Claude Code, also lean on the **effort**
parameter — `low`/`medium` for routine sweeps cuts tokens (fewer tool calls, less preamble);
reserve `high`/`xhigh` for genuinely hard work.

News worth knowing (June 2026, [Anthropic](https://www.anthropic.com/news/claude-opus-4-8)):
- **Fast mode on Opus 4.8** is now ~3× cheaper than before and runs ~2.5× faster — good for
  interactive sessions, not for batch.
- **Opus 4.8 multimodal is ~61% cheaper per token than 4.7** for reasoning over PDFs/diagrams
  — relevant if we ever OCR/parse documents in the funnel.
- **Claude Fable 5 / Mythos 5** (new top tier, $10/$50) exist but are *above* Opus — **not**
  our cost path. Don't reach for them for this business.

## 4. Prompt caching + Batch API for the repeated and async paths

- **Prompt caching** cuts cached-input cost ~90% (cache write costs +25% once, every read
  after is −90%); break-even is **2 reads**
  ([finout](https://www.finout.io/blog/anthropic-api-pricing),
  [Anthropic docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).
  Anywhere an automation re-sends the same large prefix (a household data file, a fixed system
  prompt, a statement template), put a `cache_control` breakpoint on the stable prefix and put
  the per-request variable (the household, the month) *after* it. **Audit for silent
  cache-busters**: `datetime.now()` in a prompt, unsorted JSON, a varying tool list — any of
  those invalidate the whole cache. Verify with `cache_read_input_tokens > 0`.
- **Batch API = 50% off**, all models, for anything not latency-sensitive. The **monthly
  statement run** is the textbook case: generate the whole book in one batch overnight.
  Caching + batch on the repeated portion stacks toward **~95% off**.

## 5. Better prompting — including the prompt that triggered this run

The request that launched this routine was, paraphrased: *"Find inefficiencies… reduce
tokens… better prompting… leverage other AI… hybrid… ANYTHING that could help. Search the
web… keep UP TO DATE day by day… check the news. Thanks!"*

It's warm and clear in intent, but as a **recurring** prompt it's expensive and unfocused:

1. **It mixes a one-time audit with an ongoing monitor.** "Audit our setup" should run *once*
   (this report). "What changed in the AI ecosystem" is the recurring part — and the ecosystem
   shifts weekly at most, not "day by day." Running a full open-ended survey daily pays max
   tokens to re-derive the same findings.
2. **No success criterion and no memory of the last run.** A good routine stays *silent* when
   nothing changed — but this prompt can't tell "all quiet" from "new finding" because it has
   nothing to diff against. Fix: have it **read this report and only notify on deltas**.
3. **"ANYTHING that could help" maximizes scope → maximizes tokens.** Open-ended scope is the
   enemy of a cheap routine.
4. **It can't measure our actual inefficiency** — it has no token logs, no Anthropic Console
   usage export, no per-repo session data. So it can only *theorize*. If we want measured
   findings, feed it the usage export.

**Recommended rewrite (recurring digest version):**

> *Weekly. Read `docs/ai-cto/process-efficiency-*.md` (latest). Check Anthropic's release
> notes and 2–3 reputable sources for changes since that date that would (a) cut our token
> cost, (b) add a cheaper model/feature we should adopt, or (c) deprecate something we use.
> Use Haiku, effort=low. If nothing material changed, send no notification. If something did,
> append a dated delta entry and notify with the one change and its expected $ impact.*

That version is cheap, idempotent, self-silencing, and escalates to Opus only when it finds
something worth a deep look. Keep the broad "audit everything" prompt for an explicit
**quarterly** run.

---

## Adopt-now feature checklist (all current in the API as of 2026-06)

- [ ] Trim all `CLAUDE.md` to pointers + rules (<400 tokens each); add `.claudeignore`.
- [ ] Turn LiteLLM into the real cost-router: simple→local, hard→Claude.
- [ ] Default recurring routines to Haiku/Sonnet + `effort: low`; escalate on findings.
- [ ] `cache_control` on every reused prefix (statement template, household file, system).
- [ ] Move the monthly statement build to the **Batch API**.
- [ ] **Context editing** (clear stale tool results) / **compaction** for long agent runs.
- [ ] **Subagents** for genuine fan-out (scan-all-repos), on Haiku — but note subagent-heavy
      runs cost ~7× tokens; 3–5 concurrent is the sweet spot
      ([cloudzero](https://www.cloudzero.com/blog/claude-code-agents/)).
- [ ] Give the recurring routine **memory** (this file) so it reports deltas, not the world.

## Sources

- [Reduce Claude Code token usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 ways to cut token consumption — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [23 token-saving tips — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid cloud-local architecture guide — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid workflow cost optimization — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run local models with Claude Code — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Anthropic API pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code agents / subagent token cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8)
