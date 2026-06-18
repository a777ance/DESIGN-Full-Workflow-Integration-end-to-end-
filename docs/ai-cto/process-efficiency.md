# Process efficiency — cutting token cost in how we work with Claude

How we (the founder + the AI roles NARF/ZORT) actually spend tokens, where it leaks, and
the cheaper way to get the same work done. Researched 2026-06-18; the LLM market moves
weekly, so the "current prices / current news" section is dated and should be re-checked
before acting on the numbers.

This is about **process** — the loop between a human and the model — not about product
features. Sources are linked at the bottom.

---

## TL;DR — the five biggest leaks, ranked by what they cost us

| # | Leak | Why it costs | The fix | Effort |
| - | ---- | ------------ | ------- | ------ |
| 1 | **Every session front-loads ~10 files + 6 CLAUDE.md files before any work** | NARF's "read these 4 at session start" + ZORT's "read these 6" + ~10.7K tokens of always-loaded CLAUDE.md = a large fixed cost paid on *every* session, most of it irrelevant to the task at hand | Make session-start reading *conditional* ("read X **only when** the task touches money/roadmap"), not unconditional. Trim CLAUDE.md to the ~200-line budget. | Low |
| 2 | **The same boilerplate is duplicated across 6 CLAUDE.md files** | The 30-line house-style block, the "three repos, one business" table, and the money-flow diagram are copy-pasted verbatim. We pay for every copy, every session it loads. | Keep house style in ONE file; have the others link to it. Keep repo-specific facts local. | Low |
| 3 | **Open-ended, kitchen-sink prompts (this task's own prompt is the example)** | "Find ANYTHING that could help, search the web, check the news, thanks!" has no scope, no budget, no output target — so the model fans out maximally and burns tokens deciding what you meant. | Scope + budget + output shape. Template below. | Low |
| 4 | **The hybrid local-LLM rig we already built (localDNS stage 10) is barely used for real work** | LiteLLM + the reasoning ladder + Open WebUI already exist on the t630. Mechanical/privacy-sensitive sub-tasks still go to the paid cloud model. Industry reports 60–80% cost cuts from routing the simple 60–70% of tasks local. | Route classify/extract/format/summarize + anything touching real customer data to the local model; reserve Claude for reasoning. | Medium |
| 5 | **Scheduled routines run open-ended on the top-tier model** | This very run is an open-ended "research everything" task on Opus 4.8 (1M ctx) — the most expensive way to run a recurring job. | Narrow the routine, run it weekly not daily, run it on Haiku/Sonnet, and cache the static research. | Low |

Teams applying the lean-CLAUDE.md + conditional-context + model-routing playbook together
report **40–85% token reductions** ([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage),
[agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)). We are
leaving most of that on the table.

---

## 1. The fixed cost we pay before typing a word

A CLAUDE.md is loaded into context on **every turn of every session** — a 5,000-token file
costs 5,000 tokens before you ask anything
([buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)).
Anthropic's own guidance is to keep it **under ~200 lines, essentials only**
([Claude Code docs — costs](https://code.claude.com/docs/en/costs)).

Where we stand today (measured 2026-06-18):

| Repo CLAUDE.md | Lines | ≈ tokens |
| -------------- | ----: | -------: |
| localDNS | 326 | ~3,600 |
| DESIGN (this repo) | 295 | ~3,500 |
| MARKETING | 214 | ~1,900 |
| customers | 80 | ~750 |
| claude-code-homelab | 75 | ~490 |
| Azure-lab | 50 | ~420 |
| **Total** | **1,040** | **~10,700** |

Because all seven repos are checked out under one workspace, a session can pull in *all six*
CLAUDE.md files at start — ~10.7K tokens of standing context, most of it about repos the
current task never touches.

**Then it gets worse on top of that.** This repo's CLAUDE.md instructs:

- NARF: "At session start, read 4 files" (portfolio, roadmap, tech-debt, decisions)
- ZORT: "At session start, read 6 files" (+ MARKETING/context.md)

An obedient agent therefore opens **~10 more files before doing anything** — whether or not
the task is about money or roadmap. That is the single largest, most repeated waste in the
whole process.

**Fixes (cheapest first):**

1. **Make session-start reads conditional.** Change "At session start, read X" →
   "**When the task touches finances**, read the ZORT files; **when it touches cross-repo
   priorities**, read portfolio.md." The agent then loads only what it needs.
2. **De-duplicate the boilerplate.** The house-style block (~30 lines) is identical in all
   six files. Put it in one canonical file (e.g. `docs/house-style.md`) and have each
   CLAUDE.md link to it in one line. Same for the "three repos, one business" table and the
   money-flow diagram (duplicated between DESIGN and MARKETING).
3. **Trim to the 200-line budget.** localDNS (326) and DESIGN (295) are the priorities. Move
   the long tables (full deploy-path table, full stage map) into README and have CLAUDE.md
   point to them — CLAUDE.md should be the *index*, not the *encyclopedia*.

---

## 2. Prompt-cache hygiene (free money we're probably dropping)

Claude caches identical request *prefixes*: a cache read costs ~10% of a normal input token,
a cache write ~25% more, so anything you send unchanged more than twice starts paying for
itself ([Anthropic prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[knightli.com](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)).
With June-2026 pricing, a cached input token on the top tier is **$1/M vs $10/M standard — a
90% saving** ([finout](https://www.finout.io/blog/anthropic-api-pricing)).

The cache only helps if the **prefix stays stable**. What breaks it:

- **Switching models mid-session.** The cache is keyed per model — build context on Opus then
  switch to Sonnet and the whole prefix is re-billed. Pick a model per session and stay.
- **Editing CLAUDE.md, or installing/removing MCP servers or Skills mid-session.** Each
  invalidates the cached prefix. Don't use CLAUDE.md as a scratchpad.
- **Heads up:** there was a March-2026 caching bug that inflated tokens 10–20× silently; watch
  the usage meter after Anthropic-side changes ([buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)).

Practical rule for us: **one model per session, stable CLAUDE.md, `/compact` long sessions**
(compacting shrinks the prefix that gets re-sent each turn).

---

## 3. Use the local LLM rig we already own

We already built the hard part. localDNS **stage 10** runs LiteLLM (the router), a reasoning
ladder (`local-reason` on the t630 CPU, `cloud-gpu-reason` on a rented GPU, `cloud-overflow`
to Claude), and Open WebUI. The industry pattern that produces 60–80% cost cuts is exactly
this: an intelligent routing layer that sends the **simple 60–70% of tasks** (classify,
extract, format, summarize) to a local model and reserves the frontier model for the ~10% that
needs real reasoning ([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).

What we should be routing **local**, today:

- **Anything touching real customer data** (the `customers` repo: roster lookups, sidecar
  edits, "Handled For You" log summarizing). This is a *privacy* win as well as a cost win —
  it keeps real names and figures off the cloud entirely, which is squarely the honesty/privacy
  posture the repos already insist on.
- **Mechanical doc work**: summarizing logs, first-pass drafting, reformatting, extracting
  fields from a statement JSON.
- **The cheap classification steps** in any future stage-11 automation.

Reserve Claude (cloud) for: architecture decisions, multi-repo reasoning, anything where a
wrong answer is expensive.

> ⚠️ Tie-in to **TD-14**: the privacy fallback gap means a `sensitive` task on `local-reason`
> can fail *over* to `cloud-overflow` (Claude cloud) if the local model is down. Fix TD-14
> (fail closed to a local-only chain) **before** you start routing real customer data through
> the rig, or the cost/privacy win has a hole in it.

---

## 4. Right-size the model, and don't use an LLM where a script will do

- **Model tiers (June 2026):** Haiku 4.5 ~$1/M in, Sonnet mid, Opus 4.8 $5/$25 per M, Fable 5
  $10/M ([aipricing.guru](https://www.aipricing.guru/anthropic-pricing/),
  [silicondata](https://www.silicondata.com/use-cases/anthropic-claude-api-pricing-2026/)).
  Haiku is ~25× cheaper than Opus per token. Use Opus/Fable for architecture; Sonnet for most
  coding; **Haiku for mechanical subagents** (`model: haiku` in the subagent config).
- **Subagents cut context but cost tokens.** Delegating verbose work (test output, log
  trawling, broad file search) to a subagent keeps the noise out of the main thread — but a
  subagent-heavy workflow can use **~7× the tokens** of a single thread because each carries
  its own context ([nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/)). Use
  them for genuine verbose fan-out, not as a default.
- **`check-docs.py` is the model to copy.** It validates every internal link with plain Python
  — zero tokens. The honesty checks (statement numbers must be measured), schema validation on
  `roster.json`, and link-checking are all deterministic: keep doing them as scripts, never as
  LLM calls. **The cheapest token is the one you never send.**

---

## 5. The prompt that launched this task — a worked critique

The instruction was, in essence: *"Locate inefficiencies. ANYTHING that could help. Search the
web. Check the news. Keep UP TO DATE. Thanks!"*

It got the job done, but it's the textbook **expensive prompt**: no scope, no token budget, no
defined output, and several maximalist verbs ("ANYTHING", "anything you could possibly think
of") that push the model to fan out as widely as possible — which is precisely what runs up a
bill. For a **scheduled routine** that re-runs on its own, an unbounded prompt means unbounded
recurring spend.

A tighter version that would cost a fraction and return the same value:

```
Audit our Claude process for token waste. Scope: CLAUDE.md sizes, session-start
context loading, and local-vs-cloud routing. Skip anything we've covered before.
Output: a ranked table of the top 5 fixes with effort estimates, max ~1 page.
Do up to 4 web searches only if current prices/news would change a recommendation.
Append findings to docs/ai-cto/process-efficiency.md.
```

What changed: a **scope** (three named areas), a **search budget** (≤4), an **output shape**
(ranked table, ~1 page), a **skip rule** (no re-covering old ground), and a **destination**.
That's the general template — *scope · budget · output shape · skip rule · destination* — and
it applies to almost every prompt we write.

---

## 6. Current prices & news (dated 2026-06-18 — re-verify before acting)

- **Models:** Fable 5 is the new GA top tier (1M context, 128k output, always-on adaptive
  thinking); Opus 4.8 shipped 2026-05-28. Fast Mode on Opus dropped to $10/$50 per M (was
  $30/$150 on 4.7).
- **Caching:** cached input is ~10% of standard (90% saving) across tiers.
- **Watch item:** Anthropic **paused** the June-15 Agent-SDK credit-split change — subscription
  usage continues as before, with promised advance notice before any future change
  ([digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026),
  [releasebot](https://releasebot.io/updates/anthropic)). No action needed now; revisit when
  they re-announce.
- **Platform:** Managed Agents now support **scheduled deployments** and **vault env-var
  credentials** — relevant if we move these routines onto managed scheduling.

---

## Sources

- [Claude Code docs — Manage costs](https://code.claude.com/docs/en/costs)
- [Anthropic — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code Token Optimization (buildtolaunch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Token-saving guide: models, MCP, CLAUDE.md, Skills & cache (knightli)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [7 practical ways to reduce token usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to reduce Claude Code token usage (agensi.io)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code subagents guide (nimbalyst)](https://nimbalyst.com/blog/claude-code-subagents-guide/)
- [Hybrid cloud-local LLM architecture guide (sitepoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid cloud-local AI workflow cost optimization (buildmvpfast)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run local AI models with Claude Code (mindstudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Anthropic API pricing 2026 (finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Anthropic Claude API pricing 2026 (aipricing.guru)](https://www.aipricing.guru/anthropic-pricing/)
- [Anthropic pricing — Silicon Data](https://www.silicondata.com/use-cases/anthropic-claude-api-pricing-2026/)
- [Claude credit overhaul paused June 15 (digitalapplied)](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Anthropic release notes (releasebot)](https://releasebot.io/updates/anthropic)
