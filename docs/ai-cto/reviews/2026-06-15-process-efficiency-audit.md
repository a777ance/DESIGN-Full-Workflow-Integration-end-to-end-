# Process efficiency audit — user ↔ AI loop — 2026-06-15

Scope: the *process* by which A777ance uses AI, not the product. Where are we burning
tokens, money, or attention for no marginal insight? What does current (June 2026) best
practice say, and what can we adopt with the infrastructure we already have? Findings are
ranked by payback. Estimates are labelled as such.

The audit looked at the real harness — `tools/ai-cto.py` (NARF), `tools/ai-cfo.py` (ZORT),
`.github/workflows/ai-cto.yml` — and the artifacts they produce (`docs/ai-cto/reviews/*`).

---

## TL;DR — the five levers, ranked by payback

| # | Lever | Effort | Est. saving | Evidence |
| - | ----- | ------ | ----------- | -------- |
| 1 | **Cadence: daily → change-gated/weekly** | 1 line of cron + a diff guard | ~85% fewer runs | 12 near-identical daily reviews (06-04…06-15), all "get on the t630" |
| 2 | **Model: Opus → Sonnet for routine modes** | 1 line + a mode→model map | ~80% per-run cost | `model="claude-opus-4-8"` hardcoded for every mode |
| 3 | **Route NARF/ZORT through our OWN LiteLLM** | base_url + key | 60–90% on local-eligible share | We built the router (localDNS stage 10) and don't use it for our own ops |
| 4 | **Merge NARF+ZORT context load / share warm cache** | refactor | ~1 full context load/day | Two harnesses each cold-load overlapping context daily |
| 5 | **Shrink the per-session prefix (CLAUDE.md + injected context)** | edit docs | every session, every repo | 7 full CLAUDE.md files inject each web session (~10–12k tokens) |

Stacking #1 + #2 alone is an estimated **80–95% cut** to the NARF/ZORT API bill with no
loss of signal — because most of what we're paying for today is a frontier model re-deriving
the same conclusion daily.

---

## 1. The daily cadence is the single biggest waste (and it contradicts our own design)

`ai-cto.yml` runs `cron: '0 8 * * *'` — **daily**. But `ai-cto.py`'s own docstring says
"Weekly portfolio review" and ships the homelab example as `0 9 * * 1` (**Mondays**). Design
intent was weekly; deployment is daily. That's a silent **7× cost multiplier**.

The output proves the waste: `reviews/2026-06-04` through `2026-06-15` are near-duplicates —
every one leads with "get on the t630 / 0 of 5 checkboxes / blocked by an SSH session, not
engineering." Twelve frontier-model runs to say the same true sentence twelve times. That is
exactly the anti-pattern our own routine guidance warns about: *don't spend attention when
nothing changed.*

**Fix (do both):**
- Drop the schedule to weekly (`0 8 * * 1`), matching the design intent.
- Add a **change gate**: in the workflow, only run the full review if a spoke repo changed
  since the last run (`git log --since` / compare SHAs), or if `tech-debt.md`/`portfolio.md`
  changed. On a no-change day, skip the API call entirely and log "no change."
- Keep `workflow_dispatch` for on-demand deep runs (already present — good).

This is also a *quality* win: a weekly review with real deltas reads as signal; a daily one
that repeats itself trains the reader to ignore it.

## 2. Opus for everything, every day

`run_agent()` hardcodes `model="claude-opus-4-8"` for all four modes. Opus is our most
expensive model (~5× Sonnet on both input and output). But:

- `priorities` (print top 5) and `issues` (file P1s) are mechanical — **Haiku/Sonnet** work.
- `review` on a quiet week is triage, not architecture — **Sonnet** is plenty.
- Only the occasional **deep** review (a real phase-gate decision, a cross-repo tension worth
  the "two-pole" treatment NARF's prompt is built for) justifies **Opus**.

**Fix:** a mode→model map. Default `claude-sonnet-4-6`; opt into `claude-opus-4-8` only via an
explicit `--deep` flag or `mode == "review" && big-delta`. Per current guidance, switching
models invalidates the prompt cache — so pick the model *per scheduled job*, not mid-session.

## 3. We built a hybrid router and don't use it for our own ops

This is the big one given the explicit ask about "hybrid local LLM + Claude API." We **already
own** the architecture the whole industry is writing 2026 guides about: localDNS stage 10 is a
**LiteLLM** gateway + a LangGraph "Odin" supervisor with a reasoning ladder (local
`deepseek-r1:1.5b` for light work, cloud for heavy). Industry reports put 60–70% of agent
requests in the "simple" bucket and cite **60–90% cost cuts** from routing those locally and
reserving Claude for the ~10% that needs frontier reasoning.

Yet NARF/ZORT call `anthropic.Anthropic()` **directly**, bypassing our own router. We pay
full Opus for the trivial 70%.

**Fix (sequenced, because of two real blockers):**
- Point the harness at our LiteLLM endpoint via `base_url`/`OPENAI_BASE_URL` instead of the
  raw Anthropic client. Let the router send the daily "did anything change / draft the issue"
  pass to the **local** model and escalate only the deep review to **Claude cloud**.
- **Blocker A — privacy (TD-14):** the router currently fails *open* — a `sensitive` task can
  fall back to `cloud-overflow` (Claude cloud) if local is down. Fix the fail-closed config
  first (it's a one-line change already flagged P1).
- **Blocker B — deployment (TD-03):** the t630 stack isn't deployed. So this is a *Phase-1.5*
  win, not today's. Until the box is live, just do #1 + #2 (they need no infrastructure).

Caveat worth stating plainly (conservative pole): a local 1.5B model is **not** a substitute
for Opus's judgment on a genuine architecture call. Route the *triage and the boilerplate*
locally; keep the *thinking* on Claude. The win is volume, not replacing the brain.

## 4. NARF and ZORT cold-load overlapping context, twice a day

`ai-cto.py` and `ai-cfo.py` each load `portfolio.md`, `decisions.md`, and the spoke context
files, each open their own session, each pay first-call input price. Prompt caching is set
correctly *within* a run (`cache_control` on the context block, which cumulatively caches the
system prefix too) — but **ephemeral cache TTL is 5 min / 1h**, and the two jobs run as
separate cold processes, so they get **zero shared-cache benefit**.

**Fix:** run NARF then ZORT back-to-back **in one process / one workflow job** so the second
persona reuses the still-warm cache of the shared context (within the 5-min window, or 1h with
`ENABLE_PROMPT_CACHING_1H`). Saves ~one full context load per day and tightens the CTO/CFO
"debate" they're designed to have. Lower priority than #1–3 because once #1 lands (weekly,
change-gated), the absolute number of runs is small.

## 5. Shrink the per-session prefix — this taxes *every* session, including this one

Two prefixes get re-paid constantly:

- **The injected context block at the top of every web/Claude-Code session** carries the full
  `CLAUDE.md` of **all 7 repos** (~10–12k tokens) regardless of which repo the task touches.
  This very session loaded all seven to answer a process question. Most tasks touch one repo.
- The **CLAUDE.md files themselves are large** (DESIGN's is ~18k chars). Best practice (current
  Anthropic guidance): keep CLAUDE.md a *lean, high-signal core* and push detail into linked
  files the model reads on demand. Our files are excellent reference docs but heavy as an
  always-on prefix.

**Fix:** trim each CLAUDE.md to a tight core (what's true, the hard rules, where to look) and
move the long tables/rationale into the README/context files they already cross-link. The
house-style block is duplicated byte-for-byte across 6 files (already flagged in
`RECOMMENDED-CHANGES.md` #1) — that's ~1k tokens of pure prefix tax in every repo's every
session. Canonicalize it.

---

## On *better prompting* (the NARF/ZORT system prompts)

The system prompts are genuinely good — clear persona, hard rules, the "two-pole" stance is a
real technique. Two efficiency notes:

- **Duplicated governance block.** The prompt states the CEO/CMO/advisor governance rules
  **twice** ("Governance" then "Governance — HARD RULES"), the second a louder restatement of
  the first. Collapse to one. Pure input-token tax on every call.
- **Unconstrained output → narration tax.** Reviews open with "Let me pull the current
  state… Let me find it… Here's the review… Let me update the portfolio." That chatter is
  saved into the review log *and* billed as output. Add: "Output only the dated review in the
  given structure; no narration of your steps." Cuts output tokens and makes the artifact
  cleaner.

---

## On *your* prompt that triggered this audit (you asked — here it is)

The prompt was effective: it gave clear intent and explicit license to use the web, which is
why this audit could ground itself in current sources. But it's optimized for *coverage*, not
*cost*, and that shapes what the agent does:

- **It's unbounded** ("ANYTHING that could help… ANYTHING"). Open scope makes the agent
  fan out maximally — more searches, more reading, more tokens — when a ranked short list was
  the real want. Tighter: *"Audit the NARF/ZORT daily harness for cost. Give me the top 5
  levers, ranked by payback, with estimated savings. ≤1 page."*
- **It bundles five questions** (token use, prompting, hybrid local, news, self-critique) into
  one run. That's fine for a one-off, but since you want this **recurring** ("keep up to date,
  day by day"), it shouldn't be re-typed each time — make it a **saved skill / scheduled
  routine** with a fixed scope and a budget, so the framing is paid for once.
- **"Check the news… day by day"** is the costliest instruction per unit insight: frontier-AI
  practice does *not* meaningfully change daily. A **monthly** "what changed in AI tooling"
  scan captures ~all the signal at ~1/30th the cost. Daily news-checking is lever #1's mistake
  applied to the meta-process.
- **Keep:** the explicit web license, the self-critique request, and naming the hybrid-local
  angle — that's what pointed straight at our own unused router.

Suggested standing version: *"Monthly: scan for material changes in Claude Code / Agent SDK /
model pricing since last run. Re-audit the NARF/ZORT harness against them. Output a ranked
top-5 with est. savings, ≤1 page. Notify only if a lever's payback changed."*

---

## Sources (current as of 2026-06)

- [Reduce Claude Code costs 60% — four habits (systemprompt.io)](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [Claude Code token-saving: models, MCP, CLAUDE.md, skills & cache (knightli.com)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Prompt caching — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Context engineering: memory, compaction, tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Automatic compaction — Claude API docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Hybrid cloud-local AI workflows — cost optimization 2026 (buildmvpfast)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM smart routing — cut API costs 60% (markaicode)](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
