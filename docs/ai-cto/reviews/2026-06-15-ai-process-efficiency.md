# NARF — review — 2026-06-15 — AI process efficiency (user ↔ AI)

Founder asked: find inefficiencies in **our process between the user and the AI** — token
use, prompting, leveraging other AI, a hybrid local-LLM + Claude-API setup — and to keep it
current (web-checked 2026-06-15). Also: critique the asking prompt itself.

The finding in one line: **the biggest waste isn't in any single chat — it's the fixed cost
we pay on every turn of every routine.** Everything below is ranked by that lens.

---

## Top 5, ranked by leverage

### 1. Cut the per-turn fixed cost: trim the CLAUDE.md bundle + confirm prompt caching is ON
This is #1 because it's paid on **every turn of every session, every day.** Right now the
harness injects all seven repos' `CLAUDE.md` files into context. That bundle is large (the
DESIGN + localDNS files alone are several thousand tokens each) and it rides along on every
single message — NARF, ZORT, and any web/routine session.

- **Trim CLAUDE.md to a true briefing.** The rule is already written in our own philosophy
  ("CLAUDE.md is the short briefing; README is the full guide") — but localDNS's CLAUDE.md
  has drifted into a full deploy-path table + a known-issues encyclopedia. Move the
  reference tables (deploy paths, the full known-issues list) into README and leave CLAUDE.md
  a pointer. Every token cut here is multiplied by every future turn.
- **Confirm prompt caching is active on the static prefix.** Claude Code caches the system
  prompt / CLAUDE.md by default, but it's worth verifying for these routines: a cache *read*
  is **0.1×** input price (90% off), a cache *write* is 1.25×. For a daily routine hitting
  the same 7-repo context, caching turns the bundle from a daily full-price charge into a
  one-write-then-pennies charge. If anything reorders or rewrites the prefix between runs it
  busts the cache — keep the stable stuff stable.

### 2. Right-size cadence + model + delivery for the meta-routines (NARF / ZORT / this one)
- **Cadence.** This "stay up to date on AI best practices" routine should run **weekly, not
  daily** — best practices do not change every 24h, and open-ended web research is the single
  most expensive instruction we issue. NARF/ZORT daily session-updates are also worth
  questioning: Phase 1 moves in days-to-weeks, not hours. A weekly deep pass + event-driven
  runs would cut these routines ~5–7×.
- **Model.** This session is running **Opus 4.8** ($5/$25 per M in/out). For doc analysis and
  summarization, **Sonnet 4.6 is ~5× cheaper** and fully adequate; reserve Opus for genuine
  architecture calls (e.g. the Phase-2 PWA decision). "Start on Sonnet, escalate to Opus only
  when you need deep analysis" is the documented default.
- **Delivery.** NARF/ZORT updates and this research are **non-interactive** — nobody's waiting
  on the reply. That's the textbook case for the **Batch API: a flat 50% off** input+output.
  Stacked with caching, async meta-work can drop 90%+ off its current spend.

### 3. Route deterministic + light work OFF Claude entirely
- **Deterministic work should never touch an LLM.** `tools/check-docs.py` (link/anchor
  integrity) and the `collect_stats.py` / nftables stats are plain Python — they already need
  zero tokens. Make sure no routine is "asking Claude to check the docs" when the script does
  it for free. Gate them in CI (TD-11 already wired check-docs to CI on `main`).
- **Light language work → the local ladder we already built.** The t630 runs a LiteLLM
  reasoning ladder (`10-ai-orchestration/config.yaml`): `local-reason` (deepseek-r1:1.5b,
  cool) for light work, `cloud-gpu-reason` (rented GPU) for heavy. Summarizing a log,
  classifying a lead, drafting boilerplate, first-pass "Handled For You" copy — these can run
  local for ~free, with Claude reserved for the reasoning that actually moves the needle.
  **Blocker: fix TD-14 first** — today a `sensitive`-tagged task can fail over from
  `local-reason` to `cloud-overflow` (Claude cloud). Don't widen local routing until that
  fallback fails closed.
- **The box is weak, so be realistic.** Carrizo iGPU + 16 GB can't comfortably run the 27B
  models (Qwen3.6:27b ≈ 77% SWE-bench; Qwen3-Coder-Next ≈ 70%) that now rival Sonnet. Local =
  small models for light/private tasks + the rented-GPU tier for heavy; Claude stays the
  default for hard reasoning. Since Jan 2026, Ollama/LM Studio expose a **native Anthropic
  Messages endpoint**, so pointing a tool at a local model is now two env vars and one
  `ollama pull` — no proxy. Worth a spike, not a migration.

### 4. The asking prompt is itself inefficient — here's the rewrite
The founder's prompt says, in effect, "find ANYTHING that could help, search the web, check
the news, keep up to date." That unbounded framing is *exactly* what runs up a bill: no scope
ceiling, no output contract, no cadence guard, no token budget. Three concrete fixes:

- **Bound the scope.** Name 3–5 axes and say "skip the rest," instead of "anything you can
  think of." Open-ended invites sprawl; specific decision-boundaries cut token waste sharply
  (semantic/decision-specific prompts have been shown to cut query tokens ~4× vs. generic
  instructions).
- **Set an output contract.** "≤500 words, a ranked table of findings, top 3 actions." Free
  prose with no ceiling is the default-expensive mode.
- **Guard the web + cadence.** "Run weekly. Max 5 web searches, and only if >7 days since the
  last run; otherwise reuse the prior findings doc." This kills the daily re-research loop.

Drop-in replacement:

> *Weekly, on Sonnet, via batch: review our AI process for cost/efficiency along exactly these
> axes — (1) per-turn fixed context cost, (2) model/cadence right-sizing, (3) local-vs-cloud
> routing, (4) prompt/output hygiene. Max 5 web searches, only if best-practice docs have
> moved since the last run (else cite the prior doc). Output ≤500 words: a ranked table +ICE
> top-3. Append to `docs/ai-cto/reviews/`. Notify only if a top-3 item is new.*

(Filler like "Thanks!" / "anything you could possibly think of" costs ~nothing — don't
bother; the win is structure, not word-count.)

### 5. Tactical context hygiene (small, additive)
- **Subagents for fan-out reads.** When research means sweeping many files, dispatch a
  subagent — it reads in its own window and returns only the conclusion, keeping the main
  context clean. But don't spawn them for vague work; each has its own full cost.
- **Cap tool output** (~8000 tokens) and **filter logs before Claude sees them** — feed error
  lines, not raw dumps.
- **Batch requests in one message** instead of "change this… now that… also this," and keep
  scope narrow ("the login function," not "the whole auth module").
- **Don't let threads run forever** — every new message re-reads the whole history; start a
  fresh session per task and lean on CLAUDE.md to carry the standing rules.

---

## What I'd actually do this week
1. **Trim localDNS + DESIGN CLAUDE.md** back to true briefings (move tables to README); verify
   caching on the routines. *(Highest leverage; pure win.)*
2. **Re-point the meta-routines:** weekly cadence, Sonnet, batch where non-interactive.
3. **Rewrite this routine's prompt** to the bounded version above.
4. **Fix TD-14** (fail-closed local fallback) — the prerequisite to expanding local routing.
5. Leave heavy reasoning on Claude; spike (don't commit to) local light-task routing once TD-14
   lands.

## Estimated effect
Caching + Sonnet + batch + weekly cadence on the async meta-routines compounds: each lever is
40–90% on its slice, and they stack (caching ×, model ~5×, batch 2×, cadence ~5–7×). Realistic
target: **the recurring NARF/ZORT/research spend drops by an order of magnitude** with no loss
of quality, because none of that work needed Opus, real-time delivery, or a daily beat.

---

### Sources (web-checked 2026-06-15)
- Anthropic — [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [KDnuggets — 7 Practical Ways to Reduce Claude Code Token Usage](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) · [Pairing Claude Code with Local Models](https://www.kdnuggets.com/pairing-claude-code-with-local-models)
- [Analytics Vidhya — 23 Tips for Claude Code Token Saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Finout — Anthropic API Pricing 2026 (caching, batch, optimization)](https://www.finout.io/blog/anthropic-api-pricing) · [Claude Code Pricing 2026](https://www.finout.io/blog/claude-code-pricing-2026)
- [CloudZero — Claude Code Agents 2026: subagents, teams, parallel cost](https://www.cloudzero.com/blog/claude-code-agents/) · [MindStudio — Sub-Agents Explained](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [SitePoint — Hybrid Cloud-Local LLM Architecture Guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [Shawn Mayzes — Claude Code + local LLM, no proxy (Ollama Anthropic endpoint)](https://www.shawnmayzes.com/ai-engineering/claude-code-local-llm-2026/)
- [DEV — Qwen3-Coder-Next local guide 2026](https://dev.to/sienna/qwen3-coder-next-the-complete-2026-guide-to-running-powerful-ai-coding-agents-locally-1k95)
- [CostLayer — Semantic Prompt Engineering (−74% tokens)](https://costlayer.ai/blog/semantic-prompt-engineering-reduce-ai-token-waste) · [arXiv 2511.04108 — Batch prompting suppresses overthinking](https://arxiv.org/pdf/2511.04108)
