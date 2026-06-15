# Process efficiency — token use & the human↔AI loop

**Owner:** NARF (AI CTO) · **First written:** 2026-06-15 · **Status:** findings + recommendations

How we spend tokens and attention working *with* Claude across the seven A777ance repos, where
that spend is wasted, and what to change. Findings are ordered **highest-leverage first**, not
chronologically (this is a recommendations doc, not a log). Each finding cites a current source
(June 2026) where one applies — re-check these quarterly; the tooling moves weekly.

> **TL;DR.** The single biggest waste is **not** the model tier or the cloud bill — it's that
> every session silently front-loads the full `CLAUDE.md` of *every in-scope repo* (~25–30k
> tokens) before a word of work, and several of those files are 5–10× longer than the "short
> briefing" they claim to be. Fix the instruction-file bloat and the session scoping first;
> everything else is smaller. We *already own* the hybrid local/cloud gateway the founder asked
> about (LiteLLM + `dispatcher.py` + Odin) — the gap is **using** it for the cheap work, not
> building it.

---

## 1. `CLAUDE.md` bloat is the primary token sink (P1)

**What's happening.** `CLAUDE.md` files are dropped into context *verbatim, up front*, on every
session — they are not retrieved just-in-time. This session loaded the full `CLAUDE.md` for
DESIGN, localDNS, customers, MARKETING, Azure-lab, and claude-code-homelab before any task ran.
`localDNS/CLAUDE.md` alone is ~600 lines (the entire deploy-paths table, the full known-issues
register, the verification command block). Rough cost: **~25–30k tokens of static preamble per
run**, paid again every routine tick.

**Why it's worse than just cost.** Current best-practice research is explicit that **bloated
instruction files make the model ignore instructions wholesale** rather than selectively
filter — so an over-stuffed `CLAUDE.md` *degrades* adherence, not just budget. Our DESIGN file
literally opens with "The short briefing — read this first" and then runs the full funnel
diagram, stage map, master-list spec, and verification walk-through. That's a reference manual,
not a briefing.

**Fix.**
- Cut each `CLAUDE.md` to the **always-true, always-needed** core: what the repo is, the
  invariants you must never break, the house-style pointer, and where to look for the rest.
  Target ≤120 lines.
- Move the **reference tables** — `localDNS`'s deploy-paths map, the full known-issues
  register, verification command blocks, the DESIGN stage map — into the existing `README.md` /
  context files. Claude reads those *just-in-time* via grep/glob when a task actually touches
  them. We already do this well in places (network-context.md, INSTALL-NOTES.md); finish the job.
- Keep the invariants that prevent *expensive mistakes* in `CLAUDE.md` (the privacy rule, "push
  to main no branches", "never commit real PII", honesty rule) — those earn their tokens.

Source: [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
[Agent instruction files (CLAUDE.md) — bloat degrades adherence](https://glama.ai/mcp/servers/@vrppaul/semantic-code-mcp/blob/ec06c4ade73c3e57c79951b3d267ffd65d9d7c84/docs/decisions/002-agent-instruction-files.md).

---

## 2. The house-style block is copy-pasted into all 7 repos (P1)

**What's happening.** The ~18-line "House style: ordering & typography" block is duplicated
**verbatim** in every repo's `CLAUDE.md`. That's the same ~250 tokens loaded N times whenever a
session spans repos, and N places to edit when the convention changes (it changed once already —
"Adopted 2026-06-05").

**Separate, compounding problem — the convention is *itself* expensive.** "Reverse the blocks
but keep the steps, never renumber; lists run Z→A; logs newest-first" is cognitively costly to
apply *and* to verify. Every walkthrough and list we generate burns extra reasoning tokens
getting the inversion right, and it's a frequent source of the model second-guessing itself. The
reverse-chronological-log convention is standard and cheap; the **reverse-the-blocks /
descending-alphabetical** rules are bespoke and pay an ongoing tax on every document touched.

**Fix.**
- De-duplicate: keep the canonical house-style in **one** file (e.g. a root `STYLE.md` in
  DESIGN) and have each `CLAUDE.md` link to it in one line.
- Reconsider whether "reverse the blocks" and "Z→A lists" earn their ongoing cost. Newest-first
  logs: keep. The block-reversal and descending-alphabetical rules: worth a deliberate decision
  on whether the benefit is worth the per-document tax. (Record as an ADR either way.)

---

## 3. Sessions are scoped to too many repos at once (P2)

**What's happening.** This routine has all seven repos in scope, so all seven briefings load
even for a single-repo task. Finding #1's cost is multiplied by the scope breadth.

**Fix.** Scope a session/routine to only the repo(s) the task touches. The portfolio hub
(`docs/ai-cto/portfolio.md`) is the *one* cross-repo artifact a single-repo task needs — read
that plus the one spoke, not all six other briefings. This is consistent with ADR-001's
hub-and-spoke design; we just aren't honoring it at the session-scope level.

---

## 4. Model tier discipline for routines (P2)

**What's happening.** This routine runs on **Opus 4.8 (1M)**. Opus is the right tool for hard
architecture/finance reasoning; it's overkill for a recurring "scan, summarize, diff the news"
job — Sonnet 4.6 is the speed/intelligence sweet spot at a fraction of the cost, and Haiku 4.5
is cheaper still for pure scans.

**Fix.**
- Reserve Opus for genuinely hard reasoning (architecture decisions, financial modeling, the
  thorny refactor). Default recurring/research routines to **Sonnet 4.6**; use **Haiku 4.5**
  for mechanical scans (link checks, file inventories, "did anything change").
- Cap thinking budget on routine work (`MAX_THINKING_TOKENS` ~10k) — the four highest-impact
  cost levers reported in the field are thinking caps, model selection, context hygiene, and
  specific prompting.

Sources: [7 practical ways to reduce Claude Code token usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage),
[Reduce Claude Code costs 60% — systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation).

---

## 5. We built the hybrid gateway — now route the cheap work to it (P2)

**What's happening.** The founder asked whether a hybrid local-LLM + Claude-API setup could
help. **It already exists** and is well-designed: `localDNS/10-ai-orchestration/` runs LiteLLM
as one OpenAI-compatible front door (`ai.home.lan:4040`) with local Ollama tiers as the
privacy-preserving default, a rented-GPU reasoning tier, and Claude as `cloud-overflow`/
capability tiers — plus a deterministic `dispatcher.py` and the Odin LangGraph supervisor. The
industry pattern the founder is describing (LiteLLM gateway + Ollama local + Claude cloud,
routed by sensitivity/complexity, ~60–80% cost reduction) is the architecture we *already
shipped*.

**So the gap is usage, not architecture.** Today the human is the router (picking a model in
Open WebUI). The cheap, high-volume, low-stakes parts of our own workflow should default to the
**local tiers**, reserving Claude for what needs the frontier:

| Workload | Route to | Why |
| -------- | -------- | --- |
| First-pass drafting, rephrasing to house voice, classification, extraction | `local-fast`/`local-smart` (Ollama, t630) | 60–70% of real LLM traffic is this class; runs free + private on the box |
| Doc-link integrity, schema checks, file inventories | **no LLM** — `tools/check-docs.py` & scripts | Deterministic, free, already exists; don't spend a token on what a script settles |
| Statement composition first draft, NotebookLM-bridge summaries | local tier, Claude only to polish | Keep private data on infra we control |
| Architecture/finance reasoning, the hardest code, this analysis | Claude (Opus/Sonnet) | Frontier ceiling earns the cost |

**One caveat that blocks "route sensitive work local" today:** **TD-14** — `local-reason` still
has a `cloud-overflow` fallback, so a sensitive prompt can fail *open* to Claude cloud if the
local model is down. Until that fails closed, we can't honestly claim sensitive work stays
local. Fix TD-14 before leaning on the local tier for anything private.

Sources: [Hybrid cloud-local LLM architecture guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/),
[Run local AI models with Claude Code to cut costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs),
[LiteLLM smart routing — Markaicode](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/).

---

## 6. Use the cost levers Claude Code already ships (P2)

Low-effort, high-return, available now (June 2026):

- **Prompt caching** for the static preamble. Our `CLAUDE.md` payload is large and *identical*
  across runs — the textbook case for caching, ~90% input-token reduction on repeated context.
  Enable `ENABLE_PROMPT_CACHING_1H` for routines that re-load the same briefings.
- **`/clear` between unrelated tasks; `/compact` (or `/recap`) within a long one.** A messy,
  carried-over context is the real cost driver, not the model. `/recap` (Apr 2026) resumes
  without replaying the whole conversation.
- **Subagents for read-heavy fan-out.** Tasks that read >3–4 large files should be delegated —
  the subagent's context accumulates in *its* session, not ours, so it doesn't weigh on every
  subsequent turn. (This run used Explore/agents for exactly that; keep doing it.)

Sources: [How to reduce Claude Code token usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage),
[23 tips for Claude Code token saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/),
[Claude Code changelog](https://code.claude.com/docs/en/changelog).

---

## 7. Prompting: be specific, name the deliverable, say "do it" (P3)

Smaller, focused requests consume less context and produce more usable output. Two concrete
habits:

- **Name the artifact and its bound.** "Write findings to `docs/ai-cto/process-efficiency.md`,
  ≤2 pages, top 5 only" beats "tell me everything you can think of."
- **Say "make the change," not "can you suggest."** If action is wanted, ask for action — the
  docs call this out explicitly.

Source: [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).

---

## 8. Critique of the prompt that generated this doc

The founder explicitly asked whether *this* prompt was inefficient. Honestly: yes, in two ways —
though it was right to ask broadly the *first* time.

1. **Unbounded scope, no deliverable.** "ANYTHING that could help… Anything you could possibly
   think of… search the web… check the news" invites maximal, unfocused token spend with no
   target format and no stopping condition. For a one-time kickoff that's acceptable (you don't
   yet know the shape of the answer). As a **standing instruction it's the most expensive
   possible prompt.** Better: "Review our process for token waste. Output the top 5 findings with
   a fix each to `docs/ai-cto/process-efficiency.md`. ≤2 pages."

2. **It's running as a recurring routine, and it re-derives everything each tick.** Open-ended
   web research + full-repo read on a schedule means we pay for the same survey repeatedly with
   no memory of the last run. **Recommended:** keep this doc as the persistent state, and change
   the recurring prompt to a cheap **delta** job: *"Re-read `process-efficiency.md`. Search only
   for Claude Code / LLM-cost changes since {last run date}. If nothing materially changed, send
   no notification. If something did, append it to the doc and notify."* That turns a full
   Opus survey into a short Sonnet/Haiku diff — and respects the routine rule of staying silent
   when there's nothing new.

What the prompt got **right**: bundling related questions (process + hybrid + prompting + news +
self-critique) is fine — they're one topic. And asking the AI to critique its own instructions
is a genuinely good habit; keep doing that.

---

## Recommended tech-debt entries (for the human to file)

These fall out of the findings above; filing them in `tech-debt.md` is left to a maintainer to
avoid ID churn from an automated run:

- **Trim `CLAUDE.md` files to ≤120-line briefings; move reference tables to README/context
  files** (P1, all repos) — finding #1.
- **De-duplicate the house-style block into one `STYLE.md`; revisit block-reversal / Z→A rules
  via ADR** (P2, all repos) — finding #2.
- **Enable prompt caching + set default routine model to Sonnet, Haiku for scans** (P2,
  process) — findings #4, #6.
- **(Already tracked) TD-14 — make `local-reason` fail closed** is the prerequisite for routing
  any private workload to the local tier — finding #5.
