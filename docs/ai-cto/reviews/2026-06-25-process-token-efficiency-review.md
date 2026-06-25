# NARF — review — 2026-06-25 — process & token efficiency

Scope: the **process** itself — how the founder and the AI (Claude / the API / the local
stack) work together — not the product. Question asked: where are we wasting tokens and
attention, and what's the better way? Web-researched against June 2026 best practice;
links at the bottom. This is a kept document, so every claim is either grounded in a file
in these repos or a dated source.

---

## TL;DR — the five highest-leverage moves

1. **Stop loading seven CLAUDE.md files into every session.** Cross-repo sessions inject
   all 7 briefings (~15–25k tokens) when one task touches one repo. Biggest single waste.
2. **Turn on prompt caching** for the static prefix (CLAUDE.md + tool defs). 60–90% off
   input tokens; pays for itself after one cache read. We are not using it.
3. **De-duplicate the house-style block.** The same ~290-word "ordering & typography"
   section is pasted verbatim into all 7 CLAUDE.md files. We pay for it 7× and edit it 7×.
4. **Route by task, not by habit.** We already run the hybrid stack (LiteLLM + the
   reasoning ladder on the t630). Extend it: cheap/background work → local or DeepSeek,
   frontier reasoning → Claude. Documented 50–99% savings on background tasks.
5. **Match the model to the job.** Routine doc edits, link checks, commit messages don't
   need Opus. Reserve Opus for architecture; default to Sonnet/Haiku otherwise.

Stacking caching + routing + model-match + output budgets is documented to bring typical
workloads to **20–30% of unoptimized cost** (≈70–80% savings). We have the infrastructure
for most of this already standing.

---

## A. Where the tokens actually go (our process, specifically)

**A1 — Context bloat from multi-repo briefings (P1).** Every session in this portfolio
loads the project CLAUDE.md. When a session spans the portfolio (as the AI-CTO/AI-CFO
reviews do), all seven are injected up front — and most of any single task touches one
repo. Each CLAUDE.md is large (the DESIGN one alone is ~5k tokens; localDNS similar). The
files even *call themselves* "the short briefing" while running to many screens.
*Fix:* keep CLAUDE.md to a true one-screen briefing and push the detail to README (read on
demand). Scope sessions/routines to the single repo they act on. Use Claude Code's
progressive-disclosure pattern — let the agent pull the deep file only when the task needs
it, instead of front-loading all of them.

**A2 — Verbatim duplication across repos (P2).** The "House style: ordering & typography"
block is identical in all 7 CLAUDE.md files, as is the three-repo table and the roles/money
table (3–4 copies each). Every multi-repo read pays for every copy, and a style change is a
7-file edit (drift risk — Azure-lab's copy already carries a slightly different note).
*Fix:* one canonical `HOUSE-STYLE.md` in DESIGN (the hub); each repo's CLAUDE.md links to
it in one line. Saves tokens on every load and removes the drift.

**A3 — No prompt caching (P1).** Cache writes cost 1.25× base input; cache reads cost
**0.1×**. For our shape — a big, stable CLAUDE.md/tool-def prefix followed by a small
changing task — caching is almost free money: break-even after a single read. We aren't
declaring cache breakpoints anywhere. *Caveat:* Anthropic cut the default cache TTL from
60→5 min in early 2026, so the win now requires *batching* related calls within the window
rather than spreading work across an idle hour. Note also (Feb 5 2026) caches are isolated
per workspace.

**A4 — Frontier model on routine work (P2).** This very review is running on Opus 4.8
(1M). Opus is right for the architecture call; it's overkill for "fix a link," "rewrite
this paragraph in the homeowner voice," or "write the commit message." Defaulting non-
reasoning work to Sonnet 4.6 / Haiku 4.5 is the single easiest per-task lever.

**A5 — Open-loop routines (P2).** Scheduled routines that run unattended (like the one
that produced this review) pay the full context cost on every fire. If a routine spans the
portfolio daily, the A1+A2 waste recurs daily. Scope each routine to exactly the repo and
files it needs, and let its notification — not a full re-read — carry the state.

---

## B. What we're already doing right (don't rebuild it)

- **The hybrid stack exists.** `10-ai-orchestration` on the t630 runs LiteLLM (port 4040)
  with a documented reasoning ladder: `local-reason` (deepseek-r1:1.5b on t630 CPU, cool)
  for light work, `cloud-gpu-reason` (full R1 on a rented GPU via Tailscale, on demand) for
  heavy work, `cloud-overflow` fallback. This is exactly the "route by complexity" pattern
  the 2026 hybrid guides recommend — we built it before asking the question.
- **A privacy-aware dispatcher** already tags tasks `sensitive` and is *meant* to keep them
  local. (See the open gap below — it doesn't fail closed yet.)
- **Doc-integrity gate** (`tools/check-docs.py` in CI) keeps link-rot from compounding —
  cheap, deterministic, no tokens.

So the recommendation is **extend the router we have**, not adopt a new tool. A Claude Code
Router-style layer (route Claude Code's own background/sub-agent calls to local Ollama or
DeepSeek, keep the main thread on Claude) is the natural next step and reuses LiteLLM.

⚠️ **Carry-over risk that bites the hybrid plan: TD-14.** Today a `sensitive`-tagged task
can fail over from `local-reason` to `cloud-overflow` (Claude cloud) because the local-only
chain isn't enforced at the LiteLLM failover layer. Any "send more to local" push must fix
TD-14 first, or we'll quietly route private lookups to the cloud while believing they're
local. Privacy and cost are the same fix here.

---

## C. Better prompting (fewer round-trips = fewer tokens)

Per Anthropic's 2026 prompting guidance, a well-structured prompt lands in one shot instead
of 3–4 clarifying exchanges — documented 30–50% token reduction:

- **Contract-style asks.** State role + task + context + output format + constraints, and
  define what "done" looks like, up front. Our reviews already trend this way; our *ad-hoc*
  asks don't.
- **Specify output length and shape.** "A ranked list of ≤5 items, ≤2 sentences each" stops
  the model from writing an essay you have to skim.
- **Constraints field = what to exclude.** Cheaper to say "don't touch the public repo" than
  to undo it.
- **Don't context-dump without priority flags.** Point at the 2 files that matter rather
  than pasting six.
- **Batch, then `/clear`.** Group related work to stay inside the cache window; clear stale
  context between unrelated tasks instead of dragging it forward.

### On *this* request's prompt (you asked)

The triggering prompt was, paraphrased: *"Find inefficiencies in our process… is there a
better way… better prompting… leverage other AI… hybrid local + Claude… ANYTHING… search
the web, check the news, keep up to date. Thanks!"* Honest read:

- **Strength:** it set a clear *goal* and explicitly authorized web research — good, that's
  what made this report groundable.
- **Cost:** "ANYTHING that could help" is unbounded, so the agent explores widely and
  expensively. Open scope is the most expensive instruction you can give.
- **Tighter version:** *"Audit our Claude usage for token waste. Output: a ranked ≤7-item
  list, each with the fix and a rough $/token impact, grounded in our repos + 2026 sources.
  Skip anything already in tech-debt. ≤600 words."* Same intent, a fraction of the spend,
  and a sharper deliverable.
- **Cadence:** a one-time audit like this is worth Opus; if it becomes a *recurring* routine,
  pin it to Sonnet and scope it to this one repo.

---

## D. New 2026 capabilities worth adopting

- **Context editing / the memory tool** (4.x) — auto-prunes stale tool results from the
  window so long agent runs stop dragging dead weight. Directly attacks A1/A5.
- **The `effort` parameter** — trade capability for speed/cost per call. Set it low for
  mechanical edits, high only for the hard reasoning step.
- **Agent Skills** — package a repeatable workflow once and invoke it cheaply. Our monthly
  Statement build (`make statement …`) is a textbook Skill candidate; so is "add a customer."
- **Dynamic Workflows** (Opus 4.8 preview) — orchestrate many parallel sub-agents for
  genuinely parallel jobs (e.g. a cross-repo audit). Use deliberately; it multiplies spend.
- **Managed Agents / scheduled runs** — we're already using this (this review). Keep them
  narrowly scoped.

---

## E. Recommended order of work (cheapest, highest-leverage first)

1. **Enable prompt caching** on the stable prefix in the LiteLLM path and any direct API
   use. (Config change. Biggest $/effort.)
2. **Extract `HOUSE-STYLE.md`**, slim each CLAUDE.md to one screen, link out for detail.
   (Pure docs edit; shrinks every future load.)
3. **Set model defaults by task** — Sonnet/Haiku default, Opus on request — and **fix TD-14**
   so the local-only chain fails closed, *then* push more background work to local/DeepSeek.
4. **Scope routines** to their single repo + files; let the notification carry state.
5. **Adopt the contract-style prompt template** above for ad-hoc asks; wrap the Statement
   build as an Agent Skill.

None of 1–2 touch the product or the live box; they're config + docs and reversible. Item 3
is gated on TD-14 for the privacy half.

---

## Sources (June 2026)

- [Anthropic — Prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Manage costs (Claude Code)](https://code.claude.com/docs/en/costs)
- [Anthropic — LLM gateway configuration](https://code.claude.com/docs/en/llm-gateway)
- [Anthropic — Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [DevToolLab — Prompt caching cuts LLM costs up to 90% (2026)](https://devtoollab.com/blog/prompt-caching-guide)
- [DEV — Claude prompt caching: the 5-minute TTL change (2026)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [KDnuggets — 7 ways to reduce Claude Code token usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Composio — 9 ways to cut Claude Code token consumption](https://composio.dev/content/ways-to-cut-token-consumption-in-claude-code)
- [DataCamp — Claude Code Router: multi-model routing](https://www.datacamp.com/tutorial/claude-code-router)
- [MindStudio — Run local AI models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [SitePoint — Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [MindStudio — Code with Claude 2026: new agent features](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [AI Magicx — Prompt caching: cut your API bill 60%](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
