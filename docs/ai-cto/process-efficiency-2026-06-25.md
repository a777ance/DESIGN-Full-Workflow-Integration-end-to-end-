# AI Process Efficiency Review — 2026-06-25

*Owner: NARF (AI CTO). Scope: the user ↔ AI loop across all seven A777ance repos. Newest
findings first, per house style. This is a point-in-time snapshot — the model/pricing
landscape moves weekly, so re-run the review quarterly (see §7).*

---

## TL;DR — where the tokens actually go

We measured the always-on cost of this setup. The three biggest leaks, in order:

1. **Every repo's full `CLAUDE.md` is injected on every turn.** Across the seven repos
   that's **~11,000 tokens of always-on context per turn**, before you type anything.
   The two big ones (`DESIGN` ~3,480 tok, `localDNS` ~3,640 tok) are each ~18× over the
   community "keep it under ~200 lines / ~2k tokens" guideline.
2. **The NARF/ZORT session-start reading ritual is ~16,000 tokens of doc reads** on
   *every* session before any real work. `docs/ai-cfo/metrics.md` alone is 24.7 KB
   (~6,000 tokens) and the CFO ritual reads six files.
3. **We pay full price for a lot of work a local model already on the t630 could do.**
   The LiteLLM router (port 4040) + Ollama ladder is already built — it's underused as a
   cost lever.

Fixing #1 and #2 is mostly editing and is the highest ROI. #3 is the structural win.

---

## 1. Always-on context: trim the `CLAUDE.md` files (biggest, easiest win)

**Finding.** A `CLAUDE.md` is re-sent on every request; a 3,500-token file costs 3,500
tokens *per turn*. Over a 50-turn session that's 175k tokens of repeated context for one
file. Current sizes:

| Repo | Lines | ~Tokens |
| ---- | ----- | ------- |
| `localDNS` | 326 | 3,640 |
| `DESIGN-…` | 295 | 3,480 |
| `MARKETING` | 214 | 1,930 |
| `customers` | 80 | 750 |
| `claude-code-homelab` | 75 | 490 |
| `Azure-lab` | 50 | 420 |
| **Total always-on** | — | **~11,000** |

**Why it's bloated.** Both big files inline things that belong in on-demand docs: the full
Unbound drop-in table, the nftables deploy checklist, the entire deploy-paths table
(`localDNS`), the full funnel diagram and stage map (`DESIGN`). These are *reference*, not
*always-true rules* — they're needed a few times, not every turn.

**Fix — the "rules vs. reference" split** (industry consensus for 2026):

- `CLAUDE.md` keeps only what is true for *nearly every task*: the voice rule, the
  house-style ordering/typography, the "push to main / push to branch X" rule, the
  one-source-of-truth rule, secrets rule, and a one-line pointer to each reference doc.
- Everything else becomes a **Skill** or a plain doc that loads **on demand**. The
  reported win from moving domain knowledge out of always-on context into skills is
  ~15k tokens recovered per session (~82% less upfront load).
- Target: get each big `CLAUDE.md` under ~150 lines / ~1,500 tokens. That alone removes
  ~5–6k tokens/turn.

**Concrete moves:**
- `localDNS`: move the Deploy-paths table (Section C), the nftables checklist (Section F),
  and the Unbound drop-in detail (Section D) into the existing `README.md`/skill; leave a
  one-line "deploy paths → README §C" pointer.
- `DESIGN`: the funnel ASCII, the stage map, and the verification walkthrough are
  reference — link them, don't inline them.

---

## 2. Cut the session-start reading ritual

**Finding.** The DESIGN `CLAUDE.md` instructs NARF to read 4 docs and ZORT to read 6 at
**every** session start (portfolio, roadmap, tech-debt, decisions ×2, metrics, runway,
budget, + `MARKETING/.../context.md`). Total ~65 KB ≈ **~16,000 tokens** consumed before
any task — most of it irrelevant to the task at hand.

**Fix:**
- Make the ritual **conditional, not unconditional**: "If the task touches finances, read
  the CFO docs; if it touches the roadmap, read the CTO docs." Most sessions need neither
  in full.
- Maintain a single **`STATE.md` digest** (≤1 screen) that NARF/ZORT update at session
  *end* — the next session reads the digest, not all 10 source docs. Source docs are read
  only when a specific number is needed.
- `metrics.md` at 24.7 KB is a log — it should be append-only and **never** read whole at
  startup. Keep a "current KPIs" header block (≤30 lines) and leave the history below it.

Combined with §1, a typical session starts ~25–30k tokens lighter.

---

## 3. Hybrid local + Claude: route by task, not by habit (the structural win)

**You already own the hardware for this** — `10-ai-orchestration` on the t630 runs LiteLLM
(`:4040`) + Ollama, with a reasoning ladder (`local-reason` deepseek-r1:1.5b on CPU,
`cloud-gpu-reason` on a rented GPU, `cloud-overflow`). It is currently a side-experiment;
it should be the default cost router.

**Current best practice (2026):** put an intelligent routing layer between you and the
providers. RouteLLM-style routers hit ~95% of frontier quality while sending only ~14% of
requests to the expensive model — **~85% cost reduction** on benchmark workloads. Reported
hybrid savings run **60–80%**.

**What to send where:**

| Task | Route to | Why |
| ---- | -------- | --- |
| Commit-message drafting, changelog/log formatting, "newest-first" re-ordering, link-check triage, doc-lint, JSON/CSV reshaping, simple regex/grep summarizing | **Local (Ollama on t630)** | Mechanical, low-sensitivity, no frontier reasoning needed — ~free |
| Roster/statement data transforms over **real customer data** | **Local only** | Privacy: customer PII never leaves the box (this repo's §1 rule). A strong argument for local *regardless* of cost |
| Architecture decisions, ADR drafting, multi-file refactors, anything customer-facing in voice | **Claude (Opus/Sonnet)** | Quality + judgment matters |
| Cross-repo reasoning, this kind of review | **Claude** | Needs the big context window |

**How:** static rules cover ~80% of cases ("all classification/formatting → local; all
reasoning → cloud"). LiteLLM already does **fallback routing** — if local fails or low-
confidence, it escalates to the API automatically. Start with static rules; add a trained
classifier (RouteLLM) only if the rules prove too blunt.

**Caveat (do not skip):** Claude Code itself can point at an LLM gateway, but the local
deepseek/qwen-class models are **not** substitutes for Opus *inside the agentic coding
loop* — they're weak at long tool-use chains. The hybrid win is for **discrete sub-tasks
you hand off**, not for replacing the driver. Keep Claude as the orchestrator; offload the
grunt work.

---

## 4. Prompt caching — make it work for you

**Finding.** Anthropic cache reads cost **10% of normal input** (90% discount); writes cost
1.25×. Default TTL is **5 minutes** (1-hour option exists). The lever only pays off if the
*stable* part of the prompt (the big `CLAUDE.md` blocks, system context) stays byte-stable
across turns and turns happen <5 min apart.

**Implications for our loop:**
- The trimming in §1/§2 and caching are complementary: smaller stable prefix + cache = the
  always-on cost approaches ~10% of even the trimmed size on warm turns.
- **Batch a session's work into one sitting.** Gaps >5 min cold the cache and you re-pay
  the write. The scheduled-routine pattern (long sleeps) is the worst case for cache — for
  *interactive* work, keep momentum.
- If/when we build any API-side automation (statement generation, the stage-11 glue),
  put the static system prompt + schema first and mark it cached; expect 30–50% input-cost
  cut on those loops.
- **Context editing** (new): for long agent runs, prune stale tool outputs instead of
  paying to summarize them. Relevant to long Claude Code sessions here.

---

## 5. Model selection & workflow discipline

- **Start in Sonnet, escalate to Opus only when needed.** Opus 4.6 dropped to $5/$25 (from
  $15/$75) but is still ~5× Sonnet. Most doc edits, link checks, and formatting don't need
  Opus. (Note: Opus 4.7's updated tokenizer can emit up to ~35% more tokens for the same
  text — watch output-token cost on verbose tasks.)
- **Use Plan Mode for anything touching 2–3+ files.** A plan is a few hundred tokens; a
  wrong implementation is thousands plus the redo.
- **One task per session; `/clear` between tasks; `/compact` before sessions run long.**
  Old debugging logs in context are pure waste on every subsequent turn.
- **Use subagents to isolate noisy side-quests** (broad searches, log-grepping). The
  verbose output stays in the child context; only the summary returns. They're not
  automatically cheaper — use them when the avoided main-context clutter outweighs the
  startup overhead.
- **Watch the billing change:** Anthropic *planned* (then paused, mid-June) moving Agent
  SDK / `claude -p` usage onto separate metered credits at API rates. If/when it lands, any
  headless/scripted automation we build will bill separately from the subscription — design
  the stage-11 glue assuming metered API pricing, and lean on local models there.

---

## 6. Critique of the prompt that generated this report

Your prompt was effective for a *one-off* exploratory research ask — open-ended is fine
when you genuinely want a wide net. But for anything recurring it's inefficient, for three
reasons, each with a fix:

1. **Unbounded scope** ("ANYTHING that could help… Anything you could possibly think of").
   This invites the model to keep going with no stop condition — more tokens, diffuse
   output. *Fix:* cap it — "Give me the top 5 changes ranked by token saved per hour of
   effort."
2. **No output contract.** I had to guess you wanted a written report. *Fix:* state the
   artifact — "Write a ≤2-page memo to `docs/ai-cto/`, table of fixes with est. savings."
3. **No constraints given.** Are we optimizing the Max subscription or API spend? Which
   repos? Is local-model latency acceptable? Stating these removes a research branch.

**A reusable template** for this recurring review (saves re-explaining every time):

> *"Quarterly AI-process review. Constraints: [subscription/API], [repos in scope],
> [privacy rules]. Compare our current loop against this checklist [link to this doc].
> Output: update `docs/ai-cto/process-efficiency-<date>.md` in place — only the deltas
> since last quarter, ranked by token-saved-per-effort. Cite sources. Stop at 5 findings."*

Better still: make this review a **Skill** (or a saved slash-command) so the checklist,
output path, and constraints live in the repo, not in your prompt. Then the recurring
prompt is just `/process-review` — a few tokens instead of a paragraph you re-type and that
gets re-sent in context.

A meta-note: the trailing "Thanks!" and pleasantries cost ~nothing and are fine — politeness
is not the inefficiency. The scope and missing output contract are.

---

## 7. Do-this-now checklist (ranked by ROI)

| # | Action | Est. saving | Effort |
| - | ------ | ----------- | ------ |
| 1 | Trim `localDNS` + `DESIGN` `CLAUDE.md` to rules-only; move reference tables to README/skills | ~5–6k tok/turn | 1–2 h |
| 2 | Make NARF/ZORT startup reads conditional; add a 1-screen `STATE.md` digest; stop reading `metrics.md` whole | ~12–15k tok/session | 1–2 h |
| 3 | Promote the t630 LiteLLM router to default for mechanical + PII-touching sub-tasks; static rules + fallback | 60–80% on offloaded work | 2–4 h |
| 4 | Adopt session discipline: Sonnet-first, Plan Mode, one-task-per-session, `/clear` | 40–70% on focused tasks | habit |
| 5 | Turn this review into a `/process-review` skill with the template in §6 | recurring prompt cost → ~0 | 1 h |
| 6 | When building stage-11/statement automation on the API, design for prompt caching + metered pricing | 30–50% input cost on those loops | design-time |

---

## Sources (accessed 2026-06-25)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [RouteLLM — lm-sys/RouteLLM (GitHub)](https://github.com/lm-sys/routellm)
- [LiteLLM Auto Routing docs](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Prompt Caching in 2026: Anthropic, OpenAI, Azure Compared — technspire](https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins)
- [Semantic Prompt Engineering Cuts Token Waste 74% — CostLayer](https://costlayer.ai/blog/semantic-prompt-engineering-reduce-ai-token-waste)
- [A Mental Model for Claude Code: Skills, Subagents, and Plugins — Level Up Coding](https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05)
- [Anthropic June 15 2026 billing change (paused) — DigitalApplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- [Claude Pricing in 2026 — CloudZero](https://www.cloudzero.com/blog/claude-pricing/)
