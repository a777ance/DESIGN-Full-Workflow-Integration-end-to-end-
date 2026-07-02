# Process efficiency — the user ↔ AI loop

How we work with Claude (and other models) across the A777ance repos, and where the
tokens leak. Ranked by return on effort. Written 2026-07-02 (NARF). Re-check quarterly —
this space moves weekly, so treat the dated claims as perishable.

**One-line finding:** the biggest waste isn't in any single prompt — it's the **fixed
"session-start tax"** we pay on *every* session (~12–15k tokens before a word of real work),
and a **local LLM stack we already built but don't use** to absorb the cheap 60–70% of work.
Both are fixable this week with no new spend.

---

## The measured problem (our repos, today)

| What loads | Lines | When |
| ---------- | ----- | ---- |
| Auto-loaded `CLAUDE.md` (active repo, e.g. DESIGN) | 295 | every session, automatically |
| `localDNS/CLAUDE.md` | 326 | every localDNS session |
| NARF session-start reads (portfolio + roadmap + tech-debt + decisions) | 373 | every session where NARF "wakes" |
| ZORT session-start reads (portfolio + decisions + metrics + runway + budget + MARKETING ctx) | 432+ | every session where ZORT "wakes" |
| **All six `CLAUDE.md` files combined** | 1,040 | ≈ **14.6k tokens** |

A DESIGN session that wakes **both** hats loads ~1,100 lines (**≈12–15k tokens**) *before*
the first real instruction. A one-line `tech-debt.md` fix pays the same entry tax as a
full architecture review. That tax is the highest-ROI thing to cut, because we pay it
every single time.

---

## The fixes, ranked by ROI

### 1. Trim the session-start tax (biggest lever, zero cost)

- **Get `DESIGN/CLAUDE.md` (295) and `localDNS/CLAUDE.md` (326) under ~200 lines.** Current
  best-practice ceiling is ~200 lines because every line is a *recurring* per-session cost.
  The funnel diagram, the full stage-map table, the verification walkthroughs, and the
  house-style typography block are **reference material, not always-needed briefing** —
  move them to `README.md` or a Skill and leave a one-line pointer.
- **Make NARF/ZORT reads lazy, not eager.** "At session start, read these 4/6 files" means a
  trivial edit drags in ~800 lines. Rewrite the instruction to: *"Read the CTO/CFO files
  only when the task touches architecture/finance; otherwise skip."* Load-on-demand.
- **Don't wake both hats every session.** A localDNS deploy tweak does not need ZORT's five
  finance files. Scope the wake to the repo/task.

### 2. Capture the free 90% — protect the prompt cache

Claude Code already caches the system prompt + `CLAUDE.md` + tool defs; cache **reads cost
~10% of full input**, writes cost ~25% more. We get this for free — but two habits break it:

- **Editing `CLAUDE.md` mid-session** re-writes the whole cached prefix (at 1.25×). Batch
  doc edits; don't tweak the briefing file in the middle of a task.
- **Idle gaps > ~5 min** (the cache TTL) expire the cache → full re-read at 1×. Keep a
  working session moving, or accept one re-read rather than many.
- Re-reading the 10 session-start files *after they change* pays for them again — another
  reason to make those reads on-demand (fix #1).

### 3. Move detail from `CLAUDE.md` → Skills

Skills load **only when invoked**, then stay in context for that task. Prime candidates to
move out of the always-on briefing: the house-style typography rules, the end-to-end
verification walkthrough, the stage-map table. Keeps base context small without losing
the knowledge.

### 4. Use the local LLM we already built (this is the sleeper win)

`localDNS` stage 10 already runs **LiteLLM (:4040) + Open WebUI (:3000) + a reasoning ladder**
(`local-reason` = deepseek-r1:1.5b on the t630; `cloud-gpu-reason` on a rented GPU). Today
it's a chat stack — **not wired into how we actually work.** In a typical coding/ops session
**60–70% of prompts are cheap** (reading files, summarizing logs, formatting, commit
messages, first-pass doc edits, link checks). Reported savings from shifting those to a
local/cheap model: **60–80% on the moved share.**

Two ways to wire it, cheapest-risk first:
- **Manual triage (do this now):** run the cheap, bulk, non-sensitive work in Open WebUI on
  the t630 — draft a doc, summarize a log, classify a batch — and paste only the distilled
  result into Claude. No new infra; uses the box that's already on.
- **Auto-routing (later, with a caveat):** point a tool's `ANTHROPIC_BASE_URL` at a
  LiteLLM router that sends simple prompts local and hard ones to Claude. **Blocker: TD-14** —
  our router's privacy fallback currently fails *open* to cloud (`local-reason` can fail
  over to `cloud-overflow`). **Fix TD-14 (fail closed) before routing anything sensitive
  through it.** The box is idle leverage; "make the network dull / cost discipline" argues
  for using it.

### 5. Tier the model to the task

- **Haiku 4.5** for mechanical work: link-checking (`check-docs.py`), renames, doc
  formatting, commit messages. **Opus 4.8** reserved for architecture/finance judgment.
- Push **verbose output** (test logs, `check-docs` runs, `docker ps` dumps) into a
  **subagent's** context so it never lands in the main thread. Subagents are the most
  token-efficient way to keep noise out of the primary conversation.

### 6. Multi-agent discipline (matters for NARF/ZORT + workflows)

Multi-agent orchestration costs **~15× the tokens** of a single chat, and a runaway
sub-agent can multiply that again. It only pays when the question is **large and the
directions independent** — e.g. a portfolio-wide audit across all six repos. **NARF and
ZORT are personas, not separate agents; keep them that way for routine work.** Reserve
parallel agents / workflows for genuine cross-repo sweeps, and set a scope cap when you do.

### 7. Context hygiene (per-session habits)

- `/clear` between unrelated tasks — cuts per-message cost **30–50%**.
- One feature/decision per session; `/clear` at the end.
- Don't paste whole files when a grep excerpt answers the question.

---

## About the prompt that triggered this ("locate inefficiencies…")

It's an excellent *brainstorm* prompt but a **token-expensive** one, and the same discipline
we're recommending applies to it:

- **Unbounded scope** — "ANYTHING that could help… search the web… check the news… keep up to
  date day by day" invites an open-ended research crawl with **no stopping criterion**.
- **No deliverable named** — the model has to guess the format and where output goes.
- **Two asks in one** — "analyze our process" + "critique this prompt."
- **A recurring need typed as a one-off** — "keep up to date, this changes day by day" is a
  *standing* job. Re-typing it re-derives scope every time; a **saved skill / scheduled
  routine** (which this run in fact is) meets that need far more cheaply.

**A tighter rewrite that would cost a fraction:**

> Audit our Claude-Code process for token waste across the six A777ance repos. Deliverable:
> the top 5 fixes, ranked, each with an estimated % saving and the exact file/line to change,
> written to `docs/ai-cto/process-efficiency.md`. Constraint: only fixes that work with our
> existing t630 LiteLLM stack — no new paid services. Do up to 5 web searches for current
> (2026) best practices, then stop and write.

That version names the target, the output, the constraint, and a **research cap** — so the
model stops instead of wandering. Best practice for "keep this current" is not a bigger
prompt; it's this exact prompt saved and re-run on a schedule.

---

## Sources (2026, perishable)

- [Manage costs — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How to Reduce Claude Code Token Usage: 8 Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [How to Manage Claude Code Token Usage — MindStudio](https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LiteLLM Router docs](https://docs.litellm.ai/docs/routing)
- [Steering Claude Code: skills, hooks, subagents — Anthropic](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [Claude Code Agents in 2026: what parallel sessions cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Anthropic's Multi-Agent Research Architecture — The AI Engineer](https://theaiengineer.substack.com/p/how-anthropic-built-multi-agent-deep)
