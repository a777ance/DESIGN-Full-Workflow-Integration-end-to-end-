# AI process efficiency — how we spend tokens between the founder and Claude

*Audit date: 2026-06-27. NARF (AI CTO) / ZORT (AI CFO) joint note. Revisit quarterly —
the model and pricing landscape moves week-to-week, so treat the dated rows as perishable.*

The ask: find the waste in *how we work with the AI* — token cost, prompting, and whether
a hybrid local+cloud setup helps. Short version: **we already have the right hybrid plumbing
(the LiteLLM router on the t630); we are not yet using it to deflect work off the paid API,
and our biggest single recurring cost is context we re-ship on every session.** Below, ranked
by payback, newest guidance first.

---

## TL;DR — do these in order

| # | Lever | Effort | What it saves |
| - | ----- | ------ | ------------- |
| 1 | **Trim & tier the `CLAUDE.md` files** (see §1) | 1 hr | ~14.6k tokens are injected *before a word is typed* every session; ~40% is prose a `README` link could carry |
| 2 | **Stop invalidating the prompt cache mid-session** (§2) | habit | 5-min TTL + CLAUDE.md edits silently 2–10× a session's cost |
| 3 | **Route cheap sub-tasks off the paid API** — Haiku, or the local Ollama tiers we already run (§3) | 1–2 hr | Haiku ≈ 25× cheaper than Opus; local tiers ≈ 18× cheaper than any cloud token |
| 4 | **Batch the scheduled/routine work** (this audit, doc checks, statement runs) (§3) | 1 hr | Batch API = 50% off; stacks with cache reads → up to ~95% off the repeated part |
| 5 | **Tighten the prompts themselves** — scope, budget, format (§5) | habit | The open-ended "do ANYTHING" prompt is itself a cost driver |
| 6 | **A cheap "keep-up-to-date" routine** instead of ad-hoc research (§6) | 30 min | Bounds the cost of "check the news" we'd otherwise pay unbounded |

---

## 1. The biggest lever: context we re-ship every session

Measured today across the seven repos:

```
  573  Azure-lab/CLAUDE.md
 4496  DESIGN-…/CLAUDE.md
 2665  MARKETING/CLAUDE.md
  724  claude-code-homelab/CLAUDE.md
 1033  customers/CLAUDE.md
 5118  localDNS/CLAUDE.md
        (Chronikomicon has none yet)
 ≈14,611 tokens total
```

A `CLAUDE.md` loads **before** Claude reads any code or the task — so a 5k-token file costs
5k tokens *every turn, every session*, whether or not the task touches what it describes. The
net is only positive when it saves more output than it costs as a persistent prefix. Several
of ours are over that line: the DESIGN and localDNS files are ~4.5–5k each and carry full
funnel diagrams, money-flow ASCII, and stage tables that a task rarely needs in-context.

**What to do (keeps the playbook, cuts the always-on cost):**

- **Demote, don't delete.** A `CLAUDE.md` should be the *index + invariants*, not the manual.
  Move the funnel diagram, money-flow box, stage map, and deploy-path table into the existing
  `README.md` / `network-context.md` and leave a one-line pointer. Claude reads them on demand
  when a task needs them — and only then pays for them.
- **Target ≤ ~1,500 tokens per `CLAUDE.md`.** Keep: the repo's one-liner, the hard rules
  (secrets, push-to-main vs. branch, honesty rule), and the "read these at session start"
  pointers. That alone roughly halves the 14.6k.
- **The house-style block is duplicated verbatim in all 7 files.** It's identical boilerplate
  shipped seven times. Put it once in a `STYLE.md` and link it; or accept it as a deliberate
  cost (it *is* load-bearing for output formatting). Either way, name the choice.
- **One caveat that cuts the other way:** a *stable* `CLAUDE.md` is cache-friendly (see §2).
  The win is trimming the bulk **once** and then freezing it — not editing it often.

> A subtle one specific to us: the **reverse-chronological / Z→A / reversed-walkthrough** house
> style is counter-intuitive enough that Claude will re-derive or second-guess it on edits,
> burning reasoning tokens and risking mistakes. It's a real preference, so keep it — but state
> it as a flat *rule with one example* (already mostly done) rather than rationale, so the model
> applies it without re-reasoning.

## 2. Prompt-cache discipline — the silent multiplier

Prompt caching gives **~90% off** the cached prefix on a hit; the catch is what *invalidates*
it. Most mid-session cost spikes are cache misses, not extra work. The rules that bite us:

- **The cache prefix is left-to-right and stable-first.** Anything early (system prompt, MCP
  tool list, skills, `CLAUDE.md`) that changes forces everything after it to be recomputed. So
  **editing a `CLAUDE.md` mid-session re-bills the whole session uncached.** Do CLAUDE.md edits
  as their own small session, or at the very end.
- **5-minute TTL.** Walking away for >5 min and coming back pays the full prefix again. For long
  thinking sessions, keep the cadence tight or expect the re-bill.
- **Cache is isolated per model.** Switching Opus↔Sonnet mid-session throws away the cache built
  under the other model. Pick the model for a session and stay on it.
- **Watch the read-to-write ratio** the API reports (`cache_read` vs `cache_creation` tokens).
  A high read ratio means caching is working; a low one means we keep busting it.
- **Trust-but-verify the bill.** There was a March-2026 caching incident where two Anthropic
  bugs inflated token counts 10–20× silently. Glance at usage occasionally; don't assume.

## 3. Route work to the cheapest box that can do it — we're half-built for this already

The single most valuable asset we have for this is **already deployed**: the LiteLLM router at
`ai.home.lan:4040` (`localDNS/10-ai-orchestration/`), with local Ollama tiers
(`qwen2.5:3b/7b`, `deepseek-r1:1.5b`, `nomic-embed-text`), a rented-GPU reasoning tier, and a
cloud-overflow fallback — plus a **deterministic privacy gate that pins sensitive tasks local
and fails closed.** That is exactly the 2026 best-practice "three-pillar" hybrid architecture
(route on sensitivity → complexity → availability). We're ahead of the curve on design; we're
behind on *use*.

The gap: **Claude Code itself talks straight to the Opus API**, so none of our cheap tiers
catch the easy work. Industry numbers for closing that gap:

- **Haiku ≈ 25× cheaper per token than Opus**, and handles the bulk of real sub-tasks —
  formatting, field extraction, classification, routing, short summaries, link-checking.
- **Local tiers ≈ 18× cheaper than *any* cloud token** (and free of per-token billing
  entirely), and 70–80% of everyday queries don't need a frontier model.
- **Model routing alone cuts spend 20–60%; full hybrid local+cloud cuts it 60–80%** at
  comparable quality, when the easy path actually goes local.

**Concrete moves for us:**

1. **Use the model ladder deliberately.** Reserve Opus for genuinely hard reasoning, design, and
   tricky diffs. Drop to **Sonnet** for ordinary code/build, and to **Haiku** for mechanical
   work. (We already encode this intent in `config.yaml`'s `cloud-explore`/`cloud-code` tiers —
   honor it in practice.) Note Opus 4.8 **Fast Mode is now 3× cheaper** ($10/$50 per MTok), so
   the speed/price gap narrowed — but Haiku is still the right tool for trivial work.
2. **Point routine, non-sensitive chores at the local router**, not the paid API: link checks
   (`tools/check-docs.py` triage), draft summaries, classification, embeddings for any RAG. The
   privacy gate already guarantees a sensitive lookup never leaves the box.
3. **Batch the async work.** The **Batch API is 50% off all tokens, no quality penalty**, and it
   *stacks with cache reads to ~95% off the repeated portion.* This very audit, the monthly
   statement runs, doc-integrity sweeps, and bulk roster operations are all batch-shaped — they
   don't need to be interactive.
4. **Add a semantic cache** in front of the router. On classification/extraction-heavy loads it
   deduplicates near-identical requests and cuts volume 15–30%.

## 4. Use subagents & skills to keep the main context small

Each subagent runs in its **own context window and returns only a summary** — so file dumps,
logs, and search output never land in (or get re-billed against) the main thread. The pattern
that saves the most: spawn a search/read subagent, keep the conclusion, discard the haystack.
We already do this in places; make it the default for anything that means reading across files.

- **Skills load on demand** rather than living in the always-on prefix — prefer a skill over
  pasting a procedure into `CLAUDE.md`.
- June-2026 **Dynamic Workflows** let one lead fan out tens–hundreds of subagents; for us the
  ceiling is lower — 3–5 concurrent is the sweet spot before merging summaries costs more than
  it saves. Reserve big fan-outs for genuine audits (a full doc/repo sweep), not routine edits.
- **`/compact`** mid-session distills history into a summary and shrinks the prefix; use it when
  a session has accumulated a lot of dead context rather than letting it ride.

## 5. The prompts themselves — including the one that triggered this audit

The request that produced this doc was, paraphrased: *"Find inefficiencies in our process,
reduce token use, better prompting, leverage other AI, hybrid local+Claude, search the web,
keep up to date, check the news — ANYTHING. And tell me if this prompt is inefficient."*

It is a good *strategic* prompt and a costly *operational* one. Why, and the fix:

- **It's unbounded.** "ANYTHING that could help" + "search the web" + "check the news" with no
  budget invites open-ended, expensive exploration. **Fix:** cap it — "spend ≤ N searches,"
  "≤ 1 page of findings," or "top 5 levers only."
- **It bundles many questions** (cost, prompting, other AI, hybrid, news) into one turn, so the
  answer can't cache cleanly and tends to sprawl. **Fix:** one theme per session; let each cache.
- **It doesn't name the deliverable.** Unspecified format → the model guesses long. **Fix:** say
  the shape up front ("a prioritized table + a committed `.md`, ≤ ~400 lines").
- **"Keep up to date / check the news"** is right to want but wrong to pay for ad-hoc each time —
  that's a standing routine, not a prompt (see §6).

**General prompting rules that pay off for us:**

- Lead with the **deliverable and its format**; put **stable context first** (cache-friendly)
  and the **specific task last**.
- Name the **model tier** you want for the job ("this is mechanical — use Haiku").
- Prefer **"edit X to do Y"** over "look at everything and improve it" — scope is the cheapest
  optimization there is.
- For terse output on heavy workflows, a short "be concise; tables over prose; no preamble"
  instruction measurably cuts output tokens (where the per-token cost is highest).

## 6. The cheap way to "keep up to date"

Don't pay for open-web research on every question. Stand up a **scheduled routine** (we already
run them — this audit is one) that, on a cadence, does a *bounded* sweep of a fixed source list
(Anthropic release notes / Claude Code changelog / pricing page) and **notifies only on a real
change** — model/pricing/feature deltas that change a decision above. Bounded inputs, bounded
cost, and it reaches the founder's phone instead of sitting in a transcript nobody reads.

---

## Sources (perishable — re-check quarterly)

- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Claude Code Token-Saving Guide: Models, MCP, CLAUDE.md, Skills & cache](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Anthropic API Pricing in 2026 — Models, Caching, Batch & Optimization (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing 2026: Opus 4.8 / Sonnet 4.6 / Haiku 4.5 (MetaCTO)](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Prompt Caching in 2026: Cut LLM API Costs up to 90% (DevToolLab)](https://devtoollab.com/blog/prompt-caching-guide)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026, SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Edge LLM Inference: The Routing Layer (TianPan.co, 2026-04)](https://tianpan.co/blog/2026-04-10-hybrid-cloud-edge-llm-inference-routing)
- [Model Routing LLM: strategies to reduce token cost (2026)](https://abhyashsuchi.in/model-routing-llm-2026-best-practices/)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Skills and Subagents Reduce Prompt Bloat (newline)](https://www.newline.co/@Dipen/claude-skills-and-subagents-reduce-prompt-bloat--f2920804)
- [Claude Code Advanced Best Practices 2026 (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/)
