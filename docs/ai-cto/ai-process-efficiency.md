# AI Process Efficiency — token & workflow review

*First pass: 2026-06-14. Newest findings at the top per house style. This reviews the
**process between the human and the AI** across the A777ance repos: where tokens (and money)
leak, where prompting can be tighter, and where the existing local-LLM router should carry
load instead of the Claude API.*

Findings are ranked by estimated payoff (roughly $/effort). Each is something we control.

---

## The one-paragraph answer

The single biggest, cheapest win is **CLAUDE.md hygiene**: the same 38-line "House style"
block is copy-pasted verbatim into all six CLAUDE.md files, and a multi-repo session loads
~14.6K tokens of CLAUDE.md *before any work starts*. Factor the shared text out, trim each
file to what's needed every session, and scope each session/routine to the repos it actually
touches. After that, the next tier is **using the hybrid router we already built** (stage 10)
for bulk/mechanical work instead of paying Opus rates for it, and **protecting the prompt
cache** (don't model-switch mid-session; mind the 5-minute TTL; lazy-load MCP tools).

---

## Tier 1 — measured, do these first

### F-1. CLAUDE.md is duplicated and over-long (≈14.6K tokens/session)

Measured today:

| File | Bytes | ~Tokens |
| ---- | ----- | ------- |
| localDNS | 20,472 | ~5,100 |
| DESIGN (this repo) | 17,987 | ~4,500 |
| MARKETING | 10,660 | ~2,700 |
| customers | 4,135 | ~1,000 |
| claude-code-homelab | 2,896 | ~700 |
| Azure-lab | 2,294 | ~570 |
| **Total** | **58,444** | **~14,600** |

The **"House style: ordering & typography"** block (38 lines, ~1.1 KB) is **identical in all
six files** — ~6.6 KB of pure duplication, plus repeated "three repos / two-sided guild"
tables and "AI CTO state" pointers. Every token in CLAUDE.md is loaded on *every* session and
can't be reused for the actual work, and it sits in the cached prefix, so any edit to it
invalidates the cache (see F-4).

**Fix:**
- Move the house-style rules into a single canonical doc (e.g. `docs/house-style.md` in this
  hub) and replace the six copies with a one-line pointer: *"House style: see
  DESIGN…/docs/house-style.md — newest-first, Z→A, reversed blocks, Gill Sans MT."* One source
  of truth (the repos' own stated principle) — no more 6-way drift.
- Trim each CLAUDE.md to the "never-forget, every-session" minimum; push the rest (build
  recipes, schema details, stage walkthroughs) into linked files or **Skills** that load on
  demand (F-6).
- Realistic saving: ~6–9K tokens off the always-loaded prefix, repeated every session.

*Caveat:* in a normal single-repo Claude Code session only that repo's CLAUDE.md loads, so the
cross-repo duplication only bites in multi-repo/routine sessions (like this one). The per-file
bloat (localDNS and DESIGN are both 18–20 KB) is real either way.

### F-2. Scope each session/routine to the repos it touches

This very review session loaded all six CLAUDE.md files (~14.6K tokens) **and** the full
GitHub MCP toolset for a task that only needed this repo. A scheduled routine that boots the
whole portfolio every run pays that tax on every fire.

**Fix:** point each routine/session at the minimum repo set. The harness already lazy-loads
MCP tool schemas (the `ToolSearch` deferral) — good — but the *list* of ~60 GitHub tools and
every connected MCP server still inflates the cached prefix. Disable MCP servers a routine
doesn't use.

### F-3. Reconsider (or at least de-duplicate) the unusual ordering conventions

Reverse-chronological logs are normal, but **Z→A alphabetical lists** and **reversed
walkthrough blocks** fight every model's defaults (forward, A→Z). The cost is recurring: on
each edit the model must re-read and re-apply the rule, and there's a real chance of a
correction round-trip (model writes A→Z, gets corrected, rewrites) — paid in tokens every
time. If the conventions earn their keep, fine; but state them **once** (F-1) and consider
whether "reverse the blocks, never renumber" is worth the per-edit friction versus a plain
forward guide.

---

## Tier 2 — protect the prompt cache (current as of June 2026)

Cache reads bill at ~10% of input rate (a ~90% discount), so a healthy cache is most of the
savings on long sessions. Things that *silently* throw it away:

### F-4. Cache pitfalls that apply to us
- **Model switching is the most expensive change** — the cache is isolated per model. Building
  context in Opus then `/model`-ing to Sonnet/Haiku discards the whole cache. Pick the model at
  session start and stay on it.
- **`--resume` / `--continue` currently breaks the cache every turn** (open Claude Code bug
  #43657) — content that should be a cache hit gets re-created, multiplying usage. If we rely
  on resume for long-running work, watch the bill.
- **TTL dropped from 1h to 5 min** for many requests (Anthropic tweaked defaults in spring
  2026, amid cache bugs that drained quotas). Gaps between turns lose the cache — **batch
  work**, don't leave a session idle then return.
- **Tool/MCP changes invalidate the prefix.** Adding/removing an MCP server or changing tool
  definitions busts the cache for the rest of the turn. Keep the toolset stable within a
  session.

---

## Tier 3 — leverage the hybrid local-LLM router we already own

We **already built the right architecture** — the LiteLLM router on the t630 (localDNS stage
10) with a reasoning ladder: `local-reason` (deepseek-r1:1.5b, t630 CPU, cool),
`cloud-gpu-reason` (full R1 on a rented GPU), `cloud-overflow` (Claude). Industry reports put
hybrid local/cloud routing at **60–80% cost reduction** because 60–70% of real tasks
(classification, extraction, formatting, drafting) don't need a frontier model. We're paying
Opus rates for some of that.

### F-5. Actually route bulk/mechanical work local
Good candidates to push to the local/cheap tier (or to Claude **Haiku** instead of Opus):
- doc link-checking (`tools/check-docs.py` is deterministic — doesn't need an LLM at all),
- commit-message and changelog drafting,
- roster/CRM data entry and field validation,
- first-draft summaries and "Handled For You" log entries,
- classification/triage of leads.

Reserve Opus/Sonnet for cross-repo reasoning, architecture, and anything touching real
customer judgment. **This routine ran on Opus 4.8** — overkill for a link-and-duplication scan.

**Blocker to clear first:** our own **TD-14** — `local-reason` has a cloud fallback, so a
`sensitive`-tagged task can fail over to `cloud-overflow` (Claude cloud) if the local model is
down. Fix that (fail closed, local-only chain) **before** routing real customer data locally,
or the privacy win is illusory.

### F-6. Move always-on guidance into Skills and subagents
- **Skills** load on demand instead of sitting in every-session context — move "build a
  statement", schema details, and house-style specifics into Skills. Cuts the always-loaded
  prefix (compounds with F-1).
- **Subagents** keep verbose search/log output in an isolated context; only the summary returns
  to the main thread (reported 40–70% savings on focused tasks). Use them for fan-out research
  and reviews — but not for trivial one-shot shell/git ops, where the startup overhead isn't
  worth it.

---

## On the prompt that triggered this review

The triggering prompt was effective at *intent* but expensive by design: open-ended ("Anything
you could possibly think of… ANYTHING that could help"), no scope boundary, no output format,
no budget. That invites broad, possibly redundant work and unbounded token spend. The all-caps
emphasis adds little signal the model acts on.

A tighter version costs less and lands closer:

> "Review our human↔AI workflow for token waste. Scope: the 6 A777ance repos' CLAUDE.md and
> our model-routing setup. Output: top 5 fixes ranked by estimated $ saved, each with a
> concrete change. Skip anything needing more than a half-day to implement. ≤800 words."

Pattern to reuse: **goal → scope → output format → constraints/budget → success criterion.**
Stable context first (it caches), the variable ask last.

---

## Current news worth tracking (June 2026)
- Anthropic cache bugs (Mar–Apr 2026) drained quotas ~20× for some users; defaults were tweaked
  and TTL shortened to 5 min — keep an eye on usage dashboards after any Claude Code update.
- "Context engineering" (compaction, context collapse, micro-compaction) is now the named
  discipline; newer Claude Code protects context automatically, but our CLAUDE.md hygiene still
  governs the always-loaded floor.

## Sources
- [How to Reduce Claude Code Token Usage (Agensi)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token-Saving Guide — cache/MCP/CLAUDE.md/Skills (knightli.com)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Resume/continue cache invalidation bug #43657](https://github.com/anthropics/claude-code/issues/43657)
- [Claude Code cache confusion as Anthropic tweaks defaults (DevClass)](https://www.devclass.com/ai-ml/2026/04/14/claude-code-cache-confusion-as-anthropic-tweaks-defaults-but-quotas-still-drain/5216975)
- [Anthropic investigating cache bugs draining tokens (PiunikaWeb)](https://piunikaweb.com/2026/03/31/claude-cache-bugs-tokens-20x-more-anthropic-investigating/)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM smart routing pricing (Markaicode)](https://markaicode.com/pricing/litellm-pricing-gateway-comparison/)
- [Best practices for Claude Code (docs)](https://code.claude.com/docs/en/best-practices)
- [Effective context engineering for AI agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
