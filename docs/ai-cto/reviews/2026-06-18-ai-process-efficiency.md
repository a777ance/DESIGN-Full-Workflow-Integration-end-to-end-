# AI Process Efficiency Review — user ↔ AI, token spend, hybrid local/cloud

**Date:** 2026-06-18
**Author:** NARF (AI CTO), commissioned by the founder
**Question asked:** "Locate inefficiencies in our PROCESS. Between the user and the AI.
Is there a better way to reduce token use? Better prompting? Leverage other AI / run a
hybrid local LLM + Claude API? Keep up to date — this changes day by day."

This is an operations review, not a product change. It covers how *we* run the AI that runs
the guild — Claude Code on the web across the seven repos, plus the t630's local LLM stack —
and where the spend and friction actually are. Figures are grounded against the authoritative
Claude API reference (cached 2026-06-04) and a 2026-06-18 web sweep; blog-sourced claims are
flagged where they overstate.

---

## TL;DR — the five moves that matter

1. **Prompt caching is the single highest-leverage win and we are almost certainly not using it.**
   Cache reads cost **0.1×** input; the 1-hour TTL write costs 2×, the 5-minute 1.25×. Our
   `CLAUDE.md` files + portfolio/decisions docs are a large, stable prefix re-sent on every turn —
   exactly what caching is for. Expected **30–50% input-token reduction** for ~a day of setup.
2. **The `CLAUDE.md` files are too long and re-billed every turn.** Anthropic's own guidance is
   <200 lines. Ours run many hundreds (the localDNS one alone is ~250 lines of deploy tables).
   Trim + move detail behind links → smaller fixed prefix on *every* request.
3. **We already own the hybrid rig — we just aren't routing to it.** The t630 runs LiteLLM
   (`:4040`), Open WebUI, and a reasoning ladder (`local-reason` deepseek-r1:1.5b → `cloud-gpu-reason`
   → `cloud-overflow`). Route the cheap, high-volume work (statement copy drafts, link-checks,
   classification, commit-message polish) to the local model; reserve Claude for judgment.
4. **Right-size the model per task.** We default everything to Opus 4.8 ($5/$25). Most routine
   doc/CRM/classification work is Sonnet 4.6 ($3/$15) or Haiku 4.5 ($1/$5) work. **Do NOT downgrade
   reasoning-sensitive work** — but a link-check or a roster-field edit is not that.
5. **Batch the non-urgent.** The nightly doc-integrity / review routines are latency-insensitive →
   **Batch API = 50% off** every token, caching stacks on top.

Everything below is detail behind those five.

---

## A. Where the tokens actually go (our process, not generic advice)

Our AI process has three loops, and they have very different cost shapes:

| Loop | What it is | Cost driver | Cheapest fix |
| ---- | ---------- | ----------- | ------------ |
| **Interactive sessions** | Founder ↔ Claude Code on web, editing repos | Re-reading files + long `CLAUDE.md` every turn; context bloat over a session | Caching + shorter CLAUDE.md + `/clear` discipline + subagents |
| **Scheduled routines** | These daily reviews, doc-integrity checks, PR babysitting | Re-reading the whole portfolio each run; Opus on trivial checks | Batch API + caching + route link-checks to local/Haiku |
| **Statement production** | (future, at scale) per-home copy + Handled-For-You logs | Per-home token cost × home count | Local model for first-draft copy; Claude for the honesty pass |

The third loop is the one that scales with the business (a penny-a-home product means AI cost per
home is a real margin line). The first two are where we bleed today.

### The specific inefficiencies

- **No prompt caching.** Verified behavior: a stable prefix re-sent within the TTL bills at 0.1×.
  We re-send `CLAUDE.md` + (for routines) the portfolio/decisions/changelog on every turn at full
  price. This is the big one.
- **Oversized fixed prefix.** Long `CLAUDE.md` files are input tokens on *every* turn. The
  house-style block alone is duplicated verbatim across all seven repos' `CLAUDE.md` — that is
  paid for, repeatedly, in every session in every repo.
- **One model for everything.** Opus 4.8 on a link-check is ~5× the input / ~5× the output price of
  Haiku 4.5 for a task Haiku does fine.
- **No local offload despite owning the hardware.** The reasoning ladder in
  `10-ai-orchestration/config.yaml` exists and is documented but isn't in our authoring loop.
- **Routines re-derive context.** Each daily review re-reads the full portfolio. With caching +
  the 1h TTL, the second-through-Nth run of the day reads that prefix at 0.1×.
- **Context not cleared between unrelated tasks.** A session that drifts across repos carries the
  whole transcript forward — every later turn pays for earlier, now-irrelevant context.

---

## B. Prompt caching — do this first

Authoritative economics (not blog numbers):

- Cache **read**: ~0.1× base input. Cache **write**: 1.25× (5-min TTL) or 2× (1-hour TTL).
- Break-even: 5-min TTL pays off on the **2nd** request; 1-hour TTL on the **3rd**.
- Minimum cacheable prefix is model-dependent: **Opus 4.8 = 4096 tokens**, Sonnet 4.6 / Fable 5 =
  2048. A short prefix silently won't cache.

**Correction to a widely-shared 2026 blog claim:** several posts say Anthropic "cut the cache TTL
to 5 minutes, raising costs 30–60%." The 5-minute TTL is the *default*, but the **1-hour TTL is
still available** at a 2× write multiplier — for our bursty routine workloads (several runs
clustered in a nightly window, then idle) the 1h TTL is the right call and the "cost increase" does
not apply to us if we set it.

What to cache:
- The frozen part of each `CLAUDE.md` / house-style block (system-prompt position).
- For routines: the portfolio + decisions + changelog snapshot (stable within a run-day).

The discipline that makes it work (silent cache-busters to avoid):
- **No timestamps / run-IDs in the cached prefix.** Move "today's date" to the end of the prompt.
- **Deterministic ordering.** Sort any JSON; don't iterate sets; keep tool lists stable.
- **Don't edit the system prompt mid-session** — append context as a later message instead.
- Verify with `usage.cache_read_input_tokens`; if it's 0 across identical-prefix runs, something
  upstream is mutating the prefix.

---

## C. Right-size the model (current, grounded pricing)

| Model | ID | Input $/MTok | Output $/MTok | Use it for |
| ----- | -- | -----------: | ------------: | ---------- |
| Haiku 4.5 | `claude-haiku-4-5` | 1.00 | 5.00 | Link-checks, classification, field edits, format fixes |
| Sonnet 4.6 | `claude-sonnet-4-6` | 3.00 | 15.00 | Most doc/CRM/statement-copy drafting |
| Opus 4.8 | `claude-opus-4-8` | 5.00 | 25.00 | Judgment: architecture, pricing, honesty pass, code review |
| Fable 5 | `claude-fable-5` | 10.00 | 50.00 | Only the hardest long-horizon work; **not** the default |

Rule: **never downgrade for reasoning-sensitive work** (the honesty rule on the kept document is
exactly the kind of judgment that stays on Opus). But "is this link broken," "what ZIP is this
lead in," "tidy this commit message" are not reasoning-sensitive — those are Haiku/local.

Levers that cut output tokens without changing model: lower the **effort** parameter on routine
work (default is `high`); keep adaptive thinking on but don't run `xhigh`/`max` on trivia.

---

## D. The hybrid play — we already built it, route to it

`localDNS/10-ai-orchestration/` is a LiteLLM gateway (`:4040`) with a reasoning ladder:
`local-reason` (deepseek-r1:1.5b on the t630 CPU, cool/cheap) → `cloud-gpu-reason` (full R1 on a
rented GPU via Tailscale, on demand) → `cloud-overflow`. Industry pattern in 2026 is exactly this:
a routing layer that sends ~60–70% of requests (classification, extraction, formatting) local and
reserves the cloud frontier model for the ~10% that needs it; documented savings 60–83%.

Concrete routing for *our* loops:
- **Local (t630 / LiteLLM):** first-draft statement copy, "Handled For You" log phrasing, lead
  classification, link-checking `tools/check-docs.py` failures, commit-message drafts.
- **Claude API (via the same LiteLLM gateway so it's one interface):** the honesty pass on any
  Statement, architecture/pricing decisions, code review, anything customer-facing that ships.

Caveat from our own known-issues: **don't run deepseek-r1:7b+ on the t630/laptop CPU** — it cooks
the box. The ladder already handles this (1.5b local, 7b+ on the rented GPU). Keep that boundary.

Note the **Agent SDK metering change (2026-06-15):** headless / Agent-SDK / GitHub-Action usage now
bills against a separate API-rate credit pool, *not* the interactive plan. Our scheduled routines
are headless — so their token spend is now directly metered. That makes B/C/E above pay off in real
dollars on exactly the workload we run unattended.

---

## E. Batch the latency-insensitive

The **Batch API is 50% off all tokens** and supports caching on top. Our nightly doc-integrity
sweep, the daily portfolio review, and any bulk statement-render pass are not latency-sensitive →
they belong in batches. Most complete within an hour. Stacked with caching and local-offload, the
unattended-routine bill drops substantially.

---

## F. Prompting / process hygiene (cheap, immediate)

- **Trim `CLAUDE.md` to <200 lines; push detail to linked files.** The deploy-path tables and the
  nftables checklist in `localDNS/CLAUDE.md` are reference material — link them, don't inline them
  into the per-turn prefix.
- **De-duplicate the house-style block.** It's copy-pasted into all seven `CLAUDE.md` files. Keep
  one canonical copy (it already lives in DESIGN) and have the others link to it.
- **Plan before acting on multi-file work** — fixing a plan is nearly free; fixing a half-executed
  approach costs the whole context.
- **Use subagents for codebase search** — they run in a separate context and report a summary, so
  the main session doesn't accumulate the files they read.
- **`/clear` between unrelated tasks; `/compact` when a long task nears the window.**
- **Be specific.** "Fix the broken anchor in section E of README.md," not "audit the docs."
- A note on our own house style: the "reverse the blocks, keep the steps" walkthrough rule makes
  walkthroughs *harder* for an AI to follow in one pass (the model reads top-to-bottom). It's a
  deliberate human-ergonomics choice, but it costs a little AI legibility — worth knowing, not
  worth changing.

---

## G. On the prompt that commissioned this report

Since you asked: the commissioning prompt is **broad and open-ended** ("anything you could possibly
think of"). That's fine for a research brief like this — but as a *recurring* routine prompt it
would be expensive and unfocused, because it invites maximal exploration every run. A tighter,
cheaper version for repeat use:

> "Check for new Claude/LLM efficiency features since {last_run_date} (caching, pricing, routing).
> List only what changed and what we should do about it. If nothing changed, say so and stop."

That scopes the web sweep, gives a clean no-op exit (saving a full run when nothing moved), and
keeps the output actionable. The "keep up to date / check the news" instinct is right — just bound
it to a delta since last run rather than a from-scratch survey each time.

---

## Recommended order of work

1. **Prompt caching** on the stable prefix (CLAUDE.md + portfolio for routines), 1h TTL for the
   nightly cluster. *(biggest $ win, ~1 day)*
2. **Trim + de-duplicate `CLAUDE.md`** across repos. *(cuts every-turn cost everywhere)*
3. **Route cheap work to the t630 LiteLLM ladder**; reserve Claude for judgment. *(infra exists)*
4. **Per-task model choice** (Haiku/Sonnet for routine, Opus for judgment, Fable only when hard).
5. **Batch the unattended routines** (50% off, stacks with caching).
6. **Tighten the recurring-routine prompts** to delta-since-last-run.

None of this touches the product or the honesty rule. It's pure operating-cost and friction
reduction on the machine that runs the machine.

---

*Sources: authoritative Claude API reference (skill `claude-api`, cached 2026-06-04) for pricing,
caching economics, Batch API, effort/thinking, metering change; web sweep 2026-06-18 (Anthropic
release notes / Releasebot, LiteLLM auto-routing docs, hybrid-architecture and token-optimization
write-ups). Blog claims cross-checked against the reference; the "5-min TTL raised costs" claim is
corrected above.*
