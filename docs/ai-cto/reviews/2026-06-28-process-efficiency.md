# NARF — process efficiency review — 2026-06-28

**Question (from the founder):** Where are the inefficiencies in *our process* — the
user↔AI loop itself? How do we cut token use, prompt better, leverage other AI (incl. the
local LLM we already run), and stay current? And: is the prompt that asked this inefficient?

This is a review of **how we work with the AI**, not of the product. Findings are ranked by
leverage. Numbers are measured against this repo set on 2026-06-28; best-practice claims are
cited inline and will drift — treat the dated sources as perishable.

---

## TL;DR — the five highest-leverage moves

1. **Trim the always-on context (CLAUDE.md files).** They load on *every* message. Today
   the six repos carry ~12.7k words of `CLAUDE.md` (~17k tokens). The DESIGN + localDNS
   files alone are ~7.1k tokens. Move the 80%-of-the-time-unused detail into **Skills**
   (load-on-demand) and reference docs. Industry rule of thumb: keep `CLAUDE.md` < 200
   lines; ours are 295 (DESIGN) and 326 (localDNS). Skills cut context bloat 60–80%.
2. **Right-size the model per routine.** This very analysis is running on **Opus 4.8 (1M)** —
   our most expensive model — for a web-research-and-write task that Sonnet 4.6 does at a
   fraction of the cost. Reserve Opus for genuinely hard reasoning; default routines to
   Sonnet; let Haiku/local handle extract-classify-format.
3. **Use the Batch API for non-interactive routines.** Scheduled routines (like this one)
   have no human waiting → eligible for the **50% batch discount**, and it *stacks* with
   prompt caching (combined 95%+ off on repeated context).
4. **Lean on prompt caching deliberately.** Cached input reads cost ~10% of normal (90% off);
   break-even is one hit (5-min cache). Stable system prompts, tool defs, and large docs
   should sit *before* volatile content so the cache prefix stays warm.
5. **Route the cheap 60–70% of work to the local LLM we already own.** The t630 LiteLLM +
   Ollama stack (stage 10) exists. Hybrid local/cloud routing cuts inference cost 60–80% on
   the simple-task majority and keeps sensitive lookups in-house — but mind TD-14 (fail-open
   fallback) before trusting it with anything private.

---

## 1. The biggest single lever: always-on context

Measured today:

| Repo `CLAUDE.md` | Lines | ~Tokens (loaded every turn) |
| ---------------- | ----- | --------------------------- |
| localDNS | 326 | ~3,637 |
| DESIGN-… | 295 | ~3,477 |
| MARKETING | 214 | ~1,926 |
| customers | 80 | ~749 |
| claude-code-homelab | 75 | ~494 |
| Azure-lab | 50 | ~421 |
| **total** | **1,040** | **~10,700** (one file each) |

Every message in a session re-sends that repo's `CLAUDE.md`. In a multi-repo routine the
harness can pull several at once (this session was handed all six — ~17k words). Prompt
caching softens the *cost* of re-sending (90% off on a warm prefix) but **not the context
window pressure**, which still pushes us toward earlier compaction and crowds out the actual
task.

**What to do.** Apply Anthropic's own rule: if Claude doesn't need it in 80% of sessions, it
doesn't belong in `CLAUDE.md`. Keep there only: house style, the master-list rule, the
honesty rule, repo map, forbidden patterns. Move the rest into **Skills** (`.claude/skills/`)
that load only when triggered:

- A `statements` skill (build/compose a statement) — replaces the how-to currently inlined.
- A `deploy-t630` skill — the deploy-path table + verification block from localDNS.
- A `house-style` skill — the ordering/typography rules, referenced when actually writing
  docs rather than carried on every turn.

Expected effect: 60–80% smaller base context per the 2026 skills guidance, which both lowers
token cost on cache-miss turns and delays compaction. (Custom slash-commands have merged into
Skills as of 2026 — Skills are now the recommended unit.)

Sources: Claude Code skills docs; "keep CLAUDE.md < 200 lines / 80% rule"
(agensi.io, batsov.com, KDnuggets, 2026).

## 2. Right-size the model — stop defaulting to Opus

This routine runs on `claude-opus-4-8[1m]`. Opus is correct for hard architectural reasoning
and the trickiest debugging; it is overkill for: web research + synthesis (this task), doc
edits, link-checking, status roll-ups, drafting copy. Those are Sonnet 4.6 work, and the
extract/classify/format slice is Haiku-or-local work.

**Action:** set a per-routine model policy. Default the scheduled CTO/CFO review routines and
research sweeps to **Sonnet**; keep Opus for explicitly-flagged hard problems. The 1M context
window is a further premium we're paying on every routine — only worth it when a task genuinely
spans large context. Most of our routines touch a handful of files.

Sources: Claude API pricing 2026 (Opus 4.8 / Sonnet 4.6 / Haiku 4.5 tiers); cost docs
(code.claude.com/docs/en/costs).

## 3. Batch API for the routines (50% off, stacks with caching)

Scheduled routines are non-interactive by definition — nobody is waiting on the response in
real time. That is exactly the Batch API's use case: **50% discount** on both input and output,
and it **stacks with prompt caching** for 95%+ off on the repeated-context portion. Anything
we run on a timer (portfolio review, metrics roll-up, this efficiency sweep, NotebookLM bridge
syncs) is a candidate. Interactive Claude Code sessions can't batch, but the *scheduled* ones
are the bulk of our autonomous spend.

Sources: Anthropic pricing/batch docs; finout.io Anthropic pricing 2026; tokenmix.ai cache
pricing.

## 4. Prompt caching hygiene

We likely already benefit passively (Claude Code caches system prompt + tools). To maximize it:

- Keep the *stable* stuff first and unchanging: system prompt → tool defs → large static docs
  → settled history → volatile turn. A cache breakpoint sits at the last cacheable block; any
  edit *above* a breakpoint invalidates the whole prefix.
- Don't reorder or lightly edit `CLAUDE.md` mid-session — each edit busts the cached prefix and
  forces a full re-write (cache *writes* cost 1.25×).
- Caches are now **workspace-isolated** (changed 2026-02-05) — fine for us, single workspace.

Break-even is a single cache hit on the 5-minute window, so for any back-to-back routine the
math is always favorable.

Sources: platform.claude.com prompt-caching docs; hidekazu-konishi.com efficiency guide (2026).

## 5. Hybrid local + Claude — we already own the hard part

Stage 10 (`localDNS/10-ai-orchestration`) is a LiteLLM gateway + Ollama with a reasoning ladder
(`local-reason` deepseek-r1:1.5b on t630, `cloud-gpu-reason` rented GPU, `cloud-overflow`
Claude). The 2026 hybrid pattern: route by **task complexity, data sensitivity, availability**.
~60–70% of agent traffic (classification, extraction, formatting, first-draft) runs acceptably
on a local model; 20–30% moderate; ~10% needs a frontier model. Teams report 60–80% (some claim
10×) inference-cost reduction routing the simple majority local.

Concrete fits for us:
- **Local-first, Claude-finish:** local model drafts the "Handled For You" log entry or a
  statement blurb; Claude only polishes the customer-facing final. Penny-a-home discipline
  applies here too.
- **Sensitive lookups never leave the box** — but **TD-14 is live**: the `local-reason`
  fallback chain currently fails *open* to `cloud-overflow` (Claude cloud). Close that to a
  local-only chain before routing anything private. (Tracked in tech-debt.)
- Reality check (kunalganglani.com 2026 GPU benchmark): a t630 CPU running deepseek-r1:1.5b is
  fine for routing/extraction/short drafts, **not** for agentic coding — don't over-route.

Sources: sitepoint.com hybrid architecture guide 2026; buildmvpfast.com; lushbinary.com LLM
gateway; LiteLLM auto-routing docs; mindstudio.ai local-models guide.

## 6. Subagents: a context tool, not a cost tool

Worth stating plainly because it's a common trap. Agent teams / subagent-heavy workflows use
**~7× the tokens** of a single thread (each teammate carries its own context window). Subagents
are the right call for **context isolation** (keeping a noisy search out of the main thread) and
**parallelism**, and they shave only ~11% off cost versus no routing. So: use a Haiku-class
`Explore` subagent to keep big searches off the main Opus/Sonnet context — but don't spin up
agent teams *expecting* a cost win, and always **scope what each subagent receives** (passing
full upstream context to five subagents is the classic 5×-blowup).

Sources: code.claude.com/docs/en/costs (7× figure); mindstudio.ai subagents; Towards Data
Science "Agentic AI: how to save on tokens."

## 7. Context editing & the memory tool (for long routines)

For long-running agents, Anthropic's **context editing** (auto-clear stale tool results /
thinking) + **memory tool** (file-based store outside the window) cut token use **up to 84%**
in a 100-turn eval and reduce effective later-call context 50–70%. Our routines that read many
files (portfolio reviews, doc-integrity sweeps) are the candidates. Cheaper still where it
applies: **code-execution / filesystem MCP** so the agent greps and reads on demand instead of
front-loading files into context.

Sources: anthropic.com/news/context-management; Claude cookbook context-engineering;
anthropic.com/engineering/code-execution-with-mcp.

---

## On the prompt that asked this (yes, it was inefficient)

The founder explicitly asked. Honest read:

**What worked:** clear domain, gave permission to search the web, asked for currency, and asked
for a self-critique. Good instincts.

**What cost tokens needlessly:**
- **Unbounded scope.** "ANYTHING that could help… Anything you could possibly think of" invites
  an open-ended sweep with no natural stopping point — the single biggest driver of runaway
  output. A bounded ask ("top 5 levers, ranked, with the one-line action for each") gets the
  same value for far fewer tokens.
- **No output contract.** No format, length, or destination specified, so the model has to
  guess (and tends to over-produce). State the deliverable: "a ranked markdown file in
  docs/ai-cto, ≤2 pages."
- **No model/effort hint.** Run on Opus-1M by default; the prompt could say "Sonnet is fine."
- **Recurrence not scoped.** "Keep UP TO DATE… day by day" implies a *daily* full web sweep.
  Best practice churns weekly at most; a daily research routine mostly re-pays for unchanged
  answers. Make it **weekly**, or event-triggered (run when a model/pricing change is detected),
  and have it **diff against the last report** instead of regenerating from scratch.
- **Politeness tokens** ("Thanks!", "Perhaps also…") are negligible individually but signal the
  conversational register that produces longer answers. Not worth worrying about versus the
  four points above.

**A tighter version of the same request:**

> *Audit our user↔AI process for token waste. Output a ranked markdown file in
> `docs/ai-cto/reviews/` (≤2 pages): top 5 levers, each with a one-line action and a rough
> %-savings. Cover model right-sizing, caching, batch, local-LLM routing, and context size.
> Web-search only what changed since the last report and diff against it. Sonnet is fine.
> Run weekly, not daily.*

Same answer, a fraction of the tokens, and a stable cadence.

---

## Recommended next actions (cheapest-first)

1. **Set scheduled routines to Sonnet** (and drop 1M unless a task needs it). *Config change,
   minutes, biggest recurring saving.*
2. **Switch the recurrence of this efficiency check to weekly + diff-mode.** *Stops paying daily
   for an answer that changes weekly.*
3. **Move ~60% of each `CLAUDE.md` into Skills + reference docs.** *Half a day; 60–80% base-context
   cut; helps every future session.*
4. **Move non-interactive routines onto the Batch API where the harness allows.** *50% off,
   stacks with caching.*
5. **Close TD-14, then route extract/classify/draft to the local LLM.** *Safety first, then
   60–80% off the simple-task majority.*
6. **Add a Haiku `Explore` subagent for large searches; scope every subagent's input.** *Keeps
   big reads off the main context without the 7× team tax.*

— NARF, 2026-06-28. Sources are dated and perishable; re-verify pricing and feature claims
before acting on the dollar figures.
