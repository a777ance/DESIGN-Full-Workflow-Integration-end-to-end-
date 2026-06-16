# NARF — review — 2026-06-16 — process & token efficiency

**Ask (founder, scheduled routine):** find inefficiencies in *the process between the
user and the AI* — token use, prompting, leveraging other AI, the hybrid local/cloud
setup. Keep it current. And critique the prompt that asked for this.

I checked our own setup (`localDNS/10-ai-orchestration/config.yaml`, the CLAUDE.md files,
the AI-CTO/CFO session protocols) against current best practice (June 2026). Good news
first: **we already run the architecture everyone else is writing blog posts about** — a
LiteLLM front door, local Ollama tiers as the default, cloud as overflow, a privacy gate.
The inefficiencies are not in the design. They're in three places we can fix cheaply.

---

## The headline

**We built the hybrid router and then left the two biggest, cheapest token wins switched
off:** prompt caching on the cloud tiers, and a lean session-context budget. These are
config edits, not engineering. Industry numbers put the combined win at **60–90% off
input-token cost** ([prompt caching](https://www.anthropic.com/news/prompt-caching),
[2026 playbook](https://www.programstrategyhq.com/post/techniques-to-reduce-ai-token-usage-the-2026-playbook-for-cutting-costs-without-losing-quality)).
We pay full freight on both right now.

---

## Top fixes, ranked by impact ÷ effort

### 1. Turn on prompt caching for the cloud tiers — biggest single win
**Where:** `localDNS/10-ai-orchestration/config.yaml`, the `cloud-*` models.
**Problem:** none of our Anthropic-backed tiers (`cloud-overflow`, `cloud-explore`,
`cloud-code`, `cloud-vision`) set a `cache_control` breakpoint. Every call re-pays full
input price for the same large, stable prefix (system prompt + CLAUDE.md + repo context).
**Fix:** LiteLLM supports injecting cache breakpoints without touching callers —
`cache_control_injection_points` in the model params, anchored at the end of the system
block. First call writes the cache (full price); every call within the TTL reads it at
**~10% of input cost**. Economics clear at **3+ reads in the 5-min window** (or 5+ for the
1-hour cache) — a normal working session blows past that.
**Caveat that bites us specifically:** *editing the cached prefix resets the cache.* Our
house-style churn (we touch CLAUDE.md and the portfolio constantly) silently invalidates
the cache mid-session and forces full reprocessing on the next turn. See fix #2.
Refs: [Claude prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
[how Claude Code uses caching](https://code.claude.com/docs/en/prompt-caching).

### 2. Cut the fixed per-session context tax
**Where:** the CLAUDE.md files + the AI-CTO/CFO session protocols.
**Problem:** every session pays a large fixed cost *before any work starts*. The DESIGN
CLAUDE.md is ~300 lines; on top of it, NARF's protocol mandates reading
`portfolio.md` + `roadmap.md` + `tech-debt.md` + `decisions.md`, and ZORT's mandates **six**
more files (`portfolio`, `decisions`, `metrics`, `runway`, `budget`, + MARKETING context).
That's a fat, mostly-unchanging payload re-sent on a routine that may only need one fact.
Every added line is reprocessed each message ([Claude Code best practices](https://code.claude.com/docs/en/best-practices),
[agensi: 8 methods](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)).
**Fixes:**
- **Lazy-load the spokes.** Read the *hub* (`portfolio.md`) always; read a spoke's
  `context.md` only when the session actually touches that repo. Don't load all six ZORT
  files unless the task is financial.
- **Trim CLAUDE.md to an index.** Keep the briefing + pointers; push the long tables
  (deploy-path table, full known-issues list) into linked files loaded on demand. They're
  reference, not every-message context.
- **Batch CLAUDE.md / portfolio edits to session boundaries**, not mid-session — protects
  the cache from #1. Treat CLAUDE.md "like a config file you only touch between sessions"
  ([mindstudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)).

### 3. Right-size the default model — stop paying Opus for Haiku work
**Where:** `config.yaml` cloud tiers.
**Problem:** `cloud-overflow`, `cloud-explore`, and `cloud-vision` all point at
`claude-opus-4-8` — our most expensive model — and `cloud-overflow` is the catch-all
fallback for *everything*. So a local tier failing over for a trivial task lands on Opus.
**Fix:** default `cloud-overflow` to `claude-sonnet-4-6` (or Haiku for the genuinely
light stuff); keep Opus reserved for `cloud-explore` / the hardest reasoning only.
Intelligent model routing is the second of the three big cost levers; stacked with caching
and tight output budgets it takes typical workloads to **20–30% of unoptimized cost**
([programstrategyhq](https://www.programstrategyhq.com/post/techniques-to-reduce-ai-token-usage-the-2026-playbook-for-cutting-costs-without-losing-quality),
[LiteLLM routing](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)).
*Note: this interacts with the open privacy gap TD-14 — fix that fallback to fail closed
before leaning harder on cloud-overflow.*

### 4. Push routine work onto the local tier we already pay nothing for
We treat local as the privacy default but still hand the cloud a lot of low-stakes prose
(commit messages, doc-lint, changelog summaries, first drafts). Those are exactly what
`local-fast`/`local-smart` on the t630 handle "within acceptable quality thresholds" — the
canonical hybrid split is **simple/sensitive → local, complex → cloud**, saving 60–80%
([sitepoint hybrid guide](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).
Bias the dispatcher local-first for *light + non-sensitive*, not only for sensitive.

### 5. Use subagents for the file-sweeps these reviews keep doing
NARF's daily review re-reads many files into the main context to verify a couple of facts.
That verbose reading should go to a **subagent with its own context window** — it returns
the conclusion, the raw file dumps never touch the main thread. This is the single most
recommended Claude Code context move in 2026, and Anthropic just shipped nested subagents +
better memory curation ("Dreaming") this month
([context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
[June 2026 features](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)).

### 6. Context hygiene we should make habitual
`/clear` between unrelated tasks; let compaction/auto-context-editing clear **stale tool
results** (once a file's been read and acted on, the raw bytes don't need to ride along);
keep a progress file + git commits as checkpoints so a compacted session can rehydrate from
the summary. We already do the last one well — `portfolio.md` + `CHANGELOG.md` *are* the
recommended pattern ([Anthropic context-engineering cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)).

---

## Staying current (the founder asked us to keep this fresh)
This space moves weekly. Cheap way to not fall behind: skim
[Releasebot — Anthropic](https://releasebot.io/updates/anthropic) and the
[Claude Code best-practices doc](https://code.claude.com/docs/en/best-practices) once a
week, and re-run *this* review monthly against `config.yaml`. New since we last looked:
nested subagents, context-editing/memory tooling, and the "Dreaming" cross-session memory
curation.

---

## On the prompt that asked for this
Honest feedback, since it was requested. The prompt was effective at getting a broad scan,
but it was **token-expensive by design** and would have been sharper scoped:

- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of"
  invites the model to explore wide and long — more tokens, lower signal-per-token. The
  most efficient prompts name a target and a boundary.
- **No baseline.** It asks us to cut token use without saying what we spend, where the pain
  is, or what "the process" concretely covers. The model has to *guess* the cost model,
  which wastes a research budget reconstructing context we already hold.
- **No success criterion or ranking ask.** "Find inefficiencies" with no "give me the top
  3 ranked by ROI" tends to produce an exhaustive survey instead of a decision.
- **Four asks in one** (token reduction + prompting + hybrid local/cloud + news). Each is a
  clean separate run; bundled, they share and dilute one context.

A tighter version that would cost less and return more:
> "Audit `localDNS/config.yaml` and our CLAUDE.md/session protocols for token waste.
> Goal: cut cloud API spend. Give me the top 3 fixes ranked by savings ÷ effort, with the
> exact config change for each. Note anything that's changed in Claude Code this month.
> Skip anything that needs numbers I haven't given you — flag it and ask."

Note the last clause — it turns "guess my context" into "ask me," which is the cheapest
token you'll ever spend. And for a recurring routine like this one, a saved prompt /
slash-command beats retyping an open-ended brief each time.

---

## Recommended actions (for the portfolio log)
1. Add `cache_control` breakpoints to the four `cloud-*` tiers in `config.yaml`. *(P2,
   localDNS — biggest $ win)*
2. Make the AI-CTO/CFO session protocols lazy-load spokes; trim CLAUDE.md long tables to
   linked on-demand files. *(P2, DESIGN + all repos)*
3. Re-point `cloud-overflow` to `claude-sonnet-4-6`; reserve Opus for `cloud-explore`.
   *(P2, localDNS — do after TD-14 is failed-closed)*
4. Bias the dispatcher local-first for light + non-sensitive tasks. *(P3, localDNS)*

None of these are deploy-blocked — they're repo edits. The t630 deploy (TD-03) and the
TD-14 privacy fallback remain the Phase-1 headlines; this is cost hygiene that rides
alongside them.
