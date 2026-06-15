# Process efficiency — the user↔AI loop

How we spend tokens working with Claude across the A777ance repos, and where the waste is.
Prioritized by payback (cheapest, highest-impact first). Findings dated; this page goes stale
fast — recheck the sourced links quarterly.

**Last reviewed: 2026-06-15.**

---

## TL;DR — the five wins, in order

1. **Trim the CLAUDE.md files.** They are loaded on *every* turn of *every* session. Ours are
   ~4.5k (DESIGN) and ~5.1k (localDNS) tokens each — paid before anyone types a word. Target
   <1.5k; push detail into linked files Claude reads on demand. **Biggest single win.**
2. **Stop front-loading session reads.** Our CLAUDE.md tells every session to read 4–10 hub docs
   at start (NARF: 4 files, ZORT: 6). Make those *on-demand* ("read X *when* the task touches
   finance"), not unconditional.
3. **Turn on prompt caching for the API path** (LiteLLM / the statement + agent jobs). Cache reads
   are ~10% of input price; a stable system prompt + CLAUDE.md cached saves 60–90% of input cost.
4. **Route by task size — we already have the ladder, use it deliberately.** Local model for
   trivial/sensitive, Haiku for simple, Sonnet default, Opus only for deep work. Don't run
   routine scheduled routines on Opus.
5. **Adopt the new context tools** (context editing + memory + tool-search). Anthropic measured
   84% token reduction on long agent runs and 85% on tool definitions. Free wins for our
   long-running routines.

---

## 1. CLAUDE.md is a per-turn tax (P1, do first)

A CLAUDE.md is re-sent with every single turn. Measured today:

| Repo | ~tokens loaded every turn |
| ---- | ------------------------- |
| localDNS | ~5,100 |
| DESIGN | ~4,500 |
| MARKETING | ~2,665 |
| customers | ~1,033 |
| claude-code-homelab | ~724 |
| Azure-lab | ~573 |

A 5k-token file across a 40-turn session is ~200k tokens spent *just re-reading the briefing*.
Most of our CLAUDE.md content (the funnel diagram, the full stage map, money-flow ASCII, the
verification walkthrough) is reference material the model needs *occasionally*, not every turn.

**Fix:** keep CLAUDE.md to a tight orientation (what the repo is, the hard rules, where to look)
and move the rest into the files already linked under "Further reading." The model reads them
when a task needs them. Target each CLAUDE.md under ~1.5k tokens. The house-style block is
duplicated verbatim in all six CLAUDE.md files — factor it to one `docs/house-style.md` and link
it. ([Claude Code token tips, KDnuggets 2026](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage);
[buildtolaunch 2026](https://buildtolaunch.substack.com/p/claude-code-token-optimization))

## 2. Unconditional session-start reads (P1)

CLAUDE.md §5/§6 instruct every session to read 4 (NARF) or 6 (ZORT) hub docs at start. A DNS
session doesn't need `runway.md`. Reword to conditional triggers ("read the CFO portfolio *when
the task touches money*"). Same idea as the harness's own tool-search: pull context on demand,
don't front-load it. ([Anthropic, effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))

## 3. Prompt caching on the API/router path (P1)

Anywhere we hit the Claude API directly — the statement-build jobs, the LiteLLM `cloud-overflow`
tier, any agent loop — enable prompt caching on the stable prefix (system prompt + CLAUDE.md +
schema). First call writes the cache at full price; reads within the TTL cost ~10% of input.
Rule of thumb: worth it at 3+ reads inside a 5-min window, 5+ for the 1-hour cache.

**Anti-pattern to avoid:** never put a live timestamp ("Current time: …Z") inside the cached
prefix — it busts the cache every call. Truncate to the day or move it out.
([Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching);
[Finout pricing guide 2026](https://www.finout.io/blog/anthropic-api-pricing);
[AI Magicx 2026](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026))

## 4. Deliberate model routing — we already own the ladder (P2)

`localDNS/10-ai-orchestration/config.yaml` already has `local-reason` / `cloud-gpu-reason` /
`cloud-overflow`. The discipline to add:

- **Default scheduled routines to a cheaper tier.** Opus costs ~5× Sonnet per token; most
  routine/monitoring work doesn't need it. Reserve Opus for genuine deep analysis.
- **Local-first for trivial + sensitive.** Classification, short summaries, "does this file
  exist" — the t630's `deepseek-r1:1.5b` handles these cool. (Note: **TD-14** — the privacy
  fail-open in the router — must be fixed before "sensitive→local" is actually a guarantee.)
- **Validate before retry.** Agentic retries re-bill the full token cost; check output structure
  before re-running the whole agent at premium pricing.

Hybrid local/cloud routing is reported to cut LLM spend 60–80% with little quality loss.
([sitepoint hybrid guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/);
[MindStudio: local models with Claude Code](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs);
[Cleveroad enterprise guide 2026](https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/))

## 5. New context-management tools (P2)

Public-beta features worth wiring into long-running routines:

- **Context editing** — auto-clears stale tool results/thinking from the window: **−84% tokens**
  on a 100-turn eval, and lets runs finish that would otherwise hit the context wall.
- **Memory tool** — writes essential facts to files before clearing them, so long jobs survive
  context limits and learn across sessions. Natural fit for our monthly statement runs.
- **Tool Search Tool** — discovers tools on demand instead of loading every definition upfront:
  **−85%** on tool-definition tokens. (This session already uses it — the deferred-tool list.)

([Anthropic context management](https://www.anthropic.com/news/context-management);
[context editing docs](https://platform.claude.com/docs/en/build-with-claude/context-editing);
[advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use))

## 6. In-session habits (P3, ongoing)

- **`/compact` and `/recap`** instead of long-running threads — every new message re-reads the
  whole history. Start fresh per task; `/recap` (Apr 2026) resumes without replaying.
- **Batch related asks** into one message rather than a drip of follow-ups — each follow-up
  reprocesses the full context.
- **Batch API** for non-real-time jobs (the monthly statement run, doc checks) — 50% off.
- **Don't paste; point.** Reference `file:line`; let the model read what it needs rather than
  pasting big blobs into the prompt.
([Analytics Vidhya: 23 tips 2026](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/);
[Finout 2026](https://www.finout.io/blog/anthropic-api-pricing))

---

## On prompting (and a note on the request that generated this doc)

Best-practice prompting in 2026 still reduces to: **a prompt is a small spec.** State the goal,
the constraints, the output format, and what "done" looks like. Specific prompts beat vague ones
by ~35% on clarity, and reasoning quality starts degrading past ~3k tokens of prompt — so be
specific *and* tight, not just long. ([Promptessor 2026](https://promptessor.com/blog/prompt-engineering-best-practices-2026);
[orq.ai 2026](https://orq.ai/blog/what-is-the-best-way-to-think-of-prompt-engineering))

The brief that produced this page — *"find inefficiencies… anything that could help… search the
web… anything"* — is itself the anti-pattern: open-ended, no success criterion, no scope, no
output format. It invites broad, expensive exploration and makes "done" undefinable. A tighter
version would have cost less and returned a sharper answer:

> "Audit our user↔AI token spend. Give the top 5 fixes ranked by $ saved, each with the concrete
> change to make in our repos and a rough % saving. Cite 2026 sources. Output: a one-page table.
> Skip anything that needs new paid infra."

That version names the deliverable (ranked table), the bound (top 5, no new paid infra), and the
success test (ranked by savings, cited) — so the model can stop when it's met them instead of
exploring "anything."

---

## Sources

- Anthropic — [Managing context (context editing + memory)](https://www.anthropic.com/news/context-management) ·
  [Context editing docs](https://platform.claude.com/docs/en/build-with-claude/context-editing) ·
  [Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use) ·
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) ·
  [Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Pricing/caching — [Finout 2026](https://www.finout.io/blog/anthropic-api-pricing) ·
  [AI Magicx 2026](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- Hybrid local/cloud — [SitePoint 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
  [MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) ·
  [Cleveroad 2026](https://www.cleveroad.com/blog/claude-api-cost-optimization-enterprise/)
- Claude Code token tips — [KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) ·
  [Analytics Vidhya 2026](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/) ·
  [buildtolaunch 2026](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- Prompting — [Promptessor 2026](https://promptessor.com/blog/prompt-engineering-best-practices-2026) ·
  [orq.ai 2026](https://orq.ai/blog/what-is-the-best-way-to-think-of-prompt-engineering)
