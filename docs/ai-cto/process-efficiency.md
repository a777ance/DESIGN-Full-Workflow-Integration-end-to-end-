# Process efficiency — user↔AI token & workflow review

**First written:** 2026-06-22 (by a scheduled "find inefficiencies in our process" routine).
Living note — newest findings at the top per house style.

This is about *how we talk to the models*, not what the models do. It covers token cost,
prompting, and getting more of the cheap local work off the paid cloud path. Sources for the
current-best-practice claims are listed at the bottom; recheck them before treating any number
as fresh — this space moves weekly.

---

## TL;DR — the five levers, biggest first

1. **Trim the CLAUDE.md files. This is our single biggest fixed cost.** Every session loads the
   CLAUDE.md of every repo in scope. Ours run 150–400 lines each; with all seven repos in a
   session that is ~15–25k tokens spent *before the first word of the task*, on every turn.
   Anthropic's own guidance is to keep CLAUDE.md **under ~200 lines** and treat it as a terse
   index, not a manual. Move the prose into `README.md` / `network-context.md` (already exist!)
   and leave CLAUDE.md as pointers. The detail isn't lost — it just isn't paid for on every turn.
2. **Let prompt caching do its job — keep the prefix stable.** Claude Code already caches the
   stable prefix (system prompt + tools + CLAUDE.md). A cache *read* costs ~10% of the input
   price; a 5-min write costs 1.25×. The trap: editing a CLAUDE.md *mid-session* busts the cache
   and you re-pay full price for the whole prefix. So batch CLAUDE.md edits at the *end* of a
   session, not the middle, and prefer long uninterrupted sessions over many cold starts.
3. **Match the model to the job — stop defaulting routines to Opus 1M.** A monitoring/scanning
   run (like the one that wrote this) does not need Opus 4.8 with a 1M window. Run gather/triage
   on Haiku or Sonnet, escalate to Opus only for the synthesis step. The 1M context window
   carries a real cost and most routine work never fills it.
4. **Route the cheap stuff to Odin (we already built this — use it).** 60–70% of typical LLM
   work is simple (classify, extract, format, summarize) and runs fine on the local t630 tiers.
   Industry reports 60–80% cost cuts from routing simple tasks local and reserving the cloud for
   the ~10% that genuinely needs frontier reasoning. Our `local-fast`/`local-smart` tiers and the
   reasoning ladder are exactly this — the gap is *habit*: send drafting, log-summarizing, and
   first-pass extraction to `ai.home.lan:4040`, not to a paid session.
5. **Scope the prompt and the cadence.** Open-ended "look at anything" prompts and daily
   recurring web sweeps are themselves the inefficiency (see "This routine" below).

---

## Concrete fixes for our repos

- **CLAUDE.md diet (all repos).** The `localDNS` CLAUDE.md is ~400 lines and reproduces deploy
  tables, the full known-issues log, and verification scripts that also live in README /
  INSTALL-NOTES. That duplication is paid on every turn. Target: a ~150-line index that links
  out. Same treatment for the DESIGN CLAUDE.md. Track as TD-15.
- **Privacy fallback bug is also a cost/trust bug — TD-14.** `local-reason` falls over to
  `cloud-overflow`, so a `sensitive` task can leak to Claude cloud if the local model is down.
  Fix it to a local-only chain (fail closed). Already tracked; flagging because it sits on the
  same routing layer this review is about.
- **Use subagents/Explore for fan-out research.** When a task means sweeping many files, delegate
  to a search subagent — it explores in its own context and returns only the conclusion, keeping
  the main (expensive) context clean. This routine did that implicitly by reading narrowly.
- **`/clear` between unrelated tasks, `/compact` within a long one.** `/clear` wipes context for a
  fresh task (cheapest); `/compact` summarizes when a single long task nears the window.
- **Glance at `/context`.** It breaks down where tokens go (system prompt, tools, memory, history)
  — run it once in a typical session to confirm the CLAUDE.md cost above before/after the diet.

---

## This routine (the prompt that generated this note) — critique

The triggering prompt was, paraphrased: *"Find inefficiencies in our process. Reduce tokens.
Better prompting. Leverage other AI, hybrid local+Claude. ANYTHING. Search the web. Keep up to
date day by day. Check the news."* Honest read: **the routine is itself one of the more expensive
shapes we could run**, for four reasons, each with a fix:

1. **Unbounded scope.** "Anything you could possibly think of" maximizes exploration and output.
   *Fix:* give it a fixed checklist (the five levers above) and a target output length.
2. **Top model + 1M context for a research sweep.** *Fix:* run the gather/search phase on Sonnet
   or Haiku; only synthesize on Opus if needed.
3. **Daily cadence on a slow-moving topic.** "Day by day" web sweeps mostly re-fetch the same
   advice. *Fix:* run it **weekly**, and have it **diff against this file** — notify only when a
   genuinely new practice appears, otherwise stay silent.
4. **All seven repos in scope.** Loads seven CLAUDE.md files for a task that needs maybe two.
   *Fix:* scope the routine's session to `DESIGN` + `localDNS` only.

A tighter rewrite of the recurring prompt:

> *Weekly: re-read `docs/ai-cto/process-efficiency.md`. Search only for LLM cost/prompting
> practices **published since the last run**. If something materially new vs. this file exists,
> append it (newest-first) and notify with a one-line summary. If nothing new, update the
> "last checked" date and send no notification. Scope: DESIGN + localDNS. Model: Sonnet.*

---

## Sources (recheck — this changes fast)

- Anthropic — Best practices for Claude Code: https://code.claude.com/docs/en/best-practices
- Anthropic — Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic — Pricing (cache/batch multipliers): https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic — Context engineering (memory, compaction, tool clearing): https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
- Anthropic — Steering Claude Code (skills, hooks, subagents): https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more
- Hybrid cloud-local LLM architecture guide (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Run local models with Claude Code to cut cost: https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- 12 ways to cut token consumption in Claude Code: https://www.firecrawl.dev/blog/claude-code-token-efficiency
