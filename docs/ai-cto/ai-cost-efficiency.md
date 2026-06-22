# AI Cost & Process Efficiency — how we spend tokens, and how to spend fewer

NARF (AI CTO) working note. Scope: the *process* between a human operator and the AI —
Claude Code sessions, the routines that run unattended, and the local-first Odin/LiteLLM
stack on the t630. Goal: same output, fewer tokens and dollars, without giving up the
privacy posture.

**Reviewed against live facts (2026-06-22):** Anthropic per-token pricing, prompt-caching
economics, the Batch API, context editing, and the current model line-up — plus
`localDNS/10-ai-orchestration/config.yaml` as it stands today. Where a figure moves
day-to-day (rented-GPU pricing, exact model rates), treat this as a snapshot and re-check.

---

## TL;DR — the five levers, biggest first

1. **Right-size the model per task.** Routine doc edits, refactors, link-checks, and the
   unattended routines do **not** need Opus. Default those to **Sonnet 4.6** ($3 / $15 per
   MTok vs Opus 4.8's $5 / $25) or **Haiku 4.5** ($1 / $5) for classification-grade work.
   Reserve Opus/Fable for genuinely hard reasoning. This is the single largest lever — a
   ~40–80% input-cost cut on the bulk of our work with no quality loss on tasks that never
   needed the ceiling.
2. **Turn on prompt caching wherever a big stable prefix repeats.** Cached input costs
   ~0.1× and cache writes ~1.25× (5-min TTL). Our CLAUDE.md files + house-style block are a
   large, byte-stable prefix re-sent every turn — exactly the caching sweet spot. Claude
   Code caches the system/CLAUDE.md prefix automatically; the lever we control is on the
   **`cloud-overflow` path through LiteLLM** (see §3).
3. **Batch the non-interactive work.** The monthly Statement run (06), bulk classification,
   and any "submit and come back later" job qualify for the **Batch API at 50% off** all
   tokens. As we scale past a handful of households this is found money.
4. **Use the local tiers for what they're good at.** Odin already defaults local-first.
   Push classification, short summaries, draft generation, and RAG embeddings to the t630;
   only escalate hard reasoning to the cloud. The box is the cheap tier — use it.
5. **Trim the always-loaded context.** The NARF + ZORT session-start ritual mandates reading
   ~10 docs every session (4 CTO + 6 CFO). That is tokens spent before any work begins, on
   every session, relevant or not. Make most of them load-on-demand (§6).

---

## 1. Model selection — the default is too rich

Current line-up and rates (input / output per million tokens):

| Model | Input | Output | Use it for |
| ----- | ----- | ------ | ---------- |
| Haiku 4.5 | $1 | $5 | Classification, tagging, short extraction, yes/no gates |
| Sonnet 4.6 | $3 | $15 | **Default for day-to-day** — doc edits, refactors, tests, routine routines |
| Opus 4.8 | $5 | $25 | Hard reasoning, cross-repo refactors, architecture |
| Fable 5 | $10 | $50 | Only the most demanding long-horizon agentic work |

We are currently running Opus-tier by default (this session included). For the work this
guild actually does — editing playbook docs, wiring stage-11 automations, writing Statement
templates — Sonnet 4.6 is the right floor and Haiku handles the classification-grade pieces.
In Claude Code: start a session on Sonnet, switch up to Opus only when a task is genuinely
hard. The unattended routines should be pinned to the cheapest model that does the job.

## 2. Prompt caching — the prefix is the cache

The rule: caching is a **prefix match**, and any byte change anywhere in the prefix
invalidates everything after it. Render order is `tools → system → messages`. Practical
consequences for us:

- **Keep CLAUDE.md byte-stable.** Don't interpolate dates, run IDs, or per-session context
  into it. A frozen prefix caches; a prefix with `today's date` in it never does.
- **The house-style block is identical across all 7 repos.** Within a repo that's a clean
  cached prefix. It's also ~30 lines × 7 repos of duplicated text — fine for caching, but it
  inflates every repo's always-on context (see §5/§6).
- **Economics:** break-even is ~2 requests on a 5-min TTL. Anything we re-hit within the
  window is ~90% cheaper on the cached span. Verify with `usage.cache_read_input_tokens`;
  if it's zero across repeated calls, a silent invalidator is in the prefix.

## 3. The `cloud-overflow` path needs caching turned on

When Odin spills to Claude (`cloud-overflow` / the `cloud-*` capability tiers in
`config.yaml`), we pay per token with **no caching configured**. LiteLLM passes
`cache_control` through to Anthropic — set a breakpoint on the stable system prompt for any
repeated-prefix workload routed there. Same 90%-on-cached-prefix saving as §2, on the path
that actually bills us.

Related, already tracked: **TD-14** — a `sensitive`-tagged task can fail over from
`local-reason` to `cloud-overflow`, breaking the privacy guarantee. That's a correctness bug,
but it's also a *cost* leak (sensitive work silently billing to Claude). Fixing TD-14 (fail
closed to a local-only chain) closes both.

## 4. Batch API — 50% off the work that can wait

The Batch API processes Messages-API requests asynchronously at **half price** on all tokens,
most batches finishing within the hour. It supports caching, tools, and vision. Fits:

- **Stage 06, the monthly Statement run** — every household, once a month, not latency-
  sensitive. Prime batch candidate as the book grows.
- Bulk lead classification / enrichment (02, 08), and any NotebookLM-bridge style sync.

Rule of thumb: if no human is waiting on the response *right now*, it should be a batch.

## 5. Local-first is built — now actually lean on it

Odin (`10-ai-orchestration`) already routes local-first with a cloud failover, which is the
correct shape. Two refinements:

- **Send the cheap/bulk/sensitive work local on purpose.** Classification, short summaries,
  first-draft generation, and the RAG embeddings (`local-embed`) belong on the t630 — a penny
  saved per call, and sensitive lookups never leave the network.
- **A better local model is now available.** The box is a 16 GB CPU-only Carrizo running
  `qwen2.5:7b`. **Gemma 4 12B** (released 2026-06-03) fits in 16 GB and Ollama 0.23+ ships
  MTP speculative decoding for it — a meaningful quality/throughput bump over the current
  7B on the same hardware. Worth a side-by-side `ollama pull` and timing test before the next
  statement cycle.

**Cost check on the rented-GPU reasoner (`cloud-gpu-reason`):** spinning a Vast.ai/RunPod pod
hourly to run full DeepSeek-R1 only pays off at sustained heavy-reasoning volume. For
*sporadic* hard reasoning, Claude Opus 4.8 with **adaptive thinking at `effort: low`/`medium`**
is likely cheaper per task than booting a pod — and there's nothing to remember to shut down.
Keep the pod path for batched, sustained reasoning sessions; default sporadic reasoning to the
cloud-overflow brain. (ZORT: this is a real line-item comparison once we measure.)

## 6. The session-start ritual is a per-session token tax

`CLAUDE.md` §5 + §6 instruct every session to read 4 CTO docs and 6 CFO docs at start.
That's ~10 files loaded whether the task touches them or not — pure overhead on a session
that only needed to fix one link.

Recommendation: keep **one lean index** as mandatory (portfolio.md, which already summarizes),
and make the rest **load-on-demand** — the model reads roadmap/tech-debt/decisions/runway/etc.
*when the task calls for it*. Same information available, paid for only when used. This is the
highest-leverage change to the human↔AI process itself, as opposed to the billing.

## 7. Agentic hygiene (applies to every session and routine)

- **Subagents for fan-out.** Broad multi-file searches run in a subagent's own context and
  return a summary — the file dumps never touch the main window. (This routine used that.)
- **`/compact` and `/clear`** between unrelated tasks; long contexts degrade quality *and*
  cost more per turn.
- **Grep before Read.** Locate with search, read only the slice you need; don't pull whole
  files into context to find one symbol.
- **Context editing** (clears stale tool results/thinking) and auto-compaction keep
  long-running routines from ballooning — relevant for any "watch and react" loop we add.
- **`/fast`** on Opus is a *latency* lever, not a cost one (premium pricing) — use it for
  interactive speed, never to save money.

## 8. On the prompt that commissioned this note

The commissioning prompt was open-ended ("ANYTHING that could help… search the web… check the
news") — good for a one-off survey, but two efficiency notes for next time:

- **Scope it.** "Find the top 3 token levers for the Statement pipeline" returns a tighter,
  cheaper answer than "anything." Unbounded prompts invite unbounded (token-expensive)
  exploration.
- **Mind the cadence.** "Search the web / check the news / keep up to date" is fine once;
  if this becomes a *recurring* routine, the repeated web-search + fetch cost adds up. For a
  standing routine, cache the findings here and only re-survey on a monthly cadence or when a
  new model ships.
- **Ask for a format.** "Reply with a ranked table + one paragraph each" bounds the output
  tokens and makes the result easier to act on.

---

*Newest entries first if this becomes a log. First written 2026-06-22 by NARF.*
