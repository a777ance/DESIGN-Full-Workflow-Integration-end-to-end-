# Process efficiency — user ↔ AI token & workflow audit

**Date:** 2026-06-28 · **Owner:** NARF (AI CTO) · **Scope:** how we *work with* Claude (and other
models), not what we build. Goal: same output, fewer tokens, better prompts, smarter model mix.

This audits the **interaction process** between the founder and the AI across the A777ance repos,
ranks the inefficiencies by payoff, and ties each to a concrete fix. Where useful it cites
current (June 2026) best practice. Numbers are token estimates (≈ bytes ÷ 4).

---

## TL;DR — the five wins, ranked by payoff

| # | Fix | Saves / session | Effort |
| - | --- | --------------- | ------ |
| 1 | **Start Claude Code *inside the repo you're working on*, not in `/home/user`** | ~12k tokens | zero — just `cd` first |
| 2 | **Move the duplicated "House style" block to one global memory file** | ~2.5k tokens | 30 min |
| 3 | **Make the CTO/CFO "read these 10 files at session start" reads *lazy*** | ~8–10k tokens | 20 min |
| 4 | **Tier the model: Haiku/Sonnet default, Opus only for hard reasoning** | up to ~95% on routine turns | ongoing habit |
| 5 | **Route Claude Code through the existing LiteLLM/Odin gateway (hybrid local + cloud)** | 60–80% on simple turns | ~half a day |

Wins 1–3 are pure structural cleanup with no quality cost. They alone cut the **per-session
baseline from ~25k tokens of context-before-you-type down to ~3–5k.**

---

## 1. The big structural leak: the session preamble

Every session pays for context *before the first instruction is read*. Today that baseline is large.

### 1a. All seven `CLAUDE.md` files load at once (~14.5k tokens, every session)

Because work happens with `/home/user` as the working directory and every repo is a subfolder,
Claude Code pulls in **all seven** `CLAUDE.md` files on every session — even when the task touches
only one repo:

| File | Size | ≈ tokens |
| ---- | ---- | -------- |
| `localDNS/CLAUDE.md` | 20.5 KB | ~5,100 |
| `DESIGN-…/CLAUDE.md` | 18.0 KB | ~4,500 |
| `MARKETING/CLAUDE.md` | 10.7 KB | ~2,700 |
| `customers/CLAUDE.md` | 4.1 KB | ~1,000 |
| `claude-code-homelab/CLAUDE.md` | 2.9 KB | ~725 |
| `Azure-lab/CLAUDE.md` | 2.3 KB | ~575 |
| **Total** | **~58 KB** | **~14,500** |

> A 5,000-token `CLAUDE.md` costs 5,000 tokens before you've typed a word, every turn, every
> session — a constant baseline you carry at all times. ([systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation))

**Fix (free, biggest single win):** open the session *in the repo you mean to work on*
(`cd localDNS && claude`), not in the parent that contains all of them. That drops 5 of 6
sibling files and ~10–12k tokens of irrelevant context on a typical single-repo task — and it
also *sharpens* answers, because the model isn't carrying six other businesses' rules.
Reserve a `/home/user`-level session only for genuinely cross-repo work (like this audit).

### 1b. The "House style" block is copy-pasted into all 7 files (~2.5k tokens of pure duplication)

The identical ~360-token *House style: ordering & typography* block appears verbatim in every
`CLAUDE.md`. When the parent dir loads them all, that's ~2,500 tokens of the same text, 7×.

**Fix:** it's described as applying to "**every** A777ance repo — current and future." That is
the exact definition of **user-level memory**. Put it once in `~/.claude/CLAUDE.md` (global,
loaded in every session regardless of repo) and delete the seven copies, leaving a one-line
pointer. DRY, and the rule lives in one place when it changes.

### 1c. The mandatory "read these files at session start" ritual (~8–10k tokens)

`DESIGN-…/CLAUDE.md` instructs NARF to read 4 files and ZORT to read 6 files **at the start of
every session** (`portfolio.md`, `decisions.md`, `roadmap.md`, `tech-debt.md`, `metrics.md`,
`runway.md`, `budget.md`, the spoke context, …). A session that obeys both burns ~10k+ tokens
re-reading state it usually doesn't need for the task at hand.

**Fix — make the reads lazy, not mandatory.** Reword the instruction from "at session start,
read 1–6" to: *"When the task is CTO/CFO portfolio work, read the relevant file(s) below; for a
focused code or doc change, skip them."* This is the documented pattern — load reference material
on demand rather than front-loading it. Pairs naturally with the **memory tool** (below), which
lets the agent consult a file-backed store only when it needs it.

---

## 2. Prompt caching — make the stable prefix actually stick

Anthropic prompt caching collapses repeated context to ~10% of the input rate on a cache hit, and
Claude Code uses it automatically for the system prompt + `CLAUDE.md`. Two habits keep the cache hot:

- **Keep the front of the context stable.** The cache matches a *prefix*; the cached content must
  be byte-identical across requests. The session-start file-reads in §1c can vary in order and
  bust the prefix — another reason to make them lazy and deterministic.
- **The TTL is 5 min (refreshed on each read).** A steady stream of turns keeps a hot prefix alive
  for ~10% cost; long idle gaps let it expire. Batch related work into one sitting rather than
  many cold starts. ([prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching))

Reported real-world savings from caching + context discipline land in the **60–90%** range.
([Tygart](https://tygartmedia.com/anthropic-prompt-caching-90-percent-token-savings/),
[DEV](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49))

---

## 3. Model tiering & the hybrid local/cloud play (you're already half-built for this)

> Opus output tokens cost nearly **19×** more than Haiku. A 5,000-token task is ~$0.375 on Opus
> vs ~$0.02 on Haiku — and that compounds over hundreds of tasks.
> ([systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation))

Most agent workloads split ~60–70% simple / 20–30% moderate / ~10% needs-a-frontier-model. Sending
all of it to Opus overpays on the 90%. ([sitepoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/))

**3a. In Claude Code today:** default to Sonnet, drop to Haiku for routine edits/formatting/renames,
and switch to Opus (`/model`) only for genuinely hard reasoning. Lower or disable extended thinking
on easy turns (`MAX_THINKING_TOKENS=8000`, or effort `low`) — thinking tokens bill as output.

**3b. The hybrid play you've already scaffolded.** `localDNS/10-ai-orchestration` already runs a
**LiteLLM gateway + Ollama local models + a cloud-GPU reasoning tier**, orchestrated by Odin, with a
documented reasoning ladder (`local-reason` → `cloud-gpu-reason` → `cloud-overflow`). That is exactly
the intelligent-routing layer the 2026 hybrid guides describe (LiteLLM as gateway, Ollama local,
Claude as the cloud tier) — teams report **60–80% cost cuts, up to 10×** with this shape.
([mindstudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs),
[buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026))

  The missing link: **point Claude Code's `ANTHROPIC_BASE_URL` at your LiteLLM gateway** so the
  dev process itself rides the same router — simple turns answered by the local t630 model, hard
  turns failing over to Claude. **One caveat, flagged as a hard blocker:** this collides with open
  tech-debt item **TD-14** — `local-reason`'s fallback chain can spill a `sensitive` task to
  `cloud-overflow` (Claude cloud). Do **not** route privacy-sensitive dev work (anything touching
  the private `customers`/`MARKETING` repos) through the gateway until TD-14 is fixed (fail-closed,
  local-only fallback). Until then, keep sensitive sessions on a direct, audited path.

---

## 4. Newer Anthropic features worth turning on

- **Context editing + memory tool** (GA-ish, public beta): auto-trims stale tool calls/results as
  the window fills, and gives the agent a file-backed store outside the context window. Anthropic's
  own benchmark: **+39% on long multi-step tasks**, and **−84% tokens** on search-heavy runs.
  Directly relevant to the CTO/CFO "read all the state" routines and to long agentic sessions.
  ([Anthropic](https://www.anthropic.com/news/context-management),
  [context-editing docs](https://platform.claude.com/docs/en/build-with-claude/context-editing))
- **Subagents for heavy context** (now up to 3 levels deep, with **per-agent cost attribution**):
  push token-heavy exploration into a subagent and keep the main session lean — like this audit,
  which fanned its web research out rather than dumping it into the main thread.
  ([Claude Code what's-new](https://code.claude.com/docs/en/whats-new))
- **`/compact` early, `/clear` between unrelated tasks, `/rewind`** to recover from a bad `/clear`.
  Compact while the session is still healthy — waiting for the warning yields a worse summary.

---

## 5. Was the *request* that triggered this audit efficient? (you asked — honestly, no)

The founder's prompt was: *"Locate inefficiencies in our PROCESS… Is there a better way… Perhaps
also better prompting… Anything you could possibly think of. Leveraging other AI… ANYTHING that
could help. Search the web… Keep UP TO DATE… Check the news."*

It's a **strong intent wrapped in an unbounded scope.** "Anything you could possibly think of" +
"ANYTHING that could help" + "check the news" with no target, no budget, and no format invites the
model to research broadly and write long — which costs the most tokens of any prompt shape. What
makes a prompt cheap *and* sharp:

1. **Name the deliverable + length.** "A ranked one-page memo, top 5 fixes, each with a token
   estimate" → bounded output instead of an open essay.
2. **Set a scope boundary.** "Focus on the Claude Code session workflow; skip model-training and
   non-Claude tooling" → no wasted exploration.
3. **Give a budget / depth dial.** "≤6 web sources, ≤15 min" → caps the research fan-out.
4. **State the success test.** "Each fix must save measurable tokens or name a feature we're not
   using" → filters fluff.
5. **Drop the intensifiers.** "ANYTHING / anything you can think of" doesn't add information; it
   just widens the search. The specific verbs ("reduce token use," "hybrid local+Claude," "better
   prompting") already carried the intent.

**A tighter rewrite of the same request:**

> *"Audit how we work with Claude across the repos for token waste. Deliver a ranked one-page memo:
> top 5–7 fixes, each with an estimated token saving and the effort to do it. Cover (a) per-session
> context baseline, (b) prompt caching, (c) model tiering / our LiteLLM hybrid, (d) any new
> Anthropic feature we're not using. Use ≤6 recent sources. Skip anything not about the
> Claude-interaction process."*

Same answer, a fraction of the tokens, and it forces the ranking up front. (For recurring asks like
this, save it as a Claude Code **slash command** so it's one keystroke and identical every time —
which also keeps the cache warm.)

---

## Sources

- Claude Code cost optimisation — [systemprompt.io](https://systemprompt.io/guides/claude-code-cost-optimisation)
- Prompt caching — [Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Tygart](https://tygartmedia.com/anthropic-prompt-caching-90-percent-token-savings/)
- Context editing & memory tool — [Anthropic news](https://www.anthropic.com/news/context-management) · [docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- Hybrid local + cloud routing — [SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) · [MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs) · [buildmvpfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- Claude Code June 2026 features — [What's new](https://code.claude.com/docs/en/whats-new) · [SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
- Token reduction methods — [KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage) · [agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
</content>
</invoke>
