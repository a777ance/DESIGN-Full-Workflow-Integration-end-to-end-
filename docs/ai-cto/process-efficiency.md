# Process efficiency review — user ↔ AI

_Reviewed 2026-06-19 (NARF). Scope: how we spend tokens and attention across the
guild's Claude sessions, where the waste is, and what to change. Sources cited at
the bottom; web best-practice figures are 2026-current._

**Headline:** our biggest cost is not the model — it's the *fixed context tax we pay
before any work starts*. Every session reloads ~58 KB of `CLAUDE.md` (≈15K tokens),
and a finance/CTO session is instructed to then read 4–6 more state files (~42 KB)
on top. Much of that is duplicated boilerplate. Fix the recurring load first; it
compounds across every session, every repo, every day.

---

## 1. Findings, biggest lever first

### F-1 — The `CLAUDE.md` house-style block is duplicated verbatim in 7 repos (P1, trivial fix)
The "House style: ordering & typography" block (~30 lines) is byte-identical in all
7 `CLAUDE.md` files. It loads into context on **every** session regardless of repo.
- **Cost:** ~350 tokens × 6 redundant copies ≈ **2.1K tokens wasted per multi-repo
  session**, plus the maintenance hazard of editing one and not the others.
- **Fix:** keep the canonical copy in **one** place (this repo, e.g.
  `docs/house-style.md`). In each `CLAUDE.md` replace the block with a 2-line pointer:
  "House style (ordering, Z→A lists, reversed walkthrough blocks, Gill Sans MT) is
  canonical in `DESIGN-…/docs/house-style.md` — adopted 2026-06-05." Within a single
  repo, Claude Code honours `@path` imports in `CLAUDE.md`; cross-repo, a prose
  pointer is enough because the rules rarely change.

### F-2 — Session-start instructions force eager reads that most sessions don't need (P1)
- NARF block (§5) tells every session to read `portfolio.md`, `roadmap.md`,
  `tech-debt.md`, `decisions.md` — **373 lines / ~20 KB**.
- ZORT block (§6) tells every session to read **6** CFO files + a MARKETING context
  file — **424 lines / ~22 KB**.
- A session that edits a README or a statement template pays the *entire* CTO+CFO
  reading tax for nothing. That's ~10–14K tokens of pure overhead on an unrelated task.
- **Fix — make the reads conditional, not mandatory.** Rewrite the directive as a
  *trigger*: "If the task touches roadmap/architecture/tech-debt, read `portfolio.md`
  first" and "If the task touches money, pricing, Stripe, payroll, or 1099s, read the
  CFO portfolio." Keep one always-read file per role (the portfolio) and lazy-load the
  rest. Per Anthropic's own guidance: *document only what Claude needs every session,
  not everything about the project.*

### F-3 — `CLAUDE.md` files carry reference tables that belong in linked docs (P2)
`localDNS/CLAUDE.md` (326 lines) and this repo (295 lines) embed full deploy-path
tables, port maps, and known-issue tables. Useful, but they're *lookup* material —
needed when you touch that subsystem, not on every session.
- **Fix:** keep the 1-paragraph orientation + the pointer in `CLAUDE.md`; move the big
  tables to `README.md`/`network-context.md` (where most already partly live) and link
  them. Target a `CLAUDE.md` under ~120 lines per repo.

### F-4 — Prompt caching is not being exploited on the API/router path (P1 for cost)
When sessions hit the Claude API (directly or via the `cloud-overflow` tier), the
stable prefix — `CLAUDE.md`, schema, style rules — is re-sent and re-billed at full
input price every call. 2026 best practice: mark that prefix as a cache breakpoint.
- **Payoff:** cache reads bill at ~10% of input; real-world **60–90% input-cost
  reduction** on repeat-prefix workloads.
- **Fix:** (a) for direct Anthropic API use, add `cache_control` to the system/prefix
  block; (b) in LiteLLM, enable Anthropic prompt caching passthrough on the
  `cloud-*`/`cloud-overflow` models. **Keep volatile tokens (timestamps, per-user
  names) OUT of the cached prefix** — a date string in the prefix busts the cache on
  every call. (Our routine injects `currentDate` — keep that in the user turn, never
  in a cached system block.)

### F-5 — The hybrid router is already strong; one live bug undercuts it (P1, already filed)
The LiteLLM setup (local Ollama tiers → rented-GPU reasoner → cloud overflow, with a
privacy gate) is ahead of most 2026 hybrid stacks — good. **But TD-14 is a real
privacy hole:** a `sensitive`-tagged task routed to `local-reason` can fail over to
`cloud-overflow` (Claude cloud) when the local model is down, because `allow_cloud`
isn't enforced at the LiteLLM failover layer. Fail closed: give `local-reason` a
**local-only** fallback chain. No privacy guarantee until that's fixed.
- **Routing hygiene to bank the savings:** push the cheap-and-frequent work — log
  summarization, lead/CRM field extraction, classification, "Handled For You"
  rewrites — to `local-fast`/`local-smart` (the t630, ~free). Reserve cloud Opus/Sonnet
  for genuine reasoning, code, and diagrams. Industry split: ~60–70% of requests are
  simple enough to run local; routing those off cloud is where the 50–80% savings come
  from.

### F-6 — Routines should fan out to subagents to protect the main context (P2)
This very routine reads across 7 repos. Broad sweeps (link-checks, "did anything
change across all repos") should be delegated to `Explore`/subagents that return only
the conclusion, not the file dumps — keeps the parent context lean and the run cheaper.

---

## 2. Operating habits (low effort, compounding)
- `/clear` between unrelated tasks; `/compact` at phase boundaries. Don't run one
  session to exhaustion — quality degrades as the window fills (it's a quality problem,
  not just cost).
- Prefer CLI tools over MCP servers where both exist — CLI output is more
  context-efficient and Claude can run it directly.
- Watch the context %; above ~80%, restart for the next complex task.
- These habits alone are reported to cut spend 40–70%.

---

## 3. About the prompt that triggered this review
Honest critique, since it was asked for: **the prompt was a brainstorm dump, not a
brief.** "Locate inefficiencies… Perhaps also better prompting… Anything you could
possibly think of… Search the web if helpful… Check the news. Thanks!" — it's warm and
broad, but it has no scope, no success criteria, and no output format, so the model has
to guess what "done" looks like and tends to over-produce. That *itself* is a token
inefficiency: vague asks get long, hedge-everything answers.

A tighter version of the same request:

> Review our Claude usage for token waste. Focus on (1) per-session context load
> across our `CLAUDE.md` files and session-start reads, (2) prompt caching on the API
> path, (3) local-vs-cloud routing. For each, give the issue, the rough token/cost
> impact, and a concrete fix. Cite current (2026) sources. Deliverable: a short
> ranked list, biggest lever first. Skip anything we already do well unless it's
> broken.

Same intent, but it scopes the search, names the deliverable shape, and tells the
model to skip the throat-clearing. Rule of thumb: **state the deliverable and the
constraints; a 30-second tighter prompt routinely saves thousands of output tokens.**

---

## 4. Recommended order of operations
1. **F-1** de-dupe house-style → 1 canonical doc + pointers (1 hour, every session benefits).
2. **F-2** make NARF/ZORT session-start reads conditional (1 hour, biggest per-session win).
3. **F-4** turn on prompt caching on the cloud path (config change; 60–90% input savings).
4. **F-5/TD-14** close the sensitive-task cloud-fallback hole (correctness + privacy).
5. **F-3** slim the two big `CLAUDE.md` files under ~120 lines (move tables to linked docs).
6. Adopt the §2 habits and §3 prompt discipline as standing practice.

---

## Sources
- Anthropic — Manage costs effectively (Claude Code docs): https://code.claude.com/docs/en/costs
- Anthropic — Prompt caching (Claude API docs): https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude Code context-management guide: https://claudefa.st/blog/guide/mechanics/context-management
- Claude prompt-caching cost guide (2026): https://kissapi.ai/blog/claude-prompt-caching-api-cost-optimization-2026.html
- Hybrid cloud-local LLM architecture guide (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Hybrid cloud-local AI cost optimization (2026): https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- Run local models with Claude Code to cut cost: https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- Claude Code token management techniques: https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage
- Claude Code subagents guide (2026): https://computingforgeeks.com/claude-code-subagents-guide/
