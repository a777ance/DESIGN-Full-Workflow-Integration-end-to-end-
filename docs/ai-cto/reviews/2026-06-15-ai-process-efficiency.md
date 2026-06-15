# NARF — review — 2026-06-15 — human↔AI process efficiency

**Question asked:** find inefficiencies in *the process between the user and the AI* —
reduce token use, improve prompting, leverage other AI (hybrid local LLM + Claude API),
keep current with best practice. And: critique the prompt that asked for this.

Time-based sections are newest-first per house style. Sources are linked inline and
collected at the foot.

---

## 0. The finding that changes today's math (act first)

**Today — 2026-06-15 — is the day Anthropic splits autonomous usage onto a separate,
metered credit.** As of this date, `claude -p`, the Claude Agent SDK, Claude Code GitHub
Actions, and third-party/automated agents no longer draw on the interactive subscription
session/weekly limits. They draw on a **separate monthly credit** ($20 Pro / $100 Max-5x /
$200 Max-20x), **metered at full API rates, no rollover** ([codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/),
[digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)).

**Why it matters to us specifically:** this very task is a *scheduled routine* — exactly the
autonomous category that moved. Every routine run, every GitHub-Action invocation, and every
`claude -p` call now spends real metered dollars at API rates, not "free" subscription quota.
The cost-reduction work below stopped being housekeeping and became a budget line as of today.

**Immediate actions:**
1. Inventory what runs autonomously (scheduled routines, Actions, any SDK scripts) and decide
   which are worth full-API-rate dollars. Kill or slow the ones that aren't.
2. Set/track the new credit as a ZORT budget line (see `docs/ai-cfo/budget.md`). No rollover
   means unspent credit is lost and overruns bill on top — both want watching.
3. Push the cheap, deterministic autonomous legwork onto the local Odin stack (§3) so the
   metered credit is spent only where Claude's reasoning actually earns it.

---

## 1. Where our process leaks tokens (ranked by leverage)

### 1.1 CLAUDE.md is large and the house-style block is duplicated 6×
Measured today (word-count × 4/3 ≈ tokens):

| File | est. tokens loaded **every session** |
| ---- | ------ |
| `localDNS/CLAUDE.md` | ~3,640 |
| `DESIGN-…/CLAUDE.md` | ~3,480 |
| `MARKETING/CLAUDE.md` | ~1,930 |
| `customers/CLAUDE.md` | ~750 |
| `claude-code-homelab/CLAUDE.md` | ~490 |
| `Azure-lab/CLAUDE.md` | ~420 |

A CLAUDE.md is read **before you type a word** — a 3,600-token file is a 3,600-token tax on
every session in that repo ([buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization),
[knightli](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)).
The identical ~370-word **"House style: ordering & typography"** block is pasted verbatim into
six of them. That is both a token cost *and* a maintenance cost (a one-line style change is a
six-file edit — and they already drift).

**Recommendation (keeps the "read this first" philosophy intact):**
- Trim each CLAUDE.md to the *navigational* core — what the repo is, the invariants, and a
  pointer table — and let detail live in the files it already points to (README, context.md,
  deploy tables). The big `localDNS` deploy-paths table and per-issue known-issues list are
  reference material looked up on demand, not orientation needed every session; move them
  behind a one-line "see §C in README / DEPLOY.md" pointer.
- De-duplicate house style: keep the canonical copy in **one** file (e.g.
  `DESIGN-…/docs/house-style.md`) and have each repo's CLAUDE.md carry a 2-line summary + link
  rather than the full block. Within a repo, Claude Code honours `@path` imports in CLAUDE.md,
  so the summary can `@`-import the canonical file instead of restating it.
- Target: get the two heavy files under ~1,500 tokens of always-on context. That's ~2,000
  tokens saved per session on the two repos we touch most — and it compounds across every
  autonomous run now that those are metered.

### 1.2 Session-start read protocols pull a fixed, large context regardless of task
The NARF protocol reads `portfolio.md` + spoke `context.md` + `roadmap.md` + `tech-debt.md` +
`decisions.md`; the ZORT protocol adds **six** more financial files. For a task that touches
one stage, most of that is dead weight in the window. Loading everything "at session start out
of reflex" is exactly the anti-pattern the 2026 guidance calls out ([agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)).

**Recommendation:** make the protocol *tiered*. Always read the hub index (portfolio.md, which
is the snapshot). Then load only the spoke files the task names. Keep `decisions.md`/`metrics.md`
as look-up-when-relevant, not read-on-entry. State this in the protocol so it's followed.

### 1.3 Prompt-cache cold-starts on infrequent automated runs
Claude Code caches the stable prefix (system prompt + CLAUDE.md + early context), but the cache
TTL is short (minutes) and **connecting/disconnecting an MCP server mid-session wipes the whole
cache** ([mindstudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens),
[code.claude.com](https://code.claude.com/docs/en/prompt-caching)). A routine that fires hours
apart pays a *cold* cache write every time, and the duplicated/bloated CLAUDE.md (§1.1) makes
that write bigger. Two levers: (a) keep the stable prefix small (so §1.1 pays off twice), and
(b) don't toggle MCP servers inside a run.

### 1.4 Model tier — Opus everywhere, including for legwork
Routine status-checks, file sorting, formatting, link-checking, and simple searches don't need
Opus or even Sonnet — Haiku handles them, and subagents inherit the parent model unless told
otherwise ([nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/),
[kdnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)).
This routine ran on Opus to do web fetches and string edits — most of that was Haiku-grade work.

**Recommendation:** for scheduled/legwork routines, pin a cheaper model (Haiku) and reserve
Opus for the reasoning-heavy passes. Delegate file-heavy exploration to **subagents** so their
verbose tool output stays out of the main window — but only for genuinely large fan-outs;
subagents add prompt/tool-definition overhead and are *wasteful* for small one-shot actions
([nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/)).

---

## 2. Better prompting — including the prompt that triggered this run

**Yes, the triggering prompt is itself inefficient**, and for a *scheduled* routine that's
costly because the inefficiency repeats on every fire. What worked against it:
- **Unbounded scope** — "ANYTHING that could help," "search the web," "check the news," "keep
  UP TO DATE." No budget, no stop condition. An agent will fan out web searches every run.
- **No output contract** — where should findings land? What format? When is it "done"? Left
  open, the result risks living only in a chat nobody reads (the core failure mode of a routine).
- **Not incremental** — a daily/weekly "find inefficiencies" with no "since last run" anchor
  re-derives the same report each time and re-pays for the same web research.

**A tighter version of the same ask:**
> *Monthly: review our human↔AI process for cost/efficiency. Budget: ≤8 web lookups, ≤1 Opus
> pass. Only report what changed since the last review in `docs/ai-cto/reviews/` — append a
> dated delta, don't restate. Notify only if there's a dollar-affecting change or a new
> best-practice worth adopting; otherwise stay silent. Output: one dated file + a 2-line
> notification.*

That keeps every good intent (stay current, find waste) while bounding cost and guaranteeing
the output is durable and the notification is earned.

General prompting wins that apply to us ([mindstudio](https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage)):
state the deliverable and its location up front; give a budget; say what *not* to do; prefer
"append the delta" over "produce the report" for anything recurring.

---

## 3. Leverage the AI we already built — Odin (the LiteLLM hybrid router)

The user's own question ("running a hybrid, local LLM and Claude API") describes a stack we
**already designed and have not deployed**: `localDNS/10-ai-orchestration/` — LiteLLM front
door, local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` 7b), a reasoning ladder, and
`cloud-overflow` → Claude as failover. The 2026 best-practice literature is describing exactly
this pattern and reporting **60–80% cost reductions** by running simple tasks locally and
escalating only complex ones to Claude ([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[dev.to](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b),
[mindstudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)).

**How to actually capture that here:**
- **Route by data-sensitivity + complexity + token-count** (the three-pillar rule): cheap,
  bounded, non-reasoning jobs (log triage, classification, draft-formatting, doc-link
  pre-checks, summarising stats files) → local Ollama; long-context, strict-format, or
  multi-step reasoning → Claude. Open models degrade exactly at >~3K-token context, strict
  output formats, and multi-step reasoning ([dev.to](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b))
  — so route *to* Claude precisely there and nowhere else.
- **Honest constraint (our own repo says so):** the t630 is a CPU-bound AMD Carrizo, memory-
  bandwidth limited, no usable GPU offload. Local tiers are fine for *async/batch* legwork,
  sluggish for interactive chat. So use Odin for the unattended, latency-tolerant routine work
  — which is precisely the autonomous category that just got metered (§0). Good fit.
- **Deploy it.** It's reference code today, not running (portfolio status: "landed as reference
  code + config; not yet deployed"). Deploying it is what converts the design into the savings
  the literature reports — and it shares the t630 access trip that already gates the nftables
  layer and the first real Statement (Blocker #1). One visit, three unlocks.
- **Mind the documented privacy-fallback gap:** both reasoning tiers fall back to
  `cloud-overflow` (Claude) when local is down, so "local-only" can silently reroute to the
  cloud. For anything that must stay on our infra, drop the `cloud-overflow` fallback so it
  fails closed (already flagged in the router README + tech-debt).

---

## 4. Staying current (the "keep UP TO DATE" ask), cheaply

Don't re-research the world every run. Cheapest durable pattern:
- Keep this file as the living baseline; future reviews **append a dated delta** only.
- Watch a *small* set of primary sources rather than open web every time: Anthropic's Claude
  Code docs "costs" + "prompt-caching" pages, and the release notes. Re-derive from those, not
  from scratch.
- The fast-moving facts to recheck (they changed twice in ~6 weeks): the 5-hour/weekly limits
  (doubled 2026-05-06) and the autonomous-billing split (2026-06-15). Both are pricing/limit
  facts — recheck them when a routine's cost looks off, not on a calendar.

---

## 5. Concrete checklist (in priority order)

1. **[§0] Inventory autonomous usage; set the new metered credit as a ZORT budget line.** Today.
2. **[§1.1] Trim `localDNS` + `DESIGN` CLAUDE.md to navigational cores; de-duplicate house style
   to one canonical file + `@`-import.** ~2K tokens/session saved on the hot repos.
3. **[§1.4] Pin scheduled/legwork routines to Haiku; reserve Opus for reasoning passes.**
4. **[§1.2] Make NARF/ZORT session-start reads tiered (hub index always; spokes on demand).**
5. **[§3] Deploy Odin on the t630 (same trip as nftables) and route bounded legwork local.**
6. **[§2] Rewrite recurring routine prompts with budgets, an output contract, and "append the
   delta" semantics.**

Items 2, 3, 4, 6 are doc/config edits we can do without box access. Items 1 and 5 need the
founder (budget decision; t630 visit).

---

## Sources

- Anthropic June-15 billing split: [codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/),
  [digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026),
  [morphllm — limits](https://www.morphllm.com/claude-code-usage-limits),
  [morphllm — pricing](https://www.morphllm.com/claude-code-pricing)
- Token / cache / CLAUDE.md: [buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization),
  [knightli](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/),
  [mindstudio — caching](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens),
  [code.claude.com — caching](https://code.claude.com/docs/en/prompt-caching),
  [code.claude.com — costs](https://code.claude.com/docs/en/costs)
- Subagents / skills / model tier: [nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/),
  [kdnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage),
  [agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage),
  [mindstudio — manage usage](https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage)
- Hybrid local+cloud routing: [sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
  [dev.to](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b),
  [mindstudio — local models](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs),
  [buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
