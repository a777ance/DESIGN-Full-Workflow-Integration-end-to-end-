# AI Process Efficiency Review — How We Work With the AI

*Author: NARF (AI CTO) · Date: 2026-06-25 · Status: recommendations, not yet decided*

The ask: find inefficiencies in **our process — the back-and-forth between the founder and
the AI** — and cut token use, improve prompting, and use cheaper models (incl. our own local
LLM stack) wherever it doesn't cost us quality. This is the "how we talk to the machine" review,
not a code review. Newest-first per house style; the highest-leverage item is #1.

---

## TL;DR — the five biggest levers

| # | Lever | Effort | Est. saving on a typical session |
| - | ----- | ------ | --- |
| 1 | Slim the always-loaded `CLAUDE.md` files | 1–2 hrs | **~25–35% of fixed per-turn cost** |
| 2 | Stop force-reading 4–6 hub files on every session start | 30 min | large on short sessions |
| 3 | Tier the model: Sonnet/Haiku by default, Opus only when needed | config | **40–60% on routine work** |
| 4 | Route the cheap & offline work to **our own LiteLLM stack** (already built!) | 1 day | 60–80% on the work that moves there |
| 5 | Batch the non-interactive jobs (statements, link-checks) | 1 day | **50%** on those jobs (Batch API) |

The single most important fact, from the 2026 field reports below: **`CLAUDE.md` is never
lazy-loaded or evicted. It sits in context for the entire session and is re-billed on every
single turn.** Everything in section 1 follows from that.

---

## 1. The always-on tax: our `CLAUDE.md` files (highest leverage)

Measured today, in words (≈ ×1.3 for tokens):

| Repo | `CLAUDE.md` words | ≈ tokens, **every turn, all session** |
| ---- | -----------------: | --: |
| `localDNS` | 2,728 | ~3,550 |
| `DESIGN-…` (this repo) | 2,608 | ~3,400 |
| `MARKETING` | 1,445 | ~1,900 |
| `customers` | 562 | ~730 |
| `claude-code-homelab` | 371 | ~480 |
| `Azure-lab` | 316 | ~410 |

A 40-turn session in `localDNS` pays that ~3,550-token brief **40 times ≈ 142,000 tokens** of
pure overhead before a single line of actual work. The public benchmark behind this found a
3,847-token `CLAUDE.md` could be cut to 312 tokens — **91.9% smaller — with no quality
regression** ([token reduction guide][1], [Firecrawl][4]).

**The rule to apply:** *if the AI can infer it from reading the repo, cut it. If a smart reader
would figure it out in 20 minutes of browsing, cut it.* Our `CLAUDE.md`s are beautifully
written prose — but a lot of it is re-derivable (the funnel diagram, the full stage map, the
roles/money-flow recap that also lives in `MARKETING`, the verification walkthroughs). Those
belong in `README.md` (which the AI reads *only when relevant*), not in the always-resident
brief.

**Concrete cuts (no information lost — it moves, it doesn't vanish):**
- Keep `CLAUDE.md` to: the voice rule, the house-style ordering rules, the one-master-list rule,
  the secrets rule, and a *pointer* to README/workflow-context for the rest.
- Move the funnel ASCII diagram, the full stage-map table, and Section B roles recap → `README.md`.
- Target: each `CLAUDE.md` ≤ ~800 tokens. That alone reclaims ~2,500 tokens/turn in `localDNS`
  and `DESIGN`.

> ⚠️ Caching caveat: Claude Code prompt-caches the `CLAUDE.md` prefix, so within one warm session
> the repeat cost is ~0.1×. But (a) the cache is re-written cold every new session, (b) **any edit
> to `CLAUDE.md` mid-session invalidates the whole cached prefix**, and (c) caching makes the bloat
> *cheaper*, not *free*. Slimming wins on every cold start and every edit. ([prompt-caching notes][1])

## 2. The session-start read tax

Both `CLAUDE.md`s instruct the AI to read a pile of hub files *before doing anything*:
- **NARF** block: read `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md` (4 files).
- **ZORT** block: read 6 files including `MARKETING/docs/ai-cfo/context.md`.

That's up to **10 file reads on every session**, even when the task is "fix a typo in one
README." It's the right instinct (shared state) but the wrong default (unconditional).

**Fix:** make it conditional and lazy. Reword to: *"If the task touches cross-repo status,
roadmap, or money, read the relevant hub file(s) first."* Let the model pull them on demand —
that's exactly what long chat threads and re-reads are flagged as the biggest hidden drain in
the 2026 guidance ([Agensi][2], [KDnuggets][5]).

## 3. Model tiering — stop paying Opus prices for Haiku work

Opus 4.8 is $5 / $25 per 1M tokens (in/out). Sonnet 4.6 is $3 / $15. Haiku 4.5 is $1 / $5 —
**5× cheaper in, 5× cheaper out than Opus.** Most of what this business asks the AI to do —
doc edits, link-checking, log formatting, roster updates, "Handled For You" entries, schema
tweaks — is *not* Opus-grade reasoning.

Field consensus for 2026: **start every session on Sonnet; escalate to Opus only for genuine
deep analysis or complex refactors** ([Agensi][2], [thevccorner][3]). For us:

| Task class | Model |
| ---------- | ----- |
| Cross-repo architecture, the AI-CTO/CFO judgment calls, tricky debugging | **Opus 4.8** |
| Routine doc edits, README upkeep, statement copy, CRM/schema edits | **Sonnet 4.6** |
| Link-checks, log formatting, classification, extraction, "is this on-voice?" | **Haiku 4.5** or local |

## 4. Use the LLM stack we already built (the hybrid win we're sitting on)

This is the standout finding: **`localDNS` stage 10 already runs a LiteLLM router** (`~/llm-router`,
port 4040) with a reasoning ladder — `local-reason` (deepseek-r1:1.5b on the t630 CPU, free),
`cloud-gpu-reason` (full R1 on a rented GPU via Tailscale), and `cloud-overflow`. We built the
hybrid gateway and we're **not routing our day-to-day AI work through it.**

2026 guidance: a routing layer in front of local + cloud, deciding by **data sensitivity, task
complexity, and availability**, cuts LLM cost **60–80%** by keeping simple/sensitive work local
and sending only the hard stuff to Claude. LiteLLM is the canonical gateway for exactly this, with
**automatic cloud fallback** if the local model fails ([SitePoint][6], [buildmvpfast][7],
[LiteLLM routing docs][8]).

**What to move to the local/router tier:**
- **Sensitive-by-policy work** → local first. The `customers` repo holds *real* names and figures
  and is private. Classification, redaction checks, "does this statement only cite measured
  numbers?" gates — run these against `local-reason` so customer PII never leaves the box.
  This is a privacy win *and* a cost win, and it's on-brand ("make the network dull").
- **High-volume cheap calls** (link-checker triage, log tidying, on-voice linting against
  `the-pitch.md`) → local model, Claude as fallback.
- Keep Claude (this surface) for cross-repo reasoning and the kept-document judgment calls.

Add a `cloud-overflow` → Claude API fallback in `config.yaml` so a local miss degrades gracefully
instead of failing. This is a half-day of wiring against infrastructure that already exists.

## 5. Batch the non-interactive jobs (50% off, automatically)

The statement run is described as "about a penny a home" and is a scheduled, latency-tolerant job
— the textbook case for the **Batch API: 50% off all tokens**, up to 100k requests/batch, most
finishing within the hour. Same for any monthly bulk link-check or bulk on-voice lint. Anything
that doesn't need an answer *this second* should not pay interactive prices.

Pair it with **prompt caching** on the shared preamble: the statement generator's fixed
instructions + template are identical across every home, so cache that prefix once and only the
per-home data block is billed fresh (~0.1× on the cached part). Caching + batching stack.

---

## 6. The meta-prompt itself — yes, the prompt that triggered this review was inefficient

Honest feedback, since it was asked for. The originating prompt was, in essence:

> *"Locate inefficiencies in our PROCESS… Is there a better way to reduce token use? Better
> prompting? Anything you could think of. Leveraging other AI. Hybrid local/Claude. ANYTHING.
> Search the web. Keep UP TO DATE. Check the news. Thanks!"*

What it does well: it's clearly motivated and it explicitly invites web search and self-critique.
What costs tokens and quality:

1. **No scope.** "Our process" spans 7 repos. The AI has to load and weigh everything to guess
   what's in-frame. A scoped prompt ("review how we use the AI across the three private repos,
   focus on token cost") would cut the exploration cost sharply.
2. **No output contract.** "Anything you could think of" with no format means the model defaults
   to a long, hedged survey. Saying *"give me a ranked table of the top 5 fixes with effort and
   estimated saving, then a one-paragraph rationale each"* gets a tighter, cheaper answer.
3. **Scattershot asks** ("ANYTHING… leveraging other AI… check the news… better prompting") make
   the model fan out across many half-explored threads instead of going deep on the few that matter.
4. **Open-ended verbs invite over-thinking.** "Anything that could possibly help" reads as "be
   exhaustive," which is the most expensive mode.

A tighter version of the same request:

> *"Review how we use the AI across the A777ance repos with one goal: cut token spend without
> losing quality. Cover (a) the always-loaded context files, (b) model/tier choice, (c) routing
> cheap or sensitive work to our own LiteLLM stack. Web-search for current best practice. Output:
> a ranked table of the top 5 fixes — effort + estimated saving + one-line rationale each — then
> the detail. Keep it under ~1,500 words."*

Same intent, a third of the wandering. And note the general principle for **all** our prompting:
**scope tightly, state the output format, and give one clear goal.** That single habit is worth
more than any config change because it applies to every interaction.

---

## 7. Quick wins we can turn on this week

- [ ] Use `/compact` to trim long sessions and `/recap` to resume without replaying the whole
      thread — re-reading old context is the #1 hidden drain ([Agensi][2]).
- [ ] Default new sessions to **Sonnet**; reach for Opus deliberately.
- [ ] A "terse mode" house instruction for routine turns (no preamble, no restating the task) —
      the most-cited single output-side saving in 2026 ([token guide][1]).
- [ ] Slim the two big `CLAUDE.md`s to ≤ ~800 tokens (section 1).
- [ ] Make the NARF/ZORT session-start reads conditional (section 2).

## Sources (mid-2026, verify before relying — this space moves weekly)

- [1] [Reduce Claude Code token usage by 90% — Medium][1]
- [2] [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi][2]
- [3] [How to Never Hit Claude's Usage Limits (2026) — The VC Corner][3]
- [4] [12 Ways to Cut Token Consumption in Claude Code — Firecrawl][4]
- [5] [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets][5]
- [6] [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint][6]
- [7] [Hybrid Cloud-Local AI Workflows / Cost Optimization — BuildMVPFast][7]
- [8] [Routing & Load Balancing — LiteLLM docs][8]

[1]: https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3
[2]: https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage
[3]: https://www.thevccorner.com/p/how-to-never-hit-claude-limits-token-system-2026
[4]: https://www.firecrawl.dev/blog/claude-code-token-efficiency
[5]: https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage
[6]: https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
[7]: https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
[8]: https://docs.litellm.ai/docs/routing-load-balancing
