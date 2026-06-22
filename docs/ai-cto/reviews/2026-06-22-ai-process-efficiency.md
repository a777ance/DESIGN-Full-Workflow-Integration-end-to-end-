# AI Process Efficiency Review — 2026-06-22

**Author:** NARF (AI CTO), on founder request.
**Question asked:** "Locate inefficiencies in our PROCESS between the user and the AI. Token
use, prompting, leveraging other AI, hybrid local/Claude. Keep up to date — check the news."

**One-line answer:** The biggest waste is not the model — it's the *context we hand it every
single run*, and the fact that **the hybrid router we already built is sitting idle** while
cloud Claude does even the cheap work. Fix those two and the daily token bill drops more than
any prompt-tweak ever will. Details, evidence, and a ranked action list below.

> Methodology note: findings 1, 4 and 5 are measured from *this very session's* startup
> payload — they are not generic advice. Findings 2, 3, 6 are validated against current
> (June 2026) public best-practice sources, listed at the end.

---

## The ranked action list (read this if nothing else)

| # | Action | Effort | Saving | Where |
| - | ------ | ------ | ------ | ----- |
| 1 | **Slim every `CLAUDE.md` to a lookup table; move the encyclopedic tables to README/linked docs.** | 2 hrs | 40–70% of *startup* tokens, on every run | all repos |
| 2 | **Add a `.claudeignore` per repo** (data dumps, `households/*/stats`, generated HTML, vendored assets). | 30 min | up to ~85% context reduction on file-heavy repos | all repos |
| 3 | **Actually route daily work through the LiteLLM box you built** — `local-fast`/`local-smart` for classify/extract/format/summarize; reserve cloud Claude for the hard 10%. | 1 day (finish `dispatcher.py`) | 60–80% of cloud token spend | localDNS stage 10 |
| 4 | **Scope scheduled routines to the repos they touch** (this routine loaded all 7 repos' `CLAUDE.md`; it only needed `DESIGN`). | 15 min | ~6/7 of startup payload per run | routine config |
| 5 | **Don't run meta/maintenance routines on Opus 1M.** Use Sonnet (or Haiku for scans). 1M context bills more per token and is wasted when the job fits in 200k. | 5 min | per-token + per-call | routine config |
| 6 | **Confirm prompt caching is on.** On a Claude *subscription* via Claude Code it's automatic (1-hr TTL, free). If any routine bills the *API* per-token, structure prompts stable-first and turn caching on. | 30 min | 60–90% of input tokens on repeat calls | API tier |
| 7 | **Tighten the recurring-routine prompts** (scope, output budget, "what changed since last run"). See §7 — the prompt that triggered this review is the worked example. | 1 hr | re-derivation waste each run | routine prompts |

---

## 1. The #1 inefficiency: we pay for the same context on every single run

**Evidence from this session.** Before I did *any* work, the harness injected the **full
`CLAUDE.md` of all seven repos** plus the project brief — roughly **10,000–15,000 tokens** of
standing context. The `localDNS` `CLAUDE.md` alone (the full deploy-path table, every known
issue, the whole nftables checklist) appeared **twice**. A scheduled routine that runs daily
pays this toll *every day*, forever, whether or not it touches those repos.

Current best practice (June 2026) is blunt about this: *"Claude Code token costs usually come
from bloated context, not long prompts… CLAUDE.md works best as a lookup table, not a giant
brain dump."* Our `CLAUDE.md` files are the opposite — they are excellent **documentation** but
expensive **always-on context**. The deploy-path table, the verification command block, the
nftables checklist, the full known-issues tables: a new human reader wants those, but the model
does **not** need them resident for a task about, say, pricing copy.

**The fix (keeps the docs, cuts the tokens):**
- Reduce each `CLAUDE.md` to: what the repo is, the house-style rules, the invariants that must
  never be violated, and a **link** to the detail. "The deploy paths live in `README.md §C`"
  costs ~10 tokens; the table itself costs hundreds.
- Move the encyclopedic tables (deploy paths, full known-issues, nftables checklist,
  verification blocks) into `README.md` / `INSTALL-NOTES.md` where they already half-live.
  Claude will `Read` them *when a task needs them* — pay-per-use instead of pay-always.
- Add `.claudeignore` (signal layer) + `permissions.deny` (hard block) for data and generated
  artifacts: `customers/households/*/stats/`, rendered `*.html` statements, vendored fonts,
  `.env`. Measured reductions of ~85% are reported from this discipline alone.

This is the highest-leverage change available and it touches zero product code.

---

## 2. We built a hybrid router and then didn't use it for daily work

`localDNS/10-ai-orchestration/` already has the textbook hybrid stack the industry is writing
2026 guides about: **LiteLLM front door + Ollama local tiers + rented-GPU reasoning + cloud
Claude overflow.** That is exactly the recommended architecture. The gap is that **day-to-day
work (including this routine) goes straight to cloud Claude**, while `local-fast` (qwen2.5:3b)
and `local-smart` (qwen2.5:7b) sit idle on the t630.

The published numbers on this split are large: ~**60–70% of real workloads are simple**
(classification, extraction, formatting), ~20–30% moderate (summarize, translate), and only
~**10% need a frontier model**. Teams routing on that split report **60–83% cost cuts**. One
documented case: $47k/mo → $8k/mo.

**What's actually blocking it:** `ORCHESTRATION-BLUEPRINT.md` marks the deterministic
`dispatcher.py` as the missing piece — the rule table that sends cheap tasks local and only the
hard 10% to Claude. It's scaffolded, not wired in. **Finishing that dispatcher is the single
biggest *recurring* dollar saving on this list.** Candidate first uses that are safe to run
local: drafting "Handled For You" log lines, schema-field validation, commit-message
generation, link-checking summaries, first-pass marketing copy.

**One caveat that is also a live P1 bug:** `TD-14` — a `sensitive`-tagged task can currently
fail over from `local-reason` to `cloud-overflow` (Claude cloud), because the privacy lock
isn't enforced at the LiteLLM failover layer. **Route more work local *after* TD-14 is fixed**,
or you widen a privacy hole while chasing a cost win. Fixing TD-14 and finishing the dispatcher
are the same work session — do them together.

---

## 3. Prompt caching — verify it's on, mind the 2026 TTL change

The big 2026 change: Anthropic cut the default prompt-cache TTL from 60 min to **5 min**, which
quietly raised effective API costs 30–60% for workloads that assumed the old window. Two cases
for us:

- **If a routine runs through Claude Code on a subscription:** Claude Code automatically
  requests the **1-hour** TTL at no extra charge — you're already covered, nothing to do.
- **If anything bills the Anthropic API per-token** (e.g. `cloud-overflow` via LiteLLM, or a
  future `dispatcher.py` calling the API): structure prompts **stable-first** (system prompt and
  standing context first, the changing user input last) and set `cache_control`. Cache reads
  cost ~10% of input price; the write premium amortizes after ~3 reads inside the window. And
  **never** put a timestamp or per-request value inside the cached prefix — it busts the cache
  every call.

Tie-in to finding §1: a *slim, stable* `CLAUDE.md` is also a *cacheable* one. Trimming it helps
twice.

---

## 4. Scheduled-routine hygiene (this routine is the example)

This run loaded all seven repos to answer a question that only needed `DESIGN`. For recurring
routines:

- **Scope the repo set** to what the routine actually reads. ~6/7 of this run's startup payload
  was unused repos.
- **Give the routine an anchor of "what changed since last run"** (a date, last commit, a state
  file) so it diffs instead of re-deriving the same findings from scratch every time. An
  open-ended "think of everything" routine pays full price on every fire.
- **Notify only on signal.** A daily "all healthy" message trains the founder to ignore the
  channel; silence on a quiet day is the correct output. (Note: this session had **no
  `PushNotification` tool available**, so this report was committed to the repo instead — that
  is itself a routine-config gap worth closing if phone alerts are wanted.)

---

## 5. Model selection — stop using the biggest brain for janitorial work

This meta-review ran on Opus at 1M context. Opus is the most expensive tier and the **1M
context window bills at a premium per token** — worth it for a genuine large-context synthesis,
wasted on a task that fits in 200k. Map the tier to the job:

- **Haiku 4.5** — log inspection, file scans, "read these and summarize," boilerplate. Current
  guidance explicitly recommends Haiku for subagent/scan work.
- **Sonnet 4.6** — code, diffs, structured edits, most routines (the speed/intelligence sweet
  spot; it's already our `cloud-code` tier).
- **Opus 4.8** — the hardest reasoning and genuine wide-context synthesis only.

The `config.yaml` capability tiers already encode this. The discipline is to *pick the tier per
job* rather than defaulting everything to Opus.

---

## 6. Cut tool-output bloat (cheap, new, easy to miss)

Two June-2026 platform additions worth adopting:
- **`response_inclusion`** on the developer platform now lets agentic workflows **trim consumed
  result blocks** — stale tool outputs stop riding along in context for the rest of the session.
- **Subagents for fan-out reads.** Anything that would have the main thread read 3–4+ large
  files should be a subagent that returns a short summary — keeps the expensive main context
  lean. But don't subagent trivial one-file/one-command tasks; the spin-up overhead costs more
  than it saves.

---

## 7. The prompt itself — yes, it can be tighter

The triggering prompt is a **great human brainstorm** but an **inefficient agent instruction**,
and as a *recurring* routine it pays for that every run. Specifics:

- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of" gives no
  stopping rule, so the agent fans out maximally every time.
- **No output contract.** No length, format, or destination — so each run can balloon and (with
  no memory between runs) re-derive the same findings.
- **Two jobs in one.** "Audit our process" + "critique this prompt" are separate asks; splitting
  them lets each run cheaper.
- **"Check the news / keep up to date"** with no cadence means full web-research fan-out on every
  fire — fine monthly, wasteful daily.

**A tighter version for a recurring routine:**

> *"Monthly: review our AI usage for cost/efficiency. Compare against `<this report>` and report
> only what **changed** since it — new model releases, pricing/caching changes, or a new
> inefficiency in our repos. Max one page. Search the web only for items dated after the last
> run. Output to `docs/ai-cto/reviews/` and notify only if a finding is actionable."*

That keeps every good instinct in the original (stay current, look everywhere, be thorough) but
bounds the cost and stops re-derivation.

---

## 8. News watch — June 2026 items that touch our stack

- **Caching TTL 60min → 5min** (early 2026): the cost change behind §3. Claude Code on a
  subscription is unaffected (auto 1-hr).
- **`response_inclusion`** + code-execution/web tool versions added to the developer platform —
  see §6.
- **Claude Managed Agents** can now run in a sandbox you control and reach **private MCP
  servers**; **Workload Identity Federation (WIF)** replaces static API keys with short-lived
  scoped creds. Relevant if `dispatcher.py` ever grows into a hosted agent — but
  `ORCHESTRATION-BLUEPRINT.md`'s "deterministic Python, no LLM in the routing decision" call
  still stands; don't adopt agent infra for v1.
- **Fable 5 / Mythos 5** (released June 9) were placed under a **US export-control suspension on
  June 12** — do **not** plan routing around either; stick to the `claude-opus-4-8 /
  sonnet-4-6 / haiku-4-5` IDs already in `config.yaml`.
- **Claude Code** shipped startup-clutter removal, `/config` help, and subagent/WebSearch fixes
  — worth a `claude` CLI update.

---

## Sources

- [Claude prompt caching — API docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching)
- [Claude Prompt Caching in 2026: the 5-minute TTL change](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Best practices for Claude Code — docs](https://code.claude.com/docs/en/best-practices)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Local LLM vs Claude for Coding: GPU Benchmark 2026](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [Anthropic Release Notes — June 2026 — Releasebot](https://releasebot.io/updates/anthropic)
