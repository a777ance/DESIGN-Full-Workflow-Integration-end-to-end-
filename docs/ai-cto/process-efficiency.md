# Process efficiency — cutting token spend on the human ↔ AI loop

**Audit date:** 2026-07-01 · **Scope:** how the founder works *with* Claude across the seven
A777ance repos, and where that process wastes tokens, money, and correction cycles. This is
about the **dev loop**, not the product's AI features (Huginn/Odin already handle those).

> **Read this first (the one-sentence version):** your biggest cost isn't the work Claude does
> — it's the **~24k tokens of mandatory reading that loads before any work starts, every
> session, and gets re-paid every time the 5-minute cache goes cold.** Fix that and the model
> tiering, and you cut spend more than any prompt trick will.

---

## 0. What we measured (2026-07-01)

Counted straight off the repos. A session that treats `DESIGN-…` as the portfolio hub pays,
**before the first instruction is even read:**

| Load | Words | Notes |
| ---- | ----- | ----- |
| 7× `CLAUDE.md` auto-loaded at session start | **~8,000** | DESIGN 2,608 · localDNS 2,728 · MARKETING 1,445 · customers 562 · homelab 371 · azure 316 (+ chronikomicon) |
| DESIGN CTO mandatory reads (portfolio, roadmap, tech-debt, decisions) | **~3,300** | per NARF session protocol |
| DESIGN CFO mandatory reads (portfolio, decisions, metrics, runway, budget) | **~6,800** | per ZORT protocol; `metrics.md` alone is **3,681 words** |
| **Total, before any actual task** | **~18,000 words ≈ 24,000 tokens** | |

That ~24k-token wall is loaded **every session**, and re-billed in full every time the prompt
cache expires (the cache TTL is ~5 minutes of idle — see §2.4). On Opus 4.8 (1M) that is real
money spent on *re-reading our own filing cabinet* before we do a stroke of work.

**The duplication tax on top of it:** the ~350-word "House style: ordering & typography" block
is copy-pasted **verbatim into all six present `CLAUDE.md` files**. Every multi-repo session
pays for it six times.

---

## 1. Ranked fixes (biggest lever first)

### ① Put the mandatory-read wall on a diet — *the single biggest win*
The NARF/ZORT "read these 9 files at session start" protocol is the largest recurring cost, and
most of it is irrelevant to any given task. A doc-formatting fix does not need `metrics.md`
(3,681 words) or the CFO runway.

- **Make session-start reads lazy, not mandatory.** Replace "read all 9" with: *"read
  `portfolio.md` (the snapshot) first; read the CFO/roadmap/decisions files **only when the
  task touches money / planning / an architecture decision.**"* Keep the snapshot small.
- **Split `metrics.md`.** 3,681 words is a database pretending to be a briefing. Keep a
  ~300-word "current KPIs" head in the file Claude reads; move the historical actuals log to a
  `metrics-history.md` that's opened only when asked.
- **Estimated saving:** a typical non-financial session drops from ~24k to ~8–10k startup
  tokens — a **~60% cut on the fixed cost of every session**, before touching anything else.

### ② Trim the `CLAUDE.md` files and kill the duplication
Best practice (confirmed current, July 2026): keep `CLAUDE.md` **concise**; push detail into
nested/linked files loaded on demand; document only what the code/README can't say for itself.
Ours embed full funnel diagrams, money-flow ASCII, and philosophy essays that belong in
`README.md` / `workflow-context.md` — and are already there.

- **Target ~800–1,000 words per `CLAUDE.md`.** DESIGN (2,608) and localDNS (2,728) can each
  lose half their body to links without losing a single fact.
- **De-duplicate the house-style block.** It's identical in six files. Options: (a) collapse
  each copy to a one-line pointer — *"House style: see `DESIGN-…/docs/house-style.md`"* — and
  keep the canonical copy once; (b) at minimum, **delete it entirely from the stubs**
  (`azure-lab`, `claude-code-homelab`) — a scope-undefined stub doesn't need 350 words of
  typography law.
- Note: Claude Code auto-loads `CLAUDE.md` per repo but does **not** follow cross-repo imports,
  so the canonical file only helps sessions that already have DESIGN open — which the hub
  sessions do. For the others, the one-line pointer is the honest trade.

### ③ Route your **dev loop** through the tiers you already built — not just the product
You built Odin (LangGraph supervisor) + LiteLLM with a local→cloud ladder for *Huginn/the
product*. The dev process itself still goes straight to cloud Opus for everything. Match the
model to the task:

- **Use `/model` deliberately.** Opus 4.8 (1M) is overkill for 90% of what these repos need
  (doc edits, link fixes, reversing a list Z→A, commit messages, formatting). Default to
  **Sonnet 5** ($2/$10 promo through Aug 31, then $3/$15) for routine coding; reserve **Opus**
  for genuine architecture/ambiguity. Drop to **Haiku 4.5** for the mechanical stuff.
- **The 1M context window is a premium you rarely need.** Don't pay long-context rates to hold
  seven repos in one window when a scoped session on one repo would do.
- **Pin subagents to cheap models.** When you fan out reads/edits, the sub-work can run on
  Haiku/Sonnet while the main thread stays on the smarter model.
- **The local tier (qwen2.5:3b/7b on the t630) is genuinely useful for zero-cost drudge work**
  — bulk find/replace, "reverse these bullets," first-pass link extraction — via the
  `ai.home.lan:4040` gateway you already run. Industry reports put 60–70% of requests in the
  "simple enough for local" bucket; hybrid setups routinely cut inference cost **60–83%**. You
  have the gateway — the missing piece is *using it for your own chores,* not only the product.

### ④ Prompt-cache hygiene (free money, zero code)
The cache makes repeated context up to **90% cheaper** on reads, but the standard breakpoint
evaporates after ~5 minutes idle.

- **Work in focused bursts, not all-day trickle sessions.** Every >5-min gap re-bills the whole
  startup wall from §0.
- **Start a fresh session per work-block/day** rather than resuming a cold, bloated one.
- For long single sessions, the **1-hour cache TTL** (`cache_control: {ttl: "1h"}`) is worth the
  small premium when you'll return within the hour.
- Watch out: the **March 2026 caching bug** caused 10–20× token inflation silently — keep an eye
  on `/context` and the usage dashboard so a regression like that doesn't bill unnoticed.

### ⑤ Batch API (50% off) for everything non-interactive
Anything that doesn't need a human in the loop — **monthly statement generation, the doc-link
audit, cross-repo consistency sweeps, bulk sidecar rewrites** — should run through the **Batch
API at 50% the token price.** These are exactly the jobs stage 06 / stage 11 automate; route
them through batch, not interactive Claude Code.

### ⑥ Subagents / the Explore agent for multi-file reads
When a task means sweeping many files, delegate to a subagent (or the read-only Explore agent).
It reads in a *separate* context and returns only the conclusion, so the main thread stays lean
instead of accumulating every file dump. Rule of thumb: use it when the clutter you'd avoid in
main context outweighs the ~fixed startup cost of spawning the agent.

### ⑦ Stop paying a *reasoning* tax for the house style — enforce it deterministically
The house style (reverse-chronological, alphabetical **Z→A**, reversed walkthrough blocks) runs
against the grain of how the model is trained, so Claude spends reasoning tokens re-deriving it
every time and still gets it wrong occasionally — each miss costing a correction round-trip.
`tools/check-docs.py` already deterministically enforces links. **Extend it to enforce the
ordering rules** (newest-first sections, Z→A lists). Then a script catches violations for free
and Claude stops burning tokens defending an unusual convention.

---

## 2. Is the house style itself worth its cost?
Not a token fix — a process observation worth a decision. Reverse-chronological logs are
defensible (newest-first is genuinely useful). But **Z→A alphabetical lists** and **reversed
walkthrough blocks** buy little and cost real friction: every reader (human and model) fights
them, and the model needs explicit reminding or it reverts to A→Z. If they're a deliberate brand
signature, keep them but **encode them in the linter (⑦)** so they cost nothing to maintain. If
they're habit, dropping the two unusual ones would remove a standing source of correction cycles.
*Recommendation: keep newest-first; put Z→A + reversed-blocks up for an explicit keep/drop
decision, and lint whatever you keep.*

---

## 3. Your prompt — critique & a reusable template
The kickoff prompt ("locate inefficiencies… is there a better way… ANYTHING that could help…
search the web… check the news… thanks!") is **great for a first exploratory pass** but is the
*most expensive shape a prompt can take*: unbounded scope, no target metric, no deliverable
format, and several distinct questions bundled together. That invites maximal generation + wide
web crawling every time it's run.

**Cheaper without losing anything, once you know what you want:**

> *"Audit our Claude dev-loop token spend. Deliverable: a ranked list of the top 5 fixes with a
> rough %-saving each, written to `docs/ai-cto/process-efficiency.md`. Scope to session-start
> load + model tiering. Only web-search if a 2026 best-practice would change a recommendation.
> Skip anything under ~5% saving."*

What changed and why it's cheaper: **one** question, a **named deliverable + location** (no
guessing at format), an explicit **scope boundary** (stops the wide crawl), a **stopping rule**
(the 5% floor prevents padding), and web-search made **conditional** instead of mandatory. The
"ANYTHING/thanks!" framing is friendly but signals "generate maximally" — drop it once you've
scoped the ask. Keep the open version for genuine first-pass exploration; use the scoped version
for everything you'll run more than once.

---

## 4. Keeping current (this changes weekly)
- **Claude Code release notes** — `code.claude.com/docs/en/whats-new` and the in-CLI changelog.
- **Anthropic pricing / caching / batch docs** — `platform.claude.com/docs` (watch the Sonnet 5
  promo expiry **Aug 31, 2026** and any caching-behaviour changes).
- **`/context`** in-session and the usage dashboard — your own early-warning for a caching
  regression or context bloat.

---

## Sources
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code Token Optimization (2026 guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Anthropic API Pricing 2026 — Models, Caching, Batch — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
