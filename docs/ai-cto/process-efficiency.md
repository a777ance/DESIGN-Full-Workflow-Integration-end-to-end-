# AI Process Efficiency — token cost, prompting, hybrid routing

How we (founder ⇄ AI) actually spend tokens and attention, where it leaks, and what to
change. Scoped to *our* stack: Claude Code (interactive + scheduled routines), the t630
LiteLLM/Ollama hybrid router (`localDNS/10-ai-orchestration/`), and the Odin LangGraph
supervisor. Findings are ranked by payoff. Reviewed against current public guidance and
Anthropic pricing as of **2026-06-16**.

New review notes go at the top (newest first, per house style).

---

## TL;DR — the five biggest levers

1. **Prune the CLAUDE.md files** (P1, free, do first). They are huge and load into context
   on *every* session and every routine run. Long CLAUDE.md is both a per-call token tax and
   a *quality* cost — the model follows a 5-page brief worse than a 1-page one. Cut each to a
   tight briefing; push detail into README/linked docs that get pulled on demand.
2. **Tier the cloud model by task, don't default everything to Opus 4.8.** Opus is $5/$25 per
   Mtok; Sonnet 4.6 is $3/$15; Haiku 4.5 is $1/$5. Routing the right 70% to the cheapest
   adequate tier is the single biggest cost lever (industry reports: 60–80% savings, minimal
   quality loss).
3. **Turn on prompt caching** for the stable prefix (CLAUDE.md + tool list). Cache reads bill
   at ~10% of input — a 90% discount that breaks even after ~2 reads. We re-send the same big
   brief every turn; today we pay full price for it every time.
4. **Make Odin route by task class, not just fail over.** Today local is the default and cloud
   is failover-only. That's a topology, not a router. Route draft/classify/summarize → local;
   code/diff/hard-reasoning → the right Claude tier; keep the privacy gate fail-*closed*.
5. **Batch the non-interactive work** (monthly statements, RAG embeds, bulk classification)
   through the Message Batches API — flat **50% off**, results within ~1h.

---

## 1. Reduce token use

### 1.1 CLAUDE.md bloat is the most expensive habit we have
Every Claude Code session (and every routine run) injects the project CLAUDE.md into context
before the first user word. Ours run many pages each (DESIGN, localDNS especially). That is:
- **Recurring input cost** on every single call, multiplied across interactive + routine runs.
- **A quality drag** — current guidance is explicit: "if your CLAUDE.md is too long, Claude
  ignores half of it." Important rules get lost in the noise.

Action: ruthlessly prune each CLAUDE.md to the essential briefing (what the repo is, the
invariants, the don'ts, the pointers). The house-style block, the full stage map, and the
deploy-path table belong in README/linked docs that get read on demand — not in the always-on
prefix. Target: the briefing fits on one screen.

### 1.2 Prompt caching on the stable prefix
The CLAUDE.md + tool definitions are byte-stable across a session; cache them. Cache reads cost
~0.1× input, writes ~1.25× (5-min TTL) / ~2× (1-h TTL). Break-even ≈ 2 reads (5-min). For a
working session or a chatty routine this is most of the input bill.
- In Claude Code: enable prompt caching (1-h TTL helps bursty/scheduled use).
- Keep the prefix frozen: **never interpolate `date`, session id, or per-run values into
  CLAUDE.md or a system prompt** — one byte change invalidates the whole cached prefix. (Our
  house style stamps dates *inside docs*; that's fine. Don't put `Today is …` in the prefix.)
- Verify it's working: `usage.cache_read_input_tokens` should be non-zero on repeat turns.

### 1.3 Context hygiene in interactive sessions
- `/clear` between unrelated tasks — stale context is re-billed on every subsequent message.
- Use **subagents** (Explore/Plan) for fan-out research so the main thread stays small; the
  subagent burns its own context and hands back only the conclusion.
- Prefer narrow asks ("refactor the login function in `auth.ts`") over broad ones ("refactor
  the auth module") — less context pulled, fewer tokens, more focused output.
- On long sessions, lean on `/recap` and server-side compaction rather than replaying history.

### 1.4 Batch the non-latency-sensitive jobs — 50% off
The monthly statement build, RAG re-embedding (Mímir's well), and any bulk classification are
not interactive. Run them through the **Message Batches API**: exactly half price, ~1h
turnaround, every feature (caching, tools) still works. This is free money on recurring jobs.

---

## 2. Better prompting

- **State the decision you want, not just the topic.** "Recommend one routing change and the
  config diff" beats "look at our routing." Open-ended prompts on Opus 4.8 invite long,
  exploratory runs (it's tuned to be thorough) — that's tokens and minutes.
- **Give a length/format target.** Opus 4.8 calibrates verbosity to perceived complexity; if
  you want a short answer, say so and give the shape (table / 5 bullets / diff only).
- **Front-load the full spec in the first turn**, especially for routines and long agentic
  work — 4.8 is most efficient and most accurate when the goal and constraints are clear up
  front rather than dribbled across turns.
- **Dial back "CRITICAL / YOU MUST" language.** Modern Claude follows the prompt closely;
  aggressive guardrails written for older models now over-trigger (extra tool calls, over-
  exploration). Plain instructions are cheaper and more accurate.
- **Add a silence/anti-tidying note for autonomous runs** so the agent doesn't narrate every
  step or refactor adjacent code it wasn't asked to touch.

---

## 3. Leverage other AI / the hybrid local+Claude split

We already have the hard part built: LiteLLM front door, Ollama local tiers as the default,
Claude as overflow, the Odin supervisor with a deterministic privacy gate, local embeddings for
RAG. The gaps are about *using* it well:

### 3.1 Route by task class, not only by failure
`config.yaml` today makes local the default and cloud a *failover* target. Promote Odin from
"spill on error" to "route on intent":
- **Local (t630, free, private):** drafting, summarizing, classification, extraction, "tidy
  this text", routine triage — the cheap-and-adequate 70%.
- **Cloud Claude, tiered:** Haiku 4.5 for cheap structured tasks; Sonnet 4.6 for most code /
  diffs / structured build; Opus 4.8 reserved for the genuinely hard reasoning and long-horizon
  agentic work. The capability tiers are already named in `config.yaml` — wire the supervisor to
  pick them by task, and make `cloud-code` (Sonnet) the workhorse, not Opus.

### 3.2 Stop defaulting overflow to Opus
`cloud-overflow` → `claude-opus-4-8` means every local spill lands on the most expensive model.
Make the overflow tier Sonnet 4.6 (or Haiku for light work) and escalate to Opus only when the
task warrants it. The comment in `config.yaml` already says this; the default doesn't do it.

### 3.3 Keep the privacy gate fail-closed (ties to TD-14)
Routing more traffic to cloud raises the stakes on the existing **TD-14** bug: a `sensitive`
task can fail over from `local-reason` to `cloud-overflow` if the local model is down. Fix
TD-14 (local-only fallback chain for sensitive work) *before* leaning harder on cloud routing.
Privacy is the moat; don't trade it for a cache hit.

---

## 4. Keep up to date (state as of 2026-06-16)

- **Models & price:** Opus 4.8 ($5/$25, launched 2026-05-28; Fast Mode now $10/$50), Sonnet 4.6
  ($3/$15), Haiku 4.5 ($1/$5). Opus 4.8/4.7 and Sonnet 4.6 carry **1M context at flat rate** (no
  long-context surcharge). Adaptive thinking + `effort` (`low|medium|high|xhigh|max`) replace
  fixed thinking budgets — `xhigh` is the coding/agentic sweet spot.
- **Cost mechanics:** prompt caching read = 10% of input; Batches API = 50% off.
- **Claude Code Routines** (this run's mechanism): standard API token rates + **$0.08/runtime
  hour**; **15 runs/day** cap in preview, **shared with interactive usage** — schedule so
  routines don't starve interactive work. Best practice: fold several checks into one daily
  meta-orchestrator routine; reserve real-time triggers for high-severity events only.
- **News to ignore for now:** Fable 5 / Mythos 5 launched 2026-06-09 but customer access was
  **suspended 2026-06-12** — not a dependency for us, and priced above Opus tier regardless.
  Stay on Opus 4.8 as the top tier.

This section dates quickly — re-check pricing and the routines cap before any large run.

---

## 5. Was the prompt that triggered this review efficient?

Honestly, no — and it's a useful worked example of §2:

- **It was maximally open-ended** ("ANYTHING that could help… search the web… check the news…
  keep UP TO DATE"). On Opus 4.8 that invites a long, wide run. A scoped version —
  "Audit our Claude-Code + homelab-router token spend; give me the top 5 changes ranked by
  payoff, with config diffs" — gets the same answer for a fraction of the tokens and minutes.
- **It ran on the most expensive model with the largest context** (Opus 4.8, all five repos'
  CLAUDE.md injected) for a task that's mostly synthesis. Much of the injected context was
  irrelevant to the question. A scoped session in the relevant repo, or a local-first triage
  pass, would have been cheaper.
- **It bundled several distinct asks** (token use + prompting + hybrid + news + self-critique).
  Splitting them — or naming the one decision wanted now — keeps each run small and cacheable.

Better prompt shape next time:
> "In `localDNS/10-ai-orchestration`, propose one routing change to cut cloud spend, with the
> `config.yaml` diff and the privacy implication. ≤ 1 page."

State the target, the scope, the format, the length. Save the open-ended "anything that helps"
sweeps for a deliberate, budgeted review (like this one) rather than the default working mode.
