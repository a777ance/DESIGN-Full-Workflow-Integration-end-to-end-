# AI Workflow Efficiency — process review (user ↔ AI)

A NARF (AI CTO) review of how we *use* Claude across the A777ance repos: where tokens
and attention leak, what to change, and how to keep the answer current. Commissioned by
the founder ("find inefficiencies in our PROCESS… reduce token use… hybrid local LLM +
Claude… keep up to date").

> **Reality check first.** Our AI tooling line is **~$5–15/mo** (`docs/ai-cfo/budget.md`:
> Anthropic API for NARF + ZORT; ~$0.01/Haiku run, $0.10–0.50/Opus run). At this volume,
> token optimization saves **pennies in dollars** today. The real costs are (1) the
> **founder's attention**, (2) **scaling habits we lock in now** before volume grows, and
> (3) a **hybrid local stack we already own but barely use for offload.** Optimize for
> those three, not for a bill we don't have. Don't spend an afternoon shaving $2/mo.

Review log is newest-first per house style. Latest review: **2026-06-21**.

---

## TL;DR — the five moves that matter

1. **Trim the CLAUDE.md files.** They load on *every* session and are our single largest
   fixed token cost. This scheduled run loaded **~14.6k tokens of CLAUDE.md before doing
   any work** (all six concatenated). Biggest offenders: `localDNS` (~5.1k) and this repo
   (~4.5k). Target ~1.5k each; push detail into README/linked files. (See "Lever 1".)
2. **Use the LiteLLM router we already built for offload.** `localDNS/10-ai-orchestration`
   is a working local↔cloud ladder (`local-reason` on the t630, `cloud-gpu-reason`,
   `cloud-overflow`). Today it serves chat; it should also absorb the *mechanical* AI work
   (link-checking, roster validation, summarizing, first-draft prose) so Claude is reserved
   for cross-repo reasoning. **Fix TD-14 first** — sensitive tasks can currently fail over
   to cloud. (See "Lever 4".)
3. **Turn on prompt caching for the daily NARF/ZORT runs.** They re-send a near-identical
   system prefix every day. Caching cuts repeated input cost ~90% and is the highest-
   leverage API change once volume grows. (See "Lever 2".)
4. **Ladder the model per task, not per session.** Haiku/local for mechanical, Sonnet for
   ~80% of coding, Opus only for genuine reasoning. We already price-tag this in the budget
   — make it a habit, not an afterthought. (See "Lever 3".)
5. **Tighten the prompts.** Scope the ask, name the output format, set a stop condition.
   The commissioning prompt for this very review (critiqued at the end) is the example:
   open-ended "ANYTHING that could help" invites expensive fan-out. (See "Lever 6".)

---

## Where the leaks are (in our actual workflow)

Our pattern: **scheduled routines** (like this one) and **daily NARF/ZORT runs** across
**7 repos**, often touching several at once. That shape has three specific leaks:

| Leak | Why it costs | Where |
| ---- | ------------ | ----- |
| **CLAUDE.md tax** | Loaded every session, before a single useful token. ~14.6k tokens here. | all repos |
| **Cross-repo context bloat** | A routine that reads "the portfolio + every spoke" pulls all six CLAUDE.md + several docs into one window. Tool output is appended and *compounds every turn*. | DESIGN hub runs |
| **Wrong tool for the cheap job** | Doc-link checks, roster JSON validation, "summarize the diff", first-draft prose — all sent to Claude when a local 7B or a deterministic script would do. | NARF/ZORT daily |

---

## Lever 1 — Cut the fixed CLAUDE.md cost (do this week)

CLAUDE.md loads before Claude reads any code; a 5k-token file costs 5k tokens every
session whether or not you need it. Measured footprint:

| Repo | ~est tokens (loaded every session) |
| ---- | ---------------------------------- |
| localDNS | ~5,118 |
| DESIGN (this repo) | ~4,496 |
| MARKETING | ~2,665 |
| customers | ~1,033 |
| claude-code-homelab | ~724 |
| Azure-lab | ~573 |

**Action:** keep CLAUDE.md to the *briefing* — the rules, the invariants, the "read this
first" map — and move reference tables (deploy-path tables, full known-issues logs, stage
maps) into README/linked docs that are loaded *on demand*. The deploy-path table in
`localDNS/CLAUDE.md` and the full funnel diagram in this repo are reference material, not
briefing; a one-line pointer plus the file link keeps the token-for-token tax down without
losing anything. Target ~1.5k tokens/file. Also add/maintain `.claudeignore` so large
generated artifacts (rendered statements, data dumps) never enter context.

---

## Lever 2 — Prompt caching for the recurring runs (do when API volume rises)

The daily NARF/ZORT runs and these routines re-send a stable prefix (CLAUDE.md + standing
instructions) every time. Mark that prefix cacheable: the first call writes the cache at
full price; subsequent calls within the TTL read it at **~10% of input cost**. On a 10-turn
conversation over a 30k-token context this is roughly a **5× reduction**; on large shared
inputs, up to **90%** on input tokens. Pair with **context editing / compaction**
(`compact-2026-01-12` beta): when a long routine approaches the window, it condenses history
server-side — a one-time summarize cost for a permanently smaller carried context.

In-session equivalents we should already be using: **`/recap`** (summary on resume without
replaying the whole conversation), **`/compact`** (scope session length), and **plan mode**
(catch "Claude's about to read six files when two will do" *before* it spends the tokens).

---

## Lever 3 — Ladder the model per task

Rough industry task split: ~60–70% simple (classify/extract/format), ~20–30% moderate,
~10% genuine frontier reasoning. Map ours the same way:

- **Mechanical** (link checks, JSON/schema validation, lint, "summarize this diff",
  template fills) → Haiku **or the local model** (Lever 4). Often a *script*, not an LLM.
- **Most coding / editing** (~80%) → **Sonnet** (`/model`). ~60% cheaper than Opus for
  comparable quality on routine work.
- **Cross-repo reasoning, architecture decisions, ADR drafting, this kind of review** →
  **Opus**.

For subagents, assign the **cheaper model to mechanical sub-tasks** and reserve the capable
model for the orchestrator. Note the subagent trade-off below.

---

## Lever 4 — Hybrid local + Claude (we already built the hard part)

`localDNS/10-ai-orchestration/` is a **working LiteLLM gateway** with a reasoning ladder:
`local-reason` (deepseek-r1:1.5b on the t630, cool/cheap), `cloud-gpu-reason` (full R1 on a
rented GPU, on demand), `cloud-overflow` (Claude). Industry reports put hybrid savings at
**60–80%**, and one documented case at **83%** ($47k→$8k/mo) — our absolute dollars are
tiny, but the *infrastructure is already paid for*, so offload is nearly free upside.

**What to route local** (good enough, and keeps private data on the box):
- Doc-integrity / link checking (today `tools/check-docs.py` — keep it deterministic).
- `roster.json` / schema validation, sidecar sanity checks.
- "Summarize what changed", commit-message first drafts, changelog stubs.
- First-draft customer prose (then Claude/human edits for voice — the "talk like a person" rule).

**What stays on Claude** (measurably better, worth the spend):
- Multi-step reasoning, long-context cross-repo synthesis, agentic tool-use chains,
  non-trivial code generation. Don't push these to a 7B — you'll pay more in debugging.

**Blocker — fix before routing anything sensitive:** **TD-14** — a `sensitive`-tagged task
can fail over from `local-reason` to `cloud-overflow` (Claude cloud) because `allow_cloud=False`
isn't enforced at the LiteLLM failover layer. Until `local-reason` has a **local-only,
fail-closed** fallback chain, do not route customer data through the ladder. This is a P1
privacy bug, not just an efficiency note.

**Caveat:** a fintech-scale offload assumes volume we don't have. For us this is about
*habit and privacy*, not the bill. Cap effort accordingly.

---

## Lever 5 — Subagents and parallel runs (use deliberately)

Subagents each get their own context window — great for isolating heavy exploration so it
doesn't bloat the main session, but **subagent-heavy workflows can burn ~7× the tokens** of
a single thread. Rule of thumb:
- **Tight token budget** → explore sequentially in the main session.
- **Tight time budget** → fan out subagents in parallel, accept the token multiplier.
- Use subagents when the saved main-context clutter is worth more than the startup overhead;
  use separate **parallel sessions** for genuinely unrelated workstreams.

For our cross-repo routines, a single Explore subagent that returns *conclusions* (not file
dumps) is usually the right call — it keeps the orchestrator's window clean.

---

## Lever 6 — Prompting

- **Scope tightly.** "Refactor the login function in `auth.ts`" not "refactor the auth
  module." Smaller scope → less context pulled → fewer tokens, sharper output.
- **Name the deliverable and its shape** (a table? a patch? a one-pager?) so the model
  doesn't hedge across formats.
- **Set a stop condition / budget** ("3 best ideas", "≤500 words", "don't read more than N
  files") to cap fan-out.
- **Prefer a terse output style** for mechanical work (an output-style/skill that strips
  filler can save a large fraction of *output* tokens over a session).
- **Front-load constraints** (what's private, what not to touch) so the model doesn't
  discover them by trial.

---

## Critique of the commissioning prompt (as requested)

The founder asked: *"If THIS prompt is inefficient then also let me know."* It is — usefully
so to dissect:

**What it does well:** clear intent, gives permission to use the web, asks for current info,
and explicitly invites a self-critique. Good direction-setting.

**Where it costs tokens / focus:**
1. **Unbounded scope.** "ANYTHING that could help… Perhaps also… Anything you could possibly
   think of" invites maximum fan-out — exactly the broad, expensive exploration we're trying
   to reduce. No stop condition.
2. **No output format named.** The model has to guess (report? patch? checklist?), so it
   tends to produce everything.
3. **No success metric.** "Reduce token use" — by how much, measured how? Without a target,
   the answer can't prioritize.
4. **No budget / no-go list.** Nothing says "don't spend more than X" or "don't refactor the
   repos" — so a literal agent could rack up cost chasing completeness.
5. **Repetition** ("Thanks!" ×2, "ANYTHING"/"Anything") is harmless but signals an
   un-scoped ask.

**Rewritten, tighter version** (drop-in for next time):

> *Review how we use Claude across the A777ance repos for efficiency. Output: a prioritized
> markdown report (≤1 page) of the top 5 changes, each with effort (S/M/L) and expected
> impact. Cover: (a) token/cost reduction in our daily NARF/ZORT runs and scheduled routines,
> (b) when to offload to our existing local LiteLLM router vs. Claude, (c) one concrete
> prompting fix. Use web search for anything that changed in the last ~60 days; cite sources.
> Don't modify the repos — recommend only. Budget: keep it to one focused pass.*

That version names the deliverable, caps the scope, sets a recency window, and forbids
expensive side-quests — while still inviting the self-critique.

---

## Keeping this current (it changes weekly)

Claude Code shipped a lot in June 2026 that's relevant here: `/recap`, `/cd` (move session
dir without rebuilding the prompt cache), `fallbackModel` (up to 3 fallbacks),
`--safe-mode`, subagents spawning subagents (capped 5 deep), and self-updating Artifacts.
Re-check this doc against:

- **Claude Code "What's new"** — `code.claude.com/docs/en/whats-new`
- **Anthropic release notes / Releasebot** — `releasebot.io/updates/anthropic`
- **ClaudeLog** (community best-practices) — `claudelog.com`
- **Pricing** — `platform.claude.com/docs/en/about-claude/pricing`

Cadence: glance monthly when updating the portfolio; this doc's recommendations have a
~quarterly shelf life.

---

## Action list (prioritized)

| # | Action | Effort | Owner | Status |
| - | ------ | ------ | ----- | ------ |
| 1 | Fix **TD-14** (local-only fail-closed fallback) before any sensitive offload | S | NARF | Open |
| 2 | Trim all CLAUDE.md to ~1.5k tokens; move reference tables to README/links | M | NARF | Open |
| 3 | Add a "route mechanical AI work to local LiteLLM" note to `10-ai-orchestration` README | S | NARF | Open |
| 4 | Adopt model-laddering habit (Haiku/local → Sonnet → Opus) in NARF/ZORT run configs | S | NARF/ZORT | Open |
| 5 | Enable prompt caching on the stable prefix once API volume rises | M | NARF | Deferred (low volume) |
| 6 | Add `.claudeignore` for rendered statements / data dumps | S | NARF | Open |

---

## Review log

- **2026-06-21** — First review (this document). AI spend ~$5–15/mo; key findings: CLAUDE.md
  fixed-cost tax (~14.6k tokens/cross-repo run), underused local LiteLLM router, TD-14
  privacy-failover blocker. No repo logic changed — recommendations only.

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Hybrid Cloud-Local AI Workflows — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Sub-Agents: Context, Cost, and Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Claude Code Agents in 2026: what parallel sessions cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Claude Code Updates June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
