# AI process efficiency review — 2026-06-19

A scan of how we (founder ↔ AI) actually spend tokens across the A777ance repos,
plus current (June 2026) best practices and a critique of the request that
triggered this run. Ranked by payback. Newest entry first, per house style.

**TL;DR — the three biggest levers:**
1. **Trim the per-turn context tax.** Six `CLAUDE.md` files total ~10.7k tokens; the
   identical house-style block is duplicated 6× (~2k tokens of pure copy). Every turn
   of every session pays for the repo's whole file. Cut the heavy two (`localDNS`,
   `DESIGN`) to lean lookup tables.
2. **Fix the cloud-overflow tier — it fails *up* to the most expensive model.** A 3B
   local model that errors currently falls over to **Opus 4.8**. That's a 100×+ cost
   jump for work that was meant to be cheap. Overflow should land on Haiku.
3. **Stop running advisory routines unconditionally.** A "scan for best practices"
   routine that produces near-identical output every run burns tokens for nothing.
   Gate it on a trigger or make it a manual one-off.

---

## 1. The per-turn context tax (highest payback)

Measured today:

| File | ~tokens |
| ---- | ------- |
| `localDNS/CLAUDE.md` | 3,637 |
| `DESIGN-…/CLAUDE.md` | 3,477 |
| `MARKETING/CLAUDE.md` | 1,926 |
| `customers/CLAUDE.md` | 749 |
| `claude-code-homelab/CLAUDE.md` | 494 |
| `Azure-lab/CLAUDE.md` | 421 |
| **total** | **~10,704** |

Every message in a session re-sends that repo's whole `CLAUDE.md`. A 3.6k-token file
costs 3.6k tokens on turn 2 and on turn 200. The industry rule of thumb: keep
`CLAUDE.md` "a lookup table, not a brain dump."

**What's bloating ours:** the `localDNS` deploy-path table (~40 rows) and both
repos' full known-issues tables are *reference* material — needed occasionally, re-read
every turn. The **house-style/typography block (~250 words) is copy-pasted verbatim into
all six repos** (~2k tokens duplicated, and six places to maintain one rule).

**Fixes (in order):**
- Move the deploy-path table and the long known-issues tables out of `CLAUDE.md` into
  `README.md` / `INSTALL-NOTES.md` (already exist) and leave a one-line pointer. Claude
  `Read`s them on demand — only when a task touches deploys. Saves ~2k tokens/turn on
  `localDNS` sessions.
- De-duplicate house style: keep the canonical copy in `DESIGN-…` and replace the other
  five with a 2-line summary + link, **or** use a CLAUDE.md `@import`. One source of
  truth (our own stated principle), ~1.5k tokens saved portfolio-wide, one place to edit.
- Target: every `CLAUDE.md` under ~1,500 tokens. Keep the invariants (privacy rules,
  "push to main", honesty rule); evict the tables.

**Caching caveat:** on the Claude subscription, Claude Code auto-requests a 1-hour cache,
so a *long-running interactive* session re-reads `CLAUDE.md` at ~10% cost after the first
turn. But a **scheduled routine is a cold start every run** — it pays the full cache
*write* (1.25×) each time and rarely amortizes it. So lean prefixes matter *most* for the
routines, which is exactly where we're spending unattended. (Also note the March 2026
caching incident — 10–20× silent inflation — worth watching the bill, not trusting it.)

## 2. The model ladder fails *upward* in cost

`10-ai-orchestration/config.yaml` today:
- `cloud-overflow` (the failover for `local-fast`/`local-smart`) = `claude-opus-4-8`.
- `cloud-explore` and `cloud-vision` both = `claude-opus-4-8`.

When the snappy 3B local model trips, the request lands on our **most expensive** model.
That inverts the whole point of the local-first ladder.

**Fix:** point `cloud-overflow` at `anthropic/claude-haiku-4-5` (cheap, fast — the right
catch for interactive spillover). Reserve Opus for `cloud-explore` only; set `cloud-code`
to Sonnet 4.6 (already is — good) and let it *escalate* to Opus by exception, not default.
Vision can be Sonnet 4.6 too unless a scan genuinely needs Opus. The dispatcher already
routes to capability names, so this is a one-file edit with no code change. The `effort`
parameter (4.x) is another dial here: trade capability for speed/cost on the easy tiers.

**What's already right (don't undo):** `dispatcher.py` puts **no LLM in the routing
decision** — pure rule table, deterministic, zero token cost to decide, with a hard-coded
`sensitive → local, allow_cloud=False` privacy gate. That is the textbook hybrid pattern
(local handles the 60–70% simple traffic; cloud only for the ~10% that needs frontier
reasoning). Keep it.

## 3. Routines: run on change, not on a clock

This very run is the example: a scheduled routine reloaded all six `CLAUDE.md` files and
fanned out four web searches to regenerate advice that is ~stable week to week. For an
unattended schedule, that's recurring spend for a near-constant answer.

- **Advisory/research scans** → make them manual or quarterly, not a frequent schedule.
- **Reserve the schedule for things that actually change** — a cost/usage dashboard, CI
  status, AR aging — where each run has new input and a real decision.
- A routine that finds "nothing changed" should stay **silent** (no notification, no
  commit). That's already the standing rule; apply it to advice runs too.

## 4. Push deterministic work off the model entirely

The cheapest token is the one never spent. Several recurring jobs are mechanical and
belong in scripts/hooks, not in a Claude turn:
- **Doc integrity** — `tools/check-docs.py` already exists. That's the right pattern:
  a linter, not a model, validates links. Extend it; don't ask Claude to "check the links."
- **House-style enforcement** (reverse-chron ordering, Z→A lists, font stack, anchor
  checks) is rule-based → a pre-commit hook or a local-model pass, never an Opus turn.
- **Roster/schema validation, statement composing** → the existing `make`/Python tools.
  Route any LLM step in these to a **local** tier via the router, not the Claude API.

The Skills mechanism is the token-friendly home for repeatable procedures: a 50k-token
skill costs ~100 tokens until it's actually invoked (progressive disclosure).

## 5. Prompting hygiene (founder ↔ AI)

- **Scope narrowly.** "Reformat the known-issues table in localDNS/CLAUDE.md" beats
  "tidy up the docs." Smaller scope = less context pulled = fewer tokens, better result.
- **State the deliverable and a budget.** "3 findings, each with a fix and est. savings,
  ≤1 page, cite sources" caps the run. Open-ended prompts have no "done" and fan out.
- **Use `/compact` and `/recap`** (Apr 2026) on long interactive sessions to shrink and
  re-cache the prefix instead of replaying history.
- **Subagents cost ~7× a single thread** (each carries its own context) but give ~70%
  reduction on genuinely large/parallel work via context isolation. Use them for parallel
  fan-out, not for small one-off questions.
- **Pick the model for the job.** Don't drive Haiku-shaped tasks (formatting, extraction)
  with Opus, and vice-versa.

## 6. Critique of the prompt that started this run

The triggering request was, paraphrased: *"Locate inefficiencies… Is there a better way…
ANYTHING that could help… Search the web… Check the news… also critique this prompt."*

It's a strong *intent* but an **expensive shape**:
- **No scope or acceptance criteria** ("ANYTHING you could possibly think of") forces the
  widest possible exploration — maximum tokens, no defined "done."
- **Several distinct asks bundled** (token reduction + prompting + hybrid LLM + news +
  self-critique). Each is cheaper and sharper as its own focused run.
- **"Keep UP TO DATE… day by day"** implies a *frequent* schedule for advice that barely
  moves — see §3.

**A leaner version:**
> "Audit our Claude Code token usage across the six repos. Give the top 3 cost
> inefficiencies, each with a concrete fix and a rough token/$ saving. Cite current
> sources. ≤1 page. Run this only when I ask or quarterly."

Same outcome, a fraction of the spend, and a clear stopping point.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to Reduce Claude Code Token Usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Model Routing in 2026: Cost-Quality Optimization — Digital Applied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude Code Updates — June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)
