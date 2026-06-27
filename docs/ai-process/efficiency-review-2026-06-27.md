# AI Process Efficiency Review — 2026-06-27

How to cut token cost and improve the user↔AI process (Claude Code + the LiteLLM
hybrid). Findings are ordered by **leverage** (biggest, cheapest win first). Each
carries an effort tag and an honest estimate. Sources are listed at the end.

> One-line answer: **the savings are in context discipline and model-tiering, not in
> the local box.** The Carrizo CPU can't take real coding load off Claude — but a
> leaner always-on context, the right model per task, and prompt-cache hygiene can cut
> Claude Code spend materially without losing any capability.

---

## The five recurring costs in our process (where the money actually goes)

Every Claude Code turn re-sends the whole conversation **plus** the always-on context.
For us that always-on context is unusually heavy:

| Cost | What it is | Roughly |
| ---- | ---------- | ------- |
| **Always-on `CLAUDE.md`** | 6 repo briefings auto-injected | **~8,000 words ≈ ~11k tokens** (DESIGN 2,608w + localDNS 2,728w dominate) |
| **Mandated session-start reads** | NARF reads 4 files; ZORT reads 6 more | another several-k tokens, mostly unchanged run-to-run |
| **Model tier** | Opus 4.8 (1M) driving *everything*, incl. doc edits + this routine | Opus is $5/$25 per Mtok — the most expensive option for mechanical work |
| **Re-derivation** | Open-ended routines (like the prompt that triggered this) re-explore from scratch each run | unbounded; no diff against last run |
| **Cache misses** | Interleaving edits between session-start reads breaks the cached prefix | loses the 90%-off cached-read price |

---

## Recommendations (highest leverage first)

### 1. Halve the always-on context — trim every `CLAUDE.md` to a true one-pager · *effort: M · saves: large, every turn*

`CLAUDE.md` is paid on **every turn of every session**, so it is the most expensive text
we own. Ours are 3–5× the size Anthropic recommends (their own guidance: keep it short;
"if it grows too much it can cost more than it saves"). The DESIGN and localDNS files are
each ~2,700 words — they read like full handbooks, not briefings.

**Do:** cut each `CLAUDE.md` to ≤ ~400 words — identity, the 3–5 invariants, and *pointers*
to README/context files. Move the deploy-path tables, known-issues tables, and verification
command blocks into the README (read on demand, not always). The detail isn't lost; it just
stops being re-billed when it isn't needed.
**Expected:** ~11k → ~4k always-on tokens. On a heavy day of sessions this is the single
biggest line-item we control.

### 2. Match the model to the task — stop running Opus 4.8 for mechanical work · *effort: S · saves: large*

Opus is the right brain for hard reasoning (a tricky network bug, a pricing model). It is
the wrong brain for editing a doc, updating `portfolio.md`, or checking links — and it's
driving all of it, including this very routine.

**Do:**
- Default the driver to **Sonnet 4.6**; reserve **Opus** for genuinely hard reasoning (escalate with `/model` when you hit it).
- Use **Haiku 4.5** for mechanical/read-heavy turns (status updates, link-checks, log triage).
- In `localDNS/10-ai-orchestration/config.yaml`, the `cloud-overflow` tier is hardwired to
  `anthropic/claude-opus-4-8`. Make overflow **Haiku or Sonnet** and escalate to Opus only
  deliberately — today a local-tier failover spills straight onto the priciest model.

Anthropic's own subagent math: an orchestrator at ~$15/Mtok delegating to Haiku sub-agents at
~$0.25/Mtok is the intended cost structure. We're paying orchestrator rates for everything.

### 3. Delegate session-start reading to a Haiku subagent · *effort: S · saves: medium, every session*

NARF/ZORT session-start = "read 4–10 files into the expensive main context." Instead, spawn an
**Explore** subagent (read-only, runs on Haiku by default) that reads those files and returns a
~10-line digest. The full files never enter the Opus/Sonnet context; only the digest does.
Subagents are the documented #1 lever for context economy because they explore in a *separate*
window.

### 4. Collapse the NARF/ZORT protocol to one `state.md` read · *effort: M · saves: medium, every session*

The CTO protocol mandates 4 reads, the CFO 6 — most of it unchanged run-to-run. Maintain **one
compact, newest-first `state.md` per hub** as the single mandatory session-start read; everything
else becomes on-demand. This also fixes a real failure mode visible in `portfolio.md`: three
review cycles produced no shipped Statement partly because each session re-loads and re-reasons
over the same large state. A tight digest makes "what changed + the top 3 actions" the cheap
default.

### 5. Prompt-cache hygiene · *effort: S · saves: medium*

Cached input reads are **90% cheaper** (5-min TTL; the discount applies after a single re-read).
Claude Code caches automatically, but we defeat it by interleaving edits between the session-start
reads. **Do:** read all session-start files **first, in a stable order**, *then* start editing;
avoid mid-task `/compact` churn (compact only at ~40–50% context or when switching tasks). Keep
the heavy `CLAUDE.md` stable within a session so its prefix stays warm.

### 6. Be honest about the local box: it's a cheap-task tier, not a Claude replacement · *effort: — · saves: sets expectations*

The hybrid design (LiteLLM + Ollama + Claude overflow) is sound, and the privacy gate is the right
instinct. But the t630 is a **4-core Carrizo CPU with no usable GPU offload** running `qwen2.5:3b/7b`.
That cannot take the Claude Code *coding loop* off our hands — it's too slow and not capable enough,
and the README already documents that heavy reasoning cooks the CPU. Industry data says ~60–70% of
LLM calls are "simple" (classify/extract/format) and *those* can go local for 60–80% savings — but
our expensive workload is interactive coding/writing, which is the 10% that genuinely needs a
frontier model.

**Realistic local roles:** embeddings (already local — good), log/DNS-stats triage and
classification, first-draft summaries that Claude then refines, the "Handled For You" log
boilerplate. **Not** the main build loop. Expect privacy + a cheap-task tier from the box — **not**
a cut to Claude Code spend. The Claude Code savings come from #1–#5.

### 7. Close TD-14 while you're in the config anyway · *effort: S (3-line) · saves: correctness, not tokens*

Already flagged by NARF as the only P1 fixable without box access: `local-reason` falls back to
`cloud-overflow`, so a **sensitive** task can fail *open* to Claude cloud if the local model is down —
the opposite of what three comments in the file promise. Chain `local-reason` to local-only
(`["local-smart","local-fast"]`) and remove `cloud-overflow` from any chain a sensitive task reaches.
A false privacy claim is worse than none. (Included here because #2 touches the same file — do both
in one edit.)

---

## On the prompt that triggered this routine

You asked me to critique it, so: it's an excellent **one-off brainstorming** prompt and an
**expensive recurring** one. "Locate inefficiencies… is there a better way… ANYTHING that could
help… search the web… check the news" is wide-open with no stop condition — so on a schedule it
re-explores the entire space from scratch every run, on Opus, and tends to re-surface the same
findings. The irony: the prompt asking how to save tokens is itself a token sink when looped.

**Keep it as-is for a quarterly deep-dive.** For anything recurring, make it scoped + incremental:

> *"Review our AI process for token efficiency. Read `docs/ai-process/efficiency-review-*.md`
> (the latest) and `state.md` first. Report only: (a) what has changed since that review,
> (b) any genuinely new best practice from the last N weeks, (c) the top 3 concrete actions
> with effort/savings. If nothing material changed, say so in one line and stop. Run on Sonnet."*

Why that's cheaper and better: it diffs against a saved baseline instead of re-deriving it, names a
hard stop ("say so and stop" — which, per the routine model, means *no notification* on a quiet
run), caps the output, and pins a cheaper model. Also consider **lowering its frequency** — process
best-practices move week-to-week in headlines but month-to-month in things actually worth changing.

---

## Suggested order of operations

1. **Today (S):** fix TD-14 + retarget `cloud-overflow` off Opus (#2, #7) — one edit.
2. **This week (S):** switch the default driver to Sonnet, Haiku for mechanical turns (#2);
   adopt cache hygiene (#5); rewrite the recurring prompt (above).
3. **This month (M):** trim all six `CLAUDE.md` to one-pagers (#1); collapse NARF/ZORT to one
   `state.md` + Explore-subagent session start (#3, #4).

#1 alone is the big one; #2 is nearly free and large. Together they should cut typical
per-session token cost by roughly half with **zero** loss of capability.

---

## Sources (current as of 2026-06-27)

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Code Context Window: Optimize Your Token Usage](https://claudefa.st/blog/guide/mechanics/context-management)
- [Claude Code Sub-Agents Explained: Context, Cost, and Parallel Execution — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization Guide](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Router — Load Balancing — LiteLLM docs](https://docs.litellm.ai/docs/routing)
- [Claude Code June 2026: 10 New Features — SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
