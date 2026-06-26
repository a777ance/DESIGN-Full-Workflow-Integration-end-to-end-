# Process efficiency review — user ↔ AI loop (2026-06-26)

*Standing question from the founder: where is the user↔AI process inefficient, how do we cut
tokens, prompt better, and lean on hybrid local-LLM + Claude API? Keep this up to date — the
field moves weekly.* This is the first pass; treat it as a living doc (newest notes at top per
house style).

---

## TL;DR — the five that matter

1. **Every session pays ~17k tokens before any work.** The DESIGN repo's mandatory
   session-start load (CLAUDE.md + the 4 CTO files + the 5 CFO files that NARF/ZORT are told to
   read) measures **~12,680 words ≈ 17,000 tokens**, *every session, before Claude reads the
   task or any code.* `metrics.md` alone (3,681 words) is a log re-ingested in full each time.
   This is the single biggest lever.
2. **Confirm prompt caching is actually hitting through LiteLLM.** Claude Code caches the system
   prompt + CLAUDE.md natively (cache reads ≈ 10% of input price). But for anything routed
   through the t630 `llm-router` (LiteLLM), cache breakpoints must be passed through explicitly
   or you pay full freight on every repeated persona prompt.
3. **Push more work onto the local tier you already run.** The reasoning ladder
   (`local-reason` → `cloud-gpu-reason` → `cloud-overflow`) is the right shape. ~60–70% of real
   tasks (classify, extract, format, draft-commit-message, "which stage does this belong to")
   can stay on the t630 and never touch the Claude API.
4. **Stop loading; start retrieving.** Adopt Anthropic's **memory tool + context editing**
   (shipped with Sonnet 4.5; ~39% lift on internal agentic-search evals) so NARF/ZORT *consult*
   their state on demand instead of front-loading 10 files blind.
5. **The standing prompt is itself inefficient** (see §6). "ANYTHING that could help… check the
   news" with no scope or stop condition invites unbounded, full-cost exploration on a recurring
   schedule. Scope it and make it diff-based.

---

## 1. Cut the session-start tax (highest impact, one-time work)

**Measured today:**

| Repo | CLAUDE.md | + mandatory state reads | ≈ tokens/session before work |
| ---- | --------- | ----------------------- | ---------------------------- |
| DESIGN | 2,608 w | +10,072 w (CTO+CFO files) | **~17,000** |
| localDNS | 2,728 w | — | ~3,600 |
| MARKETING | 1,445 w | + ai-cto/ai-cfo context | ~3,000+ |

A published benchmark this year trimmed a 3,847-token CLAUDE.md to 312 tokens — **91.9%
reduction, no quality regression** — by keeping only what Claude *cannot infer from the code
itself*. Our CLAUDE.md files are mostly reference prose (stage maps, deploy-path tables, money
flow) that belongs in README/context files and can be *pointed to*, not *inlined*.

**Actions:**
- **Trim each CLAUDE.md to essentials + pointers.** Target <500 tokens. Move the stage map,
  deploy-path table, topology diagrams, and the role/money-flow prose into the READMEs they
  already duplicate, and link them. Keep in CLAUDE.md only: the non-inferable rules (push-to-main
  vs branch, honesty rule, secrets rule, house style) and a one-line "further reading" map.
- **Make NARF/ZORT state reads conditional, not mandatory.** "Read these 9 files at session
  start" is the costliest instruction in the repo. Replace with: read `portfolio.md` (the index)
  only; pull `decisions.md`/`metrics.md`/`runway.md` *when the task touches them*. `metrics.md`
  (3,681 w) should almost never be loaded whole — it's an append log; read the tail.
- **De-duplicate the house-style block.** The identical ~40-line "ordering & typography" block is
  copy-pasted verbatim into 6 CLAUDE.md files. Make it one shared `docs/house-style.md` (or a
  Skill) and reference it. Saves re-authoring drift, not per-session tokens (only the active
  repo's copy loads), but it's a correctness win.
- Add a `.claudeignore` in each repo for generated/large/irrelevant paths so search and
  auto-context don't pull them.

## 2. Prompt caching — verify it's working end-to-end

- **Native Claude Code:** the frozen system prompt + tool defs + CLAUDE.md sit behind a cache
  breakpoint; cache **reads ≈ 10%** of normal input price, **writes cost ~25% more** — so it pays
  off after the request repeats ~twice. A long-but-*stable* CLAUDE.md is far cheaper than a
  short-but-*churning* one, because edits bust the cache. Implication: stop editing CLAUDE.md
  mid-session.
- **Through the LiteLLM router:** LiteLLM supports Anthropic `cache_control`, but it is **not
  automatic** — the breakpoints must be set on the system/tools blocks or every call to the
  NARF/ZORT persona prompt re-bills the full prefix. Action: add an explicit cache breakpoint on
  the persona system prompt in `~/llm-router/config.yaml`, then confirm cache-hit tokens in the
  LiteLLM logs.
- Cache TTL is ~5 min (the harness note about cache windows applies): batching related turns
  inside one warm window beats spreading them across idle gaps.
- Note: as of 2026-02-05 caches are **isolated per workspace** on the Claude API — irrelevant for
  a solo founder, but relevant if operators ever get their own workspaces (Phase 2).

## 3. Hybrid local + cloud routing — you're 70% there

The homelab already has the right architecture (LiteLLM gateway, Ollama-served local models, the
`local-reason`/`cloud-gpu-reason`/`cloud-overflow` ladder). Industry data: hybrid routing cuts
LLM spend **60–80%** because the real task mix is ~60–70% simple, ~20–30% moderate, ~10% needs a
frontier model.

**Push more down the ladder:**
- Add a **`local-fast` tier** (a small instruct model, e.g. Llama-3.x-3B / Qwen-2.5-3B on the
  t630) for the genuinely trivial: commit-message drafts, link/anchor checks (though
  `check-docs.py` already does that deterministically — keep using the *script*, not a model),
  roster field validation, "which stage/folder does this belong to" classification, statement
  copy-edits to the plain-English voice.
- **Route by task, not by habit.** Reserve the Claude API (Opus/Sonnet) for multi-file reasoning,
  architecture decisions (ADR drafting), and anything customer-facing on a kept document. Default
  everything else to local.
- **Privacy bonus that fits the brand:** routing customer/roster data (the `customers` private
  repo) through the *local* tier keeps real names and figures off third-party infrastructure —
  consistent with the "honesty / private stays private" rules.
- **Don't over-fan-out.** Multi-agent / subagent workflows use **4–7× the tokens** of a single
  thread (each subagent carries its own context); one public incident hit ~$8–15k from 49
  parallel subagents left running 2.5h. Use subagents only to isolate *verbose* output you don't
  want in the main context; cap parallelism (3–5 is the sweet spot) and never leave them running
  unattended. Add that cap as a rule in CLAUDE.md.

## 4. Adopt the new context-engineering primitives (2026)

Anthropic shipped, with Sonnet 4.5, two things that directly target our session-start tax:
- **Memory tool** — a file-based store *outside* the context window for facts that should inform
  every session (constraints, pricing decisions, learned patterns). This is the right home for
  the NARF/ZORT "persistent state" instead of re-reading 9 files. The agent consults it on
  demand.
- **Context editing** — the agent prunes stale tool results / compresses verbose output mid-run.
  Combined with memory, Anthropic reports **+39%** on internal agentic-search evals and longer
  runs before hitting the window.
- Practical Claude Code habits that follow from the same principle: `/clear` between unrelated
  tasks (don't carry a 4-hour transcript into a 2-line question), use a `session-handoff.md` to
  restart cheaply, and prefer Skills' **progressive disclosure** (load domain knowledge on
  demand) over inlining everything in CLAUDE.md — reported ~15k tokens/session recovered, ~82%
  better than load-everything-upfront.

## 5. Model selection

This session is running **Opus 4.8 (1M context)** — the most expensive tier × the most expensive
context window. For routine doc edits, log appends, and link fixes that is overkill. Default the
*routine* repo work to Sonnet (or local), and reserve Opus + 1M-context for genuinely large
cross-repo reasoning. The 1M window in particular should be opt-in per task, not the default.

## 6. The standing prompt itself — critique & rewrite

The founder's recurring prompt ("Locate inefficiencies… ANYTHING that could help… Search the
web… Keep UP TO DATE… Check the news. Thanks!") is warm and clear in *intent* but expensive in
*shape*:

- **No scope or stop condition.** "ANYTHING" + "anything you could possibly think of" tells a
  frontier model to explore without bound — the most token-hungry instruction you can give.
- **No acceptance criteria.** The model can't tell when it's done, so it over-produces.
- **"Check the news / keep up to date" on a schedule re-researches from scratch every run.** With
  no persisted prior state, run N+1 re-derives everything run N already found.
- **Politeness padding** ("Thanks!", "Perhaps also…") is harmless for cost but the open-endedness
  is not.

**A cheaper, sharper version (drop-in):**

> *Review our user↔AI process for token waste. Compare against the findings in
> `docs/ai-cto/process-efficiency-*.md` and report only what's **new or changed** since the last
> run. One web pass for genuinely recent developments (cite dates). Output: top 3 actions ranked
> by tokens-saved-per-hour-of-work, each with the concrete file/config to change. Stop at 3.
> Skip anything already logged. Notify only if there's a new high-impact item.*

That version: bounds the search, makes it **diff-based** (cheap on repeat), gives a hard stop,
and prevents the routine from re-doing this whole report every time it fires.

---

## Sources (2026)

- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching](https://code.claude.com/docs/en/prompt-caching)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Context engineering: memory, compaction, tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Introducing Claude Sonnet 4.5 (memory tool + context editing) — Anthropic](https://www.anthropic.com/news/claude-sonnet-4-5)
- [Claude Code Token Optimization (2026 guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM gateways — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Claude Code Sub-Agents: Context, Cost, Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
