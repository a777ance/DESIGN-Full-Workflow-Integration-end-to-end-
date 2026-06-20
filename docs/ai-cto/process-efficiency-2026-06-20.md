# Human↔AI Process Efficiency Review — 2026-06-20

A look at how we (founder ↔ Claude) actually work, where tokens leak, and what to
change. Scoped to the *process*, not the product. Findings are ordered by
estimated payback (biggest first); the to-do list at the bottom is the action.

> Why this matters: token cost is mostly **fixed overhead paid every session** —
> the prompt prefix loaded before any real work starts. Cutting that prefix pays
> on every turn of every session, forever. Most of our waste is here, not in the
> work itself.

---

## TL;DR — the five moves that matter

1. **Scope each session to ONE repo.** Running from `/home/user` loads all 6
   `CLAUDE.md` files (~58 KB ≈ **15 K tokens**) before a word is typed. A
   single-repo session loads one. ~**80% baseline cut** for free.
2. **De-duplicate the `CLAUDE.md` files.** The house-style block (~1.2 KB) is
   copy-pasted into all 6 files; the roles/money-flow diagram and the
   three-repo table are pasted into 2–3. Factor shared text into one referenced
   file; trim each `CLAUDE.md` to a lean index that points at detail loaded
   on demand.
3. **Route cheap work to the local LLM we already run.** The t630 LiteLLM router
   (deepseek-r1 ladder, cloud-gpu-reason) is built for exactly this. ~60–70% of
   routine work (classify a lead, extract fields, draft a "Handled For You" line,
   summarize a log) is local-model quality. Reserve Claude for reasoning/code.
4. **Lean on prompt caching for the API path.** Anything we drive through the
   Agent SDK / router should mark the stable `CLAUDE.md` prefix cacheable —
   ~90% off the prefix on a cache hit. Keep timestamps and per-household facts
   *out* of the cached prefix.
5. **Write tighter prompts.** Scoped, with an explicit deliverable + output
   shape + a "don't over-explore" budget. (The prompt that triggered this
   review is the cautionary example — see the last section.)

Published guidance puts the combined effect at **40–70% lower token cost** with
no quality loss; our duplicated/over-broad baseline means we're at the high end
of that opportunity.

---

## Findings, by payback

### 1. The session-scope tax (biggest, and free to fix)
The harness loads `CLAUDE.md` from the working directory's tree. Our working dir
is `/home/user`, which holds all 7 repos, so **6 `CLAUDE.md` files load every
session** regardless of what we're working on:

| Repo | CLAUDE.md size |
| ---- | -------------- |
| localDNS | 20.5 KB |
| DESIGN (this) | 18.0 KB |
| MARKETING | 10.7 KB |
| customers | 4.1 KB |
| claude-code-homelab | 2.9 KB |
| Azure-lab | 2.3 KB |
| **Total loaded every session** | **~58 KB ≈ 15 K tokens** |

- **Fix:** start sessions/routines with the working directory set to the *one*
  repo in play (e.g. `localDNS/`), not `/home/user`. For routines, set the
  environment's repo scope to the single target repo.
- **Payback:** a localDNS-only session drops the prefix from ~15 K to ~5 K
  tokens; a customers-only session to ~1 K. Paid back on every turn.

### 2. Duplicated text across the briefings
- The **"House style: ordering & typography"** block is verbatim in **all 6**
  `CLAUDE.md` files (~1.2 KB each → ~7 KB of pure duplication).
- The **roles & money-flow** diagram lives in both DESIGN and MARKETING.
- The **three-repos table** lives in localDNS, MARKETING, and DESIGN.
- **Fix:** keep the canonical house-style + portfolio map in ONE place (this
  repo, the hub), and have the other `CLAUDE.md` files link to it in a single
  line instead of pasting it. Trim each `CLAUDE.md` to a lean index — the rule
  of thumb in current guidance is that a `CLAUDE.md` is a *table of contents*,
  not the manual; detail goes in referenced files loaded on demand.
- **Payback:** combines with #1 — a leaner per-repo file means even the
  single-repo baseline shrinks, and edits to house style stop needing 6 commits.

### 3. We already own the hybrid setup — use it
`localDNS/10-ai-orchestration` runs LiteLLM (port 4040) with a reasoning ladder:
`local-reason` (deepseek-r1:1.5b on the t630), `cloud-gpu-reason` (full R1 on a
rented GPU via Tailscale), `cloud-overflow`. This is *exactly* the routing layer
the 2026 hybrid-architecture guides describe — we just aren't pointing routine
work at it.
- **Route to local:** lead classification, field extraction from a booking form,
  first-draft "Handled For You" lines, log/stat summarization, the nightly
  AI-CTO/CFO status digest, commit-message drafts.
- **Keep on Claude:** multi-file code changes, architecture/ADR reasoning,
  anything touching the honesty rule on a kept document, security-sensitive edits.
- **Bonus — privacy:** customer data (the `customers` repo is private) summarized
  locally never leaves the box. That aligns with the repo's own privacy rule.
- **Payback:** published numbers are 60–80% off the work that's safe to offload;
  ~60–70% of routine turns qualify.

### 4. Prompt caching on the API/SDK path
For anything driven via the Agent SDK / GitHub Actions / the router rather than
interactive Claude Code:
- Mark the stable prefix (briefing + house style) **cacheable** → ~90% off the
  prefix on a hit.
- **Anti-patterns to avoid** (these silently bust the cache): a live timestamp
  in the prefix (truncate to the day or move it to the user turn); per-household
  names/figures in the cached system block (put them in the user message);
  whitespace churn in a prompt builder. Note: interactive Claude Code already
  caches automatically — this is specifically for our own SDK/automation paths.

### 5. Structural habits (low effort, compounding)
- **Subagents for fan-out research** (like this review): the subagent reads
  widely in its own context and returns only the summary, keeping the main
  session lean. Caveat from 2026 testing: *don't* spawn a subagent for trivial
  one-shot shell/git work — the prompt+tool-def overhead costs more than it saves.
- **`/clear` between unrelated tasks** so stale file dumps stop riding along on
  every subsequent turn.
- **`.claudeignore`** to keep build output, vendored data, and rendered
  statements out of proactive context (reported ~85% context reduction from this
  alone on noisy repos).
- **Batch related asks in one session** rather than reopening cold — context is
  already loaded.

---

## On staying current (the founder asked us to keep up)
News check, June 2026:
- **Agent SDK credit change PAUSED.** The planned 2026-06-15 move of Agent SDK /
  `claude -p` / GitHub Actions / third-party-auth usage onto a *separate* monthly
  credit **did not take effect** — those surfaces still draw from the existing
  Pro/Max/Team/Enterprise limits. Anthropic says it will give advance notice
  before any future change. **Action: watch for that notice** — it would change
  the economics of our routine/Action-driven runs.
- **Managed Agents** can now run in a sandbox you control against your private
  MCP servers — relevant if we ever move the AI-CTO/CFO routines server-side.
- This space moves weekly; treat the dated guidance below as perishable and
  re-check before relying on a specific number.

---

## The prompt that triggered this review (the meta-lesson)
The request was, paraphrased: *"Find inefficiencies in our process. Reduce
tokens. Better prompting? Leverage other AI. Hybrid local/Claude. ANYTHING.
Search the web. Keep up to date. Check the news. Thanks!"*

It's a great *intent*, but it's an expensive *prompt*, and it models the exact
inefficiency it's hunting:
- **Unbounded scope** ("ANYTHING that could help") invites broad, costly
  exploration with no stopping rule.
- **No deliverable named** — no format, no length, nowhere for the answer to land.
- **Open-ended verbs stacked** ("search the web… check the news… best
  practices…") each fan out independently.

A tighter version that would have cost a fraction:

> "Audit our human↔AI token efficiency. Cover: (1) `CLAUDE.md` size/duplication,
> (2) using the t630 local-LLM router for cheap work, (3) prompt caching on the
> SDK path. Skim current best practices (≤4 web searches) and the latest
> Anthropic pricing news. Deliver a ranked findings doc committed to
> `docs/ai-cto/`, ≤2 pages, plus a one-line notification. Don't refactor
> anything yet — recommend only."

The pattern that makes any prompt cheaper and better: **scope + named deliverable
+ output shape + an explicit budget/stop rule.** Front-loading those three lines
is the single highest-leverage prompting habit.

---

## Action checklist
- [ ] Set routines/sessions to a **single-repo working directory** (kills the
      ~15 K-token multi-repo prefix). *Highest payback, zero risk.*
- [ ] Factor the shared **house-style + portfolio map** into one canonical file;
      replace the 6 pasted copies with a one-line link; trim each `CLAUDE.md` to
      a lean index.
- [ ] Point **routine/low-complexity work at the t630 LiteLLM router**; keep
      reasoning/code on Claude. Document the split in `10-ai-orchestration`.
- [ ] On the **SDK/Action path**, mark the stable briefing prefix cacheable;
      keep timestamps + per-household data out of it.
- [ ] Adopt the **prompt template** (scope + deliverable + shape + budget) as the
      default for routine tasks.
- [ ] **Watch for** the reworked Anthropic Agent-SDK-credit announcement; re-cost
      our automation when it lands.

---

### Sources (perishable — re-check before relying on a number)
- [Claude Code Token Optimization (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [How to Reduce Claude Code Token Usage (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Prompt Caching: 90% Cost Reduction Guide (2026)](https://www.respan.ai/articles/claude-prompt-caching)
- [Hybrid Cloud-Local LLM: Architecture Guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Subagents: A 2026 Practical Guide (Tembo)](https://www.tembo.io/blog/claude-code-subagents)
- [Best practices for Claude Code (docs)](https://code.claude.com/docs/en/best-practices)
- [Anthropic Pauses the June 15 Credit Change](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
