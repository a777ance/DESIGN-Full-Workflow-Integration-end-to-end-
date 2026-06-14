# AI Process Efficiency — Audit & Recommendations

**Author:** NARF (AI CTO) · **Date:** 2026-06-14 · **Trigger:** founder's recurring
"locate inefficiencies in our process" routine.

The question: where is the human↔AI loop wasting tokens/money, and what's the better way —
including better prompting and hybrid local/cloud LLM use? This is the standing answer; it's
ordered by impact (biggest win first) per house style isn't time-based, so highest-leverage
leads.

**Headline:** the orchestration layer (LiteLLM router, local Ollama tiers, cloud overflow,
the Odin privacy-gated supervisor) is already strong. The waste is almost entirely in the
**Claude Code interaction layer** — what we load into context every session — and in **how the
recurring routines themselves are scoped.** Most of the savings need *no new infrastructure.*

---

## A. The single biggest leak: CLAUDE.md is loaded every session, every turn

`CLAUDE.md` is injected into context at the start of every session and persists every turn. Our
files have grown into mirrors of the README:

| File | Words | ~Tokens loaded *every session* in that repo |
| ---- | ----: | ------: |
| `localDNS/CLAUDE.md` | 2,728 | ~3,600 |
| `DESIGN/CLAUDE.md` | 2,608 | ~3,500 |
| `MARKETING/CLAUDE.md` | 1,445 | ~1,900 |
| others (×4) | ~1,250 | ~1,650 |
| **total across repos** | **8,030** | **~10,700** |

A multi-repo session (like this routine) loads **all of them — ~10,700 tokens of instructions
before any work starts.** A `localDNS` session pays ~3,600 tokens up front on every single turn.

**Why it's waste:** `localDNS/CLAUDE.md` carries the *full* deploy-paths table (40+ rows), the
complete known-issues table, the nftables deploy checklist, and a verification command block —
all of which already live in (or belong in) README.md and are only needed when Claude is
actually touching that subsystem. CLAUDE.md should be an **index that points at the README**,
not a second copy of it.

**Fixes (no infra, do these first):**

1. **Trim each CLAUDE.md to a pointer file — target <800 words.** Keep: what the repo is, the
   hard invariants (secrets rule, push-to-`main`, privacy invariant), and a "read X before
   doing Y" map. Move the deploy-paths table, known-issues table, nftables checklist, and
   verification commands into README and link to them. Claude reads them on demand — that's
   cheaper than paying for them on every turn whether the task needs them or not.
2. **De-duplicate the house-style block.** The ~250-word "ordering & typography" block is
   byte-identical in all 7 repos. Collapse each copy to a 4-line summary + a link to one
   canonical `docs/house-style.md`. (Claude Code `@path` imports are per-repo, so each repo
   keeps a stub, but the prose lives once.)
3. **Measure it:** `wc -w */CLAUDE.md` before/after. Target: cut the two hub files by ~60%.

---

## B. Use the right model tier for the right job (we're overpaying on routines)

This very routine runs on **Opus 4.8 (1M context)** — our most expensive tier — to do
web-survey + doc-read work that **Sonnet 4.6 handles at a fraction of the cost.** Per the 2026
pricing guides, Sonnet is the speed/intelligence sweet spot; Opus/Fable should be reserved for
genuinely hard architecture/reasoning.

- **Set scheduled/monitor routines to Sonnet** (`/model sonnet` or per-routine config). Reserve
  Opus/Fable for hard design work where it earns its keep.
- This mirrors what `config.yaml` *already* does for the LLM router (capability tiers:
  `cloud-code` → Sonnet, `cloud-explore`/`cloud-vision` → Opus). Apply the same discipline to
  the Claude Code agent itself, not just the chat router.

---

## C. Keep the working context small (the fundamental constraint)

Every file Claude reads and every command's output stays in context for the rest of the
session. Tactics, in order of payoff:

1. **Fan out research to subagents.** "Use the Explore agent / a subagent to investigate X"
   runs the file-reads in a throwaway context and returns only the conclusion — the 10k-line
   log never lands in the main thread. Reach for subagents *first* for any broad search.
2. **Scope tasks narrowly.** "Refactor the login function in `auth.ts`," not "refactor the auth
   module." Smaller scope = less context pulled in.
3. **`/clear` between unrelated tasks; `/recap` to resume** without replaying the whole thread.
4. **Add a `.claudeignore`** so rendered statement HTML, `households/*/` data, embeddings
   indexes, and `node_modules` are never slurped into context by a wildcard read.
5. **Batch edits in one turn.** A stream of "tweak this a bit" follow-ups re-processes the whole
   context each time; describe the full change once.
6. **Move verification into a hook, not the model.** A `Stop`/`PostToolUse` hook that runs
   `tools/check-docs.py` and surfaces only failures keeps Claude from spending tokens running
   and reading the linter by hand. (`check-docs.py` is already in CI — TD-11 — so the hook is
   just wiring it locally.)

---

## D. Prompt caching & batch — money already on the table

- **Prompt caching:** the stable CLAUDE.md + repo files are an ideal cache *prefix*. Caching
  cuts cached-input cost by ~90%; with the 1-hour extended TTL (`ENABLE_PROMPT_CACHING_1H`) a
  cluster of runs reuses the prefix. **Note this makes a *trim* (Section A) compound:** a
  smaller prefix that's also cached is the cheapest possible per-turn floor. Avoid editing
  CLAUDE.md mid-session (busts the cache); use `/cd` to change dir without breaking it.
- **Batch API = flat 50% off** for anything non-interactive within a 24h window. The **monthly
  statement generation** and any **bulk doc-lint / cross-repo rewrite** are perfect fits — run
  them as a batched cron job, not interactively. Combined with caching, eligible workloads reach
  ~95% off standard on-demand pricing.

---

## E. Hybrid local/cloud — we have it; extend it one notch

We already route Open WebUI traffic through LiteLLM with local-first tiers and cloud overflow.
Two extensions:

1. **Point Claude Code's *cheap* calls at the local router.** The agentic coding loop should
   stay on Claude (local models aren't good enough for it), but the auxiliary calls — commit
   messages, summaries, classification, RAG embeddings, doc-lint — can go to local Ollama
   (`local-fast`/`local-embed`) or Haiku via the router. That's the "10x cheaper for the boring
   parts" play without risking code quality.
2. **Privacy gate is a live risk, not just an optimization — see TD-14.** A `sensitive`-tagged
   task can still fail over from `local-reason` to `cloud-overflow` (Claude cloud) because the
   LiteLLM failover layer doesn't enforce the dispatcher's `allow_cloud=False`. Any "send more
   to local to save money" change must **fail closed**, or we trade dollars for a privacy leak.
   Fix TD-14 before leaning harder on local routing.

---

## F. The routine prompt itself is inefficient (it asked us to check)

The founder's standing prompt is the textbook anti-pattern for token cost:

- **Unbounded scope** — "ANYTHING that could help," "anything you could possibly think of,"
  "check the news," "keep up to date." Open-endedness forces maximal fan-out (many searches,
  many file reads) and risks generic output. The 2026 prompting guidance is unanimous: a
  specific, structured prompt resolves in one shot; a vague one costs multiple expensive passes.
- **Wrong session shape** — it runs in a **7-repo session** (~10,700 tokens of instructions
  loaded) to answer a question that only needs this one doc and the web. Pin it to one repo.
- **No diff** — it re-surveys the whole field every run instead of reporting *what changed since
  last time*, so every run pays full freight.

**Better recurring-prompt template** (Goal / Constraints / Output / Success — pin to this repo,
budget it, make it incremental):

```
Review our AI-process efficiency. Scope: this repo (DESIGN) only — do NOT load other repos.
Model: Sonnet. Budget: ~15 web searches max.
1. Read docs/ai-cto/ai-process-efficiency.md (the standing audit).
2. Search only for changes since {last_run_date}: new Claude Code releases, model/price
   changes, new token-saving features. Skip anything already in the doc.
3. Output: append a dated "What changed" entry to that doc (newest-first). 3-6 bullets max.
   Each bullet = the change + the one action it implies for us.
4. Notify ONLY if something materially changes our setup (new cheaper model, a feature that
   obsoletes a workaround, a price cut). Otherwise stay silent.
Success = the doc has an accurate dated delta and I was pinged only if I'd want to act.
```

That version is cheaper per run, produces a maintained living doc instead of a fresh essay each
time, and respects the "notify only on signal" rule.

---

## What to do first (ranked)

1. **Trim the two hub CLAUDE.md files (A1) + de-dupe house style (A2).** Biggest recurring
   saving, zero infra, helped further by caching (D). → logged as **TD-15**.
2. **Switch scheduled routines to Sonnet (B).** Immediate cost cut on every unattended run.
3. **Adopt the scoped recurring-prompt template (F)** for this and other `/loop` routines.
4. **Fix TD-14 before extending local routing (E2).** Privacy fails closed first, then optimize.
5. **Batch the monthly statement job (D)** for the flat 50%.

## Sources (2026, verify periodically — this space moves weekly)

- Claude Code best practices & changelog — https://code.claude.com/docs/en/best-practices ·
  https://code.claude.com/docs/en/changelog
- Token-saving techniques — https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/ ·
  https://www.mindstudio.ai/blog/how-to-manage-claude-code-token-usage
- Context management & subagents — https://www.tembo.io/blog/claude-code-subagents ·
  https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/
- Hybrid local/cloud routing — https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/ ·
  https://www.morphllm.com/claude-code-router ·
  https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- Pricing / caching / batch — https://www.finout.io/blog/anthropic-api-pricing ·
  https://aicostcheck.com/blog/ai-prompt-caching-cost-savings
- Prompt structure — https://claude.com/blog/best-practices-for-prompt-engineering
