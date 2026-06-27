# Process efficiency: user ↔ AI — findings & actions

*NARF (AI CTO) review, 2026-06-27. Trigger: founder asked us to hunt inefficiencies in
the human↔AI process — token cost, prompting, leveraging other AI, hybrid local/cloud.
This is a living doc; keep the changelog newest-first per house style.*

> **TL;DR.** Three changes capture ~80% of the savings: (1) trim the always-loaded
> `CLAUDE.md` files (~10.7k tokens are billed on *every* turn across the portfolio),
> (2) stop running **Opus 4.8 for everything** — match the model to the task, and
> (3) actually *use* the hybrid router you already built (LiteLLM + Ollama) for the
> mechanical work instead of sending it to a frontier model. Nothing here needs new
> infrastructure — the local stack is already standing in `localDNS/10-ai-orchestration`.

---

## 0. How big is the problem, concretely

| Lever | Measured today | Note |
| ----- | -------------- | ---- |
| `CLAUDE.md` always-loaded context | **~10,700 tokens/turn** across 6 repos | DESIGN ~3,500 · localDNS ~3,640 · MARKETING ~1,930 · customers ~750 · homelab ~490 · Azure ~420 |
| Session-start mandatory reads (DESIGN) | portfolio + roadmap + tech-debt + decisions + CFO files | hundreds–thousands more tokens before any work begins |
| Default model | **Opus 4.8** for every task incl. doc edits, house-style fixes, roster updates | Opus is $5/$25 per Mtok; Sonnet ~5× cheaper; Haiku ~15× cheaper |
| Hybrid router `cloud-overflow` tier | wired to **`anthropic/claude-opus-4-8`** | the *fallback/overflow* path defaults to the priciest model |

A 3,500-token `CLAUDE.md` costs 3,500 tokens whether a session is 2 turns or 200. That's
the cheapest win because it's pure dead weight — and prompt caching only softens it, it
doesn't remove it.

---

## 1. Recommendations, highest-impact first

### 1.1 Put the `CLAUDE.md` files on a diet (biggest, easiest win)
Current best practice: **`CLAUDE.md` is a lookup table, not a brain dump.** Ours have
grown into mini-READMEs — full deploy-path tables, long known-issues prose, rationale.

- **Keep in `CLAUDE.md`:** the rules that change behaviour every turn (house style, the
  "push to main / push to branch" instruction, the honesty rule, the one-source-of-truth
  rule, a 1-line pointer to each deep doc).
- **Move out to linked docs (loaded on demand):** the full deploy-path table → already in
  README, so `CLAUDE.md` can shrink to "deploy paths: see README §C." The verbose
  known-issues tables → keep in README/INSTALL-NOTES; `CLAUDE.md` carries only the
  *currently-active* gotcha. Long narrative ("WHY this is split…") belongs in
  `*-context.md`, not the briefing.
- **Target:** localDNS and DESIGN under ~1,500 tokens each. That alone reclaims ~4k
  tokens/turn. Claude still reads the detail when a task needs it — it's one `Read` away.

### 1.2 Match the model to the task (stop defaulting to Opus)
The single biggest per-token lever. Rough policy:

| Task class | Model | Why |
| ---------- | ----- | --- |
| House-style reformat, link fixes, roster edits, renames, "reverse this list" | **Haiku 4.5** or a **local** model | mechanical; frontier reasoning wasted |
| Statement drafting, doc writing, routine code, tests | **Sonnet 4.6** | ~5× cheaper than Opus, plenty capable |
| Architecture decisions (ADRs), cross-repo reasoning, gnarly debugging | **Opus 4.8** | reserve it for what actually needs it |

In Claude Code: start sessions on Sonnet, escalate to Opus only when stuck. Consider
**Fast mode** on Opus (now ~3× cheaper than it was on 4.7, at ~$10/$50 per Mtok) when you
want frontier quality with snappier output.

### 1.3 Use the hybrid router you already own
You built `localDNS/10-ai-orchestration` (LiteLLM @ `ai.home.lan:4040`, Ollama models
`local-fast`/`local-smart`/`local-reason`, `cloud-gpu-reason` on a rented GPU, embeddings)
— but it isn't wired into the day-to-day Claude workflow. Industry hybrid setups report
**60–83% LLM cost cuts** by sending the 60–70% of requests that are simple
(classification, extraction, formatting, drafting) to local models and reserving frontier
models for the ~10% that need real reasoning.

Concrete:
- **Route mechanical NLP to local.** House-style enforcement, "summarize this log into a
  Handled-For-You entry," tagging leads, first-draft copy → `local-smart` (qwen2.5:7b) via
  the router. Free after electricity.
- **Fix the overflow tier.** `cloud-overflow` currently falls over to **Opus 4.8** — the
  most expensive model — as the *catch-all*. Make the cheap fallback Sonnet or Haiku
  (`anthropic/claude-sonnet-4-6` / `claude-haiku-4-5`) and keep Opus for an explicit
  `cloud-reason-hard` alias only. One-line change in `config.yaml`.
- **Cost-check the Odin/LangGraph fleet.** "3 orders of 5 + Loki" = 16 agents. If each
  worker hits the Claude API, that's a 16× multiplier. Orchestrator-worker best practice:
  **supervisor (Odin) on a frontier model, the 15 workers on local/cheap models.** Verify
  what each agent's backend resolves to before running the fleet on anything large.

### 1.4 Lean on deterministic tools, not the LLM
You already do this well (`tools/check-docs.py`, the penny-a-home statement generator) —
extend the pattern. Anything with a single correct output shouldn't cost a token of
inference:
- **House-style linter.** Reverse-chron ordering, Z→A lists, the Gill Sans CSS stack, the
  "never renumber" rule — these are checkable by a script. A `check-style.py` next to
  `check-docs.py` would catch violations in CI for free and stop us spending Opus turns on
  "did you order this newest-first?"
- Keep statement generation and link-checking as code, never as prompts.

### 1.5 Prompt caching hygiene (mostly automatic, two gotchas)
Claude Code caches the stable prefix automatically; a cache *read* is ~10% of input price,
so a stable `CLAUDE.md` + tool set is ~90% cheaper after the first turn. Don't sabotage it:
- **Keep volatile strings out of the cached prefix.** A per-turn timestamp/`currentDate`
  injected into a cached block busts the cache every turn. Day-granularity or move it to
  the user message.
- **Don't churn `CLAUDE.md` mid-session.** Editing it invalidates the cached prefix for the
  rest of the session — batch briefing edits.

### 1.6 Context hygiene & the new long-run primitives
- `/clear` when switching to unrelated work; `/compact` when a session drifts; `/rewind`
  (new) to resume before a `/clear` instead of rebuilding context.
- For long autonomous routines, the new **context editing** (auto-clears stale tool
  results near the limit) and the **memory tool** (file-based store outside the context
  window) let a routine run long without re-loading everything. Relevant to *this very
  routine* — a scheduled "find inefficiencies" run on Opus is itself a recurring cost.
- For cross-repo audits, prefer **fan-out subagents** (each with its own context) over
  stuffing six repos into one Opus window — but only when the saved clutter beats the
  ~startup overhead; subagents aren't automatically cheaper for small tasks.

---

## 2. On the prompt that triggered this run

The founder asked us to critique the request itself. It was effective at getting a broad
answer, but it's an expensive shape:

- **It's open-ended ("ANYTHING that could help").** Vague scope makes the model scan
  broadly and write long — more input *and* output tokens. Specific asks ("audit the
  CLAUDE.md token cost and propose cuts") read fewer files and answer tighter.
- **It bundles ~6 distinct questions** (token use, prompting, other AI, hybrid local,
  best practices, self-critique). Each is a project. Bundling forces one long pass instead
  of cheap, targeted ones.
- **No output contract** (length, format, where the answer should live). The model guesses
  and tends to over-deliver.
- **"Keep up to date / check the news" on a recurring routine** means a frontier model + web
  search *every run* — fine occasionally, pricey as a habit.

A cheaper, sharper rewrite:

```
Audit our user↔AI token cost. Focus this run ONLY on the always-loaded CLAUDE.md
files. Output: a table of each file's token cost + 3 concrete cuts per file, ranked
by tokens saved. Use Sonnet unless you hit something that needs deeper reasoning.
~1 page. Skip web search unless a specific fact is missing.
```

That swaps "boil the ocean on Opus" for "one scoped pass on Sonnet" — and you run it once
per dimension instead of all at once. General prompting wins that apply to us:
**be specific, give one job, state the output format, name the model tier, and use XML
tags (`<context>`, `<instructions>`) — Claude 4.x follows literally and structures best
around tags, not prose.**

---

## 3. Suggested next actions (pick off cheaply)

1. Trim `localDNS/CLAUDE.md` and `DESIGN/CLAUDE.md` to ~1,500 tokens each (≈ −4k tok/turn). *(local model can do the first draft)*
2. One-line fix: repoint `cloud-overflow` off Opus to Sonnet/Haiku; add an explicit `cloud-reason-hard` = Opus alias.
3. Add `tools/check-style.py` (house-style linter) alongside `check-docs.py`; wire into CI.
4. Default Claude Code sessions to Sonnet; escalate to Opus by exception.
5. Audit the Odin fleet's per-agent backend; move the 15 workers to local/cheap, Odin to frontier.
6. Adopt the scoped-prompt template above for recurring routines; run one dimension per pass.

None of these need new hardware — items 1–4 and 6 are doc/config edits; item 5 is a config
check on infrastructure that already exists.

---

## 4. Sources (current as of 2026-06-27)

- Claude Code cost management — https://code.claude.com/docs/en/costs
- 7 ways to reduce Claude Code token usage (KDnuggets) — https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
- Token optimization 2026 guide — https://buildtolaunch.substack.com/p/claude-code-token-optimization
- Prompt caching (Claude Platform docs) — https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Prompt caching cost guide — https://www.respan.ai/articles/claude-prompt-caching
- Hybrid cloud-local LLM architecture (2026) — https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Run local models with Claude Code to cut cost (MindStudio) — https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- LLM model routing 2026 (DigitalApplied) — https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide
- Anthropic context management (context editing + memory tool) — https://anthropic.com/news/context-management
- Code with Claude 2026 — new agent features — https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features
- Claude Opus 4.8 pricing & 1M context — https://www.finout.io/blog/claude-opus-4.8-pricing-2026-everything-you-need-to-know
- Prompt engineering best practices 2026 — https://thomas-wiegold.com/blog/prompt-engineering-best-practices-2026/

---

## Changelog

- **2026-06-27** — Initial review created by NARF on founder request (token/process efficiency).
