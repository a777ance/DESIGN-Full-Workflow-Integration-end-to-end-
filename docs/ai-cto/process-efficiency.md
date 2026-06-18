# Process Efficiency — reducing token spend on the human↔AI loop

NARF (AI CTO) review, 2026-06-18. Brief for the founder: where the way we *use*
AI is wasting money and attention, what to change, and what to keep watching.
Newest review at the top (house style). Sources at the bottom.

The headline: **we already own most of the machinery to cut AI cost 60–90% — a
hybrid local+cloud LLM stack (Odin/LiteLLM, `localDNS` stage 10) — and the
day-to-day Claude Code loop isn't using it.** Five fixes below, ordered by
payback. Plus one live privacy bug the hybrid path introduced (TD-14).

---

## 1. The CLAUDE.md tax — we pay it on *every* turn (biggest, cheapest fix)

A `CLAUDE.md` is re-sent to the model on **every single turn**, regardless of how
long the chat is. Today:

- The 7 repos carry **~915 lines of `CLAUDE.md` between the four biggest**
  (`DESIGN` 295, `localDNS` 326, `MARKETING` 214, `customers` 80) — and a
  multi-repo session loads **all of them, concatenated, every turn.**
- The **"House style: ordering & typography" block (~30 lines) is copy-pasted
  verbatim into all 7 files.** When a session spans repos, we send that same
  block 4–7 times per turn, forever.

A 5,000-token CLAUDE.md costs 5,000 tokens *per turn* — on a 100-turn session
that's 500,000 input tokens of pure overhead before anyone types anything.

**Do this:**
- **Scope each session to the 1–2 repos the task actually touches.** A
  statement-delivery task does not need `MARKETING` + `Azure-lab` + `homelab`
  CLAUDE.md loaded. This single habit is the largest saving available and costs
  nothing.
- **Treat CLAUDE.md as a lookup table, not a brain dump.** Move the *why*,
  history, and long prose into README/context files (Claude reads them on
  demand); keep CLAUDE.md to the rules and the map. Our files are already close
  to this — trim the narrative paragraphs.
- **De-duplicate the house-style block.** Within a repo, a `CLAUDE.md` can
  `@import` a shared file so the 30 lines live once. (Cross-repo imports don't
  resolve, so the win there comes from session scoping, above.)

## 2. Match the model to the job — and re-check the price gaps

Current API pricing per 1M tokens (verified 2026-06, input/output):

| Model | $/1M in | $/1M out | Use for |
| ----- | ------- | -------- | ------- |
| Opus 4.8 | $5 | $25 | Hard reasoning, long-horizon agentic, the 10% that needs it |
| Sonnet 4.6 | $3 | $15 | Code, diffs, structured build — the daily driver |
| Haiku 4.5 | $1 | $5 | Classify / extract / format — the routine 60–70% |

Note the gap is **not** the old "Opus is 5× Sonnet" — today Opus is ~1.7× Sonnet
and ~5× Haiku. So the move isn't "avoid Opus," it's **don't run Haiku-shaped work
(classification, extraction, log tidying, roster field-filling) on Opus.** Start
routine sessions on Sonnet; reserve Opus for genuinely hard reasoning;
push trivial transforms to Haiku or local (see §4). Subagents can run a cheaper
model than the main loop — Claude Code's Explore agents already use Haiku.

## 3. Turn on prompt caching for our repeated context

Our prompts are highly repetitive: the same big `CLAUDE.md`, the same schema,
the same statement template, the same roster shape, request after request.
**Cache reads cost ~0.1× of input price; a stable prefix can cut repeated input
cost up to ~90%.** Cache writes cost 1.25× (5-min TTL), so it pays from the
second request on.

The rule is *prefix stability*: put frozen content (CLAUDE.md, schema, template)
first and never interpolate `datetime.now()`, a UUID, or a per-run ID into it —
one byte change invalidates the whole cached prefix. This matters most for any
**scripted** A777ance use of the Claude API (statement composition, the Rainbow
Bridge sync, NARF/ZORT batch jobs), not just interactive Claude Code.

## 4. Actually use Odin — the hybrid stack we already built

`localDNS/10-ai-orchestration/config.yaml` already defines a LiteLLM front door
with local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` 7b,
`local-reason` deepseek-r1:1.5b) and a cloud failover to Claude
(`cloud-overflow`). **The LangGraph supervisor ("Odin") exists. The daily AI
workflow doesn't route through it.**

Industry pattern for 2026: ~60–70% of requests are simple (classify, extract,
format), ~20–30% moderate, ~10% need a frontier model. Routing the cheap 60–70%
to the t630's local models and reserving the Claude API for the hard tail is a
**documented 60–90% cost reduction at equal quality ceiling**, and it keeps
sensitive lookups on-box (a privacy win we already care about).

**Do this:** point the non-interactive, low-sensitivity chores at
`ai.home.lan:4040` (local-first) — first-draft Handled-For-You log entries, roster
field extraction, summarizing a call note, classifying a lead — and keep Claude
Code/Opus for architecture, multi-file edits, and the Statements. The router
already fails over to Claude when the local model is down, so there's no
reliability cost to trying local first.

## 5. Batches API for the bulk, scheduled work

Anything not latency-sensitive — generating the month's statements across all
households, bulk-classifying a lead list, the monthly metrics roll-up — can go
through the **Message Batches API at 50% off** standard token price. Statement
generation across a book of homes is the textbook fit.

---

## ⚠️ Live bug this surfaced: TD-14 (P1, privacy)

The hybrid path we want to lean on has an **open P1 privacy hole**: in
`config.yaml`, a `sensitive`-tagged task pinned to `local-reason` has a
`["cloud-gpu-reason", "cloud-overflow"]` fallback — so if the local model is
down, a sensitive prompt **fails over to Claude cloud**, defeating the local-only
guarantee. `allow_cloud=False` isn't enforced at the LiteLLM failover layer.
**Fix before routing more traffic through Odin:** give `local-reason` a
local-only fallback chain (fail closed). Until then, §4 must exclude anything
sensitive.

---

## On the prompt that triggered this review

The request was, verbatim, *"ANYTHING that could help… anything you could
possibly think of."* That phrasing is itself the inefficiency it asks about: an
open-ended, unscoped prompt makes the model fan out and scan broadly (web
searches, repo sweeps, every angle) and burns tokens proportional to the
vagueness. Specific prompts let the model act, not explore.

A tighter version of the same ask:

> "Audit our AI usage for cost. Cover: (1) CLAUDE.md / context overhead, (2)
> model tiering, (3) prompt caching, (4) using the Odin local stack, (5) batch
> jobs. Ground each in our repos, give one concrete action per point, and write
> it to `docs/ai-cto/process-efficiency.md`. Skip generic advice."

Same answer, a fraction of the exploration. **General prompting rule for the
guild:** name the scope, name the deliverable, name where it goes, and say what
to skip. For recurring/scheduled work especially, a scoped prompt + a token
budget beats "look at everything."

---

## Keep-watching (the field moves weekly)

- **Claude Code cost controls (June 2026):** `/context` and the status-line
  context-usage readout make the CLAUDE.md tax *visible* — turn them on. `/compact`
  takes custom instructions for what to preserve. Task budgets (beta) let you
  advise a token target across an agentic loop. Subagents isolate verbose work
  off the main context.
- Re-verify model IDs/prices before quoting them — they change; this review used
  the 2026-06 catalog.

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Reduce Claude Code Costs 60% With These Four Habits — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Updates, June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
- Internal: `localDNS/10-ai-orchestration/config.yaml`; `docs/ai-cto/tech-debt.md` (TD-14)
