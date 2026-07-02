# Process efficiency audit — user ↔ AI token & workflow (2026-07-02)

NARF (AI CTO) note. Question posed: *where are the inefficiencies in how we work with
Claude, how do we cut token use, prompt better, and leverage our own local LLMs / a hybrid
setup?* This is the answer, ranked by **impact ÷ effort** — do the top three first.

Grounded in two things: (1) a measurement of our own repos, and (2) current (mid-2026)
published best practice. Sources at the bottom. Keep this doc fresh — the guidance below
moves month to month.

---

## TL;DR — the five moves that matter

| # | Move | Effort | Est. saving | Why |
| - | ---- | ------ | ----------- | --- |
| 1 | **Trim the CLAUDE.md files** (they total ~58 KB ≈ 15 K tokens, loaded *every* session, *every* repo) | 1 afternoon | ~50–60% of per-session baseline | Anthropic's own rule: a 5 K-token CLAUDE.md costs 5 K tokens before you type a word. Ours are 3–4× that. |
| 2 | **Stop running every session on Opus.** Default to Sonnet 5; use `opusplan`; Haiku for mechanical jobs | minutes | ~50% of model spend | Three-tier routing is ~51% cheaper than uniform Opus at comparable quality (Anthropic's published figure). |
| 3 | **Point the *dev* drudge-work at the local router we already built.** localDNS stage 10 (LiteLLM + Ollama) serves the homelab chat — not our dev loop. Wire embeddings, doc-lint, commit-message drafts, bulk classify/summarize to it | half a day | 8–10× on those tasks | The rig exists and is idle for this purpose. Offloading non-reasoning work is the biggest documented hybrid win. |
| 4 | **Protect the prompt cache**: keep CLAUDE.md + the enabled MCP set *stable* per repo, and only enable the MCP servers a repo needs | ongoing habit | up to 90% on repeated context | Cache reads are ~10% of input cost — but only on a stable prefix. A changed CLAUDE.md or tool list busts it. |
| 5 | **Cap tool-output drain**: targeted reads/grep over whole-file reads, fan research out to sub-agents, `/compact` on long sessions | ongoing habit | the single biggest silent drain | Our big docs are landmines: `localDNS/README.md` is 68 KB, `network-context.md` 48 KB, `INSTALL-NOTES.md` 28 KB. One full read of each dumps ~35 K tokens into context that then rides every subsequent turn. |

---

## 1. CLAUDE.md bloat — the standing tax (biggest lever)

Measured today:

```
20 KB  localDNS/CLAUDE.md         (326 lines)
18 KB  DESIGN-.../CLAUDE.md       (295 lines)
11 KB  MARKETING/CLAUDE.md        (214 lines)
 4 KB  customers/CLAUDE.md
 3 KB  claude-code-homelab/CLAUDE.md
 2 KB  Azure-lab/CLAUDE.md
────
~58 KB  ≈ ~15 K tokens loaded at the top of every session in that repo
```

Two of these (`localDNS`, `DESIGN`) are on their own 3–4× the size Anthropic recommends.
Specific fixable waste, some of it already flagged in `RECOMMENDED-CHANGES.md`:

- **The house-style block is duplicated 6× verbatim** (~1.5 KB each ≈ 9 KB / ~2.3 K tokens
  total). Pure redundancy and a known drift risk. Fix: one canonical
  `house-style.md`, and each CLAUDE.md keeps a one-line pointer instead of the full block.
- **`localDNS/CLAUDE.md` re-prints README tables** (services/ports, WireGuard peers,
  hardware, the DNS-split narrative). Nominate one file canonical, link from the other.
- **Six "read these files at session start" bootstraps** (NARF + ZORT reading lists) force
  large reads every session. Collapse to a single short pointer; let the agent pull the
  detail only when a task needs it.

Target: every CLAUDE.md ≤ ~150 lines / ≤ 6 KB — a lean briefing plus pointers, detail lives
in README and gets read on demand. Realistic outcome: cut the per-session baseline ~50–60%,
which — because it recurs on *every* turn via the cached prefix — is the highest-value change
on this list.

## 2. Model routing — stop paying Opus rates for Sonnet work

This very routine ran on **Opus 4.8** to audit some docs — a job Sonnet does at a fraction of
the cost. Concretely:

- **Default new sessions to Sonnet 5** (`/model sonnet`). Introductory pricing is $2/$10 per
  M tokens through 2026-08-31, then $3/$15 — still ~5× cheaper than Opus.
- **Use `opusplan`** for planning-heavy work: Opus reasons through the plan, Sonnet executes
  the edits. Best of both for refactors/architecture.
- **Haiku 4.5** for mechanical jobs: doc link-checking (`tools/check-docs.py` babysitting),
  commit-message drafts, renames, log triage.
- **Scheduled routines (like this one) should default to a cheaper model** — recurring cost,
  low reasoning bar. Set the routine's model to Sonnet or Haiku.
- **Sub-agent models**: when we fan work out, pass `model: haiku`/`sonnet` to the cheap legs
  and reserve Opus for the synthesis leg.

Published three-tier routing (Opus plan / Sonnet build / Haiku edit) runs ~$0.98/session vs
~$2.02 uniform-Opus — a 51% cut, no quality loss on the mechanical legs.

## 3. Use the hybrid rig we already built — for the *dev* loop, not just chat

`localDNS/10-ai-orchestration/` is a mature LiteLLM router: local Ollama tiers
(`qwen2.5:3b/7b`, `deepseek-r1:1.5b`, `nomic-embed-text`), a rented-GPU reasoning tier, cloud
overflow to Claude, capability-named tiers, and a deterministic privacy gate. **But it fronts
Open WebUI / the homelab assistant — it is not in our Claude-Code development path at all.**
That's the gap.

What to move onto local tiers (the documented 8–10× wins are exactly here — non-reasoning,
format-tolerant, short-context):

- **Embeddings / RAG** — already have `local-embed`; make sure our doc search uses it, not a
  paid embedding call.
- **Commit-message and PR-body first drafts**, changelog bullets, release notes.
- **Doc link/anchor checking and lint** — mechanical, no frontier model needed.
- **Bulk classification / first-pass summarization** of logs, "Handled For You" entries,
  call notes.

Keep on Claude (local models degrade here — long context >~3 K tokens, strict output format,
multi-step reasoning): real code generation, refactors, the architecture/CFO reasoning, and
anything customer-facing where a wrong figure is expensive.

**Config nit:** the router's `cloud-overflow` tier is pinned to `claude-opus-4-8` — the most
expensive model as the *default spillover*. Make overflow `claude-sonnet-4-6` (or Haiku) so an
accidental spill doesn't bill at Opus rates; escalate to Opus only deliberately.

## 4. Protect the prompt cache

Claude Code caches by default and cache **reads cost ~10%** of normal input — but only against
a *stable* prefix (CLAUDE.md + system + tool schemas). Every time CLAUDE.md changes or a
different MCP set is enabled, the prefix changes and the cache misses. So:

- Keep CLAUDE.md **short and stable** (reinforces move #1).
- **Only enable the MCP servers a repo actually needs.** The GitHub MCP server alone exposes
  ~60 tools; their schemas ride in the context tax whether or not you use them. Scope per repo.
- **Batch related work into one warm session** rather than many cold ones — each fresh session
  re-pays the full CLAUDE.md + tool-schema cost before the cache warms.

## 5. Cap tool-output drain (the silent one)

Per current best-practice write-ups, *tool output* — not your messages — is usually the
biggest context drain: everything a tool returns is appended and then rides every later turn.
Our repos are full of large files (`localDNS/README.md` 68 KB, `network-context.md` 48 KB,
`INSTALL-NOTES.md` 28 KB). Habits that help:

- **Targeted reads** (offset/limit, grep for the section) instead of whole-file reads.
- **Fan research out to sub-agents / the Explore agent** — the big file dumps stay in the
  sub-agent's context and only the conclusion comes back to the main thread. (This audit did
  that: `wc`/`sed` snippets, not full reads.)
- **`/compact`** at natural breakpoints on long sessions; **`/clear`** between unrelated tasks.
- **Force structured output** (JSON/table) where you're going to parse it — cuts output tokens
  60–80% vs prose.

---

## On the prompt that triggered this (you asked)

The prompt was **effective at getting breadth but expensive by design.** Phrases like
"ANYTHING that could help," "Perhaps also," and "Anything you could possibly think of" tell the
model to maximize exploration — so it fans out wide, reads more, and writes long. Great for a
one-time deep sweep; wasteful as a recurring routine.

What makes a prompt like this cheaper *and* sharper:

1. **Give it a target and a budget.** "Cut our monthly Claude spend; find the 5 highest
   impact-per-effort moves" beats "anything that could help." A ranked shortlist is cheaper to
   produce and more useful than an exhaustive survey.
2. **Bound the research.** "Check 2–3 reputable sources from the last 60 days" instead of
   open-ended "keep up to date / check the news" — same freshness, far fewer fetches.
3. **Fix the output shape.** "Return a ranked table + a one-paragraph rationale each" caps
   output tokens and forces prioritization.
4. **Split scope from delivery.** One line for the ask, one for constraints, one for format.

A leaner rewrite that would have cost markedly less for the same answer:

> *"Audit our Claude usage across the repos for token waste. Rank the top 5 fixes by
> impact-per-effort — cover CLAUDE.md size, model routing, and using our local LLM rig. Check
> 2–3 sources from the last ~60 days. Return a table (fix / effort / est. saving / why) plus
> one paragraph each. Flag if this prompt itself is inefficient."*

Same coverage, a fraction of the tokens — and it names the format so the model stops when
it's done rather than free-associating.

---

## Sources (mid-2026, verify freshness on re-read)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Model configuration — Claude Code Docs](https://code.claude.com/docs/en/model-config)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [23 Tips for Smart Claude Code Token Saving](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid LLM Routing: Ollama + Claude API Without Quality Degradation](https://dev.to/lokyfour/hybrid-llm-routing-ollama-claude-api-without-quality-degradation-5e5b)
- [Run Local AI Models with Claude Code to Cut Costs 10x](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Best Model for Claude Code (2026): Opus vs Sonnet vs Haiku](https://www.morphllm.com/claude-code-models)
