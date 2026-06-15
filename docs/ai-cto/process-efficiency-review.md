# Process-efficiency review — user↔AI workflow & token spend

*NARF (AI CTO) review, 2026-06-15. Triggered by founder's standing question: "Where are
the inefficiencies in how we work with the AI, and how do we cut token use?" This is a
living doc — AI tooling moves week to week, so re-check the dated claims each quarter.*

> **Headline:** the single biggest waste isn't how we prompt — it's the **fixed tax we
> pay before any work starts**. Every session in this repo is told to read ~13,600 tokens
> of "state" docs on top of a 3,500-token CLAUDE.md, and CLAUDE.md re-injects on *every
> turn*. Fixing the fixed cost beats any prompt tweak.

---

## 1. The measured problem (our repos, today)

CLAUDE.md is injected into **every request** — it's a per-turn tax, not a one-time read.
Measured sizes:

| Repo | CLAUDE.md lines | ~tokens/turn | Best-practice ceiling |
| ---- | --------------- | ------------ | --------------------- |
| localDNS | 326 | ~3,640 | <200 lines / ~1,500 tok |
| DESIGN (this repo) | 295 | ~3,480 | " |
| MARKETING | 214 | ~1,930 | " |
| customers | 80 | ~750 | ✅ already lean |
| claude-code-homelab | 75 | ~490 | ✅ |
| Azure-lab | 50 | ~420 | ✅ |

On top of CLAUDE.md, this repo's CLAUDE.md **instructs the agent to read 11 docs at every
session start** (NARF §5 + ZORT §6):

| Bundle | Files | ~tokens |
| ------ | ----- | ------- |
| ai-cto state | portfolio, roadmap, tech-debt, decisions | ~4,340 |
| ai-cfo state | portfolio, decisions, metrics, runway, budget | ~5,790 |
| + MARKETING/docs/ai-cfo/context.md | 1 | ~1,000+ |

**A DESIGN session therefore burns ~13,600 tokens of mandatory reading + ~3,480 of
CLAUDE.md ≈ 17,000 tokens before the first useful action** — and CLAUDE.md's share repeats
every turn. For a routine that runs daily/often, that's the dominant line item, and most of
it (roadmap, runway, budget, full decision logs) is irrelevant to any given task.

---

## 2. Fixes, ranked by payoff

### A. Shrink CLAUDE.md to a pointer file (biggest win, ~50–60% of per-turn overhead)
Best practice (Anthropic + the field) is **<200 lines / ~1,500 tokens**; a 5,000-token
CLAUDE.md is a 5,000-token tax on every turn. Ours carry the *full* funnel diagram, stage
map, money-flow tables, and known-issues tables inline. Move the reference material into the
files that already exist (README, workflow-context, schema) and leave CLAUDE.md as a thin
index: the house-style rules (which genuinely must always apply), one-line repo purpose, and
**links** to the deep docs. Target: localDNS and DESIGN each under 150 lines. Estimated
saving: ~2,000 tokens/turn each.

### B. Make session-start reading lazy, not mandatory (eliminates the ~13,600 fixed tax)
Replace "read these 11 files at session start" with "**read the relevant state file when a
task touches that domain.**" A DNS-config task does not need runway.md or the 1099 budget.
Keep one tiny `STATE.md` per role (a 20-line digest: current phase, top 3 priorities, last
decision number) that the agent reads, and let it pull the full portfolio/decision log only
on demand. This is the same principle as Claude Code subagents: keep the parent context
focused, fetch detail just-in-time.

### C. Use subagents for the read-heavy fan-out (keeps the dump out of main context)
When a task genuinely needs to sweep many files (cross-repo status, "find every place X is
documented"), delegate to a subagent / the Explore agent. The subagent reads in its **own**
context window and returns only a summary — the 10k-token file dump never lands in the main
thread. This is the most token-efficient agent pattern; we should make it the default for
any "look across the repos" question rather than reading everything inline.

### D. Lean on prompt caching for the stuff that *must* stay (90% off the repeat)
Whatever fixed context we keep (CLAUDE.md, house style, a stable state digest) is exactly
what prompt caching is built for: cached reads cost ~0.1× input price, and you break even
after a single hit. Order the context **stable-first** (house style, repo purpose) so the
cache prefix stays valid across turns; put the volatile task-specific bits last. We don't
control the harness's cache breakpoints directly here, but keeping the stable preamble
genuinely stable (don't edit CLAUDE.md mid-session) maximizes hit rate for free.

### E. Per-task hygiene (the cheap, always-on habits)
- **One task per session; `/clear` (or a fresh session) between unrelated tasks.** Long
  threads re-read the whole history every turn — the second-biggest hidden drain after
  CLAUDE.md.
- **`/recap` / `/compact`** instead of letting a session sprawl; `/recap` (Apr 2026)
  summarizes where you left off without replaying the transcript.
- **Point at files, not "the whole repo."** "Edit `07-payments/README.md`" beats "fix
  payments." Smaller scope = less retrieval = fewer tokens.
- **Run `tools/check-docs.py` locally** instead of asking the agent to eyeball links — a
  script catches broken anchors for ~0 tokens vs. an agent re-reading files.

---

## 3. Hybrid local + cloud — we're already half-built; route more to local

We already run the pieces: **LiteLLM on the t630 (port 4040), Open WebUI, a reasoning
ladder** (`local-reason` deepseek-r1:1.5b on the box for light work → `cloud-gpu-reason` /
`cloud-overflow` for heavy). The field consensus: **~60–70% of real workload is
simple** (classification, extraction, formatting, drafting), and routing that tier to a
local model cuts blended LLM cost 60–90% with no quality ceiling change.

Concrete, low-risk moves that fit our stack:
- **Send the cheap, high-volume, low-sensitivity jobs local.** Statement-data summarization,
  first-draft "Handled For You" log entries, roster field extraction, link/lint checks,
  commit-message drafts, "which doc covers X" lookups → local model via the LiteLLM router.
  Reserve the Claude API for what actually needs frontier reasoning: architecture, the
  workflow glue, money/compliance judgment, customer-facing copy.
- **Privacy bonus, not just cost.** Real customer data (the private `customers` repo) is
  exactly the data we *shouldn't* be shipping to a cloud API for trivial transforms. Local-
  first on customer PII is both cheaper and more on-brand ("we keep your data home").
- **Keep the gateway self-hosted.** LiteLLM's *hosted* tiers take an 8–12% margin; our
  self-hosted proxy on the t630 avoids that entirely — keep it that way.
- **Use a cheaper Claude tier for the cloud half.** Not every cloud call needs Opus. Haiku
  4.5 handles most "moderate" tasks at a fraction of Opus cost; Opus 4.8 **Fast mode** is
  now ~3× cheaper than on prior models and 2.5× faster — good default for interactive
  coding. Reserve full-effort Opus for genuinely hard reasoning, and use the new **effort
  controls** to dial Opus down on easy tasks.

---

## 4. Prompting — what actually helps on current models

From Anthropic's current guidance (it shifted in 2026):
- **Calm and specific beats forceful.** "CRITICAL! / YOU MUST / NEVER EVER" now produces
  *worse* results on newer Claude models — drop the all-caps imperatives. (Our CLAUDE.md
  house-style section leans on bold/"Never"/"Invariant" a lot; calm declaratives read the
  same to a human and prompt better.)
- **Specify the output shape, not "be concise":** "5 bullets, <15 words each."
- **Give the *why*.** Motivated instructions generalize better than bare rules.
- **Split big asks into smaller scoped ones** — both accuracy and token use improve.
- **The colleague test:** if a teammate with no context would be confused by the prompt,
  so is Claude.

---

## 5. The meta-note: *this* prompt was inefficient (as asked)

The founder's prompt that triggered this review was, candidly, an expensive shape:

**What it did well:** clear domain, gave permission to use the web, asked for currency,
invited a critique of itself. Good intent.

**Why it cost more than it needed to:**
- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of"
  invites an exhaustive sweep — the model fans out broadly because no stop condition is
  given. Open-endedness is the most expensive instruction you can give.
- **No output contract.** No length, format, or destination specified, so the agent has to
  guess how much to produce (and tends to over-produce).
- **Several questions braided together** (token use + prompting + other AI + hybrid local +
  news) — each pulls its own research pass. Fine to ask all five, but numbering them and
  capping each keeps the work bounded.
- **Emphatic filler** ("ANYTHING," "ANYTHING that could help," "Thanks!" ×2) adds tokens
  without adding signal — and the caps-lock urgency is exactly the pattern that prompts
  *worse* on current models.

**A leaner version that gets the same answer for less:**

> "Review our user↔AI workflow for token waste. Cover, briefly: (1) CLAUDE.md / session
> overhead, (2) prompting habits, (3) what to route to the local LiteLLM model vs. the
> Claude API, (4) anything materially new this quarter — search the web for 2–3 of these.
> Output: a ranked list of the top 5 fixes with rough token impact, written to
> `docs/ai-cto/`. Skip anything that saves under ~5%."

That version bounds the scope, names the deliverable and its home, sets a relevance
threshold, and tells the agent *when to stop* — which is where most of the savings live.

---

## 6. Recommended next actions (do these in order)

1. **Diet CLAUDE.md** in localDNS and DESIGN to <150 lines (pointer-style). ~2k tok/turn each.
2. **Convert session-start "read 11 docs" → lazy/just-in-time** + a 20-line role `STATE.md`.
   Removes the ~13,600-token fixed tax.
3. **Default cross-repo "status / find" questions to a subagent**, not inline reads.
4. **Route the cheap/high-volume/PII tasks to the local LiteLLM model**; reserve Claude API
   (Haiku/Fast-Opus by default, full Opus on hard reasoning only) for what needs it.
5. **Re-tune the house-style prose** away from all-caps imperatives toward calm declaratives.
6. **Adopt the "leaner prompt" template** above for routine asks; set a relevance threshold
   so the agent stops early.

---

## Sources (current as of 2026-06-15)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Anthropic Prompt Caching & Token Efficiency Guide — hidekazu-konishi](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html)
- [Prompt Caching: cut repeated context costs up to 90% — Tygart Media](https://tygartmedia.com/anthropic-prompt-caching-90-percent-token-savings/)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM Pricing & Smart Routing — Markaicode](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo](https://www.tembo.io/blog/claude-code-subagents)
- [Claude Code Agents in 2026 / parallel-session cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Best practices for prompt engineering — Claude](https://claude.com/blog/best-practices-for-prompt-engineering)
- [Prompting best practices — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8)
