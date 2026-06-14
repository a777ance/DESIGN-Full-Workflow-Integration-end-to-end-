# AI Process Efficiency Audit — 2026-06-14

Author: NARF (AI CTO), run as a scheduled routine.
Scope: the **process between the human and the AI** across all A777ance repos — token use,
prompting, model/effort selection, and the local-LLM ↔ Claude split. Plus a self-critique of
the prompt that triggered this audit.

---

## TL;DR — read this first

1. **Absolute spend is already tiny** (~$11–27/mo Anthropic API, target <$30 — see
   `docs/ai-cfo/budget.md`). So the goal here is **not** to shave dollars; it's to stop wasting
   *context window* and *Opus reasoning* on work that doesn't need either. The wins below are
   mostly free (config + cadence + prompting), not spend cuts.
2. **The three highest-leverage fixes, in order:**
   - **Use the deterministic tool, not the model, for mechanical checks.** `check-docs.py`
     already verifies links with zero tokens. Anything that's a pass/fail rule (link integrity,
     schema validation, "did the field get written") should be a script in CI, never an LLM call.
   - **Stop running Opus-at-`high`-effort for everything.** Match model + effort to the task
     (table below). The daily review and doc-integrity passes are Haiku/Sonnet-or-low-effort work.
   - **Slim the standing context.** Every session re-ingests large `CLAUDE.md` files plus the
     NARF (4 files) and ZORT (6 files) session-start reads. Trim to a navigation index +
     progressive disclosure.
3. **You already have the hybrid local↔cloud setup** — the `localDNS` LiteLLM reasoning ladder
   (`local-reason` → `cloud-gpu-reason` → `cloud-overflow`). The opportunity isn't *building* it;
   it's **using it for the mechanical guild work** and **closing the privacy gap (TD-14)**.

---

## Where the tokens actually go (the real inefficiencies)

### 1. Standing context is re-ingested on every session

Each routine — daily review, this audit, any NARF/ZORT session — re-reads the full standing
context before doing any work:

- `localDNS/CLAUDE.md` and `DESIGN/CLAUDE.md` are each long (deploy-path tables, full
  known-issues lists, topology, etc.) — together on the order of ~8–10K tokens.
- Session-start ritual: NARF reads `portfolio.md` + `roadmap.md` + `tech-debt.md` +
  `decisions.md`; ZORT reads 6 more (`portfolio`, `decisions`, `metrics`, `runway`, `budget`,
  plus MARKETING context). That's another ~20–30K tokens of standing context before the task.

**Why it matters more than the dollar cost:** at Opus input rates this is fractions of a cent,
but it (a) crowds the working window on long agentic runs and (b) is paid *cold* on every
routine because runs are spaced ≥24h apart — far longer than any prompt-cache TTL (now 5 min by
default; 1 h max), so caching never carries across daily runs.

**Fix:**
- **Treat `CLAUDE.md` as a lean index, not a manual.** Anthropic's own guidance is to keep it
  short and load detail on demand. Move the encyclopedic content (full deploy-path tables, the
  long known-issues lists) into the README/`network-context.md`/`workflow-context.md` it already
  links to, and have `CLAUDE.md` point there. The briefing should orient, not contain.
- **Make the session-start read conditional.** A doc-link review doesn't need `runway.md` or
  `metrics.md`. Have each routine read only the files its job touches, rather than the full
  6-file ZORT / 4-file NARF ritual every time.

### 2. Mechanical verification is model work that should be tool work

`tools/check-docs.py` is the model to follow: deterministic, zero-token, CI-gated (TD-11
resolved). Anything reducible to a rule belongs there, not in a prompt:
- link/anchor integrity (done),
- `roster.json` schema validation against `schema.md`,
- "stage N wrote the expected field" spot-checks from the Section 2 verification walk,
- the Statement "honesty rule" numeric guards (a number is present in the data file or it's omitted).

Every check you can express as code is a check you never spend tokens or Opus reasoning on again.

### 3. Opus-at-`high` for routines that don't need it

Opus 4.8 defaults to `effort: high` on the API **and** in Claude Code. That's correct for
judgment-heavy work (writing, architecture, this audit) and wrong for mechanical routines.
Opus 4.8's own release guidance is explicit: *consider all effort levels — `low`/`medium` still
perform very well, often beating prior models' `xhigh`.*

| Task | Recommended | Why |
| ---- | ----------- | --- |
| Doc-integrity / link review (daily) | **Haiku 4.5**, or skip the LLM (use `check-docs.py`) | mechanical pass/fail |
| Roster/data extraction, lead classification (Stages 02/03/08) | **Haiku 4.5** or **local** | high-volume, low-judgment |
| Routine portfolio/tech-debt review | **Sonnet 4.6** or **Opus `low`/`medium`** | summarize known state |
| Statement copy, sales scripts, architecture, this audit | **Opus 4.8 `high`** | judgment + voice |
| Hard one-shot builds, long async runs | **Opus 4.8 `xhigh`/`max`** | correctness > cost |

Haiku is ~5× cheaper per token than Opus and the natural choice for the mechanical guild work.

### 4. Cadence: a full Opus review *every day* is more than a pre-revenue solo project needs

`docs/ai-cto/reviews/` shows a review every day (2026-06-04 → 06-13). For a pre-revenue project
where state changes slowly, **weekly** full reviews + **event-triggered** spot checks (on PR, on
deploy) would cut routine count ~6× with little loss. Same logic applies to *this* audit's
"check the news day by day" instruction: model/tooling news does not change daily — a
**weekly or monthly** sweep is the right cadence (see prompt critique below).

---

## The hybrid local-LLM ↔ Claude split — you've already built it

The `localDNS` LiteLLM ladder (`local-reason` = deepseek-r1:1.5b on the t630 CPU →
`cloud-gpu-reason` on a rented GPU → `cloud-overflow` = Claude cloud) is exactly the
industry-standard hybrid pattern (route by data-sensitivity / complexity / availability;
reported 60–88% cost cuts where local handles the simple tier). Two honest caveats for *our* box:

- **The t630's local tier is weak** (AMD Carrizo, 1.5b model). It's good for classification,
  routing, redaction, and short extraction — **not** for anything needing real reasoning or
  voice. Don't route Statement copy or architecture there.
- **Close the privacy hole first (TD-14, P1).** `local-reason` currently fails over to
  `cloud-overflow` (Claude cloud), so a `sensitive` prompt can leak to cloud if the local model
  is down. Give it a **local-only, fail-closed** fallback before routing any real customer data
  through it. The hybrid split is not trustworthy for sensitive work until this is fixed.

**Where the hybrid genuinely pays off for us:** the mechanical, high-volume guild work — lead
classification (Stage 02), booking-form parsing (Stage 03), roster extraction/dedup (Stage 08),
PII redaction before anything leaves the box. Keep Claude for the judgment tier (sales, copy,
recruiting vetting, financial decisions).

---

## Claude API features we should be using (current as of June 2026)

- **Prompt caching** — cache reads are 0.1× input price (~90% off the prefix). Useful *within*
  a long session (cache the slimmed `CLAUDE.md` + portfolio prefix). Not useful across daily
  routines (TTL ≪ 24 h). Opus 4.8 dropped the min cacheable prefix to 1,024 tokens.
- **Compaction API** (beta, Opus 4.6+) — auto-summarizes mid-session history so long agentic
  runs don't blow the window. Worth enabling for any routine that does many tool calls.
- **Memory tool** (public beta) + **server-side filesystem memory** — for cross-session facts,
  this is more efficient than re-reading the whole portfolio every run. Candidate replacement for
  part of the NARF/ZORT session-start ritual: keep curated state in memory, read on demand.
- **Batch API** — 50% off for non-latency-sensitive work (e.g. monthly statement generation
  across many households). Directly relevant to Stage 06 at scale.
- **Subagent caution** — a 3-agent team uses ~7× the tokens of a single session. Don't fan out
  NARF/ZORT into many subagents for work a single Sonnet pass handles.

---

## Critique of the prompt that triggered this audit

The triggering prompt ("Locate inefficiencies in our PROCESS … ANYTHING that could help …
keep UP TO DATE … check the news … day by day. Thanks!") is friendly and gets the intent across,
but as a **routine** prompt it's inefficient in four ways:

1. **Unscoped + open-ended.** "ANYTHING that could help" invites broad, expensive exploration on
   Opus. A scoped ask ("audit `CLAUDE.md` token weight and model/effort choices; output one doc")
   gets the same value for a fraction of the reasoning.
2. **No declared output or destination.** Without "write the findings to
   `docs/ai-cto/<dated>.md`", the result would have lived only in a session nobody reads. State
   the deliverable and where it goes.
3. **No effort/cadence guidance.** "Day by day" would run a full web-research sweep daily — the
   single most expensive part of this task — for news that changes weekly at most. Recommend
   **weekly** (or monthly) and say so in the routine.
4. **Could itself run cheaper.** A scoped, weekly version of this audit could run on Sonnet 4.6
   or Opus `medium` and reach the same conclusions.

**A tighter version of the prompt:**

> *Weekly: audit our AI process for waste. Specifically check (a) `CLAUDE.md` + session-start
> read token weight per repo, (b) whether any routine uses Opus-high where Haiku/Sonnet/low would
> do, (c) any mechanical check that should be a script not an LLM call. Pull current Anthropic
> model/pricing news only if >7 days since last check. Write findings to
> `docs/ai-cto/<date>-process-audit.md` and add any concrete item to `tech-debt.md`. Use Sonnet
> 4.6 / medium effort unless you hit something needing deeper analysis.*

That version is scoped, names its output, bounds the news-sweep, and sets a cheaper model — same
result, far less spend, and it reaches the human via a committed doc instead of an unread session.

---

## Concrete next steps (tracked as TD-15)

1. Slim each `CLAUDE.md` to an index + progressive disclosure; move encyclopedic content to the
   already-linked README / context files.
2. Make NARF/ZORT session-start reads conditional on the task, not a fixed full-file ritual.
3. Move every rule-based check into `check-docs.py` / CI (roster schema, field-write spot checks,
   Statement numeric guards).
4. Set per-routine model + effort defaults per the table above; reserve Opus-`high` for judgment.
5. Move the full review to **weekly** + event-triggered; bound any news-sweep to weekly/monthly.
6. Close **TD-14** before routing any sensitive customer data through the local tier.

---

## Sources (June 2026)

- [Anthropic — Introducing Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8)
- [Claude API — What's new in Opus 4.8](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8)
- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Prompt Caching in 2026: the 5-minute TTL change (DEV)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Context Engineering: reducing token usage isn't about shorter prompts (Token Optimize)](https://www.tokenoptimize.dev/guides/context-engineering-reduce-token-usage)
- [LLM Token Optimization Strategies — 2026 (Token Optimize)](https://www.tokenoptimize.dev/guides/llm-token-optimization-strategies)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Implementing LLM Model Routing with Ollama + LiteLLM (Medium)](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
- [Claude Code Token Optimization 2026 (Build to Launch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Claude API Pricing 2026 — Opus 4.8 / Sonnet 4.6 / Haiku 4.5 (MetaCTO)](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
