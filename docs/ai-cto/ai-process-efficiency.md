# AI process efficiency — where the tokens actually go, and how to spend fewer

**Standing reference doc** (not a daily review). Verified facts carry a *verified-on* date;
re-run the refresh **monthly**, not daily — the best practices change, but not fast enough to
re-research every morning. Diff against this baseline and append only what changed.

> Scope: the *process* between the operator (you) and the AI — Claude Code sessions, the
> scheduled NARF/ZORT routines, and the local↔cloud split. Tied to the live stack in
> `localDNS/10-ai-orchestration/` (LiteLLM router + Ollama tiers + `dispatcher.py`).

---

## 0. The one-paragraph answer

Your prompting is **not** where the money leaks. The leak is **structural**: high-frequency
scheduled routines (NARF + ZORT, daily) that re-read the full portfolio context and run on the
**most expensive model**, while the **local LLM tier you already built earns nothing** because
it isn't wired into any of these loops. Fix those three things — model tier, a "did anything
change" gate, and routing the mechanical chores to local — and you cut spend 40–70% with no
loss of quality. Everything else below is a smaller multiplier on top.

---

## 1. The biggest levers (ranked by payoff, tailored to this stack)

### L1 — Stop running daily routines on Opus. Default to Sonnet; escalate to Opus only on demand.
On API billing Opus is **~5× the per-token cost of Sonnet** ([Anthropic pricing](https://www.finout.io/blog/anthropic-api-pricing)),
and "start every session on Sonnet, switch to Opus only for genuinely hard reasoning" is the
single highest-impact lever in every 2026 cost guide
([KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)).
The NARF/ZORT daily reviews are **read-docs → summarize → recommend** — squarely in Sonnet 4.6's
range. Reserve Opus 4.8 for the occasional hard architecture call. *Estimated saving on the
daily-review line item alone: ~80%.*

### L2 — Gate the routines on change. Don't pay for an empty run.
Most days the portfolio hasn't moved. A routine that reads everything and concludes "same as
yesterday" still paid full freight to do so. Put a **cheap pre-check** first: `git log --since`
/ a diff of the tracked source files since the last review. **No change → skip the LLM run
entirely** (and per your own routine philosophy, send no notification). This also fixes the
notification-noise problem from the other direction. The pre-check is free shell, not inference.

### L3 — Actually use the local tier you already built.
You have a LiteLLM front door (`ai.home.lan:4040`), local Ollama (`local-fast` qwen2.5:3b,
`local-smart` :7b), and a deterministic `dispatcher.py` — but **none of the daily AI work routes
through it.** 2026 hybrid-architecture guides put 60–70% of real workload in the
"simple/mechanical" bucket that local models handle fine, and report **60–80% cost cuts** from
splitting it off ([SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)).
Concrete candidates to push to `local-fast`/`local-smart` via the existing dispatcher rule table:
  - triaging `tools/check-docs.py` output (which links broke, where);
  - drafting reverse-chron log/changelog entries from a diff;
  - classification / "which repos changed today" / tagging;
  - first-pass summaries that Claude only *reviews*.

  Reserve the Claude API for the synthesis and the hard judgment calls. The dispatcher's rule
  table is exactly the right place — no LLM in the routing decision, per your blueprint.

### L4 — Lean on prompt caching for the long, stable prefix.
Cached input tokens bill at **~10% of standard** input price; the 1-hour extended TTL
([Anthropic, 2026](https://x.com/AnthropicAI/status/1925633128174899453)) "reduces costs up to
90% and latency up to 85% for long prompts." Claude Code caches the system prompt + tool defs +
CLAUDE.md + prior turns automatically — your job is to **keep that prefix stable** (don't reorder
CLAUDE.md mid-session) and set `ENABLE_PROMPT_CACHING_1H` for long/returning sessions
([Claude Code costs docs](https://code.claude.com/docs/en/costs)).

### L5 — Run non-interactive routines through the Batch API.
The scheduled NARF/ZORT reviews are asynchronous by nature (nobody's watching), which makes them
**perfect Batch API candidates: flat 50% off all tokens**, 24h window
([Anthropic pricing](https://www.finout.io/blog/anthropic-api-pricing)). Stacks with caching —
a cached-corpus batch job can bill at **~5% of rack rate**. (Claude Code itself is interactive;
this applies to any routine you move to a direct API call / the SDK.)

### L6 — Keep file-reads out of the main context with subagents.
A subagent reads the files and returns **only a summary** to the main context — "your main
context only receives the summary, not all the files the subagent read"
([systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)). Your review
routines read many docs; doing that fan-out in subagents (or the `Explore` agent) keeps the
expensive main loop's context small.

### L7 — Cap tool output and pre-filter logs.
Set a tool-output cap (~8000 tokens) and `grep`/extract the error lines before the model sees a
log, rather than pasting raw output
([Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)).
Deferred tool search (already active in this environment) keeps MCP tool definitions out of
context until needed — keep MCP servers lean to preserve that win.

---

## 2. Critique of the prompt that commissioned this doc

You asked me to grade the prompt — so, candidly, it is **token-expensive by construction**:

| Issue | Why it costs | Better |
| ----- | ------------ | ------ |
| Unbounded scope ("ANYTHING…", "Look for best practices", "Check the news") | Open scope forces wide, deep exploration — the model can't tell when it's "done", so it over-searches | Name 1–2 levers per run ("audit model tier + caching this week") |
| Many sub-questions bundled in one go | One sprawling context instead of several tight ones; quality drops as context fills | Split into scoped runs, or a checklist the routine walks one item per day |
| "Keep UP TO DATE… day by day" on a recurring routine | Re-researching fast-changing facts *daily* pays for the same web sweep repeatedly | Cache findings in **this doc**; refresh **monthly** and diff |
| Output destination unspecified | Without "write to file X", a routine's analysis dies in an unread transcript | State the deliverable + path (this doc is that path now) |
| "Thanks!" / politeness | **Negligible** — a few tokens, rounding error vs. context. Don't optimize this; it's a myth that it matters | Keep being polite; it's free |

**Rewritten, efficient version of your standing ask:**

> *"Monthly: re-read `docs/ai-cto/ai-process-efficiency.md`. Check Anthropic pricing/feature
> news since the `verified-on` dates. Append only what changed (new model IDs, price moves, new
> cost features) to §3 and revise the ranked levers if a ranking flips. Run on Sonnet. If
> nothing material changed, push nothing and notify nothing."*

That version is bounded, names its inputs and output, picks the cheap model, and has a built-in
"do nothing" exit — the opposite of an open-ended daily sweep.

---

## 3. Verified facts (re-check dates monthly)

| Fact | Value | Verified |
| ---- | ----- | -------- |
| Opus vs Sonnet API cost | Opus ~5× Sonnet per token | 2026-06-15 |
| Cached input tokens | ~10% of standard input price | 2026-06-15 |
| Cache TTL options | 5-min (write 1.25×) / 1-hr (write 2.0×); hit = 0.10× | 2026-06-15 |
| Batch API | flat 50% off all tokens, 24h async window | 2026-06-15 |
| Current Claude IDs | `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5` | 2026-06-15 |
| Hybrid split typical saving | 60–80% of API cost by running simple tasks local | 2026-06-15 |
| Routing + compaction typical saving | 40–70% of API spend | 2026-06-15 |

---

## 4. The one guardrail this must not break

Pushing chores to local and synthesis to cloud is consistent with your privacy stance — but note
the asymmetry: **Claude Code routines send repo content to the Anthropic cloud.** That's fine for
the made-up data in `DESIGN-…`, `localDNS`, `MARKETING` (CHANGE_ME everywhere). It is **not** fine
for `customers/`, which holds **real household data**. Never point a cloud routine at
`customers/households/*/`. If a routine ever needs to read real customer data, it must run on the
**local tier only** (`local-*` via the front door, no cloud fallback) — the same fail-closed rule
as TD-14. This is a line in the dispatcher, not a hope.

---

## 5. Suggested next actions (cheap, high-leverage, in order)

1. **Switch the NARF/ZORT daily routines to Sonnet 4.6** (config/CLI flag). Biggest single saving, zero quality risk for read-summarize-recommend work. *(L1)*
2. **Add a change-gate** to each scheduled routine: `git`-diff the tracked source since last run; skip the LLM call (and the notification) on no-change. *(L2)*
3. **Add 3–4 mechanical chore types to `dispatcher.py`'s rule table** routed to `local-fast`/`local-smart` (doc-integrity triage, log-entry drafting, change classification). *(L3)*
4. **Move the daily reviews to a Batch API call** (via the SDK) if/when they leave interactive Claude Code. *(L5)*
5. **Set this doc's refresh to monthly**, not daily; diff-and-append only. *(prompt critique)*

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Anthropic on the 1-hour TTL (X)](https://x.com/AnthropicAI/status/1925633128174899453)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Code cost optimisation — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows cost optimization — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
