# Process efficiency review — human ↔ AI workflow (2026-06-19)

A routine review of how we work *with* Claude across the A777ance repos: where tokens
leak, where prompting can be tighter, and where a local model should carry the load.
Findings are ordered by payoff (biggest first). Quantities are measured from this repo set
on the date above.

> Self-note: this review is itself a process. See §7 — don't run it daily, and diff against
> this file next time instead of regenerating from scratch.

---

## TL;DR — the five that matter

1. **Every session pays ~29K tokens of fixed overhead before doing any work.** ~14.6K from
   auto-loaded CLAUDE.md files + ~14K from the NARF/ZORT "read these 10 files at session
   start" mandate. Fix the mandate and the CLAUDE.md bloat and you cut the per-session floor
   by more than half. **Biggest single lever.**
2. **The house-style block is copy-pasted verbatim into all 6 CLAUDE.md files** (~2,100
   tokens of pure duplication, re-paid on every multi-repo session). One source, link the rest.
3. **Deterministic work is being framed as AI work.** `tools/check-docs.py` already verifies
   links — never spend a model turn "checking that links resolve." Same for schema validation
   and reverse-chronological ordering.
4. **The hybrid local/cloud LLM you want already exists** — the LiteLLM reasoning ladder on
   the t630 (`10-ai-orchestration`). It's pointed at the *product's* AI features, not at *our
   own* dev/ops chores. Point routine doc chores at `local-reason`; reserve Claude for judgement.
5. **Prompt caching is free money you're probably leaving on the table.** Stable CLAUDE.md +
   mandated context = a perfect cache prefix (~90% cheaper on reads, 1-hour TTL available since
   Jan 2026). But editing CLAUDE.md mid-session cold-starts it — see §3.

---

## 1. The per-session fixed cost (the big one)

Measured on 2026-06-19:

| Source | Bytes | ≈ Tokens | Loaded when |
| --- | --- | --- | --- |
| 6 × CLAUDE.md (all repos in scope) | 58,444 | ~14,600 | **Every** session, automatically |
| NARF reads (portfolio, roadmap, tech-debt, decisions) | 22,183 | ~5,500 | Every DESIGN session, if honored |
| ZORT reads (5 CFO files) | 34,949 | ~8,700 | Every DESIGN session, if honored |
| **Floor before any task** | | **~28,800** | |

At Opus 4.8 input pricing ($5/M, standard), that's ~$0.14 of *input* burned per session before
the first useful token — and it's re-paid on every uncached session. Over hundreds of routine
sessions a month it's real money, and worse, it crowds the context window the model actually
needs for the task.

**The root cause is the "read these files at session start" mandate**, repeated in DESIGN
(NARF + ZORT), localDNS, customers, and MARKETING. It treats Claude like a person clocking in
who must re-read the whole binder. But most sessions touch one stage and need one or two of
those files, not ten.

**Fixes (in order):**

- **Make session-start reads lazy, not eager.** Change the CLAUDE.md instruction from "read
  these N files now" to "*these files exist; read the one relevant to the task.*" Keep a
  one-paragraph **state digest** at the top of `portfolio.md` so a session can get oriented
  from ~200 tokens instead of 9 KB, and only open the full file when it's actually editing
  portfolio state.
- **Trim CLAUDE.md to a true briefing.** localDNS (20 KB) and DESIGN (18 KB) have grown into
  mini-handbooks — full prose tables, rationale, deploy-path matrices. CLAUDE.md should be the
  *index and the rules*; the encyclopedic content belongs in README/network-context (read on
  demand). Target: under ~6 KB each. The deploy-path table and the nftables checklist in
  localDNS, for instance, are reference material that a deploy session can open when deploying —
  not something every session needs resident.
- **Don't auto-load repos you aren't touching.** A localDNS-only session shouldn't carry the
  customers/MARKETING/Azure-lab CLAUDE.md. Scope the session to the repo(s) in play.

## 2. Stop duplicating the house style

The full "House style: ordering & typography" block (reverse-chronological, Z→A,
reverse-the-blocks, Gill Sans MT) is pasted **identically into all 6 CLAUDE.md files**. That's
~1.4 KB × 6 ≈ 8.4 KB on disk and ~2,100 tokens re-paid every time more than one repo is in
scope.

- Put it once in a canonical location (the DESIGN repo, since it's the portfolio hub) and have
  the other five CLAUDE.md files carry a one-line pointer: *"House style: see DESIGN
  `CLAUDE.md` §House style — reverse-chron, Z→A, Gill Sans MT."* The pointer is enough for
  Claude to apply the rule; the full rationale only needs to live once.

**Separately — the "reverse the blocks, keep the steps, never renumber" convention is a
process-cost generator.** It's genuinely counterintuitive (present blocks last-first but
number them forward and never renumber), which means the model gets it wrong, a human catches
it, and a correction round-trip burns tokens on both sides. If this convention isn't earning
its keep in real readability gains, retiring it would remove a recurring source of rework.
That's a human decision, flagged here.

## 3. Use prompt caching deliberately

CLAUDE.md + the mandated context files are the ideal cache prefix: large, stable, and re-sent
every turn. Cache reads run ~10% of normal input price, and since Jan 2026 the TTL can be set
to 1 hour (not just 5 min) on Opus/Sonnet/Haiku 4.5+. Rule of thumb: 3+ reads in a 5-min window,
5+ in a 1-hour window, and it pays for the write.

The catch is the one in our own notes: *"treat CLAUDE.md like a config file you only touch
between sessions."* We violate this constantly — these repos *are* mostly doc edits, and many
sessions edit CLAUDE.md or the mandated files, which cold-starts the cache. **Implication:**
keep the volatile working docs (portfolio state, logs) *out* of the cached prefix, and keep the
cached prefix (CLAUDE.md rules) genuinely stable. The §1 trim helps here too — a smaller, more
stable prefix caches better.

## 4. Don't spend model turns on deterministic work

- **Link/anchor integrity:** `python3 tools/check-docs.py` already does this and gates CI. The
  rule should be "run the script," never "Claude, confirm the links resolve."
- **Schema conformance:** `08-client-list-and-crm/schema.md` defines roster fields. A tiny
  validator (jsonschema) catches drift for ~0 tokens; don't eyeball-validate roster.json in chat.
- **Ordering rules (reverse-chron, Z→A):** these are mechanical and lintable. A pre-commit hook
  or small script enforces them more reliably and far more cheaply than asking the model to
  re-sort by hand each time.

General principle: **anything with a single correct answer that a script can check, a script
should check.** Reserve the model for judgement, prose, and synthesis.

## 5. Run the hybrid you already built

`localDNS/10-ai-orchestration` already stands up exactly the architecture the 2026 hybrid
playbooks recommend: LiteLLM as the gateway, a reasoning ladder (`local-reason` =
deepseek-r1:1.5b on the t630 for light work, `cloud-gpu-reason` for heavy, `cloud-overflow`
fallback). The published guidance: 60–70% of real workloads are simple (classify/extract/format)
and run fine locally; only ~10% need a frontier model — hybrid setups report 60–90% cost
reduction at the same quality ceiling.

Today that ladder serves the *product's* AI features. The unused opportunity is pointing **our
own ops chores** at it:

- Local model (free, private, already running): first-pass link/format/ordering checks, draft
  commit messages, summarizing a stats JSON, extracting fields, "does this paragraph match
  house voice" pre-screens, routine roster diffs.
- Claude API: architecture decisions, ADR/FIN authoring, anything customer-facing or money-
  facing, cross-repo synthesis, this kind of review.

A bonus that fits our own honesty/privacy rules: routing the routine, data-touching chores to
the box keeps real customer data (the `customers` repo) on local inference instead of an API.

## 6. The prompt that triggered this review — critique

The triggering prompt was, condensed: *"Locate inefficiencies in our process… reduce token
use… better prompting… leverage other AI… hybrid local LLM and Claude… ANYTHING… search the
web… keep up to date… check the news… and critique this prompt too."*

It's a *good* intent but an *expensive* shape, and it models several of the anti-patterns it's
asking about:

- **Unbounded scope ("ANYTHING that could help").** Open-ended invitations make the agent fan
  out maximally — many web searches, broad exploration, a long answer — because nothing tells
  it when to stop. A scoped prompt is cheaper *and* sharper.
- **Multiple unrelated asks in one turn** (token use + prompting + hybrid LLM + news + self-
  critique). Each pulls research in a different direction; bundled, they all run at full depth.
- **No target output or budget.** "Let me know" doesn't say report vs. patch, long vs. short,
  or "stop after the top 5." The agent guesses, usually long.
- **Standing instructions belong in config, not the prompt.** "Keep up to date, check the news,
  search the web" re-issued each time is what a scheduled routine + a saved slash command are
  for — say it once, not every run.

A tighter version of the same request:

> *"Review our human↔AI process for token waste. Give me the top 5 fixes ranked by payoff,
> each with the concrete change to make. Use the repo configs as evidence; one or two web
> searches max for 2026 best practices. Output: a short ranked list, not an essay. Stop at 5."*

That keeps the value, removes the fan-out, names the output, and sets a stop condition.

## 7. This review is itself a recurring cost — cadence it

Re-running a full web-search + whole-repo analysis on a tight schedule would repeat most of this
work for little new signal. Recommended:

- **Cadence: monthly, not daily.** The best-practice landscape and model lineup move on the
  order of weeks (Opus 4.8 landed 2026-05-28), not hours.
- **Diff, don't regenerate.** Next run, read *this* file first and report only what changed —
  new model/pricing, a fix landed, a new leak — instead of re-deriving the baseline.
- **Notify only on signal.** If nothing material changed, the run should end quietly. A "ran,
  all good" ping is its own small waste of attention.

---

## Appendix — current facts grounding this review (as of 2026-06-19)

- **Model:** Claude Opus 4.8, released 2026-05-28; same price as 4.7 ($5/M in, $25/M out).
  Adds a "dynamic workflow" tool (run multiple subagents at once) and an **effort control**
  ("how much effort Claude puts into a response") — use low effort for routine doc chores,
  high only for hard synthesis. Fast mode is ~2.5× faster / 3× cheaper than prior fast mode.
- **Prompt caching:** ~90% cheaper cache reads; 1-hour TTL option since 2026-01-26 on
  Opus/Sonnet/Haiku 4.5+; cache hits require byte-identical prefixes.
- **Subagent fan-out** is now a *named* top cause of runaway cost (one task spawning 20+ agents),
  alongside autocompact cascades, MCP-server context bloat (18K+ tokens/turn/server), and
  retry resubmission loops. Delegate heavy reads to subagents (their verbose output stays out of
  the parent context) — but cap the fan-out.
- **Hybrid local/cloud:** documented 60–90% cost reduction at equal quality when ~60–70% of
  simple tasks run locally and only the hard ~10% hit a frontier model.

### Sources
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Claude Code Token Optimization (2026 Guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Subagents: A 2026 Practical Guide — Tembo](https://www.tembo.io/blog/claude-code-subagents)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [CLAUDE.md Best Practices — Arize](https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/)
- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Anthropic releases Opus 4.8 with dynamic workflow tool — TechCrunch](https://techcrunch.com/2026/05/28/anthropic-releases-opus-4-8-with-new-dynamic-workflow-tool/)
