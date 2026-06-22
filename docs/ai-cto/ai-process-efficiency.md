# AI Process Efficiency — token & workflow audit

*Audit run 2026-06-22 by the AI CTO routine. Sources: Anthropic Claude API skill
(authoritative, current), Anthropic docs, and 2026 third-party guides (linked at the
bottom). Revisit quarterly — this surface changes monthly.*

The question: where are we wasting tokens / money / latency in the human↔AI loop, and
what's the better way? This is the surround for **every** A777ance repo, so a small per-turn
saving compounds across every session and every scheduled routine.

This is ordered **biggest win first** (not reverse-chronological — it's a recommendation
list, not a log).

---

## 1. The standing-context tax — our single biggest lever

**Every session loads the full `CLAUDE.md` of every repo in scope.** This audit run alone
had **six** CLAUDE.md files concatenated into context before a single instruction was read:
DESIGN, localDNS, customers, MARKETING, Azure-lab, claude-code-homelab. That's on the order
of **25–40K tokens of standing context carried on every turn, every session** — "a
5,000-token CLAUDE.md costs 5,000 tokens before you've typed a word, every turn" (Anthropic
guidance is to keep CLAUDE.md **under ~200 lines**; ours run well over).

Prompt caching softens this — Claude Code caches the system+CLAUDE.md prefix, and cache
reads cost ~10% of normal input — **but it doesn't eliminate it**: the prefix still occupies
the context window (so compaction triggers sooner and quality degrades as it fills), and the
cache write is **re-paid in full every time any CLAUDE.md changes** (a one-byte edit anywhere
in the prefix invalidates everything after it).

**Three fixes, in order of effort:**

| Fix | What | Saving |
| --- | ---- | ------ |
| **1a. De-duplicate the House-style block** | The identical ~20-line "House style: ordering & typography" block is copied **verbatim into all 6 CLAUDE.md files**. That's ~120 lines of pure duplicated standing context. Put it in **one** file (e.g. `DESIGN/docs/house-style.md`) and have each CLAUDE.md link to it in one line. | ~100+ lines off the per-session baseline; one place to edit (today an edit means 6 cache invalidations) |
| **1b. Trim each CLAUDE.md to a lean briefing + pointers** | Move the heavy reference tables (localDNS deploy-paths, the nftables checklist, the long known-issues tables) into the files they already reference (`README.md`, `INSTALL-NOTES.md`). Claude reads them **on demand** when a task actually needs them. Keep CLAUDE.md as the map, not the territory. | Trades a constant per-turn cost for an occasional read; most sessions never touch the deploy-path table |
| **1c. Scope each session to the minimum repo set** | A MARKETING copy task does not need localDNS's deploy paths. For scheduled routines especially, add only the repos the job touches. | Drops whole CLAUDE.md files from the baseline |

**Keep CLAUDE.md stable** once trimmed — every edit re-pays the cache-write premium across
the whole prefix. Treat CLAUDE.md changes like code: review them, don't churn them.

---

## 2. We already own the hybrid rails — use them

`localDNS` stage `10-ai-orchestration` runs **LiteLLM (:4040) + Open WebUI + ollama** with a
reasoning ladder already defined in `config.yaml` (`local-reason` deepseek-r1:1.5b on the
t630, `cloud-gpu-reason` on a rented GPU, `cloud-overflow` → Claude). This is exactly the
hybrid architecture the 2026 cost-optimization guides recommend (they cite **60–80% cost
reduction** by serving routine work locally and routing only the hard 10% to a frontier
model). Industry rule of thumb: ~60–70% of tasks are simple (classify/extract/format),
20–30% moderate, ~10% genuinely need a frontier model.

**Route by task, not by habit:**

- **Local (free, on the t630/GPU):** lead classification, first-pass summarization, drafting
  routine "Handled For You" log entries, lint/format, anything high-volume and low-stakes.
  Note the doc-link checker (`tools/check-docs.py`) needs **no LLM at all** — it's already
  pure Python. Don't spend a model on what a script does.
- **Claude (paid):** architecture decisions, the Statements' honesty-critical copy, code
  review, anything on the **kept document** a customer sees. The moat is trust; don't cheap
  out where a wrong number ships on paper.

⚠️ **Blocked by TD-14:** the router's `sensitive` path can fail over to `cloud-overflow`
(Claude cloud) if the local model is down — `allow_cloud=False` isn't enforced at the
LiteLLM failover layer. **Fix TD-14 (fail closed to a local-only chain) before routing any
real customer data through the local tier.** Until then, hybrid routing is safe only for
non-sensitive, made-up, or already-public content.

---

## 3. Model-tier discipline + the two big discount levers

Current Claude pricing (per 1M tokens, input/output): **Haiku 4.5 $1/$5 · Sonnet 4.6 $3/$15
· Opus 4.8 $5/$25**. Use the cheapest tier that clears the bar. In Claude Code, Explore/search
subagents already run on Haiku — lean on that.

Two levers we are probably not using and should be:

- **Batch API — 50% off** for anything not latency-sensitive. The **monthly statement
  generation** job (stage 06, "about a penny a home") and **nightly doc-checks / report
  generation** are textbook batch candidates. Halves that line item, results within ~1h.
- **Prompt caching — ~90% off repeated context.** Statement generation reuses a big shared
  template/system prompt across many households — cache the shared prefix once, pay ~10% on
  every household after the first. Batch + caching **stack**.

---

## 4. Long-running routines: context editing, compaction, subagents

- **Context editing** (clear stale tool results) and **compaction** (summarize history) keep
  long agentic runs — PR babysitting, end-to-end funnel verification — from ballooning.
  Claude Code auto-compacts; `/compact` and `/recap` cut re-replay cost on resume.
- **Subagents** isolate heavy context (keeps the main thread clean) **but can cost ~7× tokens**
  because each carries its own context window. Use them for genuine parallel fan-out (e.g.
  checking many repos at once), **not** as a default for everything.

---

## 5. About *this* routine and the prompt that triggered it

The triggering prompt asked for "ANYTHING that could help… search the web… check the news."
Great for a **one-off audit**; **expensive as a recurring cron** — every run re-does full web
research and reloads six CLAUDE.md files. Recommendations:

1. **Run this audit one-off or quarterly, not frequently.** The frontier moves monthly, not
   daily; daily runs mostly re-pay the standing-context tax to learn nothing new.
2. **A standing "efficiency watch" routine should be narrow + silent-by-default:** "diff the
   Anthropic changelog + pricing page against last run; if changed, summarize the delta and
   notify; else stay silent." Scope it to **one** repo so it isn't carrying all six CLAUDE.md.
3. **One concrete question per run** beats an open-ended "anything" — cheaper, sharper, and
   caches better.
4. **Give routines a stop condition / budget.** "Search the web" with no bound is unbounded
   spend.

These four points apply to every scheduled routine we add, not just this one.

---

## Quick-win checklist (do these first)

- [ ] **1a** — Hoist the duplicated House-style block into one `house-style.md`; link from each CLAUDE.md. *(touches all 6 repos)*
- [ ] **Fix TD-14** — fail the `sensitive` route closed to a local-only chain before any hybrid routing of real data.
- [ ] Move the monthly statement job + nightly doc-checks onto the **Batch API** (50%) and **cache the shared template prefix** (~90% on repeats).
- [ ] Scope scheduled routines to the minimum repo set; make the "efficiency watch" routine narrow and silent-by-default.
- [ ] **1b/1c** (larger) — trim CLAUDE.md files to briefing+pointers; move heavy tables into the READMEs they already reference.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Steering Claude Code: skills, hooks, subagents](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more)
- [12 Ways to Cut Token Consumption in Claude Code (Firecrawl, 2026)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [How to Reduce Claude Code Token Usage (Agensi, 2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM Architecture Guide (SitePoint, 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio, 2026)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- Authoritative API facts (pricing, Batch API 50%, prompt caching, context editing, compaction) from the bundled Anthropic `claude-api` skill, current as of this environment.
