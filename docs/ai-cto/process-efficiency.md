# Process Efficiency — AI usage, token cost & prompting

**Owner:** NARF (AI CTO), with ZORT (AI CFO) on the cost lines.
**First written:** 2026-06-16. **Re-check cadence:** monthly (this field moves *fast* — treat
anything older than ~30 days as stale and re-search the web before trusting it).

This is the standing review of *how we work with the AI itself* — the seam between the human and
the model across all A777ance repos. It answers a founder question: where are we wasting tokens,
effort, or money, and what's the better way? Recommendations are **impact-ranked**, not
alphabetical (this is a priority list, so house-style Z→A doesn't apply). The dated review log at
the bottom is newest-first per house style.

---

## 0. TL;DR — the one thing that changed this week

**Anthropic's June 15, 2026 billing split landed *yesterday*, and it hits us directly.** The
Agent SDK, `claude -p`, the Claude Code **GitHub Actions** integration, and any third-party app
that authenticates with a Claude subscription now bill against a **separate monthly Agent SDK
credit ($20–$200, sized to plan) at full API rates** — they no longer draw on the flat
subscription. Anthropic's own framing: heavy programmatic/agent users see a **5–10× effective
cost increase**. Interactive Claude Code (you typing in the terminal) is unaffected.

**Why it matters to us specifically:** the NARF/ZORT scheduled routines (like the one that
generated this file) *are* Agent SDK runs. Every scheduled run now spends real per-token money
from that credit pool — and if it runs on **Opus 4.8 ($5 in / $25 out per M tokens)** with the
full multi-repo `CLAUDE.md` stack loaded each time, it is the single most expensive way we touch
the API. See [TD-15](tech-debt.md) and the [budget note](../ai-cfo/budget.md). **Action this
month:** decide which scheduled routines are worth full-rate Opus, downgrade the rest, and set a
hard credit ceiling so a runaway loop can't blow the <$30/mo burn target.

---

## 1. What we already do right (don't "fix" these)

A fair audit has to start here, because we're further along than most:

- **We already run a hybrid local↔cloud router.** localDNS stage 10 (LiteLLM on :4040 + Ollama +
  the reasoning ladder `local-reason` → `cloud-gpu-reason` → `cloud-overflow`) is exactly the
  architecture the 2026 cost guides recommend. Most teams are *building* what we *have*.
- **We keep a tight budget with a target** (<$30/mo, AI line ~$5–15) and review it monthly.
- **CLAUDE.md files exist and are good** — standing project rules don't get retyped each session.
- **We track AI tech debt** (e.g. TD-14, the privacy-fallback gap) instead of letting it rot.

So the gains below are mostly about *tuning* and *discipline*, not a rebuild.

---

## 2. The highest-impact levers (ranked)

| # | Lever | Est. saving | Effort | Where it applies |
| - | ----- | ----------- | ------ | ---------------- |
| 1 | **Right-size the model per task** (Haiku/Sonnet/local for routine; Opus only for architecture/security) | 50–80% | Low | Every repo; the routines especially |
| 2 | **Lean on prompt caching** (stable prefix; dynamic facts in messages, never in the system prompt) | up to 80–90% on repeat context | Low | Anything with a big stable preamble (our CLAUDE.md stack) |
| 3 | **Use subagents for exploration** (they run in their own context, report back a summary) | Large — keeps the main context small | Low | Multi-file search/research tasks |
| 4 | **Route routine work to the local box** (the ladder we already have) | 60–80% on the offloaded share | Low (built) | Classification, extraction, formatting, light reasoning |
| 5 | **Scope the task, not the module** (point at the function/file, not "the codebase") | Cuts input tokens hard | Low | Every coding/edit task |
| 6 | **Batch follow-ups; `/compact` deliberately** (every new message re-reads the whole thread) | Compounds over a session | Low | Long working sessions |
| 7 | **Cap & meter the Agent SDK credit** (post-June-15 must-do) | Prevents 5–10× surprises | Med | NARF/ZORT routines, GitHub Actions |

### Notes per lever

1. **Model right-sizing.** Industry telemetry says ~60–70% of agent requests are simple
   (classify/extract/format), ~20–30% moderate, only ~10% need a frontier model. Opus 4.8 costs
   **5×** Sonnet-class input and far more than Haiku/local. Default routines to Sonnet or local;
   reserve Opus for genuine architecture, security review, or thorny debugging. In Claude Code,
   `enforceAvailableModels` + an `availableModels` allowlist can *prevent* a routine from silently
   grabbing Opus.

2. **Prompt caching.** Caching reprices repeated context dramatically. The rule that matters:
   **static content first (system prompt → tool defs → stable docs), dynamic content last (in
   user messages)**. Never put per-run facts in the system prompt — it busts the cache prefix.
   Our giant CLAUDE.md preamble is the ideal cache candidate *if* we keep it stable.

3. **Subagents.** A subagent explores in an isolated context and returns only a summary, so the
   main thread doesn't fill with file dumps. This is the cheapest way to research a big codebase,
   and the recommended way to *switch to a cheaper model* for a sub-task.

4. **Local offload.** We have the ladder; the work is making sure routine prompts actually land on
   `local-reason`/Ollama and not the cloud. (Watch TD-14: the privacy fallback can still spill a
   `sensitive` task to cloud — fix that before leaning harder on the ladder.)

5. **Task scoping.** "Refactor this function" loads far less than "refactor this module." Name the
   file and the symbol. Less input = less money and a more focused answer.

6. **Conversation hygiene.** Each new turn re-reads the whole conversation. Batch related asks into
   one message; use `/compact` (or microcompact) at natural breakpoints; start a fresh session for
   an unrelated task instead of dragging a stale 100k-token thread along.

7. **Credit metering (new).** Set the per-user Agent SDK credit deliberately (don't default it
   high), watch the console, and give scheduled routines a "downgrade or skip" rule when near the
   cap. A scheduled loop at full API rates on Opus is exactly what the new pricing punishes.

---

## 3. Leveraging other AI / hybrid — what to tighten (not build)

We don't need to *adopt* hybrid routing — we run it. The improvements are operational:

- **Make local the default, cloud the exception.** Confirm the LiteLLM routing actually sends
  classify/extract/format/light-reason to the t630, and only escalates on complexity or length.
- **Fix the fail-closed gap (TD-14)** so privacy isn't traded for the saving.
- **Consider a cheap "judge/triage" model** (Haiku-class or local) to *decide* whether a task even
  needs Opus, before spending Opus tokens deciding that itself.
- **The "Dreaming" feature** (new in June 2026 Claude Code): a scheduled pass that reviews past
  sessions, surfaces recurring mistakes/workflows, and curates memory — i.e. it makes the agent
  *learn our preferences once* instead of us re-prompting them. Worth a look for the NARF/ZORT
  routines, since it directly attacks "we keep re-explaining the same context."

---

## 4. Critique of the prompt that triggered this run

The founder asked whether *the prompt itself* was efficient. Honest answer: **it's a good
brainstorming prompt but an expensive instruction.** What works and what to change:

**Works:** clear intent, gives permission to use the web, asks for prompt self-critique, names the
hybrid-LLM angle. Open-ended exploration is legitimately what you want here.

**Costs more than it needs to:**
- *Unbounded scope* ("ANYTHING that could help… Check the news") invites a broad, multi-search
  sweep every run. Fine once; wasteful as a recurring routine.
- *No output target* — it doesn't say *where* the answer should live, so the agent has to decide
  (and a routine with nobody watching could easily just talk into the void).
- *No model/length guidance* — a sprawling research prompt on Opus is the priciest combination.
- *"Keep UP TO DATE… day by day"* implies high frequency; daily deep web-research on Opus is
  exactly the post-June-15 cost trap.

**A tighter recurring version (drop-in):**

> *Monthly (not daily): review AI-process efficiency for A777ance. Update
> `docs/ai-cto/process-efficiency.md` in place — only append what's genuinely new since the last
> "Review log" date; don't re-derive the whole report. Do at most 3 web searches, focused on
> changes in the last 30 days. Run on Sonnet unless you hit something that needs Opus. Notify only
> if there's a material cost or capability change.*

That keeps the value (fresh, web-checked) while killing the cost drivers (daily cadence, Opus,
unbounded fan-out, no home for the output). One-off deep dives can still use the original
open-ended phrasing — the discipline is for the *recurring* version.

---

## 5. This run, concretely

This routine is a scheduled Agent SDK run on **Opus 4.8** that loads all seven repo CLAUDE.md
files on every invocation. Post-June-15 that's the most expensive shape we have. Recommended
changes are captured as [TD-15](tech-debt.md) and a [budget line](../ai-cfo/budget.md); the
headline is: **set the credit ceiling, move recurring routines to Sonnet/local, and make this a
monthly (not daily) job.**

---

## 6. Sources (2026-06-16 sweep)

- [Anthropic — Lessons from building Claude Code: prompt caching is everything](https://claude.com/blog/lessons-from-building-claude-code-prompt-caching-is-everything)
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices)
- [Claude API — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude API — Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Anthropic's June 15 billing change (codersera)](https://codersera.com/blog/anthropic-june-2026-billing-change-claude-code/) · [digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026) · [proveai](https://proveai.com/blog/anthropics-agent-sdk-credit-june-15)
- [Claude API pricing 2026 (Opus 4.8 / Sonnet 4.6 / Haiku 4.5) — metacto](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid LLM routing: Ollama + Claude without quality degradation (dev.to)](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [7 ways to reduce Claude Code token usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Guide 2026 — 25 features incl. "Dreaming" (MarkTechPost)](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)

---

## 7. Review log (newest first)

- **2026-06-16** — First version. Headline: June 15 Agent SDK billing split (full API rates,
  5–10× for heavy agent use) now bills our scheduled routines. Confirmed we already run the
  recommended hybrid router (localDNS stage 10). Filed TD-15 (credit ceiling + model right-sizing
  for routines) and a budget note. Recommended the original open-ended prompt be re-scoped to a
  monthly, Sonnet-default, append-only routine.
