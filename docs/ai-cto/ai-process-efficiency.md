# AI Process Efficiency — Review (2026-06-27)

How we (the founder) and the AI (Claude + the local LLM stack) work together, and where that
process wastes tokens, money, and time. NARF (AI CTO) review. Newest entries first per house
style.

**Scope of the word "process":** the human↔AI loop — how prompts are written, how much context
each session drags in, which model answers which task, and how the public `localDNS` LiteLLM
router (`10-ai-orchestration/`) splits work between the t630's local Ollama tiers and the Claude
cloud tiers. The good news up front: **the hard infrastructure already exists** (Odin supervisor,
privacy gate, reasoning ladder, local RAG). The waste is in *not using it for our own AI work*,
plus a few cloud-side levers we haven't switched on.

---

## TL;DR — ranked by (savings ÷ effort)

| # | Lever | Effort | Est. savings | Status |
| - | ----- | ------ | ------------ | ------ |
| 1 | **Stop loading 7 full CLAUDE.md files per session** (≈1,040 lines) — scope sessions to one repo; factor shared house-style out | Low | Large, *every* turn | Not done |
| 2 | **Turn on prompt caching** on the LiteLLM→Claude path (system prompt + repo context) | Low–Med | 90% on cached input | Not done |
| 3 | **Right-size the model per task** — default Sonnet, escalate to Opus only for hard reasoning; Haiku for grunt subagents | Low | 40–80% on cloud | Partial |
| 4 | **Batch API for non-interactive jobs** (monthly statements, recruiting emails, log summaries) | Med | 50% (stacks with caching → ~95%) | Not done |
| 5 | **Actually route the 60–70% of simple tasks to local** qwen2.5 (classify/extract/summarize) — the infra is built, we just don't aim work at it | Med | $0/inference on that slice | Underused |
| 6 | **Session hygiene** — `/clear` between unrelated tasks, `/compact`, lower thinking effort for simple work | Low | 40–70% on focused tasks | Habit |
| 7 | **Tighter prompting** — scope, success criteria, output format, budget (see the critique of *this* request below) | Low | Cuts exploration tokens | Habit |

---

## 1. The biggest lever: context bloat (do this first)

This session was launched at `/home/user`, so the harness injected **every repo's `CLAUDE.md` —
about 1,040 lines total** — into the system prompt before a single word of work. Five of the
seven repos repeat the *identical* "House style: ordering & typography" block verbatim (~25 lines
× 7 ≈ 175 lines of pure duplication), and three are stubs/guides whose CLAUDE.md isn't relevant
to most sessions.

That payload is re-sent on **every turn** of **every** session that opens from the parent
directory. It is the single largest recurring token cost in our process, and it's invisible
because it's automatic.

**Fixes (cheapest first):**

- **Open Claude in the specific repo you're working in**, not the parent folder. One repo's
  CLAUDE.md instead of seven. This alone is the biggest single win and costs nothing.
- **Extract the shared house-style block into one file** (e.g. `localDNS`-published or a gist) and
  replace the 25-line block in each CLAUDE.md with a 2-line pointer. Per Anthropic's guidance,
  CLAUDE.md should be *short and high-signal* — ours have grown into full handbooks. Move the
  funnel diagrams, money-flow ASCII, and deploy tables into README and link them; keep CLAUDE.md
  to the briefing.
- **Prune stub CLAUDE.md files** (azure-lab, claude-code-homelab) to a few lines until they have
  real scope.

Target: get the always-loaded context down by half. KDnuggets and the 2026 Claude Code
optimization guides put context management as the #1 cost lever, ahead of model choice.

---

## 2. Prompt caching is the highest-ROI switch we haven't flipped

A cache hit costs **10% of the standard input price**. For a system prompt over ~2,000 tokens
hit more than a few times in 5 minutes, it pays for itself almost immediately. Real-world
write-ups report 80–95% cache-read rates and bills dropping ~10× (one went $720→$72/mo).

- **Claude Code already caches** its system prompt and conversation prefix for us — which is
  *another* reason the bloated CLAUDE.md hurts: a cached 1,040-line prefix is cheaper than an
  uncached one, but a *short* one is cheaper still, and edits to any CLAUDE.md bust the cache.
- **Our LiteLLM router does NOT set `cache_control`** on the Claude path (`config.yaml`
  cloud-* and cloud-overflow tiers). Anything we send through Open WebUI / the supervisor to
  Claude pays full input price every call. LiteLLM supports Anthropic prompt-caching
  passthrough — add a cache breakpoint on the stable system/context block. This is a
  config-only change, P2 tech-debt sized.
- Cache the **stable** part (system prompt, repo context, schema), not the volatile tail.
  Blocks must be ≥1,024 tokens to cache at all.

---

## 3. Right-size the model — and apply our own router philosophy to ourselves

Our `localDNS` router preaches "route, don't shard" and pins sensitive work local — good. But the
cloud tiers over-reach for Opus:

- `cloud-overflow`, `cloud-explore`, **and `cloud-vision`** all point at `claude-opus-4-8`, the
  most expensive model. `cloud-code` correctly uses Sonnet.
- **`cloud-overflow` = Opus means every local failover lands on the priciest tier.** Make the
  *first* overflow Haiku 4.5 or Sonnet, and reserve Opus for an explicit "hard" escalation.
  Haiku 4.5 is ~$1/$5 per MTok vs Opus's premium; for classification/extraction/short-summary
  overflow, Haiku is plenty.
- In **Claude Code** itself: default to Sonnet, escalate to Opus only for architecture/multi-step
  reasoning, and set `model: haiku` on grunt subagents (log scraping, file search, git). Reported
  40–70% savings on focused tasks.

> ⚠️ This dovetails with open **TD-14**: `local-reason`'s fallback chain includes
> `cloud-overflow`, so a *sensitive* task can fail over to Opus-in-the-cloud. Fixing the model
> tier and the privacy fallback are the same edit to `config.yaml` — do them together.

---

## 4. Batch API for everything that isn't a live conversation

Batch processing is **50% off across all models**, async within 24h, no quality loss — and it
**stacks with caching** (a cached batch Haiku call ≈ $0.05/MTok, ~95% off standard).

Natural batch candidates in our workflow, none of which need a live human:

- **Monthly statement composition** (stage 06 — already "a penny a home"; halve it).
- **Recruiting / marketing copy** drafts (stages 02, 09).
- **DNS / activity log summarization** into "Handled For You" entries.
- Any **overnight** scheduled routine (like this one) that isn't time-critical.

If a job can wait an hour, it should be a batch job.

---

## 5. We built a local triage engine — now aim work at it

Research puts ~60–70% of typical AI workloads (classification, extraction, formatting, short
summarization, intent detection, embeddings) inside the reach of a local 3–7B model — i.e. **free
at inference**. We have `qwen2.5:3b/7b` and `nomic-embed-text` on the t630 and a privacy gate that
*wants* to use them.

Today most of our real AI work goes straight to Claude cloud. Concretely, route to local first:

- Lead/inbox **classification** and tagging for the master list (stage 08).
- First-draft **summaries** of call notes and logs.
- **Embeddings / RAG** over our own repos (already wired via `local-embed` — use it for repo Q&A
  instead of pasting files into a cloud prompt).
- Template-filled **"Handled For You"** entries from a structured event.

Keep Claude for what local can't do well: multi-step agentic work, long-context synthesis, the
customer-facing voice, hard code. The hybrid case studies show 60–83% total cost reduction from
exactly this split.

---

## 6. Session & prompting hygiene (cheap habits)

- `/clear` when switching to unrelated work (stale context is paid for every turn); `/rename`
  first if you'll want `/resume`.
- `/compact` long sessions to keep the signal, drop the noise.
- Lower **thinking effort** (or disable extended thinking) for simple tasks — thinking tokens
  bill as output.
- Delegate verbose work (test runs, log dumps, doc fetches) to **subagents** so only the summary
  returns to main context — but not for trivial one-liners, where the startup overhead isn't
  worth it.

---

## 7. Critique of the request that generated this report

The founder explicitly asked whether *this very prompt* was inefficient. It was — and it's a
perfect teaching case:

**What it did well:** gave honest intent ("reduce token use, better prompting, leverage other
AI") and permission to use the web.

**Where it cost tokens:**

- **No scope or boundary.** "ANYTHING that could help… Look for best practices… Check the news"
  forces broad, open-ended exploration — the most token-hungry mode there is. The model can't
  tell when it's done.
- **No success criteria or output format.** "Let me know" doesn't say *a ranked list? a doc? a
  one-line answer?* So the model over-produces to be safe.
- **No budget or depth cap.** Open-ended depth → maximal search.
- **Mixed registers** ("Check the news," "Thanks!") read as conversational, but the task is a
  deliverable — the model spends effort reconciling the two.

**A tighter rewrite (same intent, a fraction of the tokens):**

> *"Audit our human↔AI process for cost. Deliverable: a ranked markdown doc in
> `DESIGN/docs/ai-cto/`, top 5 levers, each with effort + estimated savings + the exact file to
> change. Ground it in our LiteLLM `config.yaml` and CLAUDE.md sizes. Do ≤4 web searches for
> 2026 best practices; cite them. Budget ~150k tokens. Skip anything we already do well."*

That version names the output, the location, the depth, the grounding, the search cap, and the
budget — so the model stops at "good," not "exhaustive." **General rule: every prompt should
answer four questions — what's the deliverable, what does done look like, how deep do I go, and
what should I *not* do.**

---

## 8. The meta-point (and the irony, owned)

This routine ran on **Opus 4.8 (1M context)** — our most expensive tier — against a prompt with
no budget, with ~1,040 lines of CLAUDE.md pre-loaded, and did broad web research. It is itself a
live example of nearly every inefficiency above:

- A scheduled, non-interactive audit like this is a textbook **Batch + Sonnet/Haiku** job, not an
  interactive-Opus one.
- It loaded seven repos' context to analyze a cross-repo topic — defensible here, wasteful as a
  default.
- An open-ended prompt drove broad search.

**Recommended standing change for routines:** run scheduled/monitoring routines on Sonnet (escalate
to Opus only on a real finding), scope them to the relevant repo, give them an explicit budget,
and prefer the Batch API when the result can wait.

---

## Sources (fetched 2026-06-27 — this space moves weekly; re-verify model IDs & prices before acting)

- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Deep Dive: cut costs 90% — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Prompt Caching $720→$72 — Du'An Lightfoot / Medium](https://medium.com/@labeveryday/prompt-caching-is-a-must-how-i-went-from-spending-720-to-72-monthly-on-api-costs-3086f3635d63)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Claude Haiku 4.5 — Anthropic](https://www.anthropic.com/claude/haiku)
- [Anthropic API Pricing 2026 — CloudZero](https://www.cloudzero.com/blog/claude-api-pricing/)
