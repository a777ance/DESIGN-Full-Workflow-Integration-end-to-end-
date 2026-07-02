# AI Process Efficiency — reducing token spend on the user↔Claude loop

**Owner:** NARF (AI CTO), with ZORT (cost) input · **Reviewed:** 2026-07-02
**Scope:** how we *work with* Claude across the seven A777ance repos — not what we build.
The goal is fewer tokens per unit of work, without losing quality on the parts that matter
(customer-facing copy, reasoning, honesty of the kept document).

This doc is a reference (not time-based); the change log at the bottom reads newest-first.

---

## TL;DR — the five moves, ranked by payback

| # | Move | Effort | Est. saving | Where |
| - | ---- | ------ | ----------- | ----- |
| 1 | **Slim the seven `CLAUDE.md` files; push detail behind `@file` refs** | Low | Large, *every* session | all repos |
| 2 | **Route bulk/low-sensitivity work to the local LLM ladder we already run** | Low (it exists) | 60–80% on routed work | localDNS stage 10 |
| 3 | **Tier the model to the task; stop using Opus for mechanical edits** | Low | High on routine work | all |
| 4 | **Scope prompts: state task + constraints + output format up front** | Low | 40–70% via less trial-and-error | the human |
| 5 | **Use plan mode, subagents, and terse output styles by default** | Low | 40–70% context, ~65% output | all |

Everything below is the reasoning and the concrete how.

---

## 1. The biggest recurring cost is our own context, not the work

Every Claude Code session in this portfolio loads **all seven `CLAUDE.md` files** plus the
per-repo AI-CTO/CFO state files the briefings tell it to read at session start. Most of that
is irrelevant to any single task. A routine that only touches `localDNS` still pays to ingest
the `MARKETING`, `customers`, and `DESIGN` briefings — on every run.

The fix is **context engineering**, the discipline Anthropic now names explicitly: give the
model the *minimum* context needed, and load the rest on demand.

- **Keep each `CLAUDE.md` to a true briefing.** It should say what the repo is, the handful of
  rules that must never be broken, and pointers. Deep rationale already lives in
  `network-context.md` / `workflow-context.md` — reference it, don't inline it.
- **Prefer `@file` references over pasted detail.** Claude Code loads `@filename.md` on demand;
  a briefing that *links* the schema is cheaper than one that *contains* it.
- **Don't make every session read every state file.** The NARF/ZORT "read these 5–6 files at
  session start" instruction is right for a planning session and wasteful for a one-line doc
  fix. Gate it: *"read the portfolio hub only when the task is cross-repo or a decision."*
- **Watch the meter.** `/context` shows exactly where tokens go (system prompt, tools, memory,
  skills, history); `/compact` collapses a long session into a summary. Build the habit of
  glancing at the token % before starting a new task.

Rule of thumb from the field: teams that do this cut 40–70% off session cost.

## 2. We already own a hybrid stack — route to it

`localDNS` stage 10 runs a LiteLLM gateway with a reasoning ladder: `local-reason`
(deepseek-r1:1.5b on the t630, cool/cheap), `cloud-gpu-reason` (full R1 on a rented GPU), and
`cloud-overflow` (Claude). That is exactly the architecture the 2026 hybrid guides recommend —
an intelligent routing layer that sends work to local or cloud based on **complexity and data
sensitivity**. We built it; we should *use* it for the routine work, not reach for the Claude
API by reflex.

Typical production mix is ~60–70% simple requests (classify, extract, format, lookup), ~20–30%
moderate, ~10% frontier-grade reasoning. Route accordingly:

| Send **local** (deepseek / t630) | Keep on **Claude API** |
| -------------------------------- | ---------------------- |
| Doc-link checks, lint, formatting, renames | Customer-facing copy (the voice rule) |
| Roster/CRM lookups and field extraction | Multi-repo reasoning, architecture, ADRs |
| First-draft summaries, changelog tidying | The honesty-sensitive parts of a Statement |
| Classifying leads / triaging issues | Anything needing the January-2026 knowledge + web |

**Two hard rules for our data:**

1. **Anything with real customer PII routes local by default.** The `customers` repo is private
   for a reason; a household's name and figures should not leave our infrastructure to save a
   few tokens. Hybrid guides make this the default; so should we.
2. **Fix TD-14 before trusting the router for sensitive work.** Today a `sensitive`-tagged task
   can fail over from `local-reason` to `cloud-overflow` (Claude) if the local model is down —
   the `allow_cloud=False` intent is not enforced at the LiteLLM failover layer. Until
   `local-reason` has a *local-only* fallback (fail closed), the privacy guarantee is not real.
   This is already logged as **P1 tech debt**; it is the gating item for move #2.

Routing simple work off the frontier model is the single biggest lever after context: the
hybrid guides report 60–80% cost reduction versus running everything on a frontier model.

## 3. Tier the model to the task

Even when we do use Claude, we don't need the top model for everything. Claude 4.x models
follow instructions literally, and the cheaper tiers are more than enough for mechanical edits,
reformatting, and short lookups. Reserve Opus-class reasoning for genuinely hard,
cross-cutting work; let Haiku/Sonnet handle the routine. Pair this with **prompt caching**,
which the Agent SDK and Claude Code apply automatically: a stable prefix (system prompt, the
briefing, the tools) is billed at ~10% of input price on cache *reads* (5-minute TTL). Practical
consequence for us: **batch related tasks into one session** so the cache stays warm, rather
than spawning a fresh session (and a cold cache + full re-ingest) per tiny change.

## 4. Prompts: scope, structure, and "why"

Vague prompts are expensive — the model opens files, explores dead ends, and reconstructs
context we could have handed it. The current best-practice shape for Claude:

- **State the contract up front:** task, constraints, and what "done" looks like.
- **Use the 4-block pattern** — INSTRUCTIONS / CONTEXT / TASK / OUTPUT FORMAT — and wrap
  source material in XML tags. Structure beats length; reasoning starts degrading past a few
  thousand tokens, and the sweet spot for most asks is a few hundred words.
- **Specify the output format** (and a length cap). Claude 4.x is literal — if you don't ask
  for brevity, you won't get it.
- **Explain *why* a rule exists.** Claude generalizes better from motivated instructions than
  from bare commands — which is exactly why our `CLAUDE.md` files already explain the *why*
  behind the voice rule and the honesty rule. Keep that; it pays off.
- **Add a one-line self-check** the model must pass before finalizing (e.g. "confirm no real
  PII left the private repo").

## 5. Lean on the harness features built for this

- **Plan mode** before any non-trivial change: get the plan, cut the fat, *then* execute. Kills
  the biggest token sink — trial-and-error runs.
- **Subagents / the Explore agent** for codebase research: they read in a separate context and
  hand back a summary, so file dumps never land in the main window. Anthropic's June-2026
  update added fan-out workflows (tens–hundreds of parallel subagents) and grader-driven
  revision — overkill for us today, but the plain "delegate research to a subagent" pattern is
  a daily win.
- **Terse output styles.** A "caveman"-style output style that strips narration and pleasantries
  while keeping every technical fact and code block intact cuts output tokens ~65%. For our
  routines — which nobody reads live — this is close to free savings. (Customer-facing copy is
  the exception: there the voice rule wins.)
- **Skills over re-pasted instructions.** A skill loads only when relevant, so a repeated
  procedure (build a statement, add a customer) costs nothing until it's actually used.
- **Note the June-15-2026 metering change:** Agent SDK and GitHub Actions usage is now metered
  separately from interactive Claude Code and billed per token. Scheduled/CI agentic work (like
  this routine) is now a *line item* — another reason to route its bulk steps local (#2) and
  keep its prompts terse (#5).

---

## On the prompt that requested this analysis

The requesting prompt was, candidly, an inefficient prompt — and a fair example of #4. It was
open-ended ("ANYTHING that could help… anything you could possibly think of"), set no scope, no
output format, and no budget, and bundled several distinct asks (token use, prompting, hybrid
routing, "check the news") into one. That maximises exploration cost: the model casts wide
because nothing tells it where to stop.

A cheaper version of the same request:

```
TASK: Audit how we use Claude across the A777ance repos and propose token-saving changes.
CONTEXT: We run scheduled routines over 7 repos; we already run a LiteLLM local/cloud
  ladder (localDNS stage 10). Assume 2026 best practices; check the web only for anything
  post-January-2026.
OUTPUT: A ranked table of ≤6 changes (effort + est. saving), each with one concrete how-to.
  Then a 3-line critique of this prompt. Commit to docs/ai-cto/. ≤2 pages.
SELF-CHECK: every recommendation must map to something in our actual stack.
```

Same answer, a fraction of the wandering. The irony — spending a wide-open, expensive prompt to
ask how to spend fewer tokens — is itself the lesson.

---

## Sources (as of 2026-07-02)

- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Best practices for Claude Code — docs](https://code.claude.com/docs/en/best-practices)
- [Steering Claude Code: skills, hooks, rules, subagents — Anthropic (2026-06-18)](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Prompting best practices — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Track cost and usage — Agent SDK docs](https://code.claude.com/docs/en/agent-sdk/cost-tracking)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Context Window: Optimize Your Token Usage — claudefast](https://claudefa.st/blog/guide/mechanics/context-management)
- [Token Economics in 2026 — Age of Product](https://age-of-product.com/token-economics-2026/)

---

## Change log

- **2026-07-02** — Initial audit (NARF). Five ranked moves; ties #2 to TD-14 (privacy
  fail-open) as its gating item.
