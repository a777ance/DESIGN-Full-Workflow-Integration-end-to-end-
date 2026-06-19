# AI Process Efficiency — cutting token spend & sharpening the human↔AI loop

A standing review of how we work *with* the AI (Claude Code, the Claude API, and the
local LLM router): where tokens leak, where prompting can be tighter, and how the
local-vs-cloud split should be drawn. Compiled 2026-06-19 from current best-practice
sources (linked at the bottom) and our own stack. Re-check quarterly — this space moves
weekly.

> **Scope note.** This is operational advice about *our* use of AI tools. It does not
> change the product, pricing, or the Statement. It belongs in the CTO/CFO hub because
> AI spend is a real line item (LLM router, Claude API, Claude Code) and a privacy
> surface (TD-14).

---

## TL;DR — the five levers, biggest first

1. **CLAUDE.md is a per-turn tax.** Every token in a `CLAUDE.md` is re-sent on *every*
   turn. Ours are large (the DESIGN one is ~250 lines; localDNS similar). Industry rule
   of thumb is **under ~200 lines / ~spend it like it's billed every message.** Trim to a
   tight briefing + links. Biggest single win, costs nothing but editing.
2. **One task per session, then `/compact` or `/clear`.** Long-running Claude Code
   sessions re-send the whole transcript each turn. Scoping to one task and compacting
   between them is where teams report **40–85% token reductions.**
3. **Point at files, not "the repo."** "Edit `05-sales-and-onboarding/README.md`" instead
   of "fix the sales stage" — smaller context pulled in, fewer tokens, better answers.
4. **Fix the hybrid split we already half-built (TD-14).** We have the right
   architecture — route cheap/sensitive work local, hard work to Claude — but the
   privacy fallback is wired wrong (a sensitive prompt can fail over to cloud). That is a
   correctness bug *and* the efficiency story; details below.
5. **Batch the non-interactive AI work.** Statement-copy generation, lead-note
   summaries, doc passes — anything not waiting on a human — through the **Batch API is
   50% off**, and stacks with prompt caching for up to ~95% off.

---

## A. The human↔AI loop (Claude Code)

This is the loop with the most waste because it's interactive and easy to let sprawl.

| Leak | Fix | Why it matters here |
| ---- | --- | ------------------- |
| Big `CLAUDE.md` files | Trim to a briefing + links; move detail into linked docs the AI reads only when needed | We have one per repo; they're loaded every turn of every session |
| Sessions that run all day | `/compact` between tasks, `/clear` when switching context, one task per chat | Our routines + dev sessions are long-lived |
| "Whole project" prompts | Name the file/function | The repos are doc-heavy; vague scope pulls a lot of markdown into context |
| MCP servers always on | Only connect the MCP servers a session actually needs | Each connected MCP server's tool defs ride in **every** message — can be ~18k tokens/turn. The GitHub MCP here is worth it for PR work but not for a docs edit |
| Re-reading files the AI just wrote | Trust the edit; don't re-Read to "verify" | Pure waste; the harness already tracks file state |

**Auto-features already working for us (don't re-do by hand):** Claude Code does prompt
caching on the system prompt + `CLAUDE.md` automatically, and auto-compacts near the
context limit. Caching is a *prefix* match — a single changing byte early in context
(a timestamp, an unsorted JSON dump) silently busts the whole cache. Keep the stable
stuff (the briefing) first and the volatile stuff (the actual question) last.

> ⚠️ **Version watch.** A regression starting ~Claude Code v2.1.89 (Mar 2026) burned
> rate limits 3–50× faster for some users. Check release notes before jumping versions;
> pin a known-good version if a release looks hot.

---

## B. The hybrid split — local LLM ↔ Claude API

We already run the textbook architecture: **LiteLLM router (`:4040`) → local models for
cheap/sensitive work, Claude for the hard stuff,** with a reasoning ladder
(`local-reason` deepseek-r1:1.5b on the t630 → `cloud-gpu-reason` rented GPU →
`cloud-overflow` Claude). The industry numbers say this is the right bet:
**60–80% cost cut** when 60–70% of traffic (classification, extraction, formatting) stays
local and only the ~10% that needs frontier reasoning hits the cloud.

Two things to act on:

1. **TD-14 is the priority — and it's already logged as P1.** A `sensitive`-tagged task
   routes to `local-reason`, but `config.yaml` gives `local-reason` a fallback chain
   ending in `cloud-overflow` (Claude). So if the local model is down, a *sensitive*
   prompt fails **open** to the cloud — the opposite of what the dispatcher's
   `allow_cloud=False` promises. **Fix: give `local-reason` a local-only fallback so it
   fails closed.** Until then we have no privacy guarantee on the local path. This is the
   single most important item in this whole doc because it's a trust/correctness issue,
   not just cost.
2. **Make the router's routing rules explicit and measured.** The cost win only lands if
   the *right* traffic actually stays local. Worth a one-page tally: what % of requests
   go local vs. cloud, and is the cheap tier catching the simple tasks? "Smart routing"
   saved one team $2,700 on a $4,500 bill — but only because the split was real, not
   aspirational.

**Where Claude (cloud) still earns its keep:** long-horizon agentic work, the hard
one-shot reasoning, anything where a wrong answer is expensive. Don't push those local to
save pennies — that's false economy. The local tier is for volume and privacy, not for
the work that needs the best model.

---

## C. Better prompting (cloud + local)

- **Specific beats forceful.** Modern Claude models follow instructions literally —
  "CRITICAL: YOU MUST…" now *over*-triggers. State the task plainly and scope it.
- **Give the *why*, not just the ask.** "I'm preparing HH-0001's May statement; I need X
  because Y" gets a better result than a bare command — the model connects the task to
  context instead of guessing.
- **Adaptive thinking + `effort`, not token budgets.** On current models, control depth
  with `effort` (`low` for routine, `high`/`xhigh` for hard agentic work) rather than a
  fixed thinking budget. Default to `high`; drop to `low`/`medium` for cheap routine
  passes.
- **Structured outputs over prompt-and-pray parsing** for anything machine-read (lead
  records, statement fields) — guarantees valid JSON, no retry loop.
- **Prompt caching for repeated context.** The Statement template, the schema, a big
  reference doc reused across many calls → put it first, mark it cached, ~90% off the
  repeated part.

---

## D. Leverage other AI / cheaper tiers

- **Batch API (50% off)** for anything not waiting on a human: statement-copy drafts,
  lead-note summaries, monthly doc passes. Stacks with caching → up to ~95% off.
- **Right-size the model.** Haiku 4.5 ($1/$5 per 1M) for classification/extraction;
  Sonnet 4.6 for high-volume production; Opus 4.8 for the genuinely hard work. We
  shouldn't be paying Opus rates to tag a lead.
- **The local tier is the cheapest tier** — for the 60–70% of simple work it's ~free
  after hardware. The router already lets us exploit this; see Section B.

---

## E. Critique of the request that generated this doc

The prompt that kicked off this review ("Locate inefficiencies in our PROCESS… token
use… better prompting… hybrid local LLM and Claude… search the web… check the news…
also tell me if THIS prompt is inefficient") is a good *outcome* prompt but is itself a
mild example of the waste it asks about:

- **It's broad ("ANYTHING that could help").** Open scope makes the AI pull in more
  context and explore more before answering — more tokens, longer turns. A scoped version
  ("Review our LLM-router config and CLAUDE.md files for token waste and the local/cloud
  privacy split") would cost less and land sharper.
- **It bundles several asks** (token use, prompting, hybrid, news, self-critique) into one
  turn. That's fine for a one-off research routine like this, but for day-to-day work,
  one ask per session keeps context lean.
- **It's well-formed where it counts:** it gives the *why* (cost), names the constraint
  (keep up to date), and asks for a recommendation rather than a survey. Keep that.

**Rewrite for a routine like this one:** *"Audit our AI spend surface for waste. Check (1)
the CLAUDE.md files, (2) the LiteLLM `config.yaml` routing + TD-14 privacy fallback, (3)
current Claude Code / API cost best practices. Give me a prioritized fix list with a
recommendation on each. Notify me with the top 3."* — narrower, still complete, cheaper to
run.

---

## F. What changed recently (as of 2026-06-19)

- **Opus 4.8** (May 28) is current top-tier at $5/$25 per 1M; **Fast Mode dropped to
  $10/$50** (was $30/$150 on 4.7). **Fable 5** is now GA above Opus for the hardest work
  (pricier — don't default to it).
- **1M-token context** at flat rates (no long-context surcharge) on Opus 4.8 / 4.7 /
  Sonnet 4.6.
- **June 15 subscription change was cancelled** — Agent SDK / app / third-party usage
  keeps drawing from existing Pro/Max/Team/Enterprise limits, no separate credit pool.
  No action needed, but it means our current plan math still holds.

---

## Recommended next actions (prioritized)

1. **Fix TD-14** — local-only fallback for `local-reason`. Privacy + correctness. (localDNS)
2. **Trim the CLAUDE.md files** to a briefing + links; target the per-turn tax. (all repos)
3. **Add a one-page router-traffic tally** — confirm the local/cloud split is real, not
   aspirational. (localDNS)
4. **Adopt session hygiene** — one task per chat, `/compact` between, name files not "the
   repo." (working practice)
5. **Move non-interactive AI passes to the Batch API.** (where we generate copy/summaries)

---

## Sources

- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [LiteLLM AI Gateway: Route Local + Cloud Models (2026) — Local AI Master](https://localaimaster.com/blog/ai-gateway-litellm)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude Credit Overhaul 2026: Anthropic Pauses the June 15 Change — digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
