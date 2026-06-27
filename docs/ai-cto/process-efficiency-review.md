# AI Process Efficiency Review — Cutting Token Spend Between User & AI

*Standing review. Newest entry at the top (house style). Each entry dated; recommendations
carry an ID (`PE-NN`) so we can track them like tech debt.*

This file answers a recurring founder question: **where are we wasting tokens (and money) in
how we work with the AI, and what's the better way?** It covers the Claude Code / Claude API
side, our own local-LLM hybrid, prompting, and the meta-question of how we *ask*.

The single highest-leverage fact, up front: **prompt caching cuts repeat-context cost by ~90%,
and our session-start context load is the biggest single thing we re-send.** Fix the context
load and turn on caching everywhere and most of the win is banked.

---

## 2026-06-27 — First full review

### TL;DR (do these five things)

1. **PE-01 — Stop force-loading 524 KB of ai-cto/ai-cfo docs at every session start.** This is
   the biggest, cheapest win. (~150K tokens before we type a word.)
2. **PE-02 — Trim & tier the CLAUDE.md files** (58 KB combined today, all loaded every session).
3. **PE-03 — Actually route to the local LLM we already built.** Odin/LiteLLM/Ollama exist and
   sit idle; free local models should do the cheap work, Claude the hard work.
4. **PE-04 — Use the cheapest model that clears the bar** (Haiku 4.5 for mechanical tasks,
   Sonnet for mid, Opus for hard) and lean on prompt caching for everything API-side.
5. **PE-05 — Tighten how we *ask*** (scope tightly, one task per session, `/clear` between
   tasks). Includes a critique of the prompt that triggered this review.

Costs today are tiny (we're pre-customer, AI budget < $15/mo, `ANTHROPIC_API_KEY=CHANGE_ME`
keeps cloud-overflow fail-closed). **The point of doing this now is habit and scale, not this
month's bill** — every one of these gets 10–100× more valuable once we're running statements
for real households and the cloud key is live.

---

### The picture today

| What | Measured | Why it matters |
| ---- | -------- | -------------- |
| Combined `CLAUDE.md` (6 repos) | **58 KB / ~1,040 lines** | Loaded into context every session for the repos touched |
| `docs/ai-cto/` | **192 KB** (incl. 18 review logs ~110 KB) | DESIGN `CLAUDE.md` §5 tells the AI to read these at session start |
| `docs/ai-cfo/` | **332 KB** (incl. 22 review logs ~290 KB) | DESIGN `CLAUDE.md` §6 tells the AI to read these at session start |
| **Session-start fixed cost (DESIGN repo)** | **~524 KB ≈ 130–160K tokens** | Re-paid on every fresh session before any work begins |
| Hybrid LLM stack (Odin/LiteLLM/Ollama) | Built, **idle** | Free local capacity we're not routing to |
| Claude Code prompt caching | On by default | Already saving us money on long sessions — keep it that way |

The CLAUDE.md files are lean and well-written; they are **not** the problem. The problem is the
**session-start reading instruction** that pulls in half a megabyte of decision logs and daily
reviews — most of which is historical and irrelevant to any given task.

---

### PE-01 — Stop force-loading the full ai-cto/ai-cfo corpus at session start *(P1, biggest win)*

**Today:** DESIGN `CLAUDE.md` §5 and §6 instruct the AI to read 4–6 files each at the start of
every session — in practice ~524 KB across `portfolio.md`, `decisions.md`, `metrics.md` (25 KB
alone), `runway.md`, `budget.md`, and the `reviews/` archives. The review archives grow forever
(40 logs already); this cost only goes up.

**Why it's wasteful:** Most sessions touch one stage or one decision. The Q1 review from three
weeks ago is dead weight in the context window for a task about the booking form. We pay for it
in tokens *and* in attention dilution (more irrelevant context = worse answers).

**Fix (cheap, do first):**
- Replace the "read all of these" instruction with **two tiny always-read pointers**:
  `docs/ai-cto/context.md` and `docs/ai-cfo/context.md` — a hand-maintained **one-page** current
  state (open items, active priorities, phase gate). The other CLAUDE.md files already point at a
  `context.md` that doesn't exist yet for ai-cto/ai-cfo — create it and make it the only required
  read. (localDNS/MARKETING already use this pattern; DESIGN is the outlier.)
- Make the heavy files **read-on-demand**: "Read `metrics.md` / `decisions.md` / a specific review
  *only when the task touches finances / a past decision*." The AI can open them when needed.
- **Cap or archive the review logs.** Keep the last ~7 days hot; move older ones to
  `reviews/archive/` that's never auto-read. A daily review nobody re-reads is a sunk file, not
  context.

**Expected effect:** session-start fixed cost drops from ~130–160K tokens to <10K. Biggest single
lever in this document.

---

### PE-02 — Trim and tier the CLAUDE.md files *(P2)*

The 58 KB is reasonable, but two cuts help:
- The **full "House style: ordering & typography" block is duplicated verbatim in all 6 repos**
  (~1.3 KB each, ~8 KB total, re-paid per repo per session). Options: (a) keep the rule, shrink
  to a 3-line summary + link to one canonical copy; (b) accept it — it's small. Low priority but
  free.
- localDNS (20 KB) and DESIGN (18 KB) carry deep reference tables (deploy paths, the full Odin
  roster, known-issues) that belong in README/network-context and could be **linked, not inlined**
  in CLAUDE.md. CLAUDE.md should be the briefing; the AI reads the deep table when it needs it.

Rule of thumb from current best practice: *CLAUDE.md is paid on every turn of every session —
keep it to high-impact rules, push reference material one click away.*

---

### PE-03 — Route to the local LLM we already own *(P1, strategic)*

We built a genuinely good hybrid: **Odin** (LangGraph supervisor) + **LiteLLM router** (`:4040`)
+ **Ollama** on the t630, with a privacy guard (Heimdall), a reasoning ladder, and an on-demand
rented-GPU tier for heavy DeepSeek-R1. It is **sitting idle** while all our actual AI work goes
to Claude.

The asymmetry to exploit: **local tokens are free** (electricity only); **Claude tokens cost
money.** The whole point of the hybrid is to spend Claude only where it earns its keep.

**Concretely:**
- Point routine, low-sensitivity, low-stakes generation at **`local-fast` (qwen2.5:3b)** or
  **`local-smart` (qwen2.5:7b)**: draft commit messages, summarize a log, first-pass classify a
  lead, rough-draft customer copy for human edit. These do not need a frontier model.
- Keep **Claude (via the API / Claude Code)** for what actually needs it: code changes across the
  repos, statement-generation logic, architecture decisions, anything customer-facing that ships.
- The split decision should be **cost/stakes**, not vibes: if a mistake is cheap to catch and the
  task is mechanical → local. If it ships to a household or touches money → Claude.
- **Watch the privacy fallback gap first.** This is already logged as **TD-14**: a `sensitive`
  task can fail over from `local-reason` to `cloud-overflow` (Claude cloud) because `allow_cloud`
  isn't enforced at the LiteLLM failover layer. Fix TD-14 (local-only fallback chains, fail
  closed) **before** we lean on local routing for anything sensitive — otherwise "route private
  stuff local" silently leaks to the cloud when the local model hiccups.

This is the "leverage other AI / run a hybrid" answer the founder asked for: **we don't need to
build anything — we need to *use* what's built**, behind a guard that's known-broken until TD-14
lands.

---

### PE-04 — Cheapest-model-that-clears-the-bar + caching everywhere *(P1, API-side)*

When work does go to Claude:

**Model tiering** (current IDs / list prices, per the Claude API reference, 2026-06):
| Model | $ / 1M in | $ / 1M out | Use for |
| ----- | --------- | ---------- | ------- |
| Claude Haiku 4.5 | $1.00 | $5.00 | Classification, extraction, short rote tasks |
| Claude Sonnet 4.6 | $3.00 | $15.00 | High-volume production, summaries, mid coding |
| Claude Opus 4.8 | $5.00 | $25.00 | Hard reasoning, multi-repo changes, architecture |

Haiku is **5× cheaper in / 5× cheaper out** than Opus. A lead-classifier or "is this paid?" check
should never call Opus. Our `config.yaml` already lists the cheaper IDs as drop-in swaps for the
overflow tier — use them.

**Prompt caching — the single highest-ROI change for any direct API integration:**
- Cache reads cost **~0.1×** normal input; a cached prefix that's read back even twice already
  pays for its write. Steady traffic keeps a hot prefix alive (5-min TTL, refreshed on each read).
- Claude Code **already does this for us** — it's why long sessions get cheaper, not more
  expensive. Don't fight it: keep stable content (the CLAUDE.md, the briefing) early and constant;
  don't inject timestamps/UUIDs into anything that sits at the front of context (those silently
  bust the cache).
- **Where we'd gain new ground:** the **langgraph-router / Odin** code path, when we eventually
  point it at the Claude API, should set `cache_control` on its stable system prompt + tool list.
  It almost certainly doesn't today. Add it before that path carries real volume.
- **Batch API** gives a flat **50%** off for anything non-latency-sensitive (e.g. a nightly
  classify-all-new-leads job). Stack it with caching.

**Right-size `max_tokens`** so we don't pay for runaway output, and prefer **streaming** for long
outputs (avoids timeouts, no cost change).

---

### PE-05 — How we *ask* (and a critique of the prompt that triggered this) *(P2)*

Workflow habits that cut tokens with no tooling change:
- **One task per session; `/clear` between tasks.** Stale context from the last task is paid for
  on every turn of the next one. A fresh session is cheaper *and* sharper.
- **Scope tightly.** "Refactor the booking form's validation in `03-funnels-and-capture/`" beats
  "improve the funnel" — less context pulled in, fewer wrong turns, fewer correction round-trips
  (the most expensive tokens are the ones spent undoing a misread).
- **Be concrete about the deliverable** ("commit + push to branch X" / "just answer, don't edit")
  so the AI doesn't do expensive work you'll throw away.
- **Let the cache work:** don't paste the same big context in by hand each time — put durable
  context in a file the AI reads, so it caches.

**Critique of the founder prompt that kicked off this review** (requested explicitly):

> *"Locate inefficiencies in our PROCESS… Is there a better way… better prompting… Anything you
> could possibly think of. Leveraging other AI. Running a hybrid… ANYTHING that could help. Search
> the web… Keep UP TO DATE… Check the news. Thanks!"*

It is a *good* brief in spirit (clear goal, names the hybrid angle, asks for current info) but
inefficient in three ways:
1. **Unbounded scope ("ANYTHING", "Anything you could possibly think of").** Invites a sprawling
   answer and lots of exploratory tokens. Better: name the 2–3 axes you care most about (cost?
   speed? quality?) and a rough depth ("one page, top 5").
2. **No success criterion / deliverable named.** "Locate inefficiencies" — into what? A doc? A
   notification? A PR? Stating the artifact up front avoids guessed-wrong work. (This review
   resolved it by writing a durable doc + a notification.)
3. **Standing intent buried in a one-off.** "Keep UP TO DATE… day by day… check the news" is a
   *recurring* want stated inside a single prompt. The efficient form is a **scheduled routine**
   (which this run is) or a saved prompt — not re-typing the ask. Consider a monthly "refresh this
   review" loop rather than re-briefing from scratch.

A tighter version of the same ask: *"Once a month, review our AI process for token/cost waste —
focus on the session-start context load and whether we're using the local LLM. Append findings to
`process-efficiency-review.md` (newest first) and notify me only if something changed materially."*

---

### What I deliberately did **not** recommend

- **Don't build new orchestration.** Odin is already more than we need; the gap is usage and the
  TD-14 guard, not features. "Liquidity before app, trust before tech" applies to our own tooling
  too.
- **Don't chase this month's bill.** We're under budget with the cloud key off. These changes are
  about **habits that scale** — they pay off at 10+ households, not at zero.

### Suggested follow-ups (for the tech-debt log)
- PE-01 → new TD item: "DESIGN session-start reading instruction loads ~524 KB; replace with
  one-page `context.md` + read-on-demand."
- PE-03 is gated on **TD-14** (privacy fallback) — sequence it after.
- PE-04 (caching on the langgraph-router Claude path) → new TD item when that path goes live.
