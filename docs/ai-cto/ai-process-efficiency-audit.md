# AI process-efficiency audit — user ↔ AI loop (2026-06-14)

A NARF (AI-CTO) audit of **how we work with the AI**, not what the AI builds: where
tokens are spent for no return, where prompting wastes a turn, and what the 2026
state-of-the-art says we should change. Scope is the whole A777ance guild (all repos)
plus the local LLM router (`localDNS/10-ai-orchestration/`). Newest-first per house style.

This is a recommendations doc, like `RECOMMENDED-CHANGES.md`, but for the *process*
rather than the docs. Findings are ranked by return-on-effort. Nothing here is applied
yet — each item needs an owner's yes.

---

## TL;DR — the five that pay for themselves

1. **Every session pre-loads a 3.5–4k-token CLAUDE.md before you type a word.** Trim each
   to a <600-token lookup table; push the prose into the files it already points to. ~80%
   per-session context saving, every repo, every session. *Highest ROI, zero risk.*
2. **The session-start "read these 4–6 docs" protocols (NARF/ZORT) load ~10–20k tokens
   eagerly.** Make them *lazy* ("read X **only when** the task touches money/architecture"),
   not unconditional. Saves the read on every session that doesn't need it.
3. **Our Claude cloud tiers don't use prompt caching.** Statement generation and any
   repeated-system-prompt job can cut input cost **60–90%** with one config change. *Pure
   money, no behaviour change.*
4. **This routine's own prompt is unbounded** ("ANYTHING… check the news… search the web")
   — it invites a long, expensive crawl with no stop condition. A scoped version (below)
   does the same job for a fraction of the tokens.
5. **The deterministic, privacy-gated router is already best-practice — keep it.** The
   2026 literature endorses exactly our "small/local default, frontier on overflow, rules
   not an LLM in the routing decision" design. Add a Haiku classify tier and caching; do
   **not** add an LLM-in-the-loop router.

---

## 1. CLAUDE.md bloat — the single biggest, cheapest win

**Measured today** (`wc`, ≈1.33 tokens/word):

| Repo CLAUDE.md | Words | ≈ Tokens loaded *every* session |
| --- | --- | --- |
| localDNS | 2,728 | ~3,600 |
| DESIGN-… | 2,608 | ~3,500 |
| Chronikomicon/access | 1,593 | ~2,100 |
| MARKETING | 1,445 | ~1,900 |
| claude-code-homelab | 371 | ~490 |
| customers | 562 | ~750 |
| Azure-lab | 316 | ~420 |

The 2026 guidance is blunt: a CLAUDE.md should read **like a lookup table, not a brain
dump**, and most projects want it **under ~500 tokens** — because "a 5,000-token CLAUDE.md
costs 5,000 tokens before you've typed a word" (KDnuggets; The Prompt Shelf, 2026). Our
two flagship files are 7× that.

The waste is concrete and already self-documented: `RECOMMENDED-CHANGES.md` item #2 notes
localDNS's CLAUDE.md **duplicates README's** service/port table, WireGuard-peer table,
hardware specs, and the DNS-split narrative. Each of those lives in two files; only one
needs to be in the always-loaded one.

**Fix (per repo):**
- Keep in CLAUDE.md: the one-paragraph "what this is", the hard invariants (push-to-main,
  honesty rule, secrets rule, privacy route), and a **table of pointers** to the detail.
- Move out to README/network-context (loaded on demand): the full port table, peer table,
  deploy-path table, verification command blocks, known-issues table.
- Target <600 tokens each. Expected saving: **~3,000 tokens/session** on localDNS and
  DESIGN — multiplied by every session you start in those repos.

## 2. House-style block — 7 byte-identical copies

The "House style: ordering & typography" block is duplicated verbatim across **7**
CLAUDE.md files (`grep` confirms: localDNS, DESIGN, MARKETING, customers, Azure-lab,
claude-code-homelab/templates, Chronikomicon/access). That's ~1,400 tokens copy-pasted
into the always-loaded context of every repo, and a 7-place update burden.
`RECOMMENDED-CHANGES.md` item #1 already flagged the drift risk but deferred the fix.

**Fix:** collapse to one or two lines in each CLAUDE.md —
> *House style (ordering, Z→A lists, reverse-block walkthroughs, Gill Sans MT): see
> `claude-code-homelab/templates/house-style.md` — canonical.*

— and put the full rules in one canonical file. Saves ~1,200 tokens/session *and* kills
the drift. (If keeping the rules inline is preferred for offline reading, at minimum
stamp each copy "edited? update all 7" so it doesn't silently fork.)

## 3. Session-start read protocols — make them lazy

Both `CLAUDE.md` agent-state sections instruct an *unconditional* multi-file read at the
start of **every** session:

- **NARF:** read `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md`.
- **ZORT:** read `portfolio.md`, `decisions.md`, `metrics.md`, `runway.md`, `budget.md`,
  *and* `MARKETING/docs/ai-cfo/context.md` — **6 files**.

A session that just fixes a typo or rotates a WireGuard key pays the full read. That is
the opposite of the 2026 "lookup table, pull detail on demand" rule.

**Fix:** rewrite the trigger as a condition, not a command —
> *Before any **financial** change, read ZORT's portfolio + decisions. Before any
> **architecture/roadmap** decision, read NARF's portfolio + the relevant log. Skip
> otherwise.*

Keeps the discipline (state is still consulted when it matters) and stops paying for it
when it doesn't.

## 4. Prompt caching on the Claude tiers — money left on the table

`10-ai-orchestration/config.yaml` routes `cloud-overflow` / `cloud-explore` /
`cloud-code` / `cloud-vision` to Claude but sets **no cache breakpoints**. Prompt caching
prices cache reads at **~10% of input** and is "the most underused cost-optimization tool
for Claude API workloads in 2026," cutting input cost **60–90%** on repeated-prefix
workloads (Anthropic docs; AI Magicx, 2026).

Our highest-value caching target is **statement generation** (`customers` → `make
statement` → localDNS `compose/generate_client.py`): the same large system prompt /
template prefix runs once per household, per month — a textbook cache-hit pattern (3+
reads inside the TTL easily met across a billing run).

**Fix:** add a `cache_control` breakpoint on the stable system-prompt/template prefix in
the statement pipeline and any batch job; keep the per-household data *after* the
breakpoint. Watch for the March-2026 caching bugs that inflated tokens 10–20×
(KDnuggets) — verify with token-count logging after enabling. **Caveat:** caching helps
the *API/batch* path, not interactive Claude Code sessions (those cache automatically).

## 5. Hybrid local/cloud routing — we're already right; two additions

The 2026 consensus is that the pragmatic hybrid — **local/small for predictable,
low-complexity, high-volume work; frontier cloud for burst and hard tasks** — cuts LLM
cost **60–80%** (SitePoint; Mavik Labs, 2026). Our stage-10 design *is* this, and our
`ORCHESTRATION-BLUEPRINT.md` makes the one call most teams get wrong correctly: **the
routing decision is deterministic Python, not an LLM** — debuggable, free, and it keeps
the privacy gate (`sensitive` → local-only, no cloud fallback) provable in code rather
than hoped-for. Do not regress this into an agentic router.

Two cheap additions, consistent with the blueprint:
- **A `cloud-classify`/cheap tier on Haiku 4.5.** For the rare task that does need a model
  to triage (summarize-then-route), Haiku is ~1/10th Opus's price. Today `cloud-overflow`
  is Opus 4.8 — the most expensive model — as the *fallback for everything local*. A small
  spillover task lands on the priciest brain. Add `cloud-cheap: claude-haiku-4-5` and let
  `local-fast`/`local-smart` spill to **that** first, Opus only for genuine depth.
- **Right-size `max_tokens` per tier.** "Do not budget 4,000 output tokens for a task that
  needs 400" (AI Magicx). Set tight output budgets on the snappy tiers.

## 6. Prompting — including this routine's own prompt

**This routine's prompt is the example to fix.** Verbatim it says *"Anything you could
possibly think of… Search the web… Look for best practices… Check the news… ANYTHING that
could help."* That is genuinely open-ended: no scope, no output format, no stop
condition, no budget — so the agent fans out across the web and the whole repo set on
every run, which is the single most expensive shape a recurring task can have. The intent
is great; the framing is unbounded.

**A tighter version that gets the same answer for a fraction of the tokens:**

> *Monthly: re-check the AI-process efficiency audit (`docs/ai-cto/ai-process-efficiency-
> audit.md`). Do ≤4 web searches for changes since the dates cited there. Output: only
> what's **new or changed** since last run as a diff against the existing findings — skip
> anything unchanged. If nothing material changed, send no notification.*

That gives it scope (the audit doc), a search budget (≤4), an output contract (a diff,
not a fresh essay), and a silence rule — turning a multi-thousand-token crawl into a
short delta check. General prompting rules worth adopting across the guild:
- **State the deliverable and its format up front** (a diff / a table / a patch), not just
  the goal.
- **Bound the search** ("≤N searches", "only sources newer than X").
- **Name the files in scope** so the agent doesn't re-discover the repo every run.
- **Give a stop/silence condition** so a no-change run costs almost nothing.
- **One ask per run.** This prompt bundles "audit the process" + "critique this prompt" +
  "check the news" — each would be cheaper and sharper as its own scoped run.

---

## What NOT to change (so we don't churn)

- **The deterministic, privacy-gated router.** Endorsed by the 2026 literature; the
  privacy gate must stay code, not an LLM. (`ORCHESTRATION-BLUEPRINT.md` §4.)
- **"Route, don't shard."** Correct; keep it.
- **The honesty rule on statements.** Unrelated to token cost; non-negotiable regardless.

---

## Sources (dated — these move fast; re-verify next run)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching for Claude: Cut Your API Bill 60% (AI Magicx, 2026)](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets, 2026)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Context Window: Why It Burns Tokens Fast (The Prompt Shelf, 2026)](https://thepromptshelf.dev/blog/claude-code-context-management/)
- [Claude Code Subagents: A 2026 Practical Guide (Tembo.io)](https://www.tembo.io/blog/claude-code-subagents)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (SitePoint, 2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Cost Optimization in 2026: Routing, Caching, Batching (Mavik Labs)](https://www.maviklabs.com/blog/llm-cost-optimization-2026)
- [Model Routing LLM: 7 Strategies to Reduce Token Cost (2026)](https://abhyashsuchi.in/model-routing-llm-2026-best-practices/)
