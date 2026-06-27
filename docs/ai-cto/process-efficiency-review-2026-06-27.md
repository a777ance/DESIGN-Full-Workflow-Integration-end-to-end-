# Process Efficiency Review — User ↔ AI (2026-06-27)

*Where our Claude tokens actually go, and how to spend fewer of them without losing
quality. Findings are ranked by impact. Numbers measured from this repo set on
2026-06-27; prices are current as of June 2026 (see Sources).*

> **One-line answer:** the biggest waste isn't *what we ask* — it's *what every session
> drags in before we ask it*. We pay ~10k tokens of CLAUDE.md plus a mandated ~10-doc
> "session-start ritual" on **every** turn of **every** session, before a single useful
> word. Fix that first; it dwarfs everything else.

---

## A. Top wins, ranked by impact

| # | Lever | Effort | Est. saving | Status today |
| - | ----- | ------ | ----------- | ------------ |
| 1 | Trim the **session-start ritual** (NARF/ZORT auto-reads) to load-on-demand | Low | 30–60% of fixed per-session cost | We auto-read ~10 docs every session |
| 2 | Slim the two heavy **CLAUDE.md** files (DESIGN 2,608w, localDNS 2,728w) | Low | ~7k→~3k tokens/turn on those repos | Both are ~2× the recommended size |
| 3 | Actually **route cheap work to the local LLM** we already run (LiteLLM :4040) | Med | 60–83% on the offloadable slice | Infra exists; underused |
| 4 | **Right-size the model** per task (Haiku/Sonnet vs Opus) | Low | 5× between Opus and Haiku | Defaulting high |
| 5 | **Prompt-caching discipline** (stable prefix, don't bust the cache) | Low | up to 90% on cached input | Implicit only |
| 6 | **Fresh session per task** + compact early; stop "obese threads" | Low | compounding | Habit |
| 7 | Tighten **the prompts themselves** (scope, format, budget) | Low | variable, large on research tasks | See §E |

---

## B. The #1 drain: context loaded *before* the work

The rule from the field is blunt: *"a 5,000-token CLAUDE.md costs 5,000 tokens before
you've typed a word, every turn, every session."* That cost is recurring, not one-time,
because it sits in the prompt prefix on every API call in the session.

**Measured, this repo set (2026-06-27):**

| Repo | CLAUDE.md (words) | ≈ tokens |
| ---- | ----------------- | -------- |
| localDNS | 2,728 | ~3,600 |
| DESIGN (this repo) | 2,608 | ~3,500 |
| MARKETING | 1,445 | ~1,900 |
| customers | 562 | ~750 |
| claude-code-homelab | 371 | ~500 |
| Azure-lab | 316 | ~420 |
| **All combined** | **8,030** | **~10,700** |

Most sessions touch one repo, so the per-session CLAUDE.md hit is ~3,500 tokens on the two
big repos. **But** our CLAUDE.md then *mandates a session-start reading list*:

- **DESIGN** (§5 NARF + §6 ZORT): read `portfolio.md`, `roadmap.md`, `tech-debt.md`,
  `decisions.md`, **plus** `ai-cfo/{portfolio,decisions,metrics,runway,budget}.md` **plus**
  `MARKETING/docs/ai-cfo/context.md` — **~10 files** before any task.
- **localDNS / customers / MARKETING / homelab / Azure-lab**: each opens with "read
  `docs/ai-cto/context.md`."

That ritual is the "obese thread from turn zero." For a one-line edit it can mean
20k–40k tokens of reading we never use — and it reloads on every fresh session.

**Fix (low effort, high payoff):**

1. **Make the reading list conditional, not mandatory.** Reword to: *"If the task touches
   finances, read ZORT docs; if it touches architecture, read NARF docs; otherwise skip."*
   A session that fixes a typo should not load the budget.
2. **Split CLAUDE.md into a thin always-on core + linked detail.** Keep the always-loaded
   file to the ~15 rules that change behavior (voice rule, house style, "push to main / use
   branch", honesty rule, secrets rule). Move the stage map, service tables, and deploy-path
   tables into README/linked files Claude reads *only when the task needs them*. Target the
   always-on CLAUDE.md at **<1,200 words (~1,500 tokens)** per repo.
3. **Prefer `/recap`** (Apr 2026) over replaying history when resuming a session.

This single section is worth more than every other item combined, because it's a *fixed
recurring tax* on every interaction.

---

## C. Use the hybrid LLM we already own

We are paying frontier prices for work a 7B local model does fine — while a LiteLLM router
(`10-ai-orchestration`, port 4040) and a reasoning ladder (`local-reason` deepseek-r1:1.5b
on the t630, `cloud-gpu-reason` on a rented GPU) sit largely idle for routine work. The
industry pattern: route **85–95%** of low-complexity calls local, keep **5–15%** on the
frontier; documented savings **60–83%** on the offloaded slice.

**What to offload to the box (no quality risk):**

| Task | Send to | Why |
| ---- | ------- | --- |
| `check-docs.py`-style link/anchor validation, lint, format | **deterministic script / local** | No model needed at all |
| Commit-message drafting, changelog bullets | **local 7–8B instruct** | Template-shaped, low stakes |
| Classifying a lead / routing a CRM field, short summaries | **local 7–8B** | Classification is the clearest local win |
| Embeddings (if/when we add RAG over the repos) | **local `nomic-embed-text`** | Called constantly; frontier is overkill |
| Statement *prose* QA, architecture decisions, customer-facing copy, security review | **Claude (Sonnet/Opus)** | Judgment + the voice rule matter |

**How to wire it:** point a *non-Claude-Code* automation lane at
`ANTHROPIC_BASE_URL=http://192.168.1.118:4040` (LiteLLM is Anthropic-compatible) so Zapier/
Make jobs (stage 11) and the nightly statement/CRM chores hit local models, while Claude
Code keeps the real Anthropic endpoint for the hard work. Don't try to run Claude Code
*itself* on a local 7B — quality drops and it's the wrong tool; route at the *task* layer.

⚠️ **Honor the privacy invariant.** The DNS split (`streaming-forward.conf`) already keeps
sensitive lookups off Cloudflare; mirror that discipline here — **never route real customer
PII from `customers/` to a rented cloud GPU.** Local box or Anthropic only for anything
carrying a real name. Fail-closed on sensitive data, exactly like the resolver does.

---

## D. Cheaper Claude, same Claude

- **Right-size the model.** June-2026 rates per 1M tokens: **Opus 4.8 $5/$25**,
  **Sonnet 4.6 $3/$15**, **Haiku 4.5 $1/$5** (output is 5× input on all three). Opus→Haiku
  is a **5×** swing. Default to **Sonnet** for normal coding/doc work; reserve **Opus** for
  genuinely hard reasoning; use **Haiku** for mechanical edits and triage.
- **Protect the cache.** Cached input is **90% cheaper**. Caching holds only if the prompt
  *prefix* is byte-stable — so keep CLAUDE.md and tool defs at the front and *unchanged*
  mid-session. Editing CLAUDE.md, swapping tools, or reordering context mid-task busts the
  cache and you re-pay full freight. (See arXiv 2601.06007, "Don't Break the Cache.")
- **Batch the non-interactive jobs.** Monthly statement generation, bulk CRM enrichment,
  nightly doc checks → the **Batch API is 50% off**. These aren't latency-sensitive.
- **One task per session; compact early.** Set the compact threshold to ~70% rather than
  riding to 95%. When the task shifts, start fresh — stale file reads and dead tool output
  never leave the window otherwise (the single biggest silent drain in long threads).
- **Output discipline.** Agentic *output* tokens cost 5× input and dominate long runs. Tell
  Claude to be terse by default and to skip narrating every step (a house "terse output"
  rule, or the community "Caveman/terse" output style, reports ~65% output reduction).

---

## E. The prompts themselves — including the one that triggered this

The honest critique you asked for: **the triggering prompt is itself an example of the
expensive pattern.** It says *"Locate inefficiencies… Anything you could possibly think of…
Search the web… Check the news… ANYTHING that could help."* That is unbounded scope + an
open invitation to do the single most token-hungry thing there is (open-ended web
research), with no output format and no budget. It reliably produces a large, expensive,
sprawling run — ironic for a token-efficiency request.

It worked out here, but the cost was higher than it needed to be. What good prompting looks
like for this same intent:

**Before (what was sent):**
> "Locate inefficiencies in our PROCESS… Anything you could possibly think of… Search the
> web… Check the news… ANYTHING that could help. Thanks!"

**After (same goal, ~3–5× cheaper, more actionable):**
> "Review our Claude usage for token waste. **Scope:** the per-session fixed cost
> (CLAUDE.md + session-start reads) and our local-LLM routing. **Do:** measure CLAUDE.md
> sizes in-repo first; do **≤4** web searches only to confirm current pricing/features;
> skip general 'news.' **Deliver:** a ranked table of ≤7 fixes with est. savings and effort,
> as a markdown file on the branch. **Budget:** keep it under ~150k tokens."

Reusable rules that make any prompt cheaper:

1. **Bound the scope** — name the subsystem, not "the process."
2. **Cap the research** — "≤N searches, only to verify X," not "search the web / check the
   news." Unbounded research is where tokens hemorrhage.
3. **Specify the deliverable and its length** — "ranked table, ≤7 rows, markdown file."
   Without a cap, output (the 5×-priced tokens) balloons.
4. **State a token/time budget** — gives the model a stopping rule.
5. **Front-load the constraints, don't repeat them** — "ANYTHING… ANYTHING… Thanks!" adds
   tokens and emphasis the model must reconcile, without adding information.
6. **For recurring routines, freeze the prompt** so the cache holds across runs.

---

## F. Process / workflow notes specific to us

- **Scheduled multi-repo routines** (like this one) each boot a full context. If we run
  the same sweep across 7 repos, that's 7× the fixed tax in §B — so §B's savings multiply
  here. Consider one routine that fans out with *small, self-contained* subagent tasks
  rather than 7 fat full-context sessions. **Caution:** agent-team/multi-agent runs can burn
  **~7× the tokens** of a single session (each teammate keeps its own window) — only fan out
  when the work is genuinely parallel and each subtask is small.
- **House-style overhead is real but it's a deliberate choice.** The reverse-chronological /
  Z→A / "reverse the blocks, never renumber" / Gill-Sans rules add instruction tokens and a
  nontrivial chance of doc-edit mistakes (every edit must reason about ordering). Not asking
  to drop it — just flagging it's a recurring cost, and the rules belong in the *thin* core
  CLAUDE.md (they do change behavior), while everything else gets demoted per §B.
- **Keep using the doc-integrity gate** (`tools/check-docs.py`) — that's the *right* pattern:
  a deterministic script doing what we'd otherwise pay a model to eyeball.

---

## G. What to ignore / watch

- **Don't run Claude Code on a local 7B to "save money."** Quality collapse costs more in
  rework than it saves. Route at the *task* layer (§C), not the *agent* layer.
- **Don't over-fan-out.** Multi-agent is ~7× tokens; reserve it for truly parallel work.
- **Watch (fast-moving, recheck monthly):** model prices and the Opus/Sonnet/Haiku lineup;
  context-editing / auto-compaction defaults; new output styles; whether LiteLLM keeps
  Anthropic-API compatibility after Anthropic SDK changes.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude API Pricing 2026: Opus 4.8, Sonnet 4.6 & Haiku 4.5](https://aimodelcalc.com/guides/claude-api-pricing)
- [Steering Claude Code: skills, hooks, subagents and more — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt Caching Deep Dive: Cut Anthropic API Costs by 90% — Agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Don't Break the Cache: Prompt Caching for Long-Horizon Agentic Tasks — arXiv 2601.06007](https://arxiv.org/html/2601.06007v2)
- [Hybrid LLM Routing: Ollama + Claude API Without Quality Degradation — DEV](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [AI Agents Burn 50x More Tokens Than Chats — LeanOps](https://leanopstech.com/blog/agentic-ai-cost-runaway-token-budget-2026/)
