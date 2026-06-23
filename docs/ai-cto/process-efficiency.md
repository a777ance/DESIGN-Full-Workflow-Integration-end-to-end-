# Process Efficiency — User ↔ AI Token & Workflow Audit

**Owner:** NARF (AI CTO) · **First written:** 2026-06-23 · **Cadence:** revisit monthly
(the model landscape moves weekly — see §6).

How we work *with* the AI, not what we build. The goal: the same intelligence per dollar,
fewer wasted tokens, the right model on the right task. Findings are ranked by leverage
(biggest dollar/token win first), not by date.

> **Scope note.** Our scheduled routines run on Anthropic's *cloud* infra (laptop closed).
> The t630's local LLM ladder is **LAN + WireGuard only**, so it is **not reachable from a
> cloud routine** — the hybrid-LLM play (§3) applies to *local* Claude Code and our own
> scripts, not to web routines. Keeping these two lanes straight is itself an efficiency win.

---

## 1. Findings, ranked by leverage

| # | Finding | Lever | Effort | Where |
| - | ------- | ----- | ------ | ----- |
| F1 | **The 7× duplicated "House style" block.** The ~40-line house-style section is byte-for-byte identical in all seven `CLAUDE.md` files. When a session/routine has multiple repos in scope (this one had all 7), that block is injected **once per repo, every turn** — ~3–4K tokens of pure duplication on *every* turn of *every* run. | Single biggest no-brainer. De-duplicate. | Low | All repos |
| F2 | **`CLAUDE.md` files exceed the 200-line guideline.** Best practice (2026): keep `CLAUDE.md` < ~200 lines because it's a fixed tax on every request. DESIGN's is ~250+, localDNS's ~250+. Across a multi-repo routine the combined injection is ~12–15K tokens *before any work starts*. | Trim to a lean core + link out. | Med | DESIGN, localDNS, MARKETING |
| F3 | **Routines run on Opus 4.8 — the most expensive tier — for triage-grade work.** This audit ran on Opus ($5/$25 per 1M). Link-checking, doc-drift, CHANGELOG/format checks, issue triage are Haiku-grade ($1/$5) → up to **5× cheaper output**. | Match model to task (§4). | Low | Routine config |
| F4 | **Heavy fixed session-start reads.** NARF reads 4 files at start; ZORT reads 6. Good for continuity, but it's a fixed per-session cost that's mostly cache-friendly *if* kept byte-stable (§5). | Consolidate + lean on caching. | Med | DESIGN hub |
| F5 | **Open-ended routine prompts maximize cost.** "Locate inefficiencies in ANYTHING / anything you could think of" forces broad exploration + long output — the opposite of token-thrift. Scoped prompts cost a fraction. | Scope each routine (§7). | Low | Prompts |
| F6 | **MCP tool overhead — already mostly handled here.** This environment uses **Tool Search / deferred tools** (GitHub schemas load on demand), the optimized pattern (one reported workflow: 51K→8.5K tokens of MCP overhead). If you run Claude Code *locally* with all ~50 GitHub MCP tools eagerly loaded, you lose that — enable tool-search/deferred loading there too. | Keep deferred loading on everywhere. | Low | Local CC config |
| F7 | **`[1m]` context premium.** We're on `claude-opus-4-8[1m]`. Long-context (>200K) pricing typically carries a premium. Routines here use a tiny fraction of that — the 1M variant buys nothing for them and may bill at premium rates. | Use the standard-window model for routines. | Low | Routine config |

---

## 2. The token tax, concretely

A fresh turn sends ~20K tokens; a long session re-sends the whole transcript every turn, so
cost grows **geometrically** with session length. Two implications for us:

- **Reset between unrelated tasks.** Don't let one long session sprawl across repos —
  start fresh; a 200-turn session sends ~200K/turn.
- **The fixed prefix (CLAUDE.md + session-start reads) is paid on every turn.** That's why
  F1/F2 matter: a 5K-token `CLAUDE.md` is a 5K tax × every turn × every run. Trimming the
  prefix is the highest-frequency saving we have.

---

## 3. Hybrid local + cloud (we already own the hard part)

The t630 already runs a LiteLLM reasoning ladder (`local-fast`/`local-reason` →
`cloud-gpu-reason` → `cloud-overflow`). Industry split for 2026: **~60–70% of requests are
simple** (classify/extract/format), ~20–30% moderate, **~10% need a frontier model**. The
win is routing the cheap bulk to local, reserving Claude API for real reasoning — reports of
~88% cost reduction with Ollama + LiteLLM.

**For us, specifically:**
- **Use it for local Claude Code + our own scripts**, not web routines (see scope note up
  top — the box isn't reachable from the cloud).
- **Candidate local jobs:** commit-message drafting, doc-drift/link-check summarization,
  CHANGELOG formatting, lead/issue triage classification, "is this section honest per the
  data" pre-screens.
- **⚠️ Tie to TD-14 first.** The privacy ladder must **fail closed** before we lean on it
  for anything `sensitive` — a `sensitive` task that falls over to `cloud-overflow` (Claude
  cloud) when the local model is down breaks the privacy promise. Fix TD-14, *then* expand
  local routing. Don't trade tokens for a false privacy claim.
- **Add semantic caching** at the LiteLLM layer — catches near-duplicate requests, cuts
  volume 15–30% on classification-heavy work.
- **Diminishing returns:** aim for ~70–80% of theoretical savings; the last 20% costs more
  in UX/reliability than it saves.

---

## 4. Right model on the right task (current prices)

| Model | $ / 1M in–out | Use for |
| ----- | ------------- | ------- |
| Haiku 4.5 | $1 / $5 | Triage, link/doc-drift checks, formatting, classification, the daily news-delta (§6) |
| Sonnet 4.6 | $3 / $15 | Most coding & content work, statement-copy edits |
| Opus 4.8 | $5 / $25 | Hard architecture, cross-repo reasoning, this monthly audit |

- **Fable 5 / Mythos 5:** released 2026-06-09, **access suspended 2026-06-12** — do **not**
  migrate routines to them right now; revisit when GA is restored. They also price higher
  ($10/$50), so they're a capability call, not a cost one.
- **Batch API = 50% off** for anything non-interactive (e.g. a nightly bulk pass). Worth it
  the moment we have >1 statement to generate per run.

---

## 5. Prompt caching — our best single lever for routines

Anthropic caches the static prefix at **−90% on cache reads** (write costs +25% once, then
every reread is near-free); cache TTL 5 min default, 1 hr configurable. Routines that
re-inject the *same* `CLAUDE.md` + portfolio every run are the textbook case.

**What we control:** keep the cached prefix **byte-identical** run-to-run. That means:
- No timestamps / "last updated" lines *inside* the cached region (put volatile status in a
  small tail block, not the top of `CLAUDE.md`).
- Stable ordering of the session-start reads.
- This also makes F4's fixed reads cheap — a stable prefix is a cached prefix.

---

## 6. Keeping current (the "check the news" ask, done cheaply)

The model/pricing landscape genuinely shifts week to week (Fable 5's 3-day life is the proof).
But a daily *Opus* web-search routine is an expensive way to learn that. Recommended split:

- **Monthly (Opus):** this full audit — re-rank findings, refresh prices, re-read best practice.
- **Weekly or daily (Haiku, scoped):** a thin "what changed in Claude model/pricing/Claude
  Code since <date>?" delta — only escalate to a human/Opus if something material moved.

Notable as of 2026-06-23: Opus 4.8 = $5/$25, Sonnet 4.6 = $3/$15, Haiku 4.5 = $1/$5; Fable 5
GA then suspended (see §4); Tool Search cuts MCP overhead ~47%; prompt caching −90% on reads.

---

## 7. On the prompt that triggered this audit

Asked to self-assess: **yes, the trigger prompt is itself inefficient** — and instructively so.

- **Unbounded scope.** "ANYTHING that could help / anything you could possibly think of"
  forces wide exploration and long output. A scoped prompt — *"Audit our CLAUDE.md token
  footprint across all repos and propose specific cuts"* — buys sharper output for a fraction
  of the tokens.
- **Bundled asks.** Token use + prompting + hybrid LLM + news + self-critique are five
  routines in a trench coat. Fine as a periodic deep audit; wasteful as a daily one. Split by
  cadence and model (§6).
- **No success criterion.** Add one ("rank by $ saved; cap at the top 5") so the run knows
  when it's done instead of exploring until it runs out.
- **Politeness ("Thanks!", "Perhaps also") costs ~nothing** — not worth changing. The cost is
  scope and cadence, not tone.

**Template for a leaner version:**
> *"Monthly: audit user↔AI token efficiency across the portfolio. Rank the top 5 findings by
> estimated $ saved, with the concrete edit for each. Use current model prices; flag only
> model/pricing news that changed since last run. Stop at 5."*

---

## 8. Recommended actions (do these, in order)

1. **F1 — De-duplicate house style.** Move the canonical block to one file (e.g.
   `DESIGN/docs/house-style.md`); replace the copy in each `CLAUDE.md` with a one-line link.
   *(Confirm with CEO: house style is a cross-repo standard — change touches all 7.)*
2. **F2 — Trim each `CLAUDE.md`** toward < 200 lines: keep the briefing + links, push detail
   into the README/context files already linked.
3. **F3/F7 — Re-tier routines:** move triage/check-style routines to **Haiku**, standard
   context window; keep Opus for the monthly audit only.
4. **F5 — Rescope the prompts** per §7; split the "news" ask into a cheap weekly delta (§6).
5. **F4/F5 — Caching hygiene:** pull volatile timestamps out of the top of `CLAUDE.md` and
   portfolio files so the cached prefix stays byte-stable.
6. **Hybrid (§3): close TD-14 first**, then route the cheap local-eligible jobs to the t630
   ladder for *local* CC sessions; add LiteLLM semantic caching.

None of these touch the product or the honesty rule; they only make the machine that builds it
cheaper to run.

---

## Sources

- [Reduce Claude Code token usage — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code token optimization — buildtolaunch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt caching deep dive — agentbrisk](https://agentbrisk.com/blog/prompt-caching-deep-dive-2026/)
- [Hybrid cloud-local LLM architecture — sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM gateways & model routing — lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [Claude API pricing 2026 — cloudzero](https://www.cloudzero.com/blog/claude-api-pricing/)
- [Models overview — Claude API docs](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Introducing routines in Claude Code](https://claude.com/blog/introducing-routines-in-claude-code)
- [Claude Code routines practical guide — nimbalyst](https://nimbalyst.com/blog/claude-code-routines-practical-guide/)
