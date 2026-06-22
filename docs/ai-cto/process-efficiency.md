# Process efficiency review — user ↔ AI workflow

_Review date: 2026-06-22 · Owner: NARF (AI CTO) · Status: recommendations, not yet adopted_

How we spend tokens and attention working with Claude across the A777ance repos, where
that spend is wasteful, and what to change. Grounded in the actual repos (measured
CLAUDE.md sizes, the live LiteLLM ladder) and current best practice as of June 2026.
Leads with the highest-leverage finding.

---

## TL;DR — the five changes that matter

1. **Trim the CLAUDE.md files.** They total **~8,030 words (~11K tokens)** across six repos
   and *all load on every turn of a portfolio session* — before anyone types a word. This is
   the single biggest standing cost. Target: cut each to a ~400–600 word "always-on" core and
   push the rest into `@import`ed or on-demand files. **Est. saving: 60–75% of standing input.**
2. **Fix the model ladder.** Today `cloud-overflow`, `cloud-explore`, and `cloud-vision` in
   `localDNS/10-ai-orchestration/config.yaml` *all* point at **Opus 4.8** ($5/$25). The
   industry-validated split is ~70% Haiku / 20% Sonnet / 8% Opus / 2% Fable — cutting cost
   60–70% with no meaningful quality loss. We are massively Opus-weighted.
3. **Actually route the cheap work to the local ladder you already built.** `local-fast`
   (qwen2.5:3b) and `local-reason` (deepseek-r1:1.5b) exist but mostly serve Open WebUI.
   Classification, link-checking, draft-summarizing, commit-message drafting, routine
   roster lint → local LLM at ~$0. Escalate to Claude only on the hard part.
4. **Lean on prompt caching — and stop breaking it.** Caching is automatic now (no
   `cache_control` markers needed); reads cost ~10% of input. We negate it by switching
   models mid-task and editing CLAUDE.md as a scratchpad. Keep the stable prefix stable.
5. **Tighten the prompts (including the one that triggered this review).** Scope, a target
   metric, and a named output location turn an open-ended "look at everything" into a
   bounded job — fewer tokens, better answers.

---

## 1. The standing cost: CLAUDE.md and multi-repo context

Measured today:

| Repo | CLAUDE.md words | ≈ tokens |
| ---- | ---------------:| --------:|
| localDNS | 2,728 | ~3,640 |
| DESIGN-… | 2,608 | ~3,480 |
| MARKETING | 1,445 | ~1,930 |
| customers | 562 | ~750 |
| claude-code-homelab | 371 | ~495 |
| Azure-lab | 316 | ~420 |
| **Total** | **8,030** | **~10,700** |

A CLAUDE.md is re-sent as input on **every** message in a session. In a cross-repo
"portfolio" session (NARF/ZORT do this daily), several of these load at once. At ~50 turns
that is hundreds of thousands of input tokens spent on instructions, much of it never
relevant to the turn at hand. Prompt caching softens this (reads ≈10% of input) — but only
while the prefix is stable, and the cache still has to be written first.

**What to do:**
- Split each CLAUDE.md into a short *always-on core* (the rules that change behaviour every
  turn: voice rule, push-to-main vs branch, secrets rule, house style) and *reference detail*
  (deploy-path tables, the full stage map, known-issues) that Claude can open when needed.
  Claude Code supports `@path` imports — the core stays loaded; the detail is pulled on demand.
- The house-style block is duplicated nearly verbatim in all six files. Put it in **one**
  file and `@import` it. ~150 words × 6 = ~900 words of pure duplication today.
- Don't use CLAUDE.md as a scratchpad mid-session — every edit invalidates the cache prefix.

## 2. The model ladder is Opus-heavy

From `localDNS/10-ai-orchestration/config.yaml`:

| Alias | Currently maps to | Should probably be |
| ----- | ----------------- | ------------------ |
| `cloud-overflow` | `claude-opus-4-8` | `claude-haiku-4-5` (it's a *fallback*, not the main tier) |
| `cloud-explore` | `claude-opus-4-8` | Opus is defensible for deep research; keep, but use sparingly |
| `cloud-vision` | `claude-opus-4-8` | `claude-sonnet-4-6` reads charts/screenshots fine at 1/5 the cost |
| `cloud-code` | `claude-sonnet-4-6` | ✅ correct — the sweet spot |

Current per-Mtok pricing: Haiku 4.5 **$1/$5**, Sonnet 4.6 **$3/$15**, Opus 4.8 **$5/$25**,
Fable 5 **$10/$50**. The validated production routing split is roughly **70% Haiku, 20%
Sonnet, 8% Opus, 2% Fable**, which cuts cost 60–70% versus all-Opus with negligible quality
loss on routine work. Reserve Opus/Fable for multi-file refactors, architecture calls, and
genuinely hard debugging — the cases where the top ~1% of capability changes the outcome.

**Also note:** Claude Code on Pro/Max moves from "free" to usage credits as of **today,
2026-06-22**, with API at $10/$50 for the top tier. Model discipline now shows up on the bill.

## 3. Use the hybrid local ladder you already own

The homelab already runs LiteLLM + Ollama (`local-fast` qwen2.5:3b, `local-smart` 7b,
`local-reason` deepseek-r1:1.5b, `local-embed` nomic-embed-text). Hybrid routing
(simple→local, hard→cloud) is documented to save **60–80%** with minimal quality impact.
We're paying Anthropic for work a 3B model on the t630 would do for free:

- **Route locally:** doc/link sanity checks (`tools/check-docs.py` triage), commit-message
  first drafts, roster.json field validation, "summarize this log", classification/labeling,
  embeddings for any repo search/RAG.
- **Escalate to Claude:** anything customer-facing (the voice rule matters), architecture,
  multi-file edits, the Statements, financial reasoning.
- **Mechanism:** LiteLLM `fallbacks` already gives local→cloud failover; add a semantic cache
  in front of the proxy to catch near-duplicate requests (15–30% volume reduction on
  classification-heavy work). Use `/usage` (now shows per-model, cache-miss, subagent, and
  per-skill/MCP breakdowns over 24h/7d) to see where the money actually goes before tuning.

## 4. Prompt caching — get the discount, keep it

- Caching is **automatic** as of early 2026 — no `cache_control` markers needed. Reads cost
  ~10% of input; writes cost 1.25×. Real agents see ~59% input-token reduction.
- Cache is **isolated per model** — switching Opus→Sonnet mid-task throws away the cache you
  paid to write. Pick the model up front.
- Keep stable content first (CLAUDE.md, tool defs, skills), volatile content last.
- Don't hot-swap MCP servers/skills mid-session; that shifts the prefix and forces a re-write.

## 5. Prompting — including this very prompt

The prompt that triggered this review (paraphrased: _"find inefficiencies in our process,
reduce tokens, better prompting, leverage other AI, hybrid local+Claude, search the web,
keep up to date, check the news, ANYTHING that could help"_) is itself a good example of an
expensive prompt:

- **Unbounded scope** ("ANYTHING", "anything you could possibly think of") invites the model
  to fan out across the web and the whole codebase — many tokens, much of it low-value.
- **No target metric** — "reduce token use" by how much, measured how? Without a number the
  model can't prioritise.
- **No output contract** — where should the answer live? A chat reply in an unattended
  routine is nearly invisible; a committed doc + a notification is not.
- **Several questions bundled** — process, tokens, prompting, hybrid AI, news — each would get
  a sharper answer asked on its own.

A leaner version that would have cost less and answered better:

> "Audit our Claude usage for token waste. Focus on (a) CLAUDE.md size and (b) the LiteLLM
> model ladder. Give me the top 5 changes ranked by $ saved, with rough estimates. Write it
> to `DESIGN/docs/ai-cto/process-efficiency.md` and notify me. Use web search only to confirm
> current pricing and the recommended model split."

**General prompting habits worth adopting:**
- State the goal, the constraints, and the definition of done up front; put scope limits in
  ("only these two files", "don't refactor").
- Ask for the conclusion/recommendation, not an exhaustive survey of options.
- One job per prompt; chain sessions rather than bundling.
- For recurring agent work (NARF/ZORT), keep a short stable system preamble and feed only the
  day's deltas — don't re-narrate the whole portfolio each run.

## 6. Quick wins checklist

- [ ] Extract the shared house-style block to one file; `@import` it into the six CLAUDE.md.
- [ ] Split each CLAUDE.md into always-on core + on-demand reference.
- [ ] Repoint `cloud-overflow`→Haiku, `cloud-vision`→Sonnet in the LiteLLM config.
- [ ] Wire local-fast/local-reason into the routine work above (doc-lint, commit drafts, roster lint).
- [ ] Add a semantic cache in front of LiteLLM for classification-heavy calls.
- [ ] Run `/usage` after one week of NARF/ZORT sessions; rebalance toward the 70/20/8/2 split.
- [ ] Adopt the leaner prompt template above for scheduled routines.

---

## Sources

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude Code Token-Saving Guide (knightli.com)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Claude Code Token Optimization (buildtolaunch)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LiteLLM Auto Routing (docs.litellm.ai)](https://docs.litellm.ai/docs/proxy/auto_routing)
- [Claude model selection — Opus vs Sonnet vs Haiku 2026 (Value Add VC)](https://valueaddvc.com/blog/claude-opus-vs-sonnet-vs-haiku-which-model-to-use-and-when-in-2026)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
- [Claude Updates by Anthropic — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude)
- [How We Cut LLM Costs by 59% With Prompt Caching (ProjectDiscovery)](https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching)
