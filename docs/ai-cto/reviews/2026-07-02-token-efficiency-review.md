# Process & Token-Efficiency Review — 2026-07-02

**Scope:** the user↔AI process across the seven A777ance repos — where tokens
are wasted, where a cheaper model or the existing local stack could do the job,
and how to prompt for less. Grounded in current (July 2026) pricing and Claude
Code features. Sources listed at the end.

**One-line answer:** the biggest waste is *fixed context re-sent every turn*
(bloated + duplicated `CLAUDE.md`), not the work itself. Fix that first, route
routine work off Opus, and turn on caching/batch for the statement job. Combined,
these cut spend an estimated **60–85%** with no quality loss.

---

## A. Ranked findings (biggest lever first)

### 1. Multi-repo CLAUDE.md re-sent every turn — ~10.7k tokens/turn `[P1]`

Measured today, the six real `CLAUDE.md` files total ~10,700 tokens:

| Repo | ~Tokens |
| ---- | ------- |
| localDNS | 3,637 |
| DESIGN (this repo) | 3,477 |
| MARKETING | 1,926 |
| customers | 749 |
| claude-code-homelab | 494 |
| Azure-lab | 421 |

When a session has several repos in scope, **all of their `CLAUDE.md` files load
on every single turn** — a 200-turn session pays that ~10.7k tokens 200 times
(~2.1M input tokens) before any real work. Anthropic's own guidance and 2026
field reports find a `CLAUDE.md` stripped to *only what the model can't infer from
the code* matches a 5k-token one with no quality regression (one report: 312
tokens vs 5,000, "91.9% context reduction, no regression").

**Action:** trim each `CLAUDE.md` to facts-not-inferable (deploy paths, ports,
invariants, "never do X"). Move narrative/rationale (funnel diagrams, the "why"
prose, roadmaps) into `README.md`/`*-context.md` that get read *on demand*, not
injected every turn. Target ≤1,200 tokens each. Estimated saving: 60–70% of fixed
context.

### 2. The house-style block is duplicated verbatim in 6 repos `[P2]`

The identical ~300-token "House style: ordering & typography" block
(reverse-chron, Z→A, Gill Sans MT) appears in all six `CLAUDE.md` files. In a
multi-repo session that's ~1,800 tokens of pure duplication per turn, and it's
copy-maintained by hand (a change means editing six files).

**Action:** keep the full block in **one** canonical place (DESIGN's `CLAUDE.md`
or a `docs/house-style.md`) and replace the other five with a one-line pointer:
`House style (ordering, Z→A lists, Gill Sans MT): see DESIGN/docs/house-style.md`.
Single source of truth, ~1,500 tokens/turn saved in cross-repo sessions.

### 3. Routine/monitoring work runs on Opus 4.8 (the top tier) `[P1]`

This scheduled routine — and likely other monitors — runs on Opus 4.8 at
**$5/$25 per 1M tokens**. Haiku 4.5 is **$1/$5** (5× cheaper in, 5× cheaper out);
Sonnet 4.6 is **$3/$15**. Monitoring, doc-integrity checks, status summaries, and
"did anything change?" sweeps do not need Opus. Field consensus in 2026: *start on
Sonnet, escalate to Opus only for deep analysis/refactors.*

**Action:** default scheduled routines and simple sweeps to **Haiku**; interactive
coding to **Sonnet**; reserve **Opus** for architecture, gnarly debugging, and
cross-repo reasoning. For Claude Code, `/model` per-session or a routine-tier
default. Estimated saving on routine spend: **~80%**.

### 4. The statement job is a perfect batch/cache target, billed per-call `[P2]`

Statements render "at about a penny a home" — a monthly, N-home, non-interactive
job with a large shared prefix (system prompt + template + house style). That is
the textbook case for two levers that stack:

- **Prompt caching** — cache reads bill at **0.1×** input (90% off) with a 1.25×
  write. The shared template/prefix is written once, read for every home.
- **Batch API** — asynchronous, **50% off** both input and output; statements
  aren't latency-sensitive.

Combined, Anthropic documents **up to ~95%** off the per-home token cost. A penny
a home → roughly a tenth of a cent at scale.

**Action:** run the monthly statement generation through the Batch API with a
cached prefix. (If generation is a local script calling the API, this is a
config/SDK change, not a rewrite.)

---

## B. Hybrid local + Claude — you already own most of it

The localDNS stack already runs the right architecture: **LiteLLM** gateway
(`:4040`), a **reasoning ladder** (`local-reason` = deepseek-r1:1.5b on the t630,
`cloud-gpu-reason` = full R1 on a rented GPU, `cloud-overflow` = Claude cloud), a
dispatcher with `allow_cloud` / `sensitive` tagging, and Open WebUI. 2026 hybrid
guides converge on exactly this shape and quantify the payoff: **60–80% cost
reduction** because ~60–70% of real traffic is simple (classify/extract/format),
~20–30% moderate, and only ~10% needs a frontier model.

Gaps to close (turns the existing ladder into real savings):

1. **Route by task class, not by hand.** Add a cheap triage step (local model or
   a rule) that tags each task simple / moderate / frontier and dispatches:
   simple → local, moderate → Sonnet, frontier → Opus. LiteLLM supports
   auto-routing for this.
2. **Fix the privacy failover (already tracked as TD-14).** `local-reason` falls
   back to `cloud-overflow`, so a `sensitive` task can leak to Claude cloud if the
   local model is down. Give `local-reason` a **local-only** fallback — fail
   closed. This is a prerequisite before routing any customer data locally.
3. **Local for the high-volume, low-stakes surround** — draft blog copy, first-pass
   summaries, log triage, "does this doc link resolve" style checks. Keep Claude
   for customer-facing prose and anything on the kept document.

**The rule of thumb:** local model handles it → keep it local (free + private);
only escalate to Claude when the local answer isn't good enough. Always keep a
cloud fallback for availability (but local-only for `sensitive`).

---

## C. Claude Code features that cut tokens (turn these on)

- **`/compact`** — summarize a long session into a compact baseline instead of
  replaying the whole transcript. **`/recap`** (Apr 2026) — resume with a summary,
  not a full replay.
- **Prompt caching** — `ENABLE_PROMPT_CACHING_1H`; `/doctor` shows whether it's on.
  Big win given the large fixed `CLAUDE.md` prefix.
- **Subagents / forking** — scope a subtask to its own context window instead of
  dragging the whole session. A *fork* reuses the parent's prompt cache (cheaper
  than a fresh subagent) and keeps the main context clean; subagent memory
  (v2.1.33) persists learned patterns across sessions so they aren't re-derived.
- **Context editing / tool-result clearing** — drop stale tool outputs from context
  automatically.
- **`.claudeignore` discipline** — exclude build output, data dumps, vendored dirs;
  reported ~85% context reduction from ignore-hygiene alone.
- **Scope narrowly** — "refactor the login function in `auth.ts`", not "refactor the
  auth module." Smaller scope = less context pulled in.
- **1M-token window is available on Opus/Sonnet at no premium** — but a bigger
  window is not free tokens; it just delays compaction. Don't treat headroom as
  license to load everything.

---

## D. Prompting improvements (repo-wide)

2026 best-practice, from Anthropic's own docs:

- **Structure beats length.** Clearer specs, not longer prompts. Verbosity only
  helps when it adds *specificity*.
- **Be concretely specific, not vaguely emphatic.** "5 bullets, ≤15 words each" >
  "be concise." "Under 1000 words" > "keep it short."
- **Drop the ALL-CAPS.** `CRITICAL: YOU MUST ABSOLUTELY…` doesn't make the model
  try harder; a calm, specific directive works better and costs fewer tokens.
- **Skip examples until you need them.** Try without; add an output schema or
  tighter instructions first; only add few-shot examples if that fails.
- **Only-what's-requested.** "Make only changes directly requested or clearly
  necessary" — the minimum complexity for the task. (This also curbs output tokens,
  which are 5× input.)

---

## E. Is *this* prompt inefficient? Yes — and here's the fix

The request that generated this review is itself a good example of the anti-pattern
it asks about:

- **Unbounded scope.** "ANYTHING that could help… Search the web… Check the news…
  Keep UP TO DATE." Open-ended invites open-ended work — many searches, long output.
  Ironic for a token-reduction task.
- **No output contract.** No length, format, or deliverable specified, so the model
  defaults to long-form.
- **Emphatic caps** ("ANYTHING", "UP TO DATE") add tokens without adding direction —
  exactly what D above warns against.
- **Two questions in one** ("find inefficiencies" + "critique this prompt") — fine,
  but each deserves its own bounded ask.

**Rewrite (same intent, ~1/3 the tokens, bounded output):**

> Audit our user↔AI process for token waste across the A777ance repos. Cover:
> (1) fixed context sent every turn (CLAUDE.md size/duplication), (2) model-tier
> fit (are routines on the right model?), (3) caching/batch for the statement job,
> (4) using the local LiteLLM ladder for simple tasks. For each, give the estimated
> saving and one concrete action. Ground it in current pricing/features; note the
> date of anything time-sensitive. Deliver ≤2 pages, ranked by impact. Flag any
> assumption you couldn't verify.

Why it's better: names the axes (bounds the search), asks for saving + action per
item (forces concreteness), sets a length cap, and asks for flagged assumptions
(no silent guessing). The web-search/"check the news" instruction is dropped from
the standing prompt — make it an explicit ask only when currency actually matters,
since it multiplies tool calls every run.

---

## F. Do-this-week checklist

1. Trim all six `CLAUDE.md` to ≤1,200 tokens; move prose to README/context files. `[#1]`
2. De-duplicate the house-style block to one source + pointers. `[#2]`
3. Set routine/monitor default to **Haiku**, interactive to **Sonnet**, Opus on demand. `[#3]`
4. Turn on `ENABLE_PROMPT_CACHING_1H`; verify via `/doctor`. `[C]`
5. Move the monthly statement job to **Batch API + cached prefix**. `[#4]`
6. Close **TD-14** (local-only failover) before routing any customer data locally. `[B.2]`
7. Add a triage/auto-route step to the LiteLLM ladder: simple→local, moderate→Sonnet,
   frontier→Opus. `[B.1]`
8. Adopt the prompting rules in **D** as house convention (a short section in the
   canonical house-style doc).

**Rough combined impact:** context fixes (#1–2) cut the per-turn floor 60–70%; model
routing (#3, B) cuts routine spend ~80%; batch+cache (#4–5) cuts the statement job up
to ~95%. Order of attack: #1 → #3 → #4, they need no new infrastructure.

---

## Sources (accessed 2026-07-02)

- [Anthropic — Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Anthropic — Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Anthropic Cookbook — Context engineering: memory, compaction, tool clearing](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Claude Code Docs — Custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Anthropic — Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Claude Cost Optimization 2026: Batch API (50% off) + Prompt Caching (90% off)](https://pecollective.com/tools/claude-pricing-guide/)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows: Cost Optimization (2026) — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM — Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Claude Code & Agent Memory: Best Practices 2026 — orchestrator.dev](https://orchestrator.dev/blog/2026-04-06--claude-code-agent-memory-2026/)
