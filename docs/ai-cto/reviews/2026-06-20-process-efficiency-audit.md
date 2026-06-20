# Process Efficiency Audit — User ↔ AI Token Use (2026-06-20)

Requested: find inefficiencies in our **process** (the user↔AI loop), reduce token use, improve
prompting, leverage other/local AI and a hybrid local-LLM + Claude-API split. Web-checked against
current (June 2026) best practice. Findings are ordered **highest-leverage first**.

## TL;DR

The biggest, cheapest win is **prompt caching + trimming the always-loaded `CLAUDE.md` files** — we
pay our two largest briefings (~3.5k tokens each) on *every turn of every session*, uncached. We
already built the hybrid infrastructure (the LiteLLM reasoning ladder, stage 10) but **don't route
Claude Code's cheap/triage work through it.** Three levers below cover ~80% of the savings.

---

## 1. The always-loaded `CLAUDE.md` tax (highest leverage)

Measured today:

| Repo | `CLAUDE.md` | ~tokens, loaded every turn |
| ---- | ----------- | -------------------------- |
| localDNS | 326 lines | **~3,640** |
| DESIGN (this repo) | 295 lines | **~3,480** |
| MARKETING | 214 lines | ~1,930 |
| customers / homelab / azure-lab | 50–80 lines | 420–750 |

A `CLAUDE.md` loads before Claude reads your task — *every turn, every session*. The localDNS file is
really a **reference manual** (full deploy-path table, six Unbound drop-ins, the nftables checklist,
~20 known-issues rows) masquerading as an always-on briefing. Most of it isn't needed until you touch
that specific subsystem.

**Fix:** keep `CLAUDE.md` to a tight core (what the repo is, the 3–4 rules, pointers) and move the
big tables to referenced files Claude reads **on demand** (it already does this well via links).
Target ≤120 lines / ~1,200 tokens for the two big ones. Net: ~40–60% off the constant baseline.

Secondary: the **house-style block** (ordering/typography, ~30 lines) is duplicated verbatim across 6
repos. Not a per-session cost (you load one repo at a time), but it *is* loaded in full by cross-repo
runs like the daily reviews and this routine. Consider a single canonical copy linked from each.

## 2. Turn on prompt caching (biggest API-cost win)

If/where we call the Claude API directly (the LiteLLM `cloud-overflow`/`ANTHROPIC_API_KEY` path, and
any scripts), **enable prompt caching** on the stable prefix (system prompt + large fixed context).
Cache reads cost ~10% of normal input; writes cost 1.25× (5-min) / 2× (1-h). Break-even is ~2 reads
(5-min) or ~3 (1-h) — trivially met by our repeated-context jobs. Reported production savings:
**60–90% of input cost.** Claude Code's own context is auto-cached, but our scripted calls likely
aren't. Verify with `usage.cache_read_input_tokens` > 0.

Caveat for our house style: caching is a **prefix match** — any byte change before the breakpoint
invalidates it. Keep volatile bits (dates, per-run IDs) *after* the stable block, never interpolated
into the system prompt header.

## 3. Use the hybrid ladder we already built (stage 10)

We have it — `local-reason` (deepseek-r1:1.5b on the t630, cool/cheap), `cloud-gpu-reason` (rented
GPU), `cloud-overflow` (Claude). Industry data: **60–70% of agent requests are simple**
(classify/extract/format/triage). Route those to the local tier; reserve Claude Opus for the ~10% that
needs frontier reasoning. The daily-review and statement-prep pipelines are prime candidates to triage
locally first and only escalate the hard parts. Claimed hybrid savings: 60–80%.

⚠️ This intersects open **TD-14** (the privacy-fallback gap): don't route `sensitive`-tagged work to a
chain that can fail over to cloud. Fix TD-14 (fail closed, local-only fallback) *before* leaning harder
on local routing.

## 4. Batch API for the scheduled, non-interactive jobs

Anything that doesn't need a live answer — nightly statement generation, the daily review digest,
bulk classification — qualifies for the **Message Batches API at 50% off** all tokens (completes
within an hour, usually minutes). This routine and the `docs/ai-cto/reviews/*` cadence are exactly
this shape.

## 5. Subagents & `/compact` — useful, not free

- `/compact` collapses a long session's history into a summary; use it before context bloats.
- Subagents isolate verbose work (searches, log dumps) and return only the summary — good for the
  multi-repo sweeps. But they carry startup overhead (prompts, tool defs, round-trips); community
  testing shows they're **wasteful for trivial tasks**. Rule: subagent only when the saved main-context
  clutter outweighs the startup cost.

## 6. Prompting for the current models (Opus 4.8)

The current models are more concise and follow instructions more literally; over-constraining now
*hurts*. Concrete adjustments to our docs/prompts:

- **Prefer positive, specific instructions** over lists of negations; keep the 2–3 constraints that
  matter and drop the rest (competing constraints degrade output).
- Tune the **`effort`** parameter deliberately (`high`/`xhigh` for coding/agentic; `low`/`medium` for
  routine) rather than relying on verbose prompt scaffolding.
- Our **house-style rules are genuinely expensive to apply** — "reverse the blocks but keep step
  numbers, never renumber," "alphabetical Z→A," "reverse-chronological within time sections" force
  extra reasoning on *every* doc edit and are a frequent error source. Worth a deliberate cost/benefit
  call: the readability gain vs. the per-edit token + mistake tax. (Business decision — flagging, not
  overriding.)

---

## Critique of the routine prompt that produced this

The prompt ("find inefficiencies… token use… better prompting… leverage other AI… hybrid… search the
web… keep UP TO DATE… check the news… ANYTHING that could help") is **itself inefficient as a recurring
job**:

1. **It's two jobs fused into one.** (a) A *one-off deep audit* of our process (this), and (b) a
   *recurring "keep current" digest*. Bundling them means every run re-does the expensive open-ended
   research. **Split them:** run the audit once (done); make the watch a *cheap weekly* digest scoped
   to "what changed in Claude/Anthropic tooling this week, 5 bullets."
2. **Unbounded scope** ("ANYTHING") → unbounded token cost. Give it a target: a fixed deliverable
   (this file) and a length cap.
3. **No output target / dedup.** Without "append to *this* file, skip if nothing material changed,"
   a daily run risks re-notifying the same findings. Add a "stay silent if nothing new" rule.
4. **Loads all 7 repos** to answer a question that only needed this repo + localDNS's stage 10. Scope
   the routine to the repos it actually reads.

Suggested replacement cadence: **monthly** efficiency re-audit (deep), **weekly** 5-bullet "what's
new" digest (cheap, notify only on material change).

---

## Sources (June 2026, web-checked)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompting Claude Opus 4.8 — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Prompt Caching for Claude: Cut Your API Bill 60% — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Anthropic June 15 2026 billing change (paused) — Codersera](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/)
- [How to Prompt Claude Opus 4.8 — MindStudio](https://www.mindstudio.ai/blog/how-to-prompt-claude-opus-4-8)

*Recent news note:* Anthropic **paused** the June 15 change that would have moved Agent SDK / `claude -p`
/ third-party usage to separate monthly credits — subscription usage still draws from existing limits,
so no billing action needed on our side right now.
