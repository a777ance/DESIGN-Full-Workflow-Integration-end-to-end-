# AI Process Efficiency — reducing token spend on the user↔AI loop

**Author:** NARF (AI CTO) · **Date:** 2026-06-26 · **Status:** Recommendations for review

A review of how we spend tokens working with Claude (and other models) across the seven
A777ance repos, with concrete, ranked fixes. Findings are current to June 2026 (Opus 4.8 era);
the landscape moves weekly, so re-check the dated claims before acting on the dollar figures.

The honest headline: the biggest savings are **structural** (what we load and where we run it),
not **stylistic** (asking Claude to be terse). Roughly in order of payoff:

---

## 1. Biggest lever — stop paying for context we re-load every turn

**The problem.** Everything in `CLAUDE.md` plus the session-start reading ritual is loaded
*before the first word of work* and re-sent **on every turn**. A 3,500-token `CLAUDE.md` costs
3,500 input tokens per turn, per session, forever — a constant baseline tax.

Measured today:

| File | ~Words | ~Tokens | Loaded |
| --- | --- | --- | --- |
| `localDNS/CLAUDE.md` | 2,728 | ~3,700 | every turn |
| `DESIGN-…/CLAUDE.md` | 2,608 | ~3,500 | every turn |
| `MARKETING/CLAUDE.md` | 1,445 | ~1,950 | every turn |
| `customers` / `homelab` / `azure` | 316–562 | ~430–760 | every turn |

On top of that, DESIGN's `CLAUDE.md` §5/§6 tells every session to **read 4 AI-CTO docs +
6 AI-CFO docs at start** before doing anything. That can be 10–20k tokens of preamble on a
session that only needed to fix one link.

**Fixes (do these first):**

- **Trim the two big `CLAUDE.md` files to a pointer + the non-obvious rules.** The funnel
  diagram, the full stage map, the money-flow ASCII, the deploy-path table — these are
  *reference*, not *every-turn briefing*. Move them into `README.md` (already exists) and let
  Claude read them **on demand** when a task actually needs them. Target: get each `CLAUDE.md`
  under ~1,200 tokens. Estimated saving: ~2,000–2,500 tokens **per turn** on the two heavy repos.
- **Make the session-start reading conditional, not mandatory.** Rewrite §5/§6 as "read these
  *when the task touches roadmap/decisions/finances*," not "read these at session start." A
  doc-link fix shouldn't pull the whole CFO portfolio into context.
- **De-duplicate the House-style block.** The identical ~270-token "ordering & typography" block
  is pasted into all six real `CLAUDE.md` files. It can't be auto-shared across repos, but it
  *can* be compressed to three terse bullets + a link to one canonical
  `house-style.md` (keep it in DESIGN, the hub). Saves ~200 tokens/turn/repo and kills a
  six-way copy-paste maintenance hazard.
- **Keep the stable prefix stable.** Prompt caching (below) only pays off if `CLAUDE.md` and the
  early context don't churn mid-session. Editing `CLAUDE.md` during a session invalidates the
  cache and re-bills the whole prefix. Batch CLAUDE.md edits between sessions.

---

## 2. Prompt caching — 90% off the context we *do* re-load

A cache hit costs **10% of standard input price** (Opus 4.8: $0.50/M cached vs $5.00/M). It
pays for itself after one read within the 5-minute window (1-hour cache available at 2× write).

- **In Claude Code:** caching is automatic, but its value is destroyed by context thrash. The
  practical move is the discipline in §1 (stable prefix) plus `/clear` between unrelated tasks so
  we're not dragging a stale 100k-token transcript that no longer cache-hits cleanly.
- **In our own LiteLLM stack (`10-ai-orchestration`):** when we call the Claude API directly
  (e.g. the statement copy, ZORT reports), set `cache_control` on the system prompt and any
  reused document context. This is a config change, not a code rewrite, and it's the single
  highest-ROI change for our programmatic Claude calls.

Sources: prompt caching cuts cached input ~90%; stacks with everything below.

---

## 3. Batch API — 50% off everything that isn't interactive

The Message Batches API is **exactly 50% off** standard token prices, results within 24h. Our
workload has an obvious fit:

- **The monthly statement run (stage 06).** Today ~"a penny a home." Statements are generated on
  a schedule, not interactively — textbook batch work. Halve the per-home model cost by sending
  the month's statements as one batch instead of synchronous calls.
- **ZORT/NARF monthly reporting, the demand-gen copy variants, any "generate N of these
  overnight" job.** None of these need a live answer.

Combined with caching, async bulk work can land at up to ~95% off naive synchronous pricing.

---

## 4. Run the cheap work locally — we already own the router

We are unusually well-positioned here: `localDNS/10-ai-orchestration` already runs **LiteLLM +
Open WebUI + a reasoning ladder** (local `deepseek-r1:1.5b` on the t630, `cloud-gpu-reason` on a
rented GPU, `cloud-overflow` → Claude). The hybrid pattern the industry is converging on in 2026
(static rules: "classification/extraction local, reasoning cloud") is *already our architecture* —
we just under-use it.

Documented savings for hybrid routing: **60–85%** with 90–95% of frontier quality retained.

**Route to local models (no Claude tokens):**
- Summarizing call notes / logs into the master list (stage 04 → 08)
- Classifying leads, tagging, dedup checks
- First-draft boilerplate (form copy, internal notes) — polish later if customer-facing
- Link/anchor checking → **this is already a deterministic script** (`tools/check-docs.py`); keep
  it that way (see §6)

**Reserve Claude (Opus/Sonnet) for:**
- Customer-facing copy that must hit the voice rule ("salesperson, not IT")
- Architecture, cross-repo reasoning, the honesty-rule judgment calls
- Anything where a wrong answer ships on a kept document

⚠️ **Privacy gate first.** TD-14 is open: a `sensitive`-tagged task can currently fail over from
`local-reason` to `cloud-overflow` (Claude cloud) because `allow_cloud=False` isn't enforced at
the LiteLLM failover layer. **Before** we lean harder on routing, fix that fail-closed — or we'll
leak exactly the lookups we promise customers we don't. Efficiency must not break the privacy
promise that *is* the product.

---

## 5. Model tiering inside Claude

Opus output tokens cost **5× Haiku**; Sonnet ~3× Haiku; output is ~5× the price of input. So the
default-to-Opus habit is expensive when the task is mechanical.

- Use **Haiku** for mechanical edits, formatting, simple lookups; **Sonnet** for most coding and
  doc work; **Opus** only for genuinely hard reasoning. In Claude Code: `/model`, and per-subagent
  model overrides when fanning out.
- Note: Opus 4.8 **fast mode** is now ~3× cheaper than on prior models — the speed/cost penalty
  for staying on Opus shrank, but tiering still wins on bulk.

---

## 6. Don't spend tokens on work a script can do

A recurring anti-pattern: asking the model to do deterministic work. `check-docs.py` is the right
model — link integrity is verified by Python, not by burning tokens reading every file. Extend the
principle: lint, format, schema-validate `roster.json`, diff-check, run tests → **scripts and CI**,
not prompts. The model should *write* the script once, then the script runs free forever.

---

## 7. Session hygiene (stylistic, real but smaller)

- **`/clear` between unrelated tasks** — 30–50% per-message savings on long sessions; stops a
  stale transcript riding along in every turn.
- **`/compact` proactively** on long tasks (consider overriding the auto-trigger down to ~70%).
- **Scope tightly** — "fix the login function in auth.ts," not "refactor auth." Less context in,
  less output out, fewer correction round-trips.
- **Terse-output rule** — a short "be concise, skip preamble" instruction cuts output (the 5×
  side of the bill). Don't overdo it where reasoning quality matters.
- **Subagents/Workflows** isolate context (keep the main thread clean) but each is a separate
  Claude instance — net *more* tokens for serial work, net *less* only for genuinely parallel
  fan-out (multi-repo audits, the doc-integrity sweep). Use deliberately, not by default.

---

## 8. On the prompt that commissioned this report

The request was effective at getting a broad answer, but it models the expensive pattern. Critique
and a reusable template:

**What cost tokens unnecessarily:**
- *Open-ended scope* — "ANYTHING that could help," "anything you could possibly think of" invites
  a maximal, exploratory sweep. Open scope = maximum tokens by construction.
- *No output contract* — no format, length, or destination specified, so the model has to guess
  how much to produce.
- *Stacked sub-questions + filler* — several asks ("token use," "prompting," "other AI," "hybrid
  local," "check the news," "critique this prompt") plus conversational filler ("Thanks!",
  "Perhaps also") in one turn. Each adds surface area.
- *"Keep UP TO DATE… day by day"* — pushes toward more web fetches than a decision usually needs.

**A leaner template (XML-tagged, scoped, output-bounded):**

```
<context>Seven A777ance repos; I work with Claude Code daily + a LiteLLM stack.</context>
<task>Find the top 5 ways to cut our token spend this month.</task>
<constraints>
- Rank by payoff. Concrete actions tied to our actual files.
- Web-check only the pricing/feature claims, not general background.
</constraints>
<output>A ranked list, ≤1 page. One example fix per item. No preamble.</output>
```

That swap alone — scope + an output contract — typically saves more than any in-conversation
trick, because it prevents the expensive exploratory pass before it starts.

---

## Recommended next actions (ranked)

1. **Trim `localDNS` and `DESIGN` `CLAUDE.md`** to pointer + non-obvious rules; move reference
   into README. (Biggest per-turn saving; pure win.)
2. **Make §5/§6 session-start reading conditional**, not mandatory.
3. **Fix TD-14 (fail-closed local routing)** — prerequisite to leaning on hybrid routing.
4. **Turn on `cache_control`** in our LiteLLM Claude calls; **batch** the monthly statement run.
5. **Adopt model tiering** (Haiku/Sonnet/Opus) and a default terse-output rule.
6. **Adopt the scoped prompt template** above as the house default for AI tasks.

Items 1, 2, and 6 are free and immediate. Item 3 is a privacy blocker we should fix regardless.
Items 4–5 need a small config pass on the LiteLLM stack.

---

### Sources (June 2026)

- Anthropic — [Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8) · [Pricing](https://platform.claude.com/docs/en/about-claude/pricing) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Claude Code best practices](https://code.claude.com/docs/en/best-practices) · [LLM gateway](https://code.claude.com/docs/en/llm-gateway)
- Token economics & Claude Code spend — [age-of-product](https://age-of-product.com/token-economics-2026/) · [Faros.ai](https://www.faros.ai/blog/claude-code-token-limits) · [agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- Hybrid local/cloud routing — [SitePoint architecture guide](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [MindStudio: local models with Claude Code](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) · [LiteLLM auto-routing](https://docs.litellm.ai/docs/proxy/auto_routing) · [digitalapplied routing guide](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- Subagents/cost — [CloudZero: what parallel sessions cost](https://www.cloudzero.com/blog/claude-code-agents/) · [Tembo subagents guide](https://www.tembo.io/blog/claude-code-subagents)
