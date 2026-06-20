# Process efficiency review — user ↔ AI token use (2026-06-20)

A scheduled routine looked at *how we work with Claude*, not what we build, and asked one
question: where are we spending tokens (and money) we don't need to? Findings are ranked by
payoff. The headline: most of our waste isn't in the conversation — it's in the **fixed
prefix** every session reloads, and in **running everything on the top model**.

> Self-check: this document is deliberately short. An efficiency report that's 4,000 words
> long is its own counter-example.

---

## TL;DR — the five levers, biggest first

1. **Stop running routines on Opus.** Model tier is the single biggest cost lever. A
   70/20/10 Haiku/Sonnet/Opus split cuts typical spend by >50% vs. all-Opus. This routine
   ran on Opus 4.8 ($5/$25 per M tokens) to read files and search the web — Sonnet 4.6
   ($3/$15) or Haiku 4.5 ($1/$5) would do it.
2. **Slim the CLAUDE.md files.** Our seven briefings total ~58 KB (~15 K tokens) and the
   project-context layer reloads on every session start, `/clear`, and `/compact`. The two
   big ones — `localDNS` (20 KB) and `DESIGN` (18 KB) — carry README-grade detail that
   belongs in README, not in the always-loaded prefix.
3. **Scope routines to one repo.** A cross-repo routine loads *all seven* CLAUDE.md files
   into a fresh (cold-cache) container every run, so it pays the full write cost of the
   whole prefix each time. A routine that only needs `localDNS` should only mount `localDNS`.
4. **Use the local LLM we already own.** The t630 runs a LiteLLM router + Ollama reasoning
   ladder (`10-ai-orchestration`). Route triage/classification/simple generation there and
   escalate only hard reasoning to Claude. Published hybrid splits report 60–80% savings.
5. **Cache hygiene inside a session.** Pick model + effort at the *start*; don't switch
   mid-task. Each model switch, effort change, fast-mode toggle, or MCP connect/disconnect
   is a full cache miss that reprocesses the entire history.

---

## A. Where the tokens actually go

Each turn re-sends the whole context; the API caches by matching the **prefix** (the part
that didn't change). Claude Code orders it so the stable stuff comes first:

| Layer | Content | Reprocessed when |
| ----- | ------- | ---------------- |
| System prompt | core instructions, tool defs, output style | tool set changes, CC upgrade |
| Project context | **CLAUDE.md**, memory, rules | session start, `/clear`, `/compact` |
| Conversation | messages, tool results | every turn |

Within a warm session, cache reads cost ~10% of normal input — so a long chat is cheap. Our
waste is elsewhere:

- **Cold starts.** A scheduled routine spins a fresh container → no warm prefix → it pays
  the **full write cost** of system prompt + every loaded CLAUDE.md, *every run*. Caching
  helps within a session, not across cold starts. So the fixed prefix size is what a routine
  pays for, repeatedly. Levers #2 and #3 attack exactly this.
- **Top-model default.** Reading files and running web searches does not need Opus-grade
  reasoning. Lever #1.

## B. CLAUDE.md diet (lever #2, detail)

Best practice: CLAUDE.md is the *briefing*, loaded every session — keep it lean and link out;
READMEs and context files are read on demand. Ours have drifted into full references.

| Repo | CLAUDE.md size | Note |
| ---- | -------------- | ---- |
| `localDNS` | 20 KB | full deploy-path table, every known issue — README material |
| `DESIGN` | 18 KB | funnel diagram, stage map, full ADR pointers |
| `MARKETING` | 11 KB | model + roadmap in full |
| `customers` | 4 KB | about right |
| `claude-code-homelab` | 3 KB | fine |
| `Azure-lab` | 2 KB | fine (stub) |

Target the two big ones: keep the "read this first" essentials + the house-style block, move
the exhaustive tables (deploy paths, full known-issues) to README and reference them. Goal
~6–8 KB each. That's ~8 K tokens shaved off the prefix every cold routine run pays for.

## C. Hybrid local + Claude (lever #4, detail)

We already built the gateway — we just don't route through it for the cheap stuff. Pattern:

- **Local (t630 Ollama / `local-reason`):** "does this even need Claude?" triage, log
  scanning, classification, boilerplate. Free, private, and the box is already on.
- **Haiku 4.5:** classification + simple generation at API tier.
- **Sonnet 4.6:** the default for real work.
- **Opus 4.8:** reserved for genuinely hard reasoning.

For our routines specifically: a local pre-filter that decides whether a run has anything
worth escalating would avoid spinning a Claude session at all on quiet days.

## D. Cache hygiene cheat-sheet (lever #5, detail)

- Set model + **effort** once, at session start. Each mid-session switch = full re-read.
- `/compact` only at natural task breaks; `/recap` to resume without replaying history;
  `/rewind` (not `/compact`) to abandon a path — it truncates to an already-cached prefix.
- Don't toggle MCP servers, plugins-with-MCP, fast mode, or whole-tool deny rules mid-task.
- Watch `cache_read_input_tokens` vs `cache_creation_input_tokens` in the statusline. High
  *creation* turn after turn = something is invalidating the prefix.
- Subscription plans already request the 1-hour cache TTL automatically — no action needed.

## E. On the prompt that triggered this review

The asking prompt was, honestly, an example of the inefficiency it asked about. It was
maximal and open-ended — "ANYTHING that could help… anything you could possibly think of…
search the web… check the news… keep UP TO DATE." Open scope makes the model fan out
broadly and burn tokens on breadth instead of the answer. It also bundled several distinct
asks (token use, prompting, hybrid local, news monitoring) into one turn.

Better shape — scope it, structure it, bound it, and recognize the recurring ones as
*routines*, not one-shot mega-prompts:

> *"Review our Claude Code token use. Give me the top 5 cost levers ranked by payoff, each
> with a concrete fix and rough savings. Focus on our setup (7 repos, scheduled routines).
> One page. Cite sources."*

And "keep up to date, this changes day by day" is a standing need → a **weekly low-cost
routine on Sonnet/Haiku** that diffs Anthropic's release notes and pings only on changes,
not a recurring open-ended Opus session.

---

## Sources

- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [How to Reduce Claude Code Token Usage: 8 Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Updates, June 2026 — Releasebot](https://releasebot.io/updates/anthropic/claude-code)

*Model-tier note: Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5 per M tokens (in/out), 2026-06.*
