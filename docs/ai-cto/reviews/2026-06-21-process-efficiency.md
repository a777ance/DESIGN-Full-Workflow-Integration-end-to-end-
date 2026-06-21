# Process efficiency review — user↔AI loop & token spend — 2026-06-21

**Brief:** Find inefficiencies in *how we use the AI* (not what it builds), cut token
spend, improve prompting, and exploit the hybrid local-LLM + Claude setup we already
designed. Web-sourced best practices are current as of June 2026 and cited at the end.

---

## Headline

**The biggest inefficiency isn't prompting — it's cadence.** We run *two* full Claude
sessions a day (NARF + ZORT), every day, June 4 → June 20 — ~26 sessions, 18 review
files — and the 2026-06-20 review's own words are: *"No new CHANGELOG entry since
2026-06-07… a fourth review cycle with zero real Statements shipped."* We are paying
full frontier-model context price, daily, to re-derive a conclusion that hasn't changed
in two weeks: **TD-14 is still open and t630 access is the bottleneck.** The AI is busy;
the business is blocked on one SSH session and two human decisions. **No amount of better
prompting fixes a loop that re-runs when nothing changed.** Fix the trigger first.

---

## The five inefficiencies, most-costly first

### 1. Unconditional daily reviews re-pay for an unchanged answer (biggest win)

26 sessions in 17 days, each loading the full multi-repo context, each concluding the
same three things. The work product (a commit a day) masks that *business* state has been
static since 06-07.

**Fix — gate the cadence, stay silent when nothing moved:**
- Before spending a full review, run a cheap **change-detection gate**: did a watched
  signal move? (new `CHANGELOG.md` entry, new commit touching a tracked path, a TD closed,
  a phase-gate checkbox flipped, a Stripe/roster change). If nothing moved → **one-line
  ping or silence**, no full review. This is exactly the routine-notification rule:
  empty run = silence.
- Run that gate on a **local model** (qwen2.5:3b on the t630, already in `config.yaml`) or
  even plain `git` diffs — $0. Escalate to Claude *only* when the gate fires.
- Move from "daily" to **event-triggered + a weekly digest**. A daily fiduciary review of a
  project whose critical path is "founder visits the box once" is calendar theatre, not
  oversight.

Expected effect: from ~26 Claude sessions/17d to maybe 3–5 — an ~80% cut on this workflow
alone, with *no* loss of signal (the signal was duplicated anyway).

### 2. Fixed per-session context tax: heavy CLAUDE.md + "read N files at session start"

Every session ingests 6 full CLAUDE.md files (this very session's preamble proves it), and
the DESIGN CLAUDE.md then orders **4 more reads for NARF + 6 more for ZORT** before any work
begins. That's a large fixed token floor on *every* turn, much of it irrelevant to the task
at hand.

**Fix:**
- **Trim CLAUDE.md to a lean index.** Best practice (Anthropic + community, 2026) is a short
  CLAUDE.md; the long deploy-path / topology tables belong in README, referenced not inlined.
- **Make session-start reads lazy/conditional:** "read `portfolio.md` *only when* doing a
  portfolio review," not always. Collapse the NARF/ZORT "read these 4–6 files" lists into one
  small `state.md` pointer each.
- Note: Claude Code **caches** the system prompt + CLAUDE.md automatically (cache hit = 10%
  of input price). But our **reverse-chronological / Z→A / "reverse the blocks" house style
  rewrites the *tops* of files**, which is the worst case for prefix caching — every newest-
  first insert busts the cached prefix. Appending (newest-last) would preserve caches; if the
  house style is non-negotiable, at least keep the high-churn logs in separate small files so
  edits don't invalidate the big stable docs.

### 3. We designed the hybrid router but route everything to Claude anyway

`ORCHESTRATION-BLUEPRINT.md` is genuinely good — deterministic rule-table dispatch, "route
don't shard," privacy gate. But the dispatch layer is *"design, not built,"* so in practice
all the real work (reviews, doc edits, commit messages, link-checking) goes straight to
frontier Claude. We own the cheap tier and don't use it.

**Fix — push the high-volume / low-stakes work down the ladder:**
- Local qwen2.5 (t630) or Haiku for: change-detection (›1), doc-integrity (`check-docs.py`
  is already deterministic — no LLM needed), changelog diffing, commit-message drafts,
  link checks, "did the roster change."
- Reserve Opus/Sonnet for what actually needs frontier reasoning: architecture calls (ADRs),
  the *warranted* reviews, pricing/compliance judgement.
- Industry data (2026): a tuned routing layer cuts the bill **40–85%**; a 70/30 cheap/frontier
  split ≈ two-thirds off — *with no visible quality drop on the routine traffic.*

### 4. `cloud-overflow` defaults to Opus — the most expensive possible fallback

`config.yaml` sets `cloud-overflow: anthropic/claude-opus-4-8`. Every time a local box
stutters, overflow lands on the priciest model (~$15–25/M in, ~$75–90/M out). Overflow is
by definition the *unimportant* path.

**Fix:** make `cloud-overflow` **Haiku 4.5** (mid-tier, ~$0.25–1/M in). Keep an explicit
`cloud-explore`/`cloud-code` tier on Opus/Sonnet for when frontier is *chosen*, not fallen
into. One-line change.

### 5. Multi-agent "Odin host" (3 orders of 5 + Loki) is a token bonfire if run on cloud

Subagent-heavy workflows run **~7× the tokens** of a single thread. The Odin design musters
15+ agents. That's fine — *if it runs local* (which the privacy gate already wants). Run it on
Claude API and a single planning session could cost more than a month of everything else.

**Fix:** pin the Odin host to local/rented-GPU tiers; use subagents the way the docs
recommend — **fan-out search that returns a small summary**, not for every small task (for
small tasks the orchestration overhead makes a subagent *more* expensive than doing it inline).

---

## Related finding worth flagging (security, not process)

The 06-20 review found **TD-14**: a `sensitive`-tagged DNS task pinned to `local-reason`
falls over — via the `fallbacks:` chain — to `cloud-gpu-reason` → `cloud-overflow` =
**Claude cloud**, whenever the local box is cooled down. The `allow_cloud=False` guard lives
only in the *un-deployed* LangGraph gate, so **nothing enforces it today**, while the config
comments assert privacy three times. It's a ~3-line fail-closed edit, no box access needed,
open 3+ review cycles. This is directly the local↔cloud boundary the brief asks about — close
it before leaning harder on the hybrid path.

---

## On the prompt that launched this task

The intent was right; the *form* models the very inefficiency it's hunting:

- **Unbounded scope** — "ANYTHING that could help… Search the web… Check the news" invites
  open-ended token spend with no stop condition. Open-ended is how a routine quietly burns a
  budget.
- **No deliverable shape / success criteria** — no "output a 1-page report with N
  recommendations," so the agent has to guess how much is enough.
- **"Keep UP TO DATE… day by day" inside a scheduled routine** — implies *re-running this*,
  which compounds exactly the cadence cost in finding #1.

**A tighter version:**

> *"Audit our user↔AI process for token waste. Deliverable: ≤1-page report, top 5
> inefficiencies ranked by $ impact, each with a concrete one-step fix and rough % saving.
> Use the existing `config.yaml`/blueprint; web-search only to confirm 2026 pricing/best
> practice (max ~4 searches). Re-run only weekly, or when `config.yaml` or the review cadence
> changes — otherwise skip."*

That bounds scope, fixes the output shape, caps research, and — crucially — sets a re-run
trigger so the audit itself obeys finding #1.

---

## Do-this-week (ranked by payoff ÷ effort)

1. **Gate the daily reviews** behind a local/git change-detector; silent when unchanged. (#1)
2. **Flip `cloud-overflow` to Haiku.** One line. (#4)
3. **Close TD-14** — fail the sensitive fallback closed. 3 lines, no box access. (security)
4. **Trim CLAUDE.md + make session-start reads conditional.** (#2)
5. **Wire the cheap tier** for doc-integrity / changelog-diff / commit-msg via local qwen2.5. (#3)

---

## Sources (June 2026)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo](https://www.tembo.io/blog/claude-code-subagents)
- [LLM Model Routing in 2026: Cost-Quality Optimization — Digital Applied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [LLM routing: route easy queries to cheap models — BuilderWorld](https://builderworld.io/en/learn/llm-routing-multi-model)
- [Claude API Cost Optimization: Caching, Batching, 60% Token Reduction — DEV](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
