# Process efficiency — user↔AI loop

How we spend tokens working with Claude, and where to spend fewer for the same or better
output. Written 2026-06-14 by the AI-CTO routine. Ordered by impact (biggest lever first),
not by date. Re-run the "best-practices refresh" cadence at the bottom rather than re-deriving
this from scratch each time.

**The one-line finding:** the loop is paying frontier-model rates to re-read a large, mostly
irrelevant standing context on every turn, while the cheap-and-local infrastructure we already
own (the t630 LiteLLM router) sits unused for the bulk work. The fixes below are ordered so the
first three capture ~80% of the savings.

---

## 1. Trim the standing context (biggest, cheapest win)

Every session injects **all seven repo `CLAUDE.md` files** — ~8,600 words ≈ **~11K tokens**
before a single useful instruction — plus the harness system prompt. On a scheduled routine
that runs daily, that prefix is paid *every run, forever*, mostly for repos the run never
touches.

| Lever | Action | Est. effect |
| ----- | ------ | ----------- |
| **Slim the `CLAUDE.md`s** | They've grown into full manuals. `localDNS` (2,728 w) and `DESIGN` (2,608 w) carry full deploy-path tables and known-issues tables that belong in `README.md`/`tech-debt.md` and should be *read on demand*, not preloaded. Anthropic's own guidance: keep `CLAUDE.md` a short pointer. Target ≤ ~500 words each. | −60–70% of the standing prefix |
| **Scope repos per task** | A run that only touches `localDNS` shouldn't load `MARKETING`, `customers`, `Azure-lab`, etc. Narrow the session's repo scope to what the task needs. | −1 to −5 CLAUDE.mds per run |
| **Don't duplicate house-style** | The identical ~250-word "House style: ordering & typography" block is pasted into 6 of 7 files. Put it once in the hub and link it. | −1,500 w across the set |

The house-style rules themselves add friction with no business payoff: reverse-chronological
logs, Z→A alphabetics, and "reverse the blocks" walkthroughs make the model spend reasoning
budget re-ordering content and make every reader (human or AI) work harder to scan. Worth
asking whether the aesthetic is worth the recurring tax.

## 2. Confirm prompt caching is on, and structure for it

Prompt caching cuts **cached input by ~90%** and is "the single largest cost-reduction technique
in LLM APIs in 2026." It applies *perfectly* to a scheduled routine because the prefix (system
prompt + CLAUDE.md + tool schemas) is identical across runs.

- Claude Code enables caching by default — **verify** it's actually hitting on these runs (watch
  for `cache_read` tokens dominating input). If the giant CLAUDE.md prefix is stable run-to-run,
  it should be a cache *read*, not a fresh write, every time after the first.
- Keep the stable stuff (instructions, schemas) at the **front**; put the volatile task at the
  **end**. Reordering CLAUDE.md content frequently *busts* the cache — another reason to freeze
  and slim it.
- Use **batch processing** (−50%) for anything non-interactive and bulk (e.g. rendering a month
  of statements, classifying a lead list).

## 3. Use the hybrid local+cloud router we already built

`localDNS` stage 10 already ships a LiteLLM gateway + a reasoning ladder (`local-reason` =
deepseek-r1:1.5b on the t630, `cloud-gpu-reason`, `cloud-overflow`). Industry hybrid setups cut
LLM spend **60–80%** by serving routine work locally and reserving Claude for hard reasoning.
We have the pipes — we're just not routing the cheap work through them.

- **Route by task, not by habit.** Doc-link checking (`tools/check-docs.py` triage), house-style
  reformatting, summarizing a log, classifying leads, drafting boilerplate → local model or
  **Haiku 4.5** ($1/$5 per M). Reserve **Opus 4.8** ($5/$25) for genuine architecture/ambiguity.
  Opus is **5× the input / 5× the output** of Haiku — paying it for formatting is pure waste.
- **This very routine** is configured on Opus 4.8. A "scan + notify" job is mostly retrieval and
  summarization → run it on **Sonnet 4.6** or Haiku and escalate to Opus only when a finding
  needs deep analysis.
- ⚠️ **Privacy guardrail:** TD-14 is still open — a `sensitive`-tagged task can fail over from
  the local model to `cloud-overflow` (Claude cloud) because `allow_cloud=False` isn't enforced
  at the LiteLLM failover layer. Fix the fail-closed path **before** leaning harder on routing,
  or sensitive lookups leak.

## 4. Delegate heavy reading to subagents / use the right skill

- **Subagents** run in their own context window; their verbose file-dumps and tool output don't
  land in (or get re-sent with) the main thread. Use them for "read many files, return the
  conclusion" — exactly the shape of audits and cross-repo sweeps. Skills load only when needed
  (reported ~40% overhead cut on code-gen).
- There is already a **`deep-research`** skill built for fan-out web research + verification, and
  a **`code-review`** skill — prefer these over hand-rolling a research/review prompt each time.
- **Cap tool output** (~8K limit) and prefer targeted reads over whole-file reads.

## 5. Tighten the session loop

- **One focused task per session.** Long threads re-send the whole history every turn —
  the biggest hidden drain. `/compact` to summarize, `/clear` between unrelated tasks,
  `/recap` to resume without replaying.
- **Merge related asks** into one instruction so the model reads the background once.
- **Right cadence for routines.** A daily "research best practices" routine re-runs the same web
  searches and burns tokens for diminishing returns. Make refresh routines **weekly/monthly**,
  and have them **diff against the last run** so they notify only on genuinely new findings
  (silent when nothing changed) — that's the whole point of a watch routine.

---

## On the prompt that requested this (the meta-finding)

The triggering prompt is itself a good example of what costs tokens for less output. Verbatim it
was open-ended and unbounded: *"Locate inefficiencies… Is there a better way… Anything you could
possibly think of… ANYTHING that could help… Search the web… Keep UP TO DATE… Check the news."*

2026 prompting research is blunt about why that's expensive: reasoning quality starts degrading
past ~3K tokens of prompt, attention scales quadratically, and **vague, maximal prompts produce
vaguer, broader, more expensive output** — detailed/specific prompts cut the iteration rate
~in half, and structured-output requests drop it from 38% to 12%. An unbounded "find anything"
invites maximal fan-out (this run did 6 web searches + read 7 CLAUDE.mds) with no stopping rule.

**A tighter version of the same request:**

> Audit our Claude usage for cost. Focus on: (1) the standing context loaded each session, (2)
> model choice per task, (3) whether we're using the local LiteLLM router. Give ≤5
> recommendations ranked by $ saved, each with a concrete action. Use web search only to confirm
> 2026 pricing/best-practice claims. Skip anything we already do. ~1 page.

That keeps scope, sets an output budget, names where to look, and gives a stop condition — same
answer, a fraction of the tokens. Enthusiasm markers ("ANYTHING!", repeated "Thanks!", heavy
caps) add tokens without signal; they're friendly but free to drop.

---

## Sources (2026)

- [KDnuggets — 7 ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Analytics Vidhya — 23 Claude Code token-saving tips](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Web2MD — Prompt caching cost optimization (80% savings)](https://web2md.org/blog/prompt-caching-cost-optimization-guide-2026)
- [LeanOps — AI agents burn 50× more tokens than chats](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
- [SitePoint — Hybrid cloud-local LLM architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [buildmvpfast — Hybrid cloud-local AI workflow cost optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [eesel — Claude Code multiple agent systems 2026 guide](https://www.eesel.ai/blog/claude-code-multiple-agent-systems-complete-2026-guide)
- [newline — Claude skills and subagents reduce prompt bloat](https://www.newline.co/@Dipen/claude-skills-and-subagents-reduce-prompt-bloat--f2920804)
- [Promptessor — Prompt engineering best practices 2026](https://promptessor.com/blog/prompt-engineering-best-practices-2026)
- [Finout — Anthropic API pricing 2026](https://www.finout.io/blog/anthropic-api-pricing)
- [pricepertoken — Claude Opus 4.8 pricing](https://pricepertoken.com/pricing-page/model/anthropic-claude-opus-4.8)
