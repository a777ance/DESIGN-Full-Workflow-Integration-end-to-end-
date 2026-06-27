# Process efficiency review — user ↔ AI workflow

*NARF (AI CTO), 2026-06-27. A standing review of how we spend tokens and effort
working with Claude across the A777ance repos. Findings are ordered by
**impact-per-effort** (biggest cheap win first), per house style for a prioritized
list rather than strict reverse-chron.*

---

## TL;DR — do these five things

1. **Cut the CLAUDE.md baseline tax.** ~58 KB of `CLAUDE.md` (~14–15K tokens) loads
   *before a word is typed*, every session. The house-style block alone is duplicated
   **verbatim in all 6 repos.** Target: each `CLAUDE.md` under ~200 lines; push reference
   detail into README/docs that get read on demand. **Est. 40–60% of fixed per-session
   overhead recoverable.**
2. **Turn on the hybrid rig you already own.** `localDNS` stage 10 already ships LiteLLM +
   a reasoning ladder (`local-reason` deepseek-r1:1.5b on the t630, `cloud-gpu-reason`).
   Route the cheap 60–70% of work (commit messages, link-checking, summarizing,
   classification, first-draft prose) to local; reserve Claude for reasoning. **Industry
   data: 60–80% cost cut.**
3. **Enable prompt caching on the LiteLLM → Anthropic path.** Cache the stable prefix
   (system prompt + CLAUDE.md + tool schemas). **60–90% input-token reduction** on repeat
   reads. Claude Code does this automatically; our proxied calls likely do not.
4. **Right-size the model.** This very routine runs on **Opus 4.8 (1M ctx)** — overkill for
   "scan docs and report." Use Sonnet/Haiku + the `effort` parameter for routine scans;
   keep Opus for architecture and hard debugging.
5. **Fix this routine itself** (see §7): it's vague, stateless, and over-frequent. Scope it,
   make it stateful, and run it monthly — not daily.

---

## 1. The CLAUDE.md baseline tax — biggest cheap win

Measured today:

| Repo | CLAUDE.md size |
| ---- | -------------- |
| `localDNS` | 20.5 KB |
| `DESIGN-…` | 18.0 KB |
| `MARKETING` | 10.7 KB |
| `customers` | 4.1 KB |
| `claude-code-homelab` | 2.9 KB |
| `Azure-lab` | 2.3 KB |
| **Total** | **~58 KB ≈ 14–15K tokens** |

Every token in CLAUDE.md is spent **before** Claude reads the task, on **every** session and
**every** turn — a constant baseline, not a one-time cost. A multi-repo session (like this one)
pays for several at once. Best practice in 2026 is to keep CLAUDE.md to *what's needed every
session* and let everything else be read on demand from README/docs.

**Concrete cuts:**

- **De-duplicate the house-style block.** The "Ordering & typography" section is identical
  in all 6 repos (~250 words × 6 ≈ ~2K duplicated tokens loaded whenever >1 repo is open).
  Keep the full text in **one** canonical place (suggest `DESIGN-…/docs/house-style.md`) and
  replace the other five with a 2-line pointer + the one rule each repo actually breaks often.
- **Demote reference tables to README.** `localDNS`'s full deploy-paths table and
  `DESIGN-…`'s stage map are *reference*, not *every-session* context. Claude can read them
  when a task touches deploys. Leave a one-line index in CLAUDE.md.
- **Gate the NARF/ZORT session-start ritual.** Both CLAUDE.mds mandate reading 4–6 `docs/ai-*`
  files at the start of *every* session. That's right for a CTO/CFO planning session, wasteful
  for "fix a typo." Reword to "read these *when doing portfolio/finance work*."

> Caution: these files are clearly hand-maintained and load-bearing. I'm **recommending**, not
> unilaterally refactoring them — sign-off first, because trimming the wrong line loses real
> guardrails (the honesty rule, the secrets rule).

## 2. Hybrid local + Claude routing — you're already 80% set up

You have the hard part done: `localDNS/10-ai-orchestration/` runs LiteLLM (port 4040),
Open WebUI, and a documented reasoning ladder. The missing piece is **routing policy**.
Typical production mix: ~60–70% simple (classify/extract/format), ~20–30% moderate, ~10%
needs a frontier model. Route accordingly:

- **Local (t630 / `local-reason`):** commit-message drafts, `check-docs.py`-style link sanity,
  summarizing a diff, "Z→A sort this list," first-pass prose you'll edit anyway.
- **Cloud GPU (`cloud-gpu-reason`):** heavy reasoning when the t630 would overheat (already
  documented as the on-demand path).
- **Claude API:** architecture, cross-repo reasoning, anything touching the honesty rule or
  customer data, final customer-facing copy.

LiteLLM gives you fail-closed fallback (local → cloud) for free. **Keep sensitive/customer data
on local-or-Claude only — never route `customers/` data anywhere experimental.**

## 3. Prompt caching on the proxied path

Cache writes cost +25%, reads cost ~10% of base input — break-even at ~3 reads inside the TTL.
Our CLAUDE.md + tool schemas are the *perfect* stable prefix. Put stable content first, a cache
breakpoint at the end of it, dynamic content last. **Anti-pattern to avoid: timestamps inside
the cached prefix** (the date line in this very context block would bust the cache every call —
truncate to the day or move it out).

## 4. Model & effort selection

- Routine/scheduled scans → **Sonnet or Haiku**, low `effort`. Reserve **Opus** for hard work.
  (This routine on Opus-1M is the standing example of over-provisioning.)
- The `effort` parameter (shipped in the 4.x line) trades speed/cost for depth — dial it down
  for mechanical tasks.

## 5. Subagents / context isolation for multi-repo work

Spawn a subagent for verbose, scoped jobs (e.g. "audit every deploy path in localDNS"). The
verbose output stays in the subagent's context and **never lands in the main session's running
cost** — you get back only the conclusion. This is the right tool for cross-repo sweeps.

## 6. Prompting practices

- **Scope + success criteria beat open-ended asks.** "Find inefficiencies in ANYTHING" forces
  broad, expensive exploration. "Reduce per-session token overhead below 8K; propose ≤5 changes
  with effort estimates" is cheaper and produces a better answer.
- **State the deliverable shape** ("a 1-page prioritized list," "a diff") so Claude doesn't
  over-produce.
- **Point at files, don't paste them.** `file_path:line` references are cheaper than pasted
  blocks and stay current.

## 7. Critique of *this* routine and prompt (you asked)

The prompt — *"Locate inefficiencies… Anything you could possibly think of… Keep UP TO DATE…
day by day… Thanks!"* — is warm and clear in intent but **inefficient to execute**:

- **Unbounded scope.** "Anything" maximizes exploration cost and dilutes focus. Give it a target
  metric and a cap on suggestions.
- **Stateless + over-frequent.** As a daily/standing routine it **re-researches the same
  best-practices and re-derives the same findings every run**, paying full freight each time.
  Fixes: (a) make it **stateful** — append to this file and have the next run read it and only
  report *deltas*; (b) run it **monthly**, not daily. The premise that these practices "change
  day by day" is mostly false — model releases and pricing move on a weeks-to-months cadence, so
  a monthly check catches everything that matters.
- **No exit condition.** A routine that always "finds something to improve" never goes quiet.
  Define done: "notify only if a *new* lever worth >X is found; otherwise stay silent."
- **Suggested rewrite:**
  > *"Monthly: read `docs/ai-cto/process-efficiency-review.md`. Check Anthropic release notes
  > and pricing for changes since the last run. Report ONLY new, actionable levers (with rough
  > token/$ impact and effort). If nothing new, send no notification. Cap: 5 items."*

## Sources

- [Claude prompt caching — Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Reduce Claude Code costs 60% — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- [7 ways to reduce Claude Code token usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code context window optimization — claudefa.st](https://claudefa.st/blog/guide/mechanics/context-management)
- [Hybrid Cloud-Local LLM architecture guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI with Claude Code to cut costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Run Claude Code with local agents via LiteLLM + Ollama — Medium](https://medium.com/@kamilmatejuk/run-claude-code-with-local-agents-using-litellm-and-ollama-ab88869cbd00)
- [Anthropic release notes (June 2026) — Releasebot](https://releasebot.io/updates/anthropic)
- [Claude Code subagents practical guide 2026 — Tembo](https://www.tembo.io/blog/claude-code-subagents)
