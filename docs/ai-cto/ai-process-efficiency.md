# AI Process Efficiency — token/cost review

NARF (AI CTO) review of *how A777ance uses AI*, not what it builds: where the
user↔AI loop and the LLM router waste tokens/dollars, and what to change. Findings
are tailored to our actual setup (Odin/LiteLLM ladder, NARF/ZORT daily runs,
template-based statements). External best-practice sources are linked inline.

**Last reviewed:** 2026-06-15. **Re-run cadence:** every ~90 days — API rate cards and
local-hardware economics both move fast; the consensus across sources is "re-run this
analysis every six months" at the outside. Newest review notes go at the top.

---

## TL;DR — do these first

1. **React to the June 15, 2026 Anthropic billing split (today).** Headless/automated
   runs — Agent SDK, `claude -p`, Claude Code GitHub Actions, scheduled routines — no
   longer draw from a Claude subscription. They bill from a **separate monthly credit**
   ($20 Pro / $100 Max-5x / $200 Max-20x) **at full API list rates, no subscription
   discount, no roll-over**. NARF + ZORT daily runs and any scheduled routine are exactly
   this category. **Action:** claim the credit (one-time), and treat automated AI spend as
   metered API again — which makes the next two items pay for themselves immediately.
2. **Turn on Batch API for every non-interactive run.** NARF/ZORT daily updates and
   statement prose are not latency-sensitive (24h window is fine) → **flat 50% off all
   tokens, every model.** Lowest-effort, highest-certainty win we have.
3. **Turn on prompt caching for the stable prefixes.** Our portfolio hub, CLAUDE.md
   files, and decision logs are re-read on every NARF/ZORT run. Cache reads cost **0.1x**
   (90% off) and break even after a single hit. Batch + caching stack to **~90–95% off**
   eligible spend.

These three together plausibly cut our automated Anthropic line (~$5–15/mo today, per
ZORT budget) by more than half even as the billing split removes the subscription subsidy.

---

## 1. The user↔AI loop (interactive Claude Code sessions)

Where tokens leak in the day-to-day session, with the fix.

| Leak | Evidence in our repos | Fix |
| ---- | --------------------- | --- |
| **Oversized CLAUDE.md** re-read into every session | `DESIGN/CLAUDE.md` = 295 lines, `localDNS/CLAUDE.md` = 326 lines — both well over the **≤200-line** guideline; every session pays this on the first turn | Trim each to a tight ≤200-line index; push the long tables (deploy-path table, full known-issues) into `README`/linked files the agent loads *on demand*, not every session |
| **Long-running threads** re-read the whole transcript every turn | Our multi-step NARF/ZORT campaigns and PR-watch sessions | `/clear` between unrelated tasks; `/recap` to resume instead of replaying; one session ≈ one task |
| **Over-broad prompts** pull more context than needed | "Locate inefficiencies… ANYTHING…" (see §5) | Scope the ask: name the file/function/stage, state the output format, set a budget |
| **Wrong effort level** for routine work | doc-link checks, formatting, simple reviews | Use `effort: low` for mechanical tasks; reserve high effort for genuine reasoning |
| **Batching missed** | separate sessions for related edits | Batch related edits in one session while context is already loaded |

Rule of thumb from the field: disciplined context hygiene reports **40–85%** token
reduction, up to **90%** in aggressive cases — almost all of it from *how you work*, not
from a model swap.

---

## 2. The LLM router (Odin / LiteLLM) — already strong, three gaps

Our hybrid stack is genuinely good and matches 2026 best practice: LiteLLM as a unified
gateway, model aliases, fallback chains, a deterministic (non-LLM) dispatcher, local-first
with cloud overflow, privacy classification *before* any LLM runs (Heimdall/Warden),
spend cap (Hoard-Warden), local embeddings for RAG. Hybrid setups report **40–70%** cost
savings vs. all-cloud; we already capture most of that. Gaps:

1. **No Batch path for cloud tiers.** `cloud-explore`/`cloud-code`/`cloud-overflow` go
   synchronous. Add a batch-eligible route for non-interactive jobs (NARF/ZORT, statement
   prose, bulk classification) → 50% off those crossings for free.
2. **No prompt caching at the cloud boundary.** Add cache breakpoints on the stable
   system prefix (tool schemas, portfolio hub, instructions). Caveat from the sources:
   *editing one tool description or compacting history invalidates the whole prefix cache* —
   so keep tool schemas versioned/stable and compact at predictable boundaries only.
3. **Token accounting is a guess.** `hoard.py` estimates `chars/4`. Use LiteLLM's actual
   per-request token/cost logging (it tracks routing decisions, latency, tokens, cost) so
   the budget cap and ZORT's numbers reflect reality, not an approximation.

Keep doing: deterministic routing for classification (Heimdall, `compose.py` archetype
classifier) stays **local** — that's the right call; classification is the canonical
"keep it off the cloud meter" workload.

---

## 3. Statements — keep them template-based; batch the optional prose

Statements are pure template/rule-based today (cost $0 in tokens). The "~$0.01/home"
("penny a home") figure is the *optional* future Haiku prose step, not current spend.
When/if we enable it: run it through **Batch API** (statements are produced on a monthly
schedule — perfectly async) → the penny becomes a half-penny, and caching the shared
prompt scaffold across a whole operator's book drops it further. No reason to ever call
that path synchronously.

---

## 4. Leverage we're not yet using

- **Local models for more of the cheap, high-volume work.** Anything classification-,
  extraction-, or redaction-shaped should stay on the t630 tier (qwen2.5 / nomic-embed),
  not a cloud call. Already partly done; widen it.
- **Rented-GPU burst for heavy reasoning** is already designed (`cloud-gpu-reason`,
  DeepSeek-R1 32b/70b over Tailscale, spot ~$0.15–0.50/hr). Good pattern — only spin up
  on demand, never idle.
- **Skills over re-prompting.** Codify repeated NARF/ZORT procedures as Claude Code skills
  so the instructions aren't re-pasted into context each run.
- **Model right-sizing.** Default to the cheapest model that clears the bar: Haiku for
  prose/classification, Sonnet for code/diffs, Opus only for genuine wide-context
  reasoning. We mostly do this; enforce it as the router default rather than the exception.

---

## 5. Is the *prompt that triggered this review* efficient? No — here's the fix

The originating request was, paraphrased: *"Locate inefficiencies in our process…
Is there a better way to reduce token use? Better prompting? Leverage other AI? Hybrid
local+Claude? ANYTHING that could help. Search the web… Keep UP TO DATE… Check the news."*

What makes it expensive to answer:

- **Unbounded scope.** "ANYTHING you could possibly think of" + "Anything that could help"
  removes every natural stopping point, so the agent fans out maximally — ironic for a
  token-reduction request.
- **No output contract.** No format, length, or destination specified, so the agent must
  guess (and tends to over-produce).
- **Several distinct asks bundled, unranked** (token use / prompting / other AI / hybrid /
  news) — the agent can't tell what matters most, so it does all of them at full depth.
- **Open-ended web research** ("search the web… check the news… keep up to date") with no
  depth cap can trigger a large, expensive fan-out.

A tighter version that gets the same answer for less:

> "Review how we use AI for token/cost waste. Prioritize: (1) the cloud-API spend in
> NARF/ZORT runs, (2) interactive Claude Code session hygiene. For each, give the top 3
> fixes with rough $ impact. Do **≤5** web searches for 2026 best practices; skip anything
> already in our docs. Output a one-page list, commit it to `docs/ai-cto/`. Budget: keep it
> tight."

That fixes scope (one page, ≤5 searches), ranks the asks, names a destination, and sets a
budget — the same four levers we apply to the agent everywhere else.

---

## Sources (2026)

- [Anthropic splits billing — Agent SDK separate credit pools (The New Stack)](https://thenewstack.io/anthropic-agent-sdk-credits/)
- [Claude subscriptions no longer include Agent SDK / `claude -p` (XDA)](https://www.xda-developers.com/anthropics-claude-subscriptions-no-longer-include-agent-sdk-and-claude-p-usage/)
- [Anthropic API pricing 2026 — models, caching, batch (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt caching 2026 — real cost wins (Technspire)](https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins)
- [Anthropic prompt caching & token efficiency — cache breakpoints, batch (hidekazu-konishi)](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html)
- [23 tips for Claude Code token saving (Analytics Vidhya)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Reduce Claude Code token usage by 90% (Medium / Mehul Gupta)](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Model routing LLM — strategies to cut token cost 2026](https://abhyashsuchi.in/model-routing-llm-2026-best-practices/)
- [Local LLMs vs cloud APIs — 2026 TCO analysis (SitePoint)](https://www.sitepoint.com/local-llms-vs-cloud-api-cost-analysis-2026/)
