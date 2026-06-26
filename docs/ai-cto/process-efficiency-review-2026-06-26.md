# Process-efficiency review — the user ↔ AI loop

**Date:** 2026-06-26 · **Author:** NARF (AI CTO) · **Scope:** how we work *with* Claude
(and other models), where tokens leak, and what to change. Requested by the founder:
"locate inefficiencies in our PROCESS… reduce token use… better prompting… leverage
other AI… hybrid local + Claude… keep up to date."

This is a one-time audit, not a daily review. Findings are grounded in our actual stack
(the `localDNS` LiteLLM router) and in current best practice as of June 2026 (sources at
the end). Re-check the dated items quarterly — this space moves weekly.

---

## TL;DR — ranked by (impact ÷ effort)

| # | Lever | Est. saving | Effort | Status today |
| - | ----- | ----------- | ------ | ------------ |
| 1 | **Prompt caching** on every repeated API call (router + any scripts) | **60–90% of input cost** | Half a day | Not wired — `config.yaml` has no `cache_control` |
| 2 | **Right-size the model**: default Sonnet, escalate to Opus only on hard work | Opus is **5× Sonnet**; ~50–70% of calls don't need it | Habit + 1 config line | Router defaults to Opus 4.8 on overflow |
| 3 | **Slim the seven `CLAUDE.md` files** — they load into *every* session | ~10–18k tokens/session of fixed overhead | One pass | Each is 200–400 lines; all 7 load regardless of repo |
| 4 | **Context hygiene**: `/clear` between tasks, subagents for verbose work | 30–50% per-message | Habit | Ad hoc |
| 5 | **Use the local tier we already built** as a pre-filter for cheap work | Drafts/summaries/classification at ~$0 | It's already deployed | Router exists; underused for real work |
| 6 | **Sharper prompts** (specific, motivated, example-led, one-shot) | Fewer round-trips = fewer full-context replays | Habit | This very request is the counter-example (§7) |

The single highest-leverage move is **#1 (caching)** because it's a one-time config change
that compounds on every subsequent call. Everything else is habit or a small edit.

---

## 1. Prompt caching — the biggest single lever (do this first)

A cache **hit costs 10% of the normal input price**. A 5-minute write costs 1.25×, so it
pays for itself after ~2–3 reads; a 1-hour write costs 2× and pays off after ~5 reads.
Done well this is **60–90% off input tokens** on any workload that re-sends a stable
prefix — which is *every* agentic loop, because the system prompt + tool defs + repo
context are re-sent on every turn.

**What to do:**
- In the LiteLLM router (`localDNS/10-ai-orchestration/config.yaml`), enable caching on the
  Anthropic backends. LiteLLM passes `cache_control` breakpoints through to Anthropic;
  mark the **system prompt** and any large, stable context block as the cached prefix.
- Put the **volatile** part (the actual user turn) *last*, after the cache breakpoint.
  Anti-patterns that silently break the cache: a timestamp, a per-call user id, or trailing
  whitespace *before* the breakpoint. Audit for those three first.
- **June 2026 gotcha:** Anthropic moved the default cache TTL from 60 min → **5 min**. For
  bursty interactive work that's fine; for a batch job that pauses >5 min between calls,
  request the **1-hour TTL** explicitly or the cache is cold every time. This change alone
  raised many teams' bills 30–60% without them noticing.
- Instrument the **cache-hit rate** (LiteLLM logs `cache_creation_input_tokens` vs
  `cache_read_input_tokens`). If reads aren't dwarfing writes, the breakpoint is wrong.

For Claude Code sessions specifically, caching is already on under the hood — the
actionable lever there is **not invalidating it**: avoid edits that rewrite early context,
and don't bounce models mid-task (a model switch starts a new cache).

---

## 2. Right-size the model — stop paying Opus rates for Sonnet work

Opus 4.8 is **$5 / $25** per M tokens (in/out); Sonnet is the speed/intelligence sweet
spot at a fraction of that. Industry telemetry: **60–70% of requests are "simple"**
(classify, extract, format, summarize), 20–30% moderate, only ~10% need a frontier model.

Our router currently makes **Opus 4.8 the overflow brain** (`cloud-overflow`,
`cloud-explore`, `cloud-vision` all = `claude-opus-4-8`). That's correct for the hardest
work and wrong as a *default*. Concretely:
- Keep `cloud-code` on **Sonnet 4.6** (already is) and make it the default cloud tier for
  build/diff/structured work. Escalate to Opus only for genuinely hard reasoning.
- In Claude Code: **start every session on Sonnet**, switch to Opus (`/model`) only when a
  task is actually deep. The habit matters more than any config.
- Batch, non-interactive jobs (e.g. generating statement copy for N households) → the
  Anthropic **Batch API** is **50% off**. Anything that doesn't need an answer *now*
  belongs there.

---

## 3. The seven `CLAUDE.md` files are a fixed tax on every session

Every Claude Code session in this portfolio loads **all seven** repo `CLAUDE.md` files
into context — I can see them in my own system prompt right now. They're thorough (good for
onboarding) but several are 200–400 lines, and the **House style block is duplicated
verbatim in all seven**. That's ~10–18k tokens of fixed overhead paid on *every* turn of
*every* session, in *every* repo, whether or not it's relevant.

**Fixes, in order of payoff:**
- Factor the shared **House style / typography** block into one short canonical file and
  have each `CLAUDE.md` link to it instead of restating it. (Saves the duplication ~6–7×.)
- Move the deep tables (full deploy-path maps, exhaustive known-issues) into `README.md` /
  `network-context.md` and leave `CLAUDE.md` as a **tight index that points to them**.
  Claude reads the detail on demand; it doesn't need it pre-loaded every turn.
- Target: each `CLAUDE.md` ≲ 120 lines of "what this is + where to look." The current files
  are closer to a manual than a briefing.

This is the cleanest win after caching because it's pure overhead — paid even on a one-line
question.

---

## 4. Context hygiene — cheap habits, real savings

- **`/clear` between unrelated tasks.** Cuts per-message cost 30–50% by dropping dead
  context. Don't carry a finished task's transcript into the next one.
- **Subagents for verbose work** (test output, log greps, broad file sweeps): the noise
  stays in the subagent; only a summary returns to the main thread. *Caveat:* subagents
  carry start-up overhead and each keeps its own context — for a tiny task they're *more*
  expensive, and parallel "agent teams" can burn ~7× a normal session. Use them when the
  saved main-context clutter is worth more than the overhead, not by reflex.
- **Be specific so Claude reads less.** A vague ask ("look at everything") triggers a broad
  file scan; a precise ask ("in `config.yaml`, change the overflow model") reads one file.
  Specificity *is* token economy.
- **Compaction** keeps long sessions alive, but a fresh `/clear` is cheaper than a compacted
  120k-token history. Prefer ending and restarting over endlessly compacting.

---

## 5. Leverage the hybrid stack we already built (it's underused)

We have a real asset most people are still trying to build: a **privacy-gated local→cloud
router** (`localDNS/10-ai-orchestration/`) — local Ollama tiers on the t630 (`local-fast`
qwen2.5:3b, `local-smart` 7b, `local-reason` deepseek-r1:1.5b, `local-embed`), a rented-GPU
tier for heavy reasoning, and Claude as overflow, with the Odin/LangGraph supervisor's
**deterministic privacy gate** pinning sensitive tasks local. Hybrid setups like this are
documented cutting **60–80% of LLM spend** by keeping the cheap 60–70% off the paid API.

We're paying for the box anyway, so **every task that runs locally is free at the margin.**
Push more of the cheap tier onto it:
- **Drafting & summarizing** internal docs, commit messages, changelog lines, statement
  prose first drafts → `local-smart`, then Claude only to polish the final customer-facing
  copy.
- **Classification/extraction** (tagging leads, parsing call notes into roster fields) →
  local. This is exactly the "simple 60%."
- **RAG over our own repos** via `local-embed` (Mímir's well) so Claude answers from
  retrieved snippets instead of us pasting whole files into context.
- Keep the **privacy gate** authoritative: customer PII and the roster never leave the box
  — that's a feature, not just a cost play. (Mirrors our own DNS split philosophy: sensitive
  stays home, bulk/low-sensitivity can go out encrypted.)

The discipline: **local drafts, Claude finishes.** Don't spend Opus tokens on a first pass
a 7B model can rough out.

---

## 6. Better prompting — fewer, sharper turns

Each clarifying round-trip replays the whole context, so a prompt that lands in one shot is
a *token* win, not just a UX one. The 2026 best-practice that actually moves the needle:
- **Specificity over adjectives.** "5 bullets, ≤15 words each" beats "be concise." List the
  features you want; show **one example** of a good output — examples outperform description.
- **Motivated instructions.** Say *why* a rule exists ("plain English because a grandparent
  reads the Statement"), not just the rule. Newer Claude generalizes better from the reason —
  and our `CLAUDE.md` voice rule already does this well; extend it to ad-hoc prompts.
- **State the output contract up front:** format, length, audience, and what *not* to do.
- **The colleague test:** if a teammate with no context would be confused by the prompt,
  Claude will be too.

---

## 7. Yes — *this* request was inefficient. Here's the fix.

The prompt that triggered this review ("Locate inefficiencies… Is there a better way…
Perhaps also better prompting… Anything you could possibly think of… ANYTHING that could
help… Search the web… Check the news. Thanks!") is a good example of the pattern above. It's
warm and clear in *intent*, but for an agent it's **maximally open-ended**, which forces the
broadest, most expensive possible exploration:
- **No scope** → I have to consider everything from caching to org process.
- **No success criteria** → I can't tell when the answer is "enough," so I over-collect.
- **No constraints** (budget? which repos? local-only?) → no way to prune.
- **No output contract** → I guess at format and length.
- **"ANYTHING / Search the web / check the news"** → maximal tool fan-out by instruction.

That open-endedness is *fine for a brainstorm* and is what you wanted here — but as a habit
it's the single most expensive prompt shape. A tighter version of the same ask:

> *"Audit our Claude usage for cost. Focus on the LiteLLM router config and our Claude Code
> habits. Give me the top 5 changes ranked by $-saved ÷ effort, each with the concrete
> config/habit change. Skip anything we already do (caching? check first). ≤1 page. Cite
> 2026 sources for any number."*

Same outcome, a fraction of the wandering: it names the scope, caps the output, sets the
ranking, and tells me what to skip. **Rule of thumb:** lead with the deliverable and its
shape; save "anything you can think of" for when you genuinely want a wide net (and know
it costs more).

---

## 8. What's current (June 2026 — re-check quarterly)

- **Claude Opus 4.8** (shipped 2026-05-28): **1M context on by default**; **61% cheaper per
  token than Opus 4.7** per Databricks; up to **90% off with caching, 50% with batch**.
- **Mid-conversation system messages went GA** (no beta header): you can append/replace
  instructions mid-task via a `role: "system"` entry in the messages array **without
  restating the full system prompt and without breaking the cache.** Directly useful for our
  long supervisor runs — update Odin's guidance mid-session instead of rebuilding context.
- **Context editing + memory tool**: prune stale tool results and persist state across a long
  agentic run instead of carrying everything in-context — relevant once our LangGraph runs
  get long.
- **Cache TTL default is now 5 min** (was 60) — see §1; opt into 1-hour for spaced-out jobs.
- **Claude Tag** (Team/Enterprise beta): `@Claude` in Slack for async delegation — worth a
  look if we want hand-offs without a full session.

---

## 9. Recommended next actions (concrete)

1. **Wire `cache_control` into the router's Anthropic backends** and add cache-hit-rate to
   the LiteLLM logs we watch. *(localDNS, `10-ai-orchestration/config.yaml`.)* — biggest win.
2. **Make Sonnet the default cloud tier; reserve Opus for hard reasoning.** One-line intent
   change in routing + a personal habit in Claude Code (`start on Sonnet`).
3. **Refactor the seven `CLAUDE.md`s:** one shared House-style file + tight per-repo index;
   push deep tables down into README/context files.
4. **Adopt the habits:** `/clear` between tasks; subagents only when they pay; one-shot,
   example-led prompts with an explicit output contract.
5. **Route the cheap 60% to the t630** (drafts, summaries, classification, repo RAG); Claude
   finishes. Keep the privacy gate authoritative.
6. **Use the Batch API** for any non-interactive bulk generation (statement copy, etc.) for
   the 50% discount.

---

## Sources (June 2026)

- Anthropic — [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching),
  [Pricing](https://platform.claude.com/docs/en/about-claude/pricing),
  [Manage costs (Claude Code)](https://code.claude.com/docs/en/costs),
  [What's new in Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8),
  [Introducing Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8),
  [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
  [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Claude Prompt Caching in 2026: the 5-minute TTL change](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363) (DEV)
- [Anthropic API Pricing 2026 — caching, batch, optimization](https://www.finout.io/blog/anthropic-api-pricing) (Finout)
- [23 Tips for Claude Code token saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/) (Analytics Vidhya);
  [7 Practical Ways to Reduce Claude Code Token Usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) (KDnuggets);
  [Claude Code Agents in 2026 — what parallel sessions cost](https://www.cloudzero.com/blog/claude-code-agents/) (CloudZero)
- [Run Local AI Models with Claude Code to Cut Costs 10×](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) (MindStudio);
  [Hybrid Cloud-Local LLM Architecture Guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) (SitePoint);
  [Hybrid Cloud-Local AI Cost Optimization 2026](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026) (BuildMVPFast)
