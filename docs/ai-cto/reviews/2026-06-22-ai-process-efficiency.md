# AI Process Efficiency Review — 2026-06-22

**Scope:** the *process* between the human and the AI (Claude Code / Claude API) across the
A777ance repos — where tokens (and money) leak, how to prompt better, and how to lean harder
on the hybrid local-LLM stack we already run. Researched against current (June 2026) best
practice; sources at the bottom.

**Bottom line:** the single biggest leak is **repeated context we pay for on every run** —
this routine alone reloads ~6 full `CLAUDE.md` files *plus* the entire `claude-api` skill on
each scheduled fire, most of it irrelevant to the task. Fixing context + model selection +
caching is worth a conservatively estimated **60–90% cut** on our agent token spend, and we
already own the hybrid plumbing (the LiteLLM reasoning ladder in `localDNS`) to capture most
of it. None of this requires new infrastructure — it's configuration and discipline.

---

## 1. Findings, highest-leverage first

### F1 — Recurring routines reload the whole world every run *(biggest single leak)*
This very session preloaded all repo `CLAUDE.md` files and the full `claude-api` skill — tens
of thousands of tokens — before reading the task. The harness itself flags it: *"this context
may or may not be relevant."* For a **scheduled, unattended routine** that re-fires on a
cadence, that fixed preamble is paid for on every run, forever.

- **Fix:** scope each routine to the repo(s) it touches. A "watch the funnel / check status"
  routine does not need `localDNS`'s Unbound config or the 9-language `claude-api` skill in
  context. Trim the routine's repo scope and skill set to what the job reads.
- **Impact:** the largest, most repeatable saving we have, precisely because it recurs.

### F2 — `CLAUDE.md` files are brain-dumps, not lookup tables
Our `DESIGN/CLAUDE.md` is the full funnel narrative (stage map, money flow, philosophy). A
published 2026 benchmark stripped a 3,847-token `CLAUDE.md` to 312 tokens — *only what Claude
can't infer from the code* — for **91.9% context reduction with no quality regression** (~$460/mo
saved from one file). We already have the long-form home for the narrative: `README.md`,
`workflow-context.md`, `LAUNCH-NOTES.md`.

- **Fix:** make `CLAUDE.md` a lookup table (paths, invariants, the few non-obvious rules).
  Push the "why" and the prose into the README/context docs that already exist, and move
  occasional procedures into **skills** that load only when invoked.
- **Watch:** keep the house-style block — it's load-bearing — but the funnel diagram and the
  multi-paragraph philosophy can be a one-line link.

### F3 — This routine runs on Opus 4.8; a watcher rarely needs it
Opus is ~5× Sonnet per token, and Sonnet/Haiku are fine for monitoring, status checks, and
extraction. Best practice is **start on the cheap model, escalate only for genuine reasoning**.

- **Fix:** run scheduled watcher/monitor routines on **Sonnet 4.6** (or **Haiku 4.5** for
  pure checks) with **`effort: "low"`**. Reserve Opus 4.8 + high effort for real architecture,
  refactors, and hard debugging — invoked deliberately, not as the default for a cron job.

### F4 — Prompt caching: we may be invalidating our own prefix
Caching cuts the cost of a stable prefix by ~90% (cache reads ≈ 0.1× input), and Claude Code
caches automatically — *if the prefix stays byte-stable*. Anything volatile injected early
(a `currentDate`, a per-run ID, unsorted JSON) silently busts the cache for everything after
it. Our session injects `currentDate` — confirm it isn't sitting ahead of the cached prefix.

- **Fix:** keep `CLAUDE.md`/system frozen; put volatile per-run context at the *end* of the
  prompt, not the front. Verify with `usage.cache_read_input_tokens > 0` across runs.

### F5 — We already own the hybrid local/cloud stack — use it harder
`localDNS` stage 10 (LiteLLM + the reasoning ladder: `local-reason` deepseek-r1:1.5b on the
t630, `cloud-gpu-reason`, `cloud-overflow`) is exactly the architecture the industry is
reporting **60–80% cost cuts** from. Typical task mix: ~60–70% simple (classify/extract/format),
~20–30% moderate, ~10% needs a frontier model. Route the first two tiers local.

- **Fix:** push classification, extraction, formatting, and the cheap parts of scheduled
  routines to the local model; reserve the Claude API for the ~10% that needs it.
- ⚠️ **Blocker:** **TD-14** — `local-reason`'s fallback chain can fail *open* to
  `cloud-overflow` (Claude cloud) for a `sensitive`-tagged prompt if the local model is down.
  Do **not** route sensitive customer data through the local tier until that fails *closed*.

### F6 — Session hygiene (the slow, invisible drain)
Long threads re-read the entire conversation every turn. Best practice: **one task per chat**,
`/compact` to summarize, `/recap` (new Apr 2026) to resume without replaying, `/context` to
find bloat, and **subagents** to keep verbose fan-out (searches, log dumps) out of the main
context — only the summary returns. June 2026 shipped subagent transcript + backgrounding
fixes, so this is now reliable.

### F7 — Batch API for bulk, non-interactive work (50% off)
Anything not latency-sensitive — e.g. generating the monthly Statements at scale (stage 06),
bulk lead enrichment — belongs on the Batch API at **half price**. As we add households this
compounds.

---

## 2. On *this* prompt (the one that triggered this review)

It asked, honestly: *"ANYTHING that could help… search the web… check the news."* That openness
is friendly to a human but **expensive to an agent** — an unbounded "find everything" prompt
invites broad, Opus-priced exploration. It also reads like a one-off research ask, yet runs as
a recurring routine, so it re-pays that exploration every fire.

**Better shape for a recurring efficiency routine:**
- Name the **target** ("audit token spend in DESIGN + MARKETING," not "anything").
- State a **budget/threshold** so it only escalates when something crosses it.
- Make it **diff-based** ("what changed since last run") so steady-state runs are cheap and
  silent, and it only pings when there's something to act on.
- Pin it to a **cheap model + low effort**; let it escalate to Opus only on a real finding.

---

## 3. Recommended actions (in order)

1. **Scope routines** to their repos/skills (F1) — biggest recurring win, do first.
2. **Move scheduled watcher routines to Sonnet/Haiku + `effort:low`** (F3).
3. **Slim `CLAUDE.md` → lookup table**, prose to README/skills (F2).
4. **Verify cache hits**; move volatile content to the prompt tail (F4).
5. **Expand local-tier routing** once **TD-14 fails closed** (F5).
6. **Adopt `/context`, `/compact`, `/recap`, subagents** as standing hygiene (F6).
7. **Move bulk/offline jobs to the Batch API** (F7).

---

## Sources

- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [12 Ways to Cut Token Consumption in Claude Code (Firecrawl)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Reduce Claude Code token usage by 90% (Medium, Apr 2026)](https://medium.com/data-science-in-your-pocket/reduce-claude-code-token-usage-by-90-baa2a27b9ca3)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026, SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Updates — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-code)
