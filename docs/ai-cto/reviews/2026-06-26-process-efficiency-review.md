# Process Efficiency Review — User ↔ AI Loop — 2026-06-26

Prepared by: NARF (AI CTO), Claude Code on the web. Scope: how the founder and the
AI work together across the seven A777ance repos — where tokens (and money) leak, where
prompting can be tighter, and how to use the **hybrid local-LLM + Claude infrastructure
you already own**. Web-checked against June 2026 best practice (sources at the end).

This belongs in the portfolio hub's review folder because the findings cross every repo.

---

## TL;DR — the five moves, ranked by leverage

1. **Stop loading all six CLAUDE.md files every session.** Working from `/home/user`
   pulls ~8,000 words (~11k tokens) of standing context into *every* session, most of it
   irrelevant to the task at hand. Open the *one* repo you're working in. Biggest single win.
2. **Trim the CLAUDE.md files and de-duplicate the house-style block.** The DESIGN file is
   2,600 words; localDNS is 2,700. CLAUDE.md is meant to be a thin set of standing
   instructions — push detail into README/linked files that the AI reads *on demand*.
3. **Route by task to the LiteLLM stack you already run (localDNS stage 10).** ~60–70% of
   your work (link-checks, commit messages, roster edits, formatting, classification) does
   not need Opus. Send it to local Ollama / Haiku; reserve Opus 4.8 for planning and hard
   reasoning.
4. **Match the model to the routine.** Opus 4.8 is now the default and the most expensive
   tier. This very routine is running on Opus 4.8 (1M) — overkill for a news-and-status
   sweep. Run monitors on Haiku/Sonnet; promote to Opus only on a real finding.
5. **Guardrail autonomous & parallel agents.** Parallel subagents multiply token spend with
   independent context windows; one team reported a **$47k, 3-day** runaway from unattended
   agents. Set budgets/turn caps on anything that runs while you're away.

---

## 1. The context-bloat problem (the expensive one)

**What's happening.** This session loaded the CLAUDE.md for DESIGN, localDNS, customers,
MARKETING, Azure-lab, and claude-code-homelab — all of them — because the working directory
is `/home/user` and every repo is a subfolder. Measured:

| Repo | CLAUDE.md words | ~tokens |
| ---- | ---: | ---: |
| localDNS | 2,728 | ~3,640 |
| DESIGN-… | 2,608 | ~3,480 |
| MARKETING | 1,445 | ~1,930 |
| customers | 562 | ~750 |
| claude-code-homelab | 371 | ~490 |
| Azure-lab | 316 | ~420 |
| **Total** | **~8,030** | **~10,700** |

That ~11k tokens rides on **every turn of every session**, regardless of whether the task
touches one repo or all seven. On a doc edit in `customers`, the entire localDNS network
spec and the DESIGN funnel playbook are dead weight.

**Why caching doesn't save you here.** Claude Code caches the system-prompt prefix, but the
5-minute cache TTL means a once-a-day session (or a scheduled routine) almost always pays the
full *cache-write* price, not the cheap read. The savings only land inside a single busy
working session.

**Fixes (in order of effort):**
- **Open the single repo you're working in**, not the parent folder. Then only that repo's
  CLAUDE.md loads. Free, immediate, ~70% context reduction for single-repo work.
- **De-duplicate the house-style block.** The identical ~230-word "ordering & typography"
  section is copy-pasted verbatim into all six files — that's ~1,400 redundant tokens. Shrink
  each to a 3-line summary + a link to one canonical `docs/house-style.md` in DESIGN. The AI
  reads the link only when a task actually needs the rules.
- **Slim CLAUDE.md to standing instructions.** Best practice in 2026 is a *terse* CLAUDE.md
  (the things you'd otherwise re-explain every time) with everything else in README/linked
  docs that get pulled on demand. The DESIGN funnel diagram, the full stage map, and the ZORT
  field-by-field briefing are reference material — link them, don't inline them. Target: each
  CLAUDE.md under ~800 words.

---

## 2. You already own the hybrid stack — now route to it

localDNS stage 10 (`10-ai-orchestration/`) already runs **LiteLLM as a gateway + Ollama
local models + a cloud GPU reasoning tier + the Anthropic API.** That is *exactly* the
hybrid architecture every 2026 cost guide recommends — you built it; you're under-using it.

The economics the field reports: ~60–70% of LLM requests are simple (classify, extract,
format), ~20–30% moderate, ~10% genuinely need a frontier model. Splitting that workload
saves **60–80%** of cloud spend.

**Concrete routing for A777ance:**
- **Local Ollama (free, on the t630)** — link-checking (`check-docs.py` triage), commit-message
  drafting, roster.json field edits, statement data sanity checks, "summarize this log."
  Your reasoning ladder (`local-reason` = deepseek-r1:1.5b) already exists for the light tier.
- **Haiku 4.5 ($1/MTok in)** — mechanical multi-file edits, doc reformatting, first-pass
  reviews, the *finder* legs of any audit.
- **Sonnet 4.6 / Opus 4.8** — planning, architecture, ADR/FIN decisions, the *synthesis* leg
  of an audit, anything customer-facing where the prose quality is the product.

**Caveat from your own CLAUDE.md:** don't run `deepseek-r1:7b`+ on the t630/laptop CPU — long
chain-of-thought pins every core and overheats the client. Keep heavy reasoning on the cloud
GPU pod, light reasoning on `local-reason`. That guardrail is already documented; honour it
in the routing rules.

---

## 3. Model & mode selection for Claude Code itself

- **Opus 4.8 is now the default tier and the priciest** (fast mode $10/$50 per MTok). Use
  **opusplan / start-on-Sonnet**: Opus reasons during plan mode, then hands off to Sonnet for
  implementation — Opus quality where it matters, Sonnet rates for the typing.
- **Right-size the scheduled routines.** This process-review routine fired on Opus 4.8 (1M
  context). A daily news + portfolio-status sweep is a Haiku/Sonnet job; reserve Opus for the
  turn where a real decision has to be made. Set the routine's model explicitly.
- **Use the session hygiene commands.** `/clear` between unrelated tasks (stale context is
  taxed on every later message), `/compact` for long sessions, `/recap` (new Apr 2026) to
  resume without replaying the whole transcript, `/usage` to watch spend live.

---

## 4. Use workflows instead of one long Opus session for audits

For codebase-wide work (the kind of cross-repo review this very file is), the 2026 pattern is
a **workflow**: many cheap **Haiku finder** agents fan out in parallel, a single **Opus
synthesizer** writes the conclusion. You pay frontier rates once, not for every file read.
This is cheaper *and* more thorough than one long Opus session — but only with guardrails
(next point).

**Guardrail, because it's the real failure mode:** parallel subagents each carry a full,
independent context window, so cost multiplies by fan-out. The widely-reported incident: 23
unattended subagents → **$47,000 in 3 days.** For anything autonomous (routines, web sessions,
overnight runs): cap turns, set a token budget, and prefer a bounded workflow over an
open-ended "keep going" agent.

---

## 5. On prompting (you asked me to grade the prompt that started this)

The prompt was clear in *intent* and gave good latitude, but against 2026 best practice it
leaves money on the table:

- **No output contract.** It never said *what* it wanted back (a report? a patch? a one-pager?
  committed where?). I had to infer "write a review file." A single line — *"Output: a ranked
  markdown report committed to DESIGN/docs/ai-cto/reviews/"* — removes a guess and a possible
  wasted pass.
- **No scope bound.** "ANYTHING that could help" invites an unbounded sweep. The current
  models reward a tight scope ("the three biggest token sinks, with a fix each") over "find
  everything."
- **ALL-CAPS emphasis.** "PROCESS", "ANYTHING", "UP TO DATE" — newer Claude models *over-
  trigger* on shouting and aggressive emphasis ("CRITICAL!", "YOU MUST"); calm, specific
  wording now produces *better* results. Plain case is fine.
- **What it did well:** stated the goal, invited web research, flagged recency, and asked for
  a self-critique. Keep all of that.

**A tighter rewrite (≈120 words, the 2026 sweet spot is 150–300):**

> *Audit our user↔AI workflow for cost and efficiency. Focus on the three biggest
> token sinks and a concrete fix for each. Cover: (1) context/CLAUDE.md size, (2) model
> routing across our LiteLLM+Ollama stack, (3) prompting. Use web search for current
> (June 2026) best practice and cite sources. Output a ranked markdown report committed to
> `DESIGN/docs/ai-cto/reviews/`. End with a one-paragraph critique of this prompt.*

General prompting wins for this repo set (all from current Anthropic guidance): wrap
source/context in **XML tags**, give an **explicit output schema**, use **one example**
before reaching for few-shot, and **let the model say "I'm not sure"** rather than guess —
cuts hallucination on the honesty-critical Statements.

---

## 6. Quick wins checklist

- [ ] Default to opening a single repo, not `/home/user`, for single-repo work.
- [ ] Collapse the duplicated house-style block to a 3-line stub + one canonical doc.
- [ ] Trim each CLAUDE.md toward <800 words; move reference detail to linked README sections.
- [ ] Add explicit model routing rules to the LiteLLM config (local/Haiku/Sonnet/Opus by task).
- [ ] Set the model for each scheduled routine deliberately (monitors → Haiku/Sonnet).
- [ ] Put a token budget / turn cap on any autonomous or parallel-agent run.
- [ ] Adopt the output-contract + scoped + no-caps prompt template above.
- [ ] For cross-repo audits, use a Haiku-finders → Opus-synthesis workflow, bounded.

---

## Sources (checked 2026-06-26)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Prompting best practices — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Agents 2026: subagents, teams, what parallel sessions cost — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Claude Code Sub-Agents Explained: Context, Cost, Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Code with Claude 2026: New Agent Features — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [Claude Prompt Engineering Best Practices 2026 — Prompt Builder](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026)
