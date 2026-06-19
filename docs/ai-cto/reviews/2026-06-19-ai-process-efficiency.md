# AI process efficiency review — user↔AI loop, token spend, hybrid routing

**Date:** 2026-06-19 · **By:** NARF (AI CTO), scheduled routine
**Ask:** Find inefficiencies in *how we work with the AI* — token use, prompting,
leveraging other/local AI, the local-LLM↔Claude hybrid. Keep it current (web-checked
2026-06-19). Critique the requesting prompt too.

**One-line verdict:** The architecture is good; the *waste is in the standing context we
reload every session and in running everything on the top model.* Biggest single dollar
lever is trimming the always-on CLAUDE.md/session-start load and tiering the model to the
task. Biggest **risk** lever (unrelated to cost) is the still-open TD-14 privacy fallback.

---

## 0. TL;DR — do these, in order

| # | Action | Effort | Payoff |
| - | ------ | ------ | ------ |
| 1 | **Tier the model to the task.** Run monitoring/triage/doc-lint routines (like this one) on **Haiku 4.5 ($1/$5)** or **Sonnet 4.6 ($3/$15)**, reserve **Opus 4.8 ($5/$25)** for genuine design/architecture. | 5 min | 5–25× cheaper per routine run |
| 2 | **Cut the always-on context.** Trim each `CLAUDE.md` to a true briefing; push detail into READMEs read on demand. De-duplicate the house-style block (see §2). | 1–2 hr | ~30–50% off the fixed per-session token floor |
| 3 | **Make session-start reads conditional, not mandatory.** The ZORT block alone mandates 6 file reads before any work. Read the hub; read spokes only when touched. | 30 min | Removes a guaranteed multi-file read every session |
| 4 | **Close TD-14** (privacy fail-open in `config.yaml`). 3-line edit, flagged 3 review cycles running. Not a cost item — a correctness/trust item. | 5 min | Stops a sensitive prompt leaking to Claude cloud on local outage |
| 5 | **Deploy the local router** so cheap/sensitive work actually runs local instead of on the Claude API. It's built but **not deployed** — so today we pay cloud for work the t630 could do free. | 1 t630 session | Moves the 70% "easy" traffic off per-token billing |
| 6 | **Use the Batch API for non-interactive routines** (monthly statement copy, recaps, this review). 50% off, results within 24h. | per-job | Half price on everything that isn't a live conversation |

---

## 1. Critique of the requesting prompt (you asked)

The prompt was effective at *intent* but expensive by construction. Specifics:

- **"ANYTHING that could help… anything you could possibly think of"** is an unbounded
  scope. Open scope = the model fans out wide, reads broadly, and bills for exploration
  that may not land. A scoped ask ("cut our monthly Claude spend 30%; give me the 5
  highest-leverage changes ranked by effort") gets the same answer for a fraction of the
  tokens.
- **No deliverable shape.** Without "write a ranked table to `docs/…`" the model has to
  guess the format. State the artifact and where it goes.
- **No budget / depth cap.** "Keep up to date, check the news, search the web" with no
  limit invites many searches. "Up to 4 web searches, last 60 days" bounds it.
- **Two unrelated jobs in one prompt** (analyze the process *and* critique the prompt).
  Fine here, but in general one prompt = one objective caches and re-runs better.
- **It's a great fit for a cheaper model.** This is research + synthesis, not deep
  architecture — Sonnet would have produced ~the same report at ~⅕ the cost.

**Reusable template:**
> *Goal:* [one sentence + a metric]. *Scope:* [files/dirs in bounds]. *Deliverable:*
> [artifact + path]. *Budget:* [≤N searches / ≤N tool calls]. *Model:* [tier]. *Done when:*
> [check].

A 60-word scoped prompt routinely beats a 200-word open one on both cost *and* answer quality.

---

## 2. The standing-context tax (our biggest fixable cost)

Every session pays for context *before the first instruction*. Measured today:

- **~10.5k tokens** of `CLAUDE.md` across the six repo briefings (DESIGN 2.6k words,
  localDNS 2.7k words are the heavy two). In a multi-repo web session these load together.
- The **house-style block (~310 words) is duplicated verbatim in 6 of 7 CLAUDE.md files** —
  ~1,900 words / ~2,400 tokens of pure duplication, re-read every session, forever.
- The session-start ritual then *mandates* more reads: NARF wants portfolio + spoke
  context; **ZORT mandates 6 files** (portfolio, decisions, metrics, runway, budget, plus
  the MARKETING spoke). That's a guaranteed read fan-out before any actual task.

This is the cost that scales with *every* session, so it's the one worth cutting first.

**Fixes:**
1. **CLAUDE.md = briefing, not manual.** Cap each at the ~1-screen essentials + links.
   Detail belongs in README/context docs that get read *on demand*. (localDNS already does
   this well in spirit — the file just grew.)
2. **De-duplicate house style.** Keep the full block in *one* canonical file
   (`DESIGN/docs/house-style.md`); each CLAUDE.md keeps a 2-line pointer + the 3 rules
   actually used while editing. Saves the duplication tax on every session.
3. **Make session-start reads conditional.** "Read the hub portfolio; read a spoke's
   context only when you touch that spoke." Drop the blanket 6-file ZORT read into "read X
   when doing finance work."
4. **Prefer `/clear` between unrelated jobs** and `/recap` (Apr 2026) on resume rather than
   replaying history — both shrink the live prefix.

---

## 3. Token mechanics — current best practice (web-checked 2026-06-19)

The cheapest call is the one you don't make; after that it's caching + the right model.

- **Prompt caching: ~90% off repeated input.** Cache reads cost 0.1× base input; writes
  1.25×. Our large, stable CLAUDE.md prefix is *ideal* cache material — but caches are
  isolated per workspace (since 2026-02-05) and evaporate when the prefix churns. So: keep
  the standing context **stable and front-loaded** (don't edit CLAUDE.md mid-session) to
  keep cache hits; trimming it (§2) compounds the win.
- **Batch API: exactly 50% off**, async, ≤24h. Use it for everything non-interactive:
  monthly statement copy generation, these daily reviews, bulk recaps. A scheduled routine
  that doesn't need a live answer should almost never pay full price.
- **Model tiering** (the single biggest knob): Haiku 4.5 **$1/$5**, Sonnet 4.6 **$3/$15**,
  Opus 4.8 **$5/$25**. Industry data shows ~60–86% cost reduction routing the easy ~70% of
  traffic to small models with minimal quality loss. Most of our routine/monitoring/lint
  work is "easy."
- **Subagents** isolate big search/read output in a child context so the parent prefix
  stays small (reported 55–65% reduction on heavy workflows). Good for "go read 20 files
  and tell me the conclusion" — which the hub-and-spoke review pattern does a lot.
- **Scope the task** ("fix the login fn in auth.ts," not "refactor auth") — smaller scope,
  fewer tokens, more focused output.

---

## 4. The hybrid (local LLM ↔ Claude) — we're ahead, but it's not switched on

We already have what most teams are still drawing on whiteboards: a **LiteLLM front door,
Ollama local tiers, a deterministic privacy-gated dispatcher, a reasoning ladder, and a
cloud failover** (`localDNS/10-ai-orchestration/`). The 2026 "hybrid architecture guide"
canon (LiteLLM gateway + Ollama + Claude cloud + classify-by-sensitivity/complexity/
availability) is *exactly* our blueprint. So the design is validated by the field.

**The gap is execution, not architecture:**

1. **It isn't deployed** (portfolio: reference code, not running). Until it is, every "easy"
   or "sensitive" turn that *could* run on the t630 is instead billed on the Claude API.
   The cheapest token is the local one. Deploying the router is the structural cost win
   that §0–§3 only approximate.
2. **TD-14 — privacy fail-open — is still live.** Confirmed today at `config.yaml:108`:
   ```
   - local-reason: ["cloud-gpu-reason", "cloud-overflow"]
   ```
   A `sensitive` task whose local model is down falls **through to Claude cloud** — the
   opposite of what three comments in the file promise (the guarantee lives only in the
   un-deployed LangGraph gate). The fix is 3 lines: chain `local-reason` to local-only
   (`["local-smart","local-fast"]`) and remove `cloud-overflow` from any chain a sensitive
   task can reach. **A false privacy claim is worse than no claim.** This has been the top
   actionable for 3 review cycles; it needs no box access. *(Note: localDNS is push-to-main;
   this routine is scoped to a feature branch, so I'm flagging rather than committing the
   localDNS edit — land it on main next localDNS touch.)*
3. **Once deployed + TD-14 closed,** the routing target is the standard tiered split:
   ~70% easy → local Qwen/Haiku, ~20% medium → Sonnet/Haiku, ~10% hard → Opus, with
   *sensitive* pinned local-only and failing closed. That's the 60–80% saving the field
   reports, and it's a config-table change, not new engineering.

---

## 5. What's new since our last look (the "check the news" part)

- **Opus 4.8** (2026-05-28) is the current top general model at **$5/$25**; Fast Mode
  dropped to **$10/$50** (was $30/$150 on 4.7) — Fast Mode is now far less of a penalty.
- **Fable 5** is GA as a new top tier as of June 2026 (Mythos 5 limited-preview above it).
  Worth evaluating *only* for tasks where Opus is genuinely capacity-bound — not for routine
  ops, where the move is *down* the ladder, not up.
- **Sonnet 4.6 / Opus 4.8 carry 1M context at flat rate, no long-context surcharge** — so
  the old "split the job to dodge the 200k surcharge" tactic is obsolete; just don't *fill*
  the window with stale context (that's a cache + speed cost, not a surcharge).
- **Server-side compaction** (beta, `compact-2026-01-12`) condenses history at the window
  edge so long sessions continue — complements `/clear` and `/recap`.

These move fast; re-check model IDs/prices at build time against the API's `/v1/models`.

---

## 6. Net

The thinking is sound and, on the hybrid front, ahead of the field's published best
practice. The money is leaking in two ordinary places: **(a)** we reload a large, partly
duplicated standing context every session, and **(b)** we run everything on the top model
including jobs a small one would ace. Fix those two and deploy the router we already built,
and the spend drops without touching answer quality. The one item that isn't about money —
TD-14 — should be closed regardless, because it's a trust claim we're currently not keeping.

**Sources:** Anthropic prompt-caching & pricing docs; Claude Code cost docs; SitePoint
*Hybrid Cloud-Local LLM Architecture Guide 2026*; MindStudio *Run Local Models with Claude
Code*; Finout/DevTk Anthropic pricing 2026; MarkTechPost *Claude Code 2026 features*;
KDnuggets/Firecrawl/Agensi token-reduction guides. (Web-checked 2026-06-19.)
