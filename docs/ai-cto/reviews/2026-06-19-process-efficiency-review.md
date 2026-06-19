# 2026-06-19 — Process efficiency review: user ↔ AI, token spend, hybrid routing

**Ask:** find inefficiencies in how we work with the AI; cut token use; better prompting;
leverage local LLM + Claude API hybrid. Keep current (researched 2026-06-19).

**Verdict in one line:** the single biggest waste is **CLAUDE.md bloat — ~14.6K tokens
loaded on every session before a word is typed** — and we've *built* a hybrid local/cloud
router but **don't route anything cheap to it**. Both are fixable this week. Detail below,
newest-priority first.

---

## 1. CLAUDE.md bloat — the top win (P1, easy)

Every CLAUDE.md loads in full on **every turn**, before Claude reads the task or any code.
Measured today:

| Repo | CLAUDE.md size | ~tokens |
| ---- | -------------- | ------- |
| localDNS | 20.5 KB | ~5,100 |
| DESIGN (this repo) | 18.0 KB | ~4,500 |
| MARKETING | 10.7 KB | ~2,700 |
| customers | 4.1 KB | ~1,000 |
| claude-code-homelab | 2.9 KB | ~720 |
| Azure-lab | 2.3 KB | ~570 |
| **Total** | | **~14.6K** |

2026 best practice is **keep CLAUDE.md under ~500 tokens — a lookup table, not a brain
dump.** Ours are 5–10× that. This very routine paid ~14.6K input tokens of CLAUDE.md
context before starting, on a task that needed almost none of it.

**Fix:** Each CLAUDE.md keeps only (a) the voice/house-style one-liners, (b) the
"read these N files at session start" pointers, and (c) a 1-line-per-section index. Push the
deep tables (deploy-path map, Unbound drop-in table, known-issues matrix) into the existing
`README.md` / `network-context.md` / per-folder READMEs they already duplicate, and let
Claude read them **on demand**. The house-style block (~250 tokens) is repeated verbatim in
all 6 files — factor it into one `STYLE.md` and point at it.
Expected: ~14.6K → ~3K, with prompt caching making the rest nearly free within a session.
Verify each trim with `/context` before/after.

> ⚠️ Don't over-trim: CLAUDE.md content is *cached* (90% cheaper on warm reads), so the win
> is real but second-order within a long session. The clean win is **short idle bursts +
> caching**, not gutting guidance that prevents re-work (re-work costs far more than the
> context it'd have saved).

## 2. Cloud-overflow points at Opus — a cost trap, and it's also the TD-14 leak (P1)

`localDNS/10-ai-orchestration/config.yaml` sets `cloud-overflow: anthropic/claude-opus-4-8`.
That is **the failover for the cheapest local tiers**. So when the t630 is busy/down, a
classification/extraction/formatting task that `local-fast` (qwen2.5:3b) should handle spills
to **the most expensive model we pay for**. Asymmetric and silent.

- **Fix the cost:** make `cloud-overflow` → `anthropic/claude-haiku-4-5` (or `sonnet-4-6`).
  Reserve `opus-4-8` for the `cloud-explore`/`cloud-vision` tiers that actually need it.
- **Same line is the open privacy bug (TD-14):** `local-reason`'s fallback chain reaches
  `cloud-overflow`, so a `sensitive` task fails *open* to cloud. Give `local-reason` a
  **local-only** fallback (fail closed). One edit closes a cost trap and a P1 privacy gap.

## 3. We built the hybrid — now actually use it (P2, high payoff)

The router, the local Ollama tiers, the LangGraph privacy gate: all built. But **interactive
Claude Code sessions hit Opus directly** and the cheap local tiers sit idle. 2026 hybrid
guides report **60–80% cost cuts** because ~60–70% of real workload is simple
(classify/extract/format/commit-message) and belongs on a local model.

What to move to `ai.home.lan:4040` (local-first), keeping Claude Code for the hard 10–30%:
- Commit-message + PR-body drafting, changelog stitching.
- `tools/check-docs.py`-style lint triage, link-fix suggestions.
- Roster/statement data classification + extraction (also keeps PII *inside the walls* —
  the whole point of the privacy gate).
- The daily `docs/ai-cto/reviews/` first-pass draft — local model drafts, Claude reviews.

Heuristic: **draft local, judge/finish with Claude.** Claude API is the frontier tier, not
the default tier.

## 4. Claude Code session habits (P2, free)

- **One task per session.** Don't carry an unrelated task into a warm context — start fresh.
- **`/compact` deliberately** at natural breakpoints instead of letting auto-compaction fire
  at the worst moment; **`/context`** to audit what's loaded; **`/recap`** on resume instead
  of replaying history.
- **Work in focused bursts** — the prompt cache stays warm ~5 min; idle gaps re-bill cold.
- **Subagents for heavy reads.** Multi-file sweeps, "audit all repos," research — delegate so
  the verbose context stays in the subagent and only the conclusion returns to main. (This
  routine did that for the web research.)
- **Pick the model to the task** — Haiku/Sonnet for mechanical edits, Opus for design.

## 5. New 2026 features worth adopting (P3, watch)

- **Context editing** — programmatic removal of stale turns; better than blunt compaction for
  long sessions.
- **Skills pipelines** — `.claude/skills/<name>/SKILL.md`; chain so one skill's output feeds
  the next. Chronikomicon already has a `.claude/` + session-start hook; the other repos have
  none — standardize a session-start hook that runs `check-docs.py` and the right reads.
- **Outcomes / grader** — define a rubric, a grader sends the agent back until it passes.
  Good fit for "a Statement only ships with numbers the box measured" (the honesty rule) and
  for the doc-integrity gate.
- **Dreaming** — scheduled review of past sessions that curates memory. Maps cleanly onto our
  daily-review cadence; could auto-summarize recurring mistakes into the trimmed CLAUDE.md.

## 6. The prompt that requested this review was itself inefficient

The request was open-ended — *"ANYTHING that could help… search the web… check the news"* —
with no scope, no output format, no length bound. That invites a sprawling, expensive
exploratory session and risks an unfocused answer. It worked out, but the cheaper, sharper
version is a **scoped, output-shaped** prompt:

> "Audit our Claude usage for token waste. Cover only: (1) CLAUDE.md size, (2) the
> local/cloud router config, (3) session habits. For each, give the finding, the token/£
> cost, and the one-line fix. ≤1 page. Cite 2026 sources. Don't read repo code beyond the
> two config files named."

Pattern to reuse for routines: **state scope, name the files, fix the output shape, bound the
length, and say what *not* to do.** A vague prompt is a token cost like any other.

---

## Do-this-week shortlist

1. Trim all 6 CLAUDE.md to a lookup table + extract shared house-style to `STYLE.md`. (#1)
2. One edit to `config.yaml`: `cloud-overflow` → Haiku, and `local-reason` → local-only
   fallback. Closes a cost trap **and** TD-14. (#2)
3. Route commit messages / doc-lint / data extraction to `ai.home.lan:4040`. (#3)
4. Adopt one-task-per-session + `/context` audits + burst working. (#4)

## Sources (researched 2026-06-19)

- [Manage costs — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM Model Routing in 2026: Cost-Quality Optimization — Digital Applied](https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide)
- [Claude Code Guide 2026: 25 Features — MarkTechPost](https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/)
- [Code with Claude 2026: 5 New Agent Features — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
