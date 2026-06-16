# AI process efficiency review — user↔AI workflow, token use, hybrid routing

**Date:** 2026-06-16 · **Author:** NARF (AI CTO) · **Trigger:** founder ask —
"locate inefficiencies in our PROCESS between the user and the AI; reduce token
use; better prompting; leverage other AI; hybrid local+Claude. Keep current."

**Scope:** how we work *with* Claude (Claude Code on the web, scheduled routines,
the LiteLLM/Ollama hybrid), not the network stack. Findings are ordered by
impact (biggest token win first), per the founder ask — this is not time-based,
so house-style reverse-chron doesn't apply.

---

## TL;DR — the five that matter

1. **Every session pays a huge fixed "session-start tax."** Our CLAUDE.md files
   are large *and* they instruct reading 4–10 more files before any work. A
   one-line task pays the same context bill as a major one. **Biggest single win.**
2. **We don't use prompt caching on the cloud tier.** Our system prompts /
   CLAUDE.md are stable across calls — textbook cache candidates. Caching cuts
   *input* cost 60–90% on the repeated prefix. We leave this on the table.
3. **We run Opus 4.8 for everything**, including doc edits and link-checking that
   Sonnet/Haiku — or our own local Ollama tier — would do at a fraction of the cost.
4. **The house-style "reverse the blocks, never renumber" rule is expensive** in
   both tokens and error-rate, and it's duplicated verbatim in 7 CLAUDE.md files.
5. **The triggering prompt is itself inefficient** — unbounded scope, no output
   target. Rewrite below.

Industry baselines for the levers we're missing: model routing + semantic
caching cut LLM cost **40–70%**; running simple work locally and reserving
frontier models for hard reasoning cuts **60–80%**; prompt caching cuts the
cached-prefix input cost **60–90%**.

---

## 1. The session-start tax (highest impact)

**What's happening.** `DESIGN/CLAUDE.md` is ~295 lines and ends with two
protocols that say, unconditionally, *at session start read*: `portfolio.md`,
`roadmap.md`, `tech-debt.md`, `decisions.md` (CTO) **plus** `ai-cfo/portfolio.md`,
`decisions.md`, `metrics.md`, `runway.md`, `budget.md`, and
`MARKETING/.../context.md` (CFO). That's **10+ files loaded before a single line
of work**, on every session, regardless of task. Most of our scheduled routines
touch one of them.

Why it's the top issue: this is the one cost paid *every* run, and it scales with
run frequency. A daily routine pays it 365×/yr whether or not the task needs the
CFO runway.

**Fixes (cheapest first):**

- **Gate the reading on task type.** Replace "read all of these at session start"
  with "read the index; read the rest *only if the task touches that domain*." A
  CTO task shouldn't auto-load all six CFO files and vice-versa.
- **Add a thin `INDEX.md` / one-screen state file** per hub that summarizes the
  current focus + pointers, so most sessions read *one* small file and pull the
  heavy ones on demand. (This is the "small summary back to the parent" subagent
  principle applied to our own docs.)
- **Trim CLAUDE.md to a router, not a manual.** CLAUDE.md is carried in context
  the *entire* session. Anything that's reference-only (full deploy-path tables,
  long known-issues) can live in README/INSTALL-NOTES and be read on demand. Keep
  CLAUDE.md to: what the repo is, the rules, and where to look. Target < ~120 lines.
- **De-duplicate the house-style block.** It is copy-pasted into all 7 CLAUDE.md
  files. Put it once in a `STYLE.md` (or a shared snippet) and point to it. Today
  every session in every repo re-loads the same ~25 lines.

---

## 2. Turn on prompt caching for the cloud tier

Our cloud calls (`cloud-overflow`, `cloud-explore`, `cloud-code`, `cloud-vision`
in `localDNS/10-ai-orchestration/config.yaml`) send a stable system prefix every
time. That's exactly what prompt caching is for: a cache *read* costs ~10% of
normal input, so a large stable prefix gets **60–90% cheaper** on the repeated
portion. Rule of thumb: worth it at **3+ reads within the 5-min TTL** (or 5+ for
the 1-hr TTL).

**Concrete steps:**

- LiteLLM supports Anthropic cache-control. Mark the stable system/context block
  as an `ephemeral` cache breakpoint so repeated routine calls hit the cache.
  Put the **stable content first**, volatile content last — cache hits require a
  byte-identical prefix up to the breakpoint.
- Claude Code on the web already caches its own system prompt; the win here is on
  *our own* LiteLLM-mediated calls and any agent loops we build.
- **Instrument cache-hit rate.** If we can't see it, we can't tune it. Add it to
  whatever we log from LiteLLM.

---

## 3. Match the model to the job (stop defaulting to Opus)

Our `config.yaml` already does this well for the *home* stack — `cloud-code` is
Sonnet, only `cloud-explore`/`cloud-vision` are Opus. **Apply the same discipline
to the Claude Code sessions themselves.** Doc edits, link-checks
(`tools/check-docs.py`), roster updates, and routine triage do not need Opus 4.8.

- Use **Haiku/Sonnet** for mechanical doc/code edits; reserve **Opus** for
  genuine architecture/strategy work. Most of our routine load is the former.
- **Push read-heavy work to subagents.** Anything that needs reading more than
  3–4 large files (e.g. "scan all repos for stale figures") should be a subagent:
  it runs in its own context and returns only a small summary, keeping the main
  session's context — and cost — small. This is the single most-cited 2026 Claude
  Code practice.

---

## 4. Use the hybrid stack we already built

We have a privacy-gated LiteLLM + Ollama hybrid (`local-fast`, `local-smart`,
`local-reason`, `local-embed`) on the t630, plus a deterministic dispatcher
design. It is **not in the loop** for our day-to-day AI work — Claude Code on the
web can't reach `ai.home.lan:4040` (LAN+WG only). That's a real gap:

- **Local-first for cheap, non-sensitive bulk text:** first-draft summaries,
  classification, embedding/RAG over our own repos, link-text rewriting. These
  are exactly the `40–80%` cost-saver tasks. Today they'd run on Opus instead of
  free local CPU.
- **The dispatcher is the right design** (rule-based, no LLM in the routing
  decision — debuggable and free). Worth *building* the stage-10 dispatcher so
  the routing we describe actually happens, rather than a human picking a model
  in Open WebUI.
- **Bridge gap to note for CTO roadmap:** there's no path today from a web-based
  Claude Code routine to the home LiteLLM. Either (a) accept that web routines are
  cloud-only and run hybrid work from a box on the WG net, or (b) expose a
  narrow, authenticated endpoint. Decide deliberately — don't port-forward 4040.

---

## 5. Routine cadence & caching of research

Scheduled routines that re-run web research every execution re-pay for findings
that change weekly, not hourly. For this kind of "keep current" routine:

- **Cadence:** weekly is plenty for "AI best-practices news"; daily burns tokens
  re-discovering the same articles.
- **Diff, don't dump:** have the routine read its *own last report* and emit only
  *what changed* — and **only notify when something actually changed** (silence on
  a no-change run is the correct, kind behavior for a routine nobody is watching).

---

## 6. The house-style "reverse the blocks" rule — reconsider it

The convention (newest-first logs *and* "present major blocks in reverse order,
keep steps forward, never renumber") is unusually expensive for an AI workflow:

- It forces a re-read to reconstruct intended order on **every** doc edit, and
  it's error-prone (easy to renumber by accident, or reverse steps that should
  stay forward). Every mistake is a correction round-trip = more tokens.
- The reverse-chron-for-logs part is standard and fine. The **reverse-the-blocks
  walkthrough rule is the costly, non-standard part.** Recommend: keep newest-first
  for time-based logs; **drop block-reversal for walkthroughs** (or scope it to a
  single showcase doc). Net: fewer tokens, fewer errors, easier onboarding.

This is a judgment call for the founder — flagging the cost, not overriding the
preference.

---

## 7. The triggering prompt — critique & rewrite (as asked)

**What made it inefficient:**
- **Unbounded scope** ("ANYTHING that could help… search the web… check the
  news") with **no output target, no budget, no priority** → invites an open-ended
  crawl and a sprawling answer.
- **Mixed registers** — strategy + token mechanics + prompt critique + a
  meta-request, in one go. Each wants a different depth.
- **No success criterion** — "better way" isn't measurable, so there's no natural
  stopping point.

**A tighter version:**

> "Audit how we work with Claude across the repos for token waste. Give me the
> **top 5 fixes ranked by token saved**, each with the concrete change and a
> rough % saving. Ground it in our LiteLLM config and CLAUDE.md files; cite 2–3
> current sources for any best-practice claim. **Output: one review doc, ≤2
> pages**, committed to `docs/ai-cto/reviews/`. Skip anything we already do well."

Why it's better: bounded (top 5, ≤2 pages, one doc), prioritized (ranked by
saving), grounded (names the files), verifiable (% + sources), and it tells me
where to put the result. Same answer, far fewer tokens spent circling.

**General prompting habits that save tokens for us:**
- State the **deliverable and its size** up front ("a 1-paragraph answer", "a
  diff", "a ≤2-page doc"). Open-ended asks produce open-ended (expensive) output.
- **Point at the files.** "Look at `config.yaml` and the 7 CLAUDE.md files" beats
  "look at our setup" — it stops exploratory searching.
- **Say what to skip** ("we already cache X; don't re-explain it").
- **One job per prompt** where practical; batch only truly independent asks.

---

## Recommended order of operations

| # | Action | Effort | Est. saving | Owner |
|---|--------|--------|-------------|-------|
| 1 | Gate session-start reads on task type; add per-hub INDEX | low | High (every session) | NARF |
| 2 | De-dup house-style into one `STYLE.md`, trim CLAUDE.md → router | low | Medium (every session) | NARF |
| 3 | Enable prompt caching + cache-hit logging on cloud tier | med | 60–90% on cached prefix | NARF |
| 4 | Default routine/doc work to Sonnet/Haiku; Opus only for strategy | low | High | founder |
| 5 | Weekly (not daily) "keep-current" cadence; diff-only reports | low | Medium | founder |
| 6 | Build the stage-10 dispatcher; route bulk text to local Ollama | high | 40–80% on routed tasks | NARF |
| 7 | Founder call: drop block-reversal walkthrough rule | n/a | Medium + fewer errors | founder |

---

## Sources (current as of 2026-06-16)

- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching for Claude: Cut Your API Bill 60% in Production — AI Magicx](https://www.aimagicx.com/blog/prompt-caching-claude-api-cost-optimization-2026)
- [Anthropic Claude API Prompt Caching and Token Efficiency Guide — hidekazu-konishi.com](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html)
- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Claude Code Advanced Best Practices 2026 — SmartScope](https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Context Window: Why It Burns Tokens Fast — The Prompt Shelf](https://thepromptshelf.dev/blog/claude-code-context-management/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid AI Architecture: Cloud Routing + Local Models — eLink Design](https://www.elinkdesign.com/hybrid-ai-architecture-cloud-routing-local-models-for-privacy-and-savings)
- [LLM Gateways & Model Routing: Cut AI Costs 2026 — Lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
