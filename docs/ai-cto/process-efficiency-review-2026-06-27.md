# Process efficiency review — the user ↔ AI loop

**Author:** NARF (AI CTO), scheduled routine · **Date:** 2026-06-27
**Question asked:** "Locate inefficiencies in our PROCESS — between the user and the AI.
Is there a better way to reduce token use? Better prompting? Leverage other AI? Run a
hybrid local LLM + Claude API? Keep up to date — check the news."

This is a review of *how we work with Claude*, not of the product. It is deliberately
short and ranked by payoff. Everything here is sourced against the live Claude docs and
2026 best-practice write-ups (sources at the bottom); re-run it quarterly because the
surface changes fast.

> **The one-line answer:** the biggest cheap win is **context hygiene** (what we re-send
> every turn), and the biggest structural win is **routing the cheap 70% of work off the
> Opus API** — onto Haiku/Sonnet *and* onto the local box we already own. We're already
> halfway there; we just haven't pointed the router at the right work.

---

## A. The single most expensive habit: re-billing context every turn

Every token in the context window is **re-charged on every turn** of a conversation —
input is reprocessed each time, not just once. So the question that governs cost isn't
"how good was my prompt," it's "what am I dragging along on every single turn."

Two concrete leaks in *our* setup:

### A1. The CLAUDE.md baseline (the constant tax)

`CLAUDE.md` loads on **every turn of every session**. Current sizes:

| Repo | words | ≈ tokens | loads when… |
| ---- | ----: | -------: | ----------- |
| localDNS | 2,728 | ~4,000 | every localDNS session |
| DESIGN (this repo) | 2,608 | ~3,800 | every DESIGN session |
| MARKETING | 1,445 | ~2,100 | every MARKETING session |
| customers | 562 | ~800 | — |
| claude-code-homelab | 371 | ~550 | — |
| Azure-lab | 316 | ~460 | — |
| **all 7 combined** | **8,030** | **~11,700** | **a cross-repo run like this routine** |

A 4,000-token CLAUDE.md costs 4,000 tokens *before anyone types a word*, on every turn,
for the life of the session. The localDNS and DESIGN files are the two to trim — they're
excellent reference docs, but reference material doesn't belong in the always-loaded file.

**Fix (no information lost):**
- Keep `CLAUDE.md` to the briefing a new reader needs *to act*: the rules, the map, the
  "don't do X." Push the long tables (deploy-path table, the full Unbound drop-in matrix,
  the nftables deploy checklist) into `README.md` / `network-context.md` and link to them.
  Claude reads the linked file *only when the task needs it* — pay-per-use instead of
  pay-always. Target: each CLAUDE.md under ~1,500 words.
- This routine (and any cross-repo automation) pays the full ~11.7k every turn. If a
  scheduled job only touches one repo, run it *scoped to that repo* so it loads one
  CLAUDE.md, not seven.

### A2. Session hygiene — `/clear` and `/compact`

The highest-ROI habit in interactive use is `/clear` at the **start of each new task**.
Old, unrelated context is dead weight you keep paying to reprocess. Use `/compact` when
you need continuity but the thread has gotten long. One write-up reports a 72% monthly
spend drop from caching + budgets + model switching + this discipline alone.

### A3. Prompt caching is on — don't silently break it

Claude Code uses prompt caching (cached reads ~0.1× price, cache stays warm ~5 min). The
trap: any byte change in the *prefix* invalidates the cache after it. For our automations,
the silent killers are **timestamps/UUIDs interpolated near the top of a prompt** and
**non-deterministic JSON** (unsorted keys). Keep stable content first, volatile content
last. If a job runs back-to-back, the second run should be largely a cache *read*.

---

## B. Newer Anthropic features that cut tokens (2026) — adopt these

These shipped/matured in 2026 and directly reduce what we pay; we are not using them yet.

| Feature | What it does | Why it matters to us |
| ------- | ------------ | -------------------- |
| **Context editing** | Auto-clears stale tool calls/results from the window as a long agent run grows. Anthropic measured **~84% token reduction** on a 100-turn web-search eval, and runs that would otherwise fail on context exhaustion now complete. | Our long agentic runs (statement builds, multi-stage funnel walks, this routine) are exactly the shape that benefits. |
| **Tool Search Tool** | Loads tool *schemas* on demand instead of all upfront — ~**85%** of tool-definition tokens preserved. | Relevant once an automation exposes many MCP/tools (the Stage-11 glue, the GitHub MCP surface). |
| **Memory tool** | Stores facts in a file outside the context window, consulted on demand. | Cross-session state (e.g. "which households are done this month") without re-stuffing it into every prompt. |
| **Subagents** | Each runs in its *own* context window, does the heavy reading on the side, returns only the answer. | Keep the main session lean — fan a big read-only sweep out to a subagent, keep the conclusion, drop the file dumps. |

---

## C. Model selection — stop paying Opus rates for Haiku work

Current API pricing (per 1M tokens, in/out):

| Model | Input | Output | Use it for |
| ----- | ----: | -----: | ---------- |
| Opus 4.8 | $5 | $25 | Hard reasoning, long-horizon agentic work, the genuinely ambiguous |
| Sonnet 4.6 | $3 | $15 | High-volume production work, summaries, most coding |
| Haiku 4.5 | $1 | $5 | Classification, extraction, formatting, label/triage, short outputs |

Opus output is **5× the price of Haiku**. The standard production task mix is ~60–70%
"simple" (classify/extract/format), ~20–30% moderate, ~10% genuinely needs a frontier
model. Running the simple bucket on Opus is the most common avoidable cost. In Claude Code,
delegate the cheap, mechanical sub-tasks to a Haiku/Sonnet **subagent** and keep the main
Opus loop for the part that's actually hard.

(For batch, non-latency-sensitive jobs — e.g. a monthly sweep over every household's data
file — the **Batch API runs at 50% of standard price**. Worth it for statement-prep passes.)

---

## D. The hybrid local + Claude play — we already own the hardware

This is the highest-leverage structural change, and we're unusually well-positioned:
`10-ai-orchestration` already runs **LiteLLM on the t630** with a reasoning ladder
(`local-reason` = deepseek-r1:1.5b on the box; `cloud-gpu-reason` = full R1 on a rented
GPU; `cloud-overflow` = Claude). The infrastructure to do hybrid routing *exists* — it's
just not pointed at the bulk of the work yet.

2026 write-ups put the realistic saving at **60–80%** of LLM spend by running simple tasks
locally and reserving cloud frontier models for genuine reasoning. The pattern:

```
                    ┌── simple (classify / extract / format / draft commit msg / lint summary)
   request ──route──┤        → local model on the t630   (≈ free, electricity only)
                    ├── moderate → Sonnet 4.6 / batch
                    └── hard / ambiguous → Opus 4.8
   always: cloud fallback if the local model is down (a surprise cloud call beats a dropped job)
```

What to route **local** (privacy-safe and cheap): drafting commit messages, summarizing a
diff or a log, classifying a lead/household record, extracting fields from a form, first-pass
"is this doc link broken" triage, boilerplate generation. None of these need Opus, and many
touch customer data we'd *rather* keep on the box anyway (the `customers` repo is private for
exactly this reason).

⚠️ **Blocker first:** `TD-14` (this repo's tech-debt log) — a `sensitive`-tagged task can
currently fail *over* from `local-reason` to `cloud-overflow` (Claude cloud), because
`allow_cloud=False` isn't enforced at the LiteLLM failover layer. **Fix TD-14 before
expanding local routing**, or we'll leak the very lookups we moved local to protect. Give
`local-reason` a local-only fallback chain (fail closed).

---

## E. On the prompt that triggered this review

You asked me to flag it if it was inefficient — it is, and it's a useful teaching example
because the fix generalizes.

**What made it expensive:** it was a shotgun. "Anything you could possibly think of…
ANYTHING that could help… search the web… check the news… keep up to date." Open-ended,
unbounded scope, several distinct sub-questions bundled together, no output format, no
budget. An unbounded prompt makes the model explore widely (more thinking, more searches,
more tokens) and produce a sprawling answer you then have to mine — the cost lands twice.

**The same request, tightened (≈80% fewer wasted tokens, sharper output):**

> *"Review our Claude Code workflow for cost. Give me the top 5 token-saving changes ranked
> by payoff, each with: the change, rough % saved, and the one command/edit to make it.
> Cover (a) context/CLAUDE.md size, (b) model routing incl. our local LiteLLM box, (c) any
> 2026 Anthropic feature we're not using. Web-check only point (c). One page max."*

The principles, which apply to every prompt we write:
1. **Bound the scope** — "top 5," not "anything."
2. **Specify the output shape** — a ranked table beats an essay you have to re-read.
3. **Set a length/effort ceiling** — "one page max" is a token budget in plain English.
4. **Say when to use the expensive tools** — "web-check only point (c)" stops it searching
   the web for things we already know.
5. **Give the *why*, not just the ask** — "for cost" focuses the whole answer.

A good prompt is itself a token-efficiency tool: it's cheaper to spend 30 seconds scoping
than to pay for a wide exploration and then read it all.

---

## F. Recommended actions (ranked by payoff ÷ effort)

| # | Action | Effort | Est. saving |
| - | ------ | ------ | ----------- |
| 1 | Trim `localDNS` + `DESIGN` CLAUDE.md to <1,500 words; move tables to README/context, link them | 1–2 hrs | ~5k tokens/turn on the two busiest repos |
| 2 | Scope scheduled routines to one repo where possible (don't load 7 CLAUDE.md) | trivial | ~8k tokens/turn on cross-repo jobs |
| 3 | Fix **TD-14** (local-only fallback for `sensitive`), then route simple/PII tasks to the t630 | 1 hr + config | 60–80% of spend on the simple bucket; closes a privacy leak |
| 4 | Default mechanical sub-tasks to a Haiku/Sonnet subagent; reserve Opus for hard reasoning | per-task habit | up to 5× on the misrouted tasks |
| 5 | Adopt `/clear`-per-task and prompt-caching discipline (no timestamps/UUIDs in prefixes) | habit | large, compounding |
| 6 | Use the Batch API (50% off) for the monthly statement-prep sweep | 1 hr | 50% on that workload |
| 7 | Trial context editing on long agentic runs (statement builds, this routine) | small | up to ~84% on long runs |

Items 1, 2, and 5 are free and can be done today. Item 3 is the big structural win but is
**gated on a privacy fix** — do not expand local routing until TD-14 is closed.

---

## Sources (checked 2026-06-27)

- Claude Code — Manage costs: https://code.claude.com/docs/en/costs
- Prompt caching (Claude Platform docs): https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic — Managing context (context editing, memory tool): https://anthropic.com/news/context-management
- Anthropic — Advanced tool use (Tool Search Tool, ~85% reduction): https://www.anthropic.com/engineering/advanced-tool-use
- Anthropic — Effective harnesses for long-running agents: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Hybrid cloud-local LLM architecture (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Hybrid cloud-local cost optimization (60–80%): https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- LiteLLM auto-routing: https://docs.litellm.ai/docs/proxy/auto_routing
- Claude Code token optimization (72% drop case study): https://buildtolaunch.substack.com/p/claude-code-token-optimization
- Model pricing: Claude API model catalog (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5), cached 2026-06-04
