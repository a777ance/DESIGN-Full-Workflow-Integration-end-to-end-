# AI Process Efficiency Review — how we work with the AI

*Prepared 2026-06-25 (routine review). Scope: the **process between the founder and the
AI** across the A777ance repos — token cost, prompting quality, and where to lean on the
local LLM stack we already built. Newest-first per house style.*

> **TL;DR — the three highest-leverage moves**
> 1. **Slim the `CLAUDE.md` files.** They are README mirrors, not briefings. Every session
>    in every repo pays for the whole thing on the cache write, and an over-long file makes
>    the AI *ignore* rules (Anthropic's own warning). Biggest single win.
> 2. **Use the hybrid router we already own.** The LiteLLM/Ollama ladder on the t630 exists
>    and bills $0 for local tiers. Today it serves the product agents (Odin/NARF), not our
>    *coding* grunt work. Point the cheap, non-sensitive grunt work at it; keep Claude for
>    the hard reasoning. (Close **TD-14** first so it's safe.)
> 3. **Prompt by contract, not by wish.** State goal + boundaries + definition-of-done +
>    output format. The prompt that triggered this review is the counter-example (§5).

---

## 1. Where the tokens actually go (and the fix for each)

| Inefficiency (today) | Why it costs | The fix |
| --- | --- | --- |
| **Bloated `CLAUDE.md` in every repo.** DESIGN's is the full funnel + tables + NARF + ZORT protocols; localDNS's mirrors the whole README. | Loaded at the **start of every session**, paid on every cache write, and re-read on every context reset. Long files also degrade instruction-following — rules get lost in the noise. | Cut each to "rules the AI can't infer." Move diagrams, stage maps, and the deploy tables into the README / a skill, pulled in **on demand** with `@file` or a `SKILL.md`. Test: for each line ask *"would removing this cause a mistake?"* If no, cut it. |
| **The "House style" block is copy-pasted verbatim into all 7 repos.** | ~400 tokens of identical content loaded redundantly, maintained in 7 places (drift risk). | Keep it once (e.g. `~/.claude/CLAUDE.md` for the founder, or a single `house-style.md`), `@`-import where needed. One source of truth — the same rule we apply to business facts. |
| **Session-start "read all these files" protocols (NARF reads 4 files, ZORT reads 6).** | Every session front-loads ~10 portfolio/roadmap/decisions/metrics/runway/budget files whether or not the task needs them. | Change the protocol to **"read `portfolio.md` first; pull the others *when the task touches them*."** Let the AI fetch context itself (a documented best practice) instead of mandating it up front. |
| **Open-ended "investigate everything" prompts** (this review's own prompt). | Triggers reading hundreds of files into the *main* context. | Scope the task, or delegate the reading to **subagents / the Explore agent** — they read in a separate context and return only the summary (40–70% main-context savings on research-heavy tasks). This review used that pattern. |
| **One long kitchen-sink session across repos/tasks.** | Stale context from repo A pollutes work on repo B; performance drops, cost rises. | `/clear` between unrelated tasks; `/compact <focus>` to keep the mental model while shedding tokens. After two failed corrections, `/clear` and re-prompt — almost always beats a long polluted session. |

---

## 2. The hybrid lever we already built but don't use for *coding*

We stood up a real **route-don't-shard** stack (`localDNS/10-ai-orchestration/`): a LiteLLM
front door at `ai.home.lan:4040` with a local-first ladder
(`local-fast` qwen2.5:3b → `local-smart` 7b → `local-reason` deepseek-r1:1.5b) failing over
to a rented-GPU tier and finally `cloud-overflow` (Claude). The industry is converging on
exactly this: hybrid routing is becoming the **default** deployment for serious shops in
2026, with **60–80% cost cuts** by sending the ~60–70% of "simple" work local and reserving
frontier models for the ~10% that needs them.

**The gap:** that router serves our *product* agents. Our *own* AI-assisted workflow — drafting,
summarizing, doc checks, commit messages — still goes straight to a frontier model. Candidates
to push to the **local, $0, private** tier:

- **Doc-integrity & link checks**, first-draft commit messages, changelog reformatting,
  reverse-chronological re-sorting to house style — mechanical, cheap, local-suitable.
- **RAG over our own docs** — the embeddings tier (`local-embed` / nomic-embed-text) is
  already configured. Index the three repos so "where did we decide X?" is answered locally
  instead of by re-reading files into a frontier context.
- **Statement drafting at "a penny a home"** — the compose step's boilerplate can be a local
  pass; Claude reviews only the honesty-sensitive numbers.

**Keep on Claude (don't false-economize):** multi-file reasoning, architecture decisions,
anything touching the *honesty rule* on a kept document, and final review. Local 1.5–7B models
on a CPU box are not a substitute there — quality and the thermal limit (the DeepSeek-R1
known-issue) both say no.

> ⚠️ **Prerequisite: close TD-14 first.** The router's privacy fallback isn't fail-closed yet,
> so a `sensitive` task could spill to a cloud tier. Until that lands, don't widen what flows
> through the router. This is already the #1 actionable item in the portfolio — it now has a
> second reason to ship.

---

## 3. Prompt-caching hygiene (cheap, immediate)

Claude Code auto-caches, and the cache point moves forward as a conversation grows — up to
**~90% cost reduction** on multi-turn sessions, with a cache read costing ~10% of normal input.
We get this nearly for free **if** the stable prefix stays stable:

- **Keep volatile content out of the cached prefix.** A timestamp, "Last updated: …", or a
  per-session note near the top of a `CLAUDE.md` invalidates the cache every run. (Our
  portfolio header carries a long dated note — fine in a doc, costly if it sits in a file
  loaded as a cached prefix.)
- **Stable stuff first, variable stuff last.** Put the unchanging rules at the top; anything
  that changes per task goes in the message, not the briefing file.
- **Normalize whitespace** — trivial reformatting churn causes silent cache misses.

---

## 4. Prompting patterns worth standardizing

Anthropic's 2026 guidance: **a good agent prompt reads like a job description, not a question** —
goal, boundaries (what *not* to touch), definition of done, available tools, and an output
schema. Concrete upgrades for our recurring work:

- **Give the AI a check it can run.** Our `tools/check-docs.py` is exactly this — name it in
  the prompt ("…then run `python3 tools/check-docs.py` and fix until green"). A self-verifying
  task finishes unattended; an unverified one waits on a human. Same idea for `make statement`.
- **Explore → Plan → Implement** for anything multi-file or unfamiliar; skip the plan for a
  one-line diff (planning has overhead — don't pay it for a typo).
- **Reverse the chain-of-thought instinct.** Reasoning models (Opus 4.x) think step-by-step on
  their own now; hand-written "think step by step" scaffolding often *hurts*. State the goal,
  let it reason.
- **Templatize the repeated jobs.** "Build a statement," "Add a customer," "Run the monthly
  job" are documented prose — turn them into `disable-model-invocation` skills (`/add-customer`,
  `/build-statement`) so the steps load on demand and run consistently instead of being
  re-described each time.

---

## 5. The prompt that triggered this review — graded

The request *("Locate inefficiencies… Is there a better way… Anything you could possibly
think of… ANYTHING that could help…")* is a textbook **infinite-exploration** prompt: no
scope, no definition of done, no output format. It's fine for *discovery* (you genuinely
wanted a wide net, and that's a legitimate use), but it's the most expensive shape of prompt.
A lower-token version of the same intent:

```
Review how we use the AI across the repos for token waste. Cover: CLAUDE.md size,
session-start protocols, and whether to route grunt work to our local LiteLLM tier.
Use subagents for the file reading. Output: a ranked table of fixes (lever, cost,
effort) + a one-paragraph verdict on the local-model option. Skip generic listicles —
tie every point to a file in our repos. ≤2 pages.
```

That version scopes the search, forces delegation of the expensive reads, fixes the output
shape, and would cost a fraction. It also bans the generic-listicle failure mode.

**On running this as a scheduled routine:** an open-ended "find anything" task re-run on a
timer re-pays the full discovery cost each time and mostly re-derives the same findings. If
this should recur, narrow it to a *delta* check — e.g. "diff the Claude Code changelog since
last run; flag only new features that change our token math" — which is cheap and actually
benefits from repetition. The broad sweep is a one-shot.

---

## 6. Quick-win checklist (ranked: leverage ÷ effort)

1. **Slim every `CLAUDE.md`** to high-impact rules; move the rest to README/skills. *(High leverage, low effort.)*
2. **De-duplicate the house-style block** into one `@`-imported file. *(Med / low.)*
3. **Relax NARF/ZORT session protocols** to "portfolio first, rest on demand." *(High / low.)*
4. **Adopt `/clear` + subagent-for-research as default habits.** *(High / habit.)*
5. **Close TD-14**, then route doc-checks / commit-messages / RAG to the local tier. *(High / med.)*
6. **Turn the repeated playbooks into slash-command skills.** *(Med / med.)*
7. **Prompt by contract; name the verification check.** *(High / habit.)*

---

## Sources

- [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) — context management, CLAUDE.md sizing, subagents, plan mode, `/clear`+`/compact`.
- [Prompt caching — Claude API](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) & [Claude prompt-caching guide (2026)](https://www.respan.ai/articles/claude-prompt-caching) — ~90% multi-turn savings, cache-prefix hygiene.
- [Hybrid Cloud-Local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) & [Hybrid cost-optimization](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026) — 60–80% savings; routing by sensitivity/complexity; hybrid as 2026 default.
- [Run local models with Claude Code](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) & [LiteLLM + Claude Code setup](https://www.truefoundry.com/blog/claude-code-with-litellm-setup-guide-when-to-use-truefoundry-ai-gateway).
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) & [Prompting best practices — Claude](https://claude.com/blog/best-practices-for-prompt-engineering) — job-description prompts, reasoning-model CoT caveat.
- [Claude Code subagents (2026)](https://www.tembo.io/blog/claude-code-subagents) — 40–70% context savings on research; the 7× over-delegation caveat.
- [Claude Code June 2026 features](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/) & [changelog](https://code.claude.com/docs/en/changelog) — agent teams, nested subagents, per-agent cost attribution, `Tool(param:value)` permission rules.
