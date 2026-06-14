# Human ↔ AI process efficiency

A standing audit of *how we work with the models* — where the user↔AI loop wastes
tokens, money, or trust, and the highest-leverage fixes. Findings are newest-first
(house style). This is the operations counterpart to the architecture in
`localDNS/10-ai-orchestration/` (the **Odin**/LiteLLM ladder) — that repo owns the
*plumbing*; this doc owns *how we spend through it*.

**Bottom line up front:** the architecture is already right (local-small-first, cloud
overflow). The waste is in **execution**, in this order of leverage:
1. Prompt caching is not deliberately exploited (≈90% off repeated context).
2. The hybrid ladder isn't load-bearing yet — routing is manual (Open WebUI dropdown),
   so most real work still hits the cloud by default.
3. We pay interactive (full) price for work that is batchable at 50% off.
4. A sensitive prompt can still fail over to the cloud (TD-14) — a trust cost, not a token cost.

Dated context (verify before acting — this field moves weekly): 2026 LLM pricing is up
("no more cheap Claude"), so optimization pays more than it did six months ago. And a
March 2026 prompt-caching bug caused 10–20× silent token inflation — **always verify
cache hits**, never assume them.

---

## The findings (newest first)

### PE-08 — This routine's own prompt is broad and will re-pay its research cost every run
The prompt that generated this doc ("locate inefficiencies… leverage other AI… search
the web… check the news… ANYTHING") is open-ended by design, which is fine for a
one-off but expensive as a *scheduled* routine: each run re-does the same web research
from scratch and re-derives the same conclusions, burning tokens on ground already
covered. **Two fixes:** (a) scope future runs to a concrete deliverable — e.g. "diff
`config.yaml` and the CLAUDE.md files against last run; report only what changed and any
new token-waste"; (b) make it **diff-based** — this doc is now the baseline, so the
routine should update findings, not regenerate them. An open "explore everything"
instruction also invites wandering; a scoped instruction with a named output is both
cheaper and more reliable.

### PE-07 — Right-size the model per task; stop defaulting to Opus
The cloud tiers already encode this (`cloud-code` → Sonnet, `cloud-explore`/`overflow`
→ Opus), but the *default* path and our Claude Code habits don't. Routine repo work —
doc edits, link-checking (`tools/check-docs.py`), summarizing a log, classifying a lead
— is Haiku/Sonnet work. Reserve Opus for genuine multi-step reasoning. In Claude Code,
the **effort** parameter is the dial: `high` is the sweet spot for most coding;
`xhigh`/`max` only when correctness outranks cost; `low` for subagents and simple tasks.
Lower effort also means fewer tool calls and less preamble — a compounding saving.

### PE-06 — Batch the non-interactive work (50% off, same models)
Anything that doesn't need a human waiting is a candidate for the **Message Batches API**
(half price, ≤24 h turnaround, all features incl. caching):
- **Monthly statement generation** (stage 06) — we build one per household "at a penny a
  home"; a month's worth is a textbook batch job, not N interactive calls.
- **Lead classification / enrichment** (stages 02–03), bulk summarization, the doc-check
  sweep across repos.
Combine with a shared cached system prefix per batch and the per-statement cost drops
again. Interactive price should be reserved for things a person is actually waiting on.

### PE-05 — Retrieve, don't paste: lean on the local RAG index
`localDNS` already runs a **local embeddings tier** (`local-embed` / nomic-embed-text,
"Mímir's well") for Huginn's RAG — index build and query never cross the Bifröst. Use it
as the default way to answer "what does the repo say about X" instead of pasting whole
files (or whole CLAUDE.md files) into a cloud prompt. Embeddings are free (local) and
turn a 5k-token paste into a 300-token retrieved snippet. This is the cheapest, most
private layer we have and it's under-used in day-to-day work.

### PE-04 — The hybrid ladder is scaffolded but not load-bearing — finish the auto-router
Industry hybrid setups report **60–85% blended-cost reduction** by serving routine/bulk
work from a small local model and routing only hard reasoning to a frontier API. We have
the parts (`local-fast` qwen2.5:3b, `local-smart` 7b, the reasoning ladder, cloud
overflow) but routing today is **manual** — a human picks the model in the Open WebUI
dropdown, and scripts hit whatever they're pointed at. So in practice most real work
defaults to the cloud and the local tier idles. The **LangGraph supervisor**
(`langgraph-router/` — Heimdall gate → Odin musters the host) is the missing piece: it's
the deterministic classifier that sends "cheap/sensitive → local, hard → cloud"
automatically. Until it's deployed and in the request path, the cost ceiling is "cloud
for everything." **Prioritize standing it up** — it's where the 60–85% lives.

### PE-03 — Keep the cloud tier honest about what it's worth (measure, don't assume)
The t630 is CPU-bound and memory-bandwidth-limited; a 7B local model is "submit and
wait," not interactive. So the honest split is: local for **privacy-sensitive and
high-volume-but-latency-tolerant** work, cloud for **interactive and hard-reasoning**
work. Don't force interactive chat onto the local 7B (frustration is a cost too), and
don't send a batch summarization job to Opus. Time a representative prompt on the box
(`README` "measure, don't trust this page") and let the measured tok/s decide the
boundary, rather than guessing.

### PE-02 — Prompt caching is the single highest-leverage unused lever
Cache **reads cost ≈10%** of full input; **writes ≈125%**, so it pays back after the
second hit. Two places we repeat large stable context and should be caching it:
- **Claude Code / cloud sessions over these repos.** Every session re-sends the CLAUDE.md
  briefings. They're large and *should* be cacheable — but caching is a strict **prefix
  match**: any byte change before the breakpoint invalidates everything after it. So
  **keep CLAUDE.md short and stable, and never interpolate a volatile value** (a
  `datetime.now()`, a per-session ID) into it. The static "(Adopted 2026-06-05)" dates
  are fine; a *live* date would silently kill the cache for the whole file.
- **LiteLLM cloud calls** (`cloud-*`) with a shared system prefix — put the stable prefix
  first, the per-request question last, one `cache_control` breakpoint at the boundary.
**Verify it works:** check `usage.cache_read_input_tokens` > 0 across repeated calls. If
it's zero, a silent invalidator is at work (the March-2026 bug, a moving date, unsorted
JSON, a varying tool set). Caching you *assume* is worse than none — it hides the leak.

### PE-01 — Sessions rot; clear and scope them (this is where the biggest real-world bills came from)
Public 2026 write-ups put most of their savings (one case: **$2,400 → $680/mo, −72%**)
not on exotic features but on **session hygiene**: `/clear` between unrelated tasks,
finishing a task before the context drifts, not leaving a heavy session idle for hours
("context rot" — quality drops *and* every later message re-pays for stale tokens). For
us: one focused session per stage/repo, clear when switching repos, and prefer many
small scoped sessions over one sprawling one. Free, immediate, and the highest ROI of
anything here.

---

## Cross-references
- Architecture & the routing ladder: `localDNS/10-ai-orchestration/README.md`,
  `ORCHESTRATION-BLUEPRINT.md`, `config.yaml`.
- **TD-14** (tech-debt.md): sensitive→cloud failover gap — the trust cost. Fixing the
  auto-router (PE-04) and TD-14 are the same workstream: the deterministic gate that
  decides "local vs cloud" is also what enforces "sensitive fails closed, never to cloud."
- Honesty rule (CLAUDE.md §3): applies here too — don't claim a cache hit or a cost
  saving the `usage` numbers don't show.

## Sources (2026, verify before acting — fast-moving)
- [Claude Code token optimization (2026 guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [Manage costs — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Token economics in 2026: no more cheap Claude](https://age-of-product.com/token-economics-2026/)
- [Hybrid AI strategy — 50% cost reduction (2026)](https://www.oflight.co.jp/en/columns/hybrid-ai-cloud-local-llm-cost-reduction-2026)
- [Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
