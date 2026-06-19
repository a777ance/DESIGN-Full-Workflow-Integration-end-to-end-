# AI Process Efficiency — review (2026-06-19)

A standing review of *how we use AI* (the human↔AI loop), where tokens leak, and the
levers that cut cost without cutting quality. Newest entry first, per house style.

> **Scope.** This is about our *process*, not the product. It covers: the standing
> context tax we pay every session, model/routing choices, prompt-caching and batch
> economics, the Claude Code / Routines surface we run on, prompting patterns, and a
> read on what's changing month-to-month. Numbers below were measured on this box on
> 2026-06-19.

---

## 2026-06-19 — first pass

### TL;DR (do these first)

1. **Trim the session-start context tax.** Our two big `CLAUDE.md` files are ~5,000–5,500
   tokens *each*, and both instruct the agent to read 4–6 more state files at the start of
   every session. That whole payload is re-paid on **every routine run, every repo, every
   day** before a single useful token. This is our largest, most boring leak. Target: a
   lean `CLAUDE.md` core + on-demand detail. (Details below.)
2. **Right-size the model per routine.** A health-check / "did anything change?" routine
   does not need Opus. Opus is $5/$25 per Mtok; Haiku 4.5 is $1/$5; Sonnet 4.6 is $3/$15.
   Watcher and triage routines should run on Haiku/Sonnet; reserve Opus for the
   judgment-heavy ones.
3. **We already own a hybrid stack — point the cheap tier at it.** `localDNS` runs a
   LiteLLM router (`:4040`) with a local reasoning ladder and a cloud-GPU fallback. The
   "is this worth waking a human / a frontier model?" gate is exactly the local tier's job.
   We're paying for frontier tokens on triage that a local 1.5–7B model can pre-filter.
4. **This very prompt is a worked example of the leak** (see *Meta* below).

### Finding 1 — the session-start context tax (biggest lever)

Measured on this box:

| File | words | ≈ tokens | Loaded… |
| ---- | ----- | -------- | ------- |
| `DESIGN-…/CLAUDE.md` | 2,608 | ~5,000 | every session in this repo |
| `localDNS/CLAUDE.md` | 2,728 | ~5,500 | every session in localDNS |
| `MARKETING/CLAUDE.md` | 1,445 | ~2,900 | every session in MARKETING |
| `customers` / `homelab` / `Azure-lab` | 316–562 | ~600–1,100 | (these are already right-sized) |

On top of the file itself, `DESIGN/CLAUDE.md` §5–6 tells the agent to **read four AI-CTO
files and six AI-CFO files at session start**, and `localDNS` / `MARKETING` / `customers`
each point at their own `context.md`. A routine that does five minutes of real work can
spend its first several thousand tokens just hydrating standing state — and a *scheduled*
routine pays this with nobody benefiting from the ceremony.

**Why it matters here specifically:** Routines run unattended and repeatedly. A 5k-token
preamble that's tolerable in one interactive session is a recurring tax across N repos × M
runs/day. It also pushes useful work closer to the compaction threshold sooner.

**Fixes, in order of payoff:**

- **Split `CLAUDE.md` into a lean core + linked detail.** Keep the always-loaded file to
  the rules an agent truly needs on turn one (house style, the one-master-list rule, the
  honesty rule, "push to `main` vs. feature-branch"). Move stage-by-stage tables, the
  funnel ASCII, and long rationale into the existing `README.md` / `workflow-context.md`
  and *link* to them. The customers/homelab/Azure files are already at the right altitude —
  use them as the size target (~600 words).
- **Make the NARF/ZORT "read these N files at session start" conditional, not mandatory.**
  Phrase it as "when the task touches roadmap/decisions/finances, read X" rather than an
  unconditional session-start ritual. A watcher routine checking CI does not need the CFO
  runway file.
- **Per-routine `CLAUDE.md` is not required reading for narrow routines.** If a routine's
  whole job is "diff yesterday's metrics," it doesn't need the full playbook in context.

Rough math: shaving the DESIGN core from ~5k→~1.5k tokens and dropping the unconditional
10-file read saves on the order of 10–15k tokens *per run* in that repo. Across daily
routines and seven repos that is the single biggest, lowest-risk win on the board.

### Finding 2 — model & routing per routine

We default everything to Opus 4.8 (it's the configured model). That's correct for
hard reasoning and wrong for watchers. Concrete policy:

| Routine type | Suggested model | Why |
| ------------ | --------------- | --- |
| "Did anything change / is it healthy?" watchers | **Haiku 4.5** | classification-grade work; 5× cheaper input than Opus |
| Triage, summarize-and-flag, doc-link checks | **Sonnet 4.6** | strong, ~40% cheaper than Opus |
| Judgment-heavy authoring, cross-repo reasoning, this kind of review | **Opus 4.8** | worth it |

In Claude Code the model is per-session, so set it per routine rather than globally.
Don't downgrade silently inside a task — pick the tier when you define the routine.

### Finding 3 — use the hybrid stack we already built

`localDNS/10-ai-orchestration/` already runs **LiteLLM on `:4040`** with a documented
reasoning ladder: `local-reason` (deepseek-r1:1.5b on the t630, cool/cheap),
`cloud-gpu-reason` (full R1 on a rented GPU via Tailscale, on demand), and
`cloud-overflow`. Open WebUI sits on `:3000`. This is a *working hybrid router* — we just
aren't using it as the front door for routine triage.

The industry pattern (and the one our own stack is shaped for): a routing layer decides by
**(a) task complexity, (b) data sensitivity, (c) availability**. ~60–70% of real workload
is simple (classify / extract / "anything new?") and can resolve locally or on a cheap
tier; ~10% needs a frontier model. Reported hybrid savings run 60–80% on the cheap-eligible
slice. Wins for us:

- **Local pre-filter on watchers.** Let a local model answer "is there anything here a
  human or Opus should look at?" Only escalate to the Claude API on a yes. Most days the
  answer is no and we spend ~nothing.
- **Sensitive data stays home.** `customers/` holds real roster data; the privacy posture
  already says keep it private. Local inference on that material is a feature, not just a
  cost play.
- **Caveat (our own ADR-style discipline):** the moat is the guild, not more software.
  Don't build a bespoke routing app — extend the LiteLLM config we already deploy. Tech,
  not moat.

### Finding 4 — prompt caching + batch (for any API-side automation)

If/where we call the Claude API directly (statement generation tooling, bulk jobs), two
stacking levers:

- **Prompt caching.** Cache the large stable prefix (system prompt, the statement template,
  shared context). Cache writes cost ~1.25×; cache reads cost ~0.1×. Reused-prefix workloads
  see **85–90% input cost reduction**. The invariant: caching is a *prefix match* — a
  timestamp or unsorted-JSON key early in the prompt silently invalidates everything after
  it. Put volatile content last; verify with `cache_read_input_tokens`.
- **Batch API.** Anything tolerant of up-to-an-hour latency (nightly statement runs, bulk
  analysis, evals) goes through the Batches API at a flat **50% discount**. It stacks with
  caching — combined effective input cost can drop **>95%**.
- **Don't estimate tokens with `tiktoken`** (it's OpenAI's tokenizer and undercounts Claude
  by ~15–20%); use the `count_tokens` endpoint.

### Finding 5 — the Claude Code / Routines surface itself

We run on **Claude Code Routines** (cloud, scheduled — research preview since 2026-04-14).
Specifics that matter for us:

- **Routines can burn more tokens than an interactive session** — Anthropic's own caveat.
  Scope each routine to a narrow task; broad "go look at everything" prompts are expensive.
- **Context management is now largely automatic** (microcompact clears stale tool results
  without a model call; auto-compact summarizes near the limit and is near-instant since
  v2.0.64). Lean on it — but it's *cleanup*, not a license to load 10 files up front.
- **`.claudeignore` discipline** reportedly yields up to ~85% context reduction by keeping
  the agent from reading junk (build output, vendored data, large fixtures). Add one to the
  repos that have generated/large artifacts.
- **Scope file reads.** Prefer "read these specific files" over "explore the repo." Most of
  a routine's cost is re-reading things it already read or didn't need.

### Finding 6 — prompting patterns (quality *and* tokens)

- **Lead with the outcome; don't narrate.** For unattended routines, the deliverable is the
  notification. Verbose step-by-step narration into a transcript nobody reads is pure waste.
- **One well-specified first turn beats many follow-ups.** Each turn reprocesses the whole
  history; batching the spec up front is both cheaper and higher-quality on current models.
- **Don't over-instruct.** Aggressive "CRITICAL: YOU MUST" language makes current models
  over-trigger tools. State the condition plainly.
- **Define "done" and "when to notify" explicitly** so a routine doesn't keep digging (or
  keep pinging) past the point of value.

### Meta — this prompt is itself a worked example

The request that produced this review said roughly: *"reduce token use… better prompting…
leverage other AI… hybrid local LLM and Claude API… search the web… check the news."* That
phrasing named **Claude, the API, hybrid LLM, and prompting** — which triggered the loading
of a very large Claude-API skill (tens of thousands of tokens of reference) into the
context before any work began, the same class of leak as Finding 1. It worked, but it's the
illustration: **broad, capability-naming prompts pull in heavy machinery.** A leaner version
would scope it: *"Review how our scheduled routines spend tokens and recommend cuts; check
current best practices for prompt caching, batch, and local-model routing."* Same answer,
far less standing context. (None of this is a complaint — it's the exact pattern the review
is about, caught in the act.)

### What's changing (keep-up-to-date read)

Fast-moving area; re-check ~monthly. As of mid-2026: context management has moved
*server-side* and into the harness (microcompact / context-editing / multi-tier compaction),
so manual context babysitting matters less than it did — the leverage has shifted to **what
you load in the first place** and **which model you load it into.** Caching + batch
economics are stable and large. Hybrid local/cloud routing is now a well-trodden pattern
(LiteLLM + Ollama + a frontier API), which is precisely the shape of our existing stack.

### Prioritized action list

1. [ ] Slim `DESIGN/CLAUDE.md` and `localDNS/CLAUDE.md` to a lean core; move tables/rationale
   to README/`workflow-context.md` and link. (Biggest win.)
2. [ ] Make the NARF/ZORT session-start file reads **conditional**, not mandatory.
3. [ ] Set per-routine models: Haiku for watchers, Sonnet for triage, Opus for judgment.
4. [ ] Route triage through the existing LiteLLM `:4040` local tier; escalate to Claude only
   on a "yes, this needs attention."
5. [ ] Add `.claudeignore` to repos with generated/large artifacts.
6. [ ] For any direct-API jobs: prompt-cache the stable prefix; batch the latency-tolerant
   runs; stop estimating tokens with `tiktoken`.
7. [ ] Scope routine prompts narrowly; lead with the outcome; define "done" + "when to notify."

### Sources

- KDnuggets — *7 Practical Ways to Reduce Claude Code Token Usage*
- Firecrawl — *12 Ways to Cut Token Consumption in Claude Code*
- SitePoint — *Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026)*
- MindStudio — *Run Local AI Models with Claude Code to Cut Costs*
- Finout / CloudZero / TokenMix — *Anthropic API pricing & prompt-caching guides (2026)*
- InfoQ / Anthropic — *Routines for Claude Code (research preview, 2026-04-14)*
- "Inside Claude Code" / HarrisonSec — *context compaction & microcompact pipeline*
