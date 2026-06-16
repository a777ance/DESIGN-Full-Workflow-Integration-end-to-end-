# Process efficiency — user ↔ AI token & workflow review

Living doc. Newest review at the top (house style). Each review locates inefficiencies in how
we work *with* the AI (Claude Code / the API), estimates the cost, and proposes a fix. Concrete
actionable items are also filed in [`tech-debt.md`](tech-debt.md) so NARF sees them every session.

---

## 2026-06-16 — first pass (token tax, hybrid routing, prompting)

**TL;DR.** The single biggest waste isn't how we prompt — it's the **standing context tax**.
Every session loads **~14,600 tokens of `CLAUDE.md`** (six repos) plus a **10-file session
protocol** before a word of the task is read. That's a fixed cost paid on every turn, every run,
every repo — including this scheduled routine. Fix the standing cost first; it dwarfs prompt
wording. We *already own* the second-biggest lever (a local LLM router on the t630) and aren't
pointing the cheap work at it.

### 1. The standing context tax (highest leverage — fix first)

Measured 2026-06-16, the locally-cloned repos:

| `CLAUDE.md` | ~tokens | What's in it that isn't always needed |
| ----------- | ------: | ------------------------------------- |
| `localDNS` | ~5,100 | The full **Deploy-paths table** + the **nftables deploy checklist** (a config dump) — only relevant when deploying that box |
| `DESIGN` | ~4,500 | Full funnel diagram, stage map, money-flow tables — reference, not per-session briefing |
| `MARKETING` | ~2,700 | Full roles/money-flow tables (duplicated from DESIGN) |
| `customers` | ~1,000 | |
| `claude-code-homelab` | ~720 | |
| `azure-lab` | ~570 | A *stub* repo — still pays a 570-token tax |
| **Total** | **~14,600** | Loaded into **every** session regardless of which repo the task touches |

Industry guidance lands in the same place: a 5k-token `CLAUDE.md` is "a 5k-token tax on every
turn"; the rule of thumb is **keep it under ~200 lines** ([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage),
[Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)). `localDNS` and
`DESIGN` are ~280 and ~250 lines.

**Why it compounds:** prompt caching (Claude Code does this automatically) makes the *repeat*
reads ~10% of input price — good — but (a) the **first** read each session still pays full
freight and writes the cache at 1.25×, (b) a 14.6k-token prefix still consumes the model's
attention budget on every turn, and (c) the worst offenders carry content (deploy tables, config
dumps) that is pure noise for 90% of tasks.

**Fixes, in order of leverage:**

1. **Split each `CLAUDE.md` into a thin briefing + a deep reference.** Keep `CLAUDE.md` to the
   ~40-line "what this is / the rules / where to look" core; move the Deploy-paths table, the
   nftables checklist, the funnel/stage/money tables into `README.md` / `network-context.md`
   (where most already have a copy) and link to them. The agent reads the reference *only when
   the task needs it*. Realistic target: **~14.6k → ~4–5k tokens** of standing context.
2. **De-duplicate the house-style block.** The ~20-line "ordering & typography" section is
   copied **verbatim into all seven repos** (~140 lines total). Put it once in a `STYLE.md` (or
   the homelab repo, which is the meta/setup repo) and link to it. Saves ~120 lines × the repos
   that load together.
3. **Trim the stub.** `azure-lab`'s `CLAUDE.md` pays a 570-token tax to say "scope undefined."
   Two lines + a link to the ADR would do.
4. **Reconsider the reverse-ordering house rules as an *AI*-cost item.** "Newest-first logs"
   is fine. But **"reverse the blocks, keep the steps"** for walkthroughs and **"alphabetical
   Z→A"** actively cost tokens *and* accuracy: the agent (and any human) must re-derive the
   intended order every time, and it's a frequent source of "did I order this right?" churn. This
   is a house-style decision, not mine to make — flagging it as a real, recurring friction cost.

### 2. We own a hybrid local/cloud router — and aren't using it for the cheap work

`localDNS/10-ai-orchestration` already runs **LiteLLM + Ollama on the t630** with a capability
ladder (`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason`, cloud overflow → Claude). This
is *exactly* the architecture the 2026 guides recommend — most teams have to build it
([SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[BuildMVPfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).
The reported win is **60–80% cost reduction** by keeping the 60–70% of *simple* requests local
and reserving frontier models for the ~10% that need them.

The gap: **the router fronts Open WebUI, not our actual high-volume AI consumer — these Claude
Code sessions and the daily CTO/CFO reviews.** Those go straight to the Claude API at Opus rates.

What to do (don't need the toggle app — this is plumbing):
- **Point bulk, low-stakes jobs at the local tier:** doc-link checks (`tools/check-docs.py` is
  deterministic already — keep it code, not LLM), draft generation, classification, summarizing
  a diff, the *first* pass of a daily digest. Ollama on the t630 handles these at ~$0.
- **Reserve Claude (Opus) for what actually needs frontier reasoning:** architecture decisions,
  the security/correctness review, ambiguous multi-repo work.
- **Caveat — honor the privacy gate.** [`tech-debt.md` TD-14](tech-debt.md) already flags that a
  `sensitive`-tagged task can fail over from `local-reason` to `cloud-overflow` (Claude). Any
  "route more to local" push must fix TD-14 first (fail *closed* to a local-only chain), or we'd
  widen a privacy leak while chasing a cost saving.

### 3. Model selection, batching, caching (Claude-side)

- **Don't run routine maintenance on Opus.** This very routine is on `opus-4-8` ($5/$25 per
  MTok). Doc upkeep, link-checking, status digests, and first-draft generation are Haiku 4.5
  ($1/$5) or Sonnet 4.6 ($3/$15) work — **3–5× cheaper input, 5× cheaper output**. Reserve Opus
  for design/decision/review. (Model facts via the bundled `claude-api` skill, cached 2026-06-04.)
- **Batch the non-interactive generation.** The daily `reviews/` files are produced unattended on
  a cadence — a textbook fit for the **Message Batches API: 50% off**, results within the hour.
- **Caching already helps; protect it.** The shared `CLAUDE.md` prefixes are stable, so cache
  reads are cheap — *as long as we don't invalidate the prefix.* Keep volatile content (dates,
  per-run IDs) **out** of `CLAUDE.md` and out of the front of prompts. (One real risk: the
  "Last updated: <date>" line in `portfolio.md` — fine there, but never let a timestamp creep
  into a `CLAUDE.md`.)
- **MCP tool definitions.** The GitHub MCP server exposes ~55 tools; loaded eagerly that's a
  large per-turn tax (industry reports cite up to ~18k tokens/turn for fat MCP setups). Good
  news: this harness already **defers** tool schemas (loads them on demand via search) — keep
  that on; don't pin the whole GitHub toolset into every session.

### 4. Session protocol overhead

`CLAUDE.md` instructs the agent to read, at session start, **4 CTO files** (portfolio, roadmap,
tech-debt, decisions) **+ 6 CFO files** (portfolio, decisions, metrics, runway, budget, context)
= **10 files before any task.** Most tasks need two of them. Make the protocol *conditional*:
"read `portfolio.md`; read the others only if the task touches that area." Same idea as the
context tax — load deep state on demand, not by ritual.

### 5. Prompting (smaller lever than the above, but real)

The triggering prompt for this review is a good worked example. Paraphrased: *"Locate
inefficiencies in our PROCESS … reduce token use? … better prompting? … ANYTHING … leveraging
other AI … hybrid local LLM … Search the web … Keep UP TO DATE … Check the news."*

What works: the intent is clear, and "search the web / stay current" is the right instinct (model
prices and Claude Code features move monthly — this doc's web sources are dated for that reason).

What costs tokens unnecessarily:
- **Unscoped.** "ANYTHING that could help" forces an exhaustive survey instead of a targeted
  answer — the model spends output enumerating possibilities to be safe. On Opus 4.6+, emphatic
  caps ("ANYTHING", "UP TO DATE") also tend to *over-trigger* exploration. Plain phrasing lands
  better and shorter.
- **No deliverable or "done" definition.** For an *unattended* routine this matters most: the
  run has nobody to ask "where should this go?" State the output location and the stop condition.

A tighter template for this kind of ask:

> Review our AI-usage cost. Focus on the standing context tax and model selection — skip
> anything that needs a code change. Check current best practices on the web (model pricing,
> Claude Code features). Write findings to `docs/ai-cto/process-efficiency.md`, add any
> actionable items to `tech-debt.md`, and notify me with the top 3. Don't refactor anything yet.

Same intent, ~60% fewer words, names the scope + deliverable + stop condition — so an unattended
run produces a durable artifact instead of a chat reply nobody reads.

### Sources (2026, web — verify periodically; this space moves fast)

- [KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Agensi — Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [systemprompt.io — Reduce Claude Code Costs 60% With Four Habits](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Claude Code Docs — Manage costs effectively](https://code.claude.com/docs/en/costs)
- [SitePoint — Hybrid Cloud-Local LLM: Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [MindStudio — Run Local AI Models with Claude Code to Cut Costs 10x](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [DEV — Claude API Cost Optimization: Caching, Batching, 60% Reduction](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)

Model pricing/feature facts (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5; Batches 50% off;
prompt caching ~0.1× read / 1.25× write) are from the bundled `claude-api` skill, cached 2026-06-04.
