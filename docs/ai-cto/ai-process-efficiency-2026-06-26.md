# AI process efficiency review — user ↔ AI workflow

**Date:** 2026-06-26 · **Author:** NARF (AI CTO), scheduled routine · **Status:** findings + recommendations

A review of how we spend tokens between the human and the AI across the A777ance repos, what
the current best practice is (mid-2026), and the concrete changes that would cut cost without
cutting capability. Findings are ordered **highest-leverage first**. Each is rated
**impact** (token/cost savings) × **effort**.

> **Why this changes fast:** caching rules, tool-loading mechanics, and routing tooling are
> shipping monthly. The "Staying current" section at the end is the part to re-run, not re-read.

---

## TL;DR — the five that matter

1. **Claude Code bypasses our own LiteLLM router entirely.** We built a hybrid local+cloud
   router (stage 10) to keep cheap work local — but our single biggest Claude consumer
   (Claude Code) talks straight to the Anthropic API and never touches it. The router saves
   us ~nothing on the bill that actually hurts. **(High impact / Medium effort)**
2. **~1,040 lines of CLAUDE.md auto-load every session** (326 localDNS, 295 DESIGN). Much of
   it is reference material — deploy-path tables, verification blocks, full known-issues
   tables — that belongs in files read *on demand*, not in the system prompt of every turn.
   **(High impact / Low effort)**
3. **No prompt-caching discipline on scheduled routines / Agent SDK work.** As of 2026-06-15
   Agent SDK + GitHub Actions are metered per-token, separate from interactive Claude Code.
   Routines like *this one* now have a real, recurring bill, and caching is the 60–90% lever
   we're not pulling deliberately. **(High impact / Low effort)**
4. **The dispatcher is designed but not built**, so model selection is still a human picking
   in Open WebUI. 60–70% of typical requests are simple enough for a local model; we're
   paying frontier rates (or human attention) for them. **(Medium impact / Medium effort)**
5. **We're already getting the new Tool Search win for free** (this session loads tools via
   `ToolSearch` on demand — ~85% fewer tool-definition tokens). Lean into it for any custom
   agents we build; don't regress to loading all tools upfront. **(Already winning / keep it)**

---

## 1. The big disconnect: Claude Code doesn't use our router

**Finding.** The whole point of `10-ai-orchestration/` is "route cheap/private work local,
overflow to cloud." But the tool we use most — Claude Code, in these repos — connects
directly to the Anthropic API. The LiteLLM front door at `ai.home.lan:4040` only sees traffic
from Open WebUI and (future) the dispatcher. So:

- The local Ollama tiers (`qwen2.5:3b/7b`) reduce our *chat* spend, not our *coding-agent* spend.
- Every Claude Code turn pays full cloud rates regardless of how trivial the task.

**What to do.** Two complementary moves:

- **Point an LLM router at Claude Code for the cheap turns.** Claude Code respects
  `ANTHROPIC_BASE_URL` / a custom endpoint. A drop-in OpenAI-compatible router (LiteLLM with
  `routing_strategy` by task, or a purpose-built proxy like NadirClaw) can send simple
  prompts to a local/cheap model and escalate hard ones to Opus/Sonnet — reported 40–70%
  savings. Caveat: routing Claude Code through a proxy can blunt Anthropic's own automatic
  prompt caching, so measure net effect before committing.
- **Or split the workloads by tool, not by proxy.** Keep Claude Code on the direct API for
  real engineering (where Opus/Sonnet quality pays for itself), and *deliberately* push the
  high-volume, low-stakes, privacy-sensitive jobs (log triage, draft summaries, classify a
  lead) through the local router. This is the cleaner version of the same idea and needs no
  proxy in the Claude Code hot path.

**Recommendation:** the second option first (zero risk to the coding workflow), then build the
dispatcher (§4) so "which jobs go local" is a rule table, not a habit.

---

## 2. CLAUDE.md is a reference manual where it should be a lookup table

**Finding.** Best practice (2026) is unambiguous: CLAUDE.md should read "more like a lookup
table than a giant brain dump." Ours has grown into a system reference. `localDNS/CLAUDE.md`
(326 lines) carries the full **deploy-path table** (40+ rows), a **verification command
block**, the **nftables deploy checklist**, and a **full known-issues table**. All of it loads
into the system prompt on *every* turn in that repo — and is mostly read-once reference, not
per-turn guidance.

**What to do (lossless — move, don't delete):**

- Keep in CLAUDE.md: the 1-paragraph "what this repo is," the hard invariants (push-to-main,
  honesty rule, privacy rules), and *pointers* to the reference docs.
- Move to on-demand files Claude reads when relevant: the deploy-path table → `DEPLOY.md`;
  the verification block → `VERIFY.md` (or leave in README); the nftables checklist →
  its own doc; the long known-issues table → `KNOWN-ISSUES.md`. CLAUDE.md links to them.
- Net effect: every session in `localDNS`/`DESIGN` starts lighter, and the reference is still
  one `Read` away when a task actually needs it.

**Estimate:** trimming the two big files from ~620 combined lines to ~150 of true per-turn
guidance saves roughly 3–5k tokens of *recurring fixed cost per session* in those repos —
multiplied by every interactive session and every scheduled routine.

**Caution:** don't strip the invariants — the privacy split, "honesty of the kept document,"
push-to-main. Those genuinely need to be in-context every turn. This is about relocating
*reference*, not *rules*.

---

## 3. Prompt caching — the 60–90% lever we're not pulling on routines

**Finding.** Interactive Claude Code already caches automatically. But our *programmatic*
surface — scheduled routines (this one), any Agent SDK scripts, the future dispatcher's cloud
calls — is where caching has to be done on purpose, and where, since 2026-06-15, we now pay
per-token separately.

**The rules that matter:**

- Cache reads cost ~10% of base input; cache writes cost ~25% more. Break-even ≈ 3 reads
  within the 5-min TTL (or 5 reads for the 1-hr TTL).
- Structure prompts **static-first**: system prompt → tool defs → big docs → *then* the
  dynamic user turn last. Put a cache breakpoint after the stable prefix.
- Use **mid-conversation system messages** (now supported) to update instructions without
  restating the whole prompt — preserves cache hits in agentic loops.
- 200K+ context no longer carries a premium; a 900K request bills at the same per-token rate
  as 9K. Counter-intuitively, giving the model *more* context can lower total tokens because
  it re-reads less.

**What to do:** when we write Agent SDK scripts or the dispatcher, enforce static-first
ordering + a breakpoint on the stable prefix, and prefer the Batch API (≈50% off) for any
non-interactive, latency-tolerant job (e.g. monthly statement copy passes, bulk lead triage).

---

## 4. Finish the dispatcher — make "go local" a rule, not a human

**Finding.** `ORCHESTRATION-BLUEPRINT.md` already specifies the right design: a *deterministic*
Python dispatcher (no LLM in the routing decision) that classifies → routes → integrates, with
a hard privacy lock. `dispatcher.py` is a runnable stub. Until it's built, a human picks the
model in Open WebUI for every job — and humans default to "use the big one."

**Why it pays:** typical task mix is ~60–70% simple, ~20–30% moderate, ~10% needs frontier
reasoning. A rule table that sends the 60–70% to `local-fast`/`local-smart` and reserves
cloud for the 10% is the documented 60–88% cost cut — and it's *free at the routing layer*
because the decision is `if/elif`, not inference.

**What to do:** execute Phase 3→4 of the blueprint. Keep the privacy gate deterministic
(sensitive → local-only, no cloud fallback) exactly as designed. Add the opt-in reflection log
so we can see, after a month, what actually routed where and tune the table with data.

**Optional enhancement (new since the blueprint):** LiteLLM now ships **semantic routing** and
**semantic caching** (embedding-match a new prompt to a prior one, return the cached answer).
For repetitive internal queries this catches repeats a literal cache misses. Worth a look once
the deterministic table is in — as an *addition under* the privacy gate, never replacing it.

---

## 5. Tool loading — we're already on the right side of this

**Finding.** Anthropic's **Tool Search Tool** loads tool definitions on demand instead of
dumping all schemas upfront — ~85% fewer tool-definition tokens (preserves ~191k vs ~123k
context in their benchmark). This very session uses it (`ToolSearch` + deferred MCP tools).

**What to do:** nothing to fix — just *don't regress*. If we build custom agents or wire many
MCP servers, keep tools deferred/searched, not all-loaded. A typical MCP agent otherwise burns
3–8k tokens of schemas on every single request.

---

## 6. Claude Code hygiene (habits, near-zero effort)

These are per-session habits that compound:

- **`/context`** before a big task — see exactly where tokens go (system prompt, tools,
  memory files, skills, history). It's how we'd *measure* finding #2.
- **Plan mode** (Shift+Tab) before expensive multi-file work — eliminates trial-and-error
  execution, the biggest single source of waste.
- **`/clear`** between unrelated tasks; **`/compact`** when continuing a long one.
- **Subagents for research/search** — verbose file-dumps stay in the subagent's context; only
  the conclusion returns. (This routine used that pattern.)
- **Specific prompts** — vague asks make Claude open files and reconstruct context you could
  have handed it. One good sentence of scope saves a dozen exploratory reads.
- **Cap tool output** (~8k) so a chatty command doesn't flood context.

---

## 7. Meta — this prompt, and this routine's own cost

**The prompt that triggered this review** was effective in intent but token-loose: it ended
with "ANYTHING that could help" and several open-ended sweeps. That phrasing invites broad,
unfocused exploration (more searches, more reading) than a scoped ask. A tighter version that
gets the same answer for less:

> *"Audit our user↔AI token spend across the repos. Rank the top 5 inefficiencies by
> $-impact, with a fix and rough savings for each. Cover: CLAUDE.md size, prompt caching,
> local-vs-cloud routing, and whether Claude Code should use our LiteLLM router. Check for any
> Anthropic pricing/feature changes in the last 30 days. One page."*

Same coverage, bounded scope, names the deliverable shape — cheaper to run and easier to act on.

**This routine itself** is now a metered, recurring cost (per the 2026-06-15 billing change).
It's worth it only when it surfaces something actionable; a "ran, all fine" pass should stay
silent (and it does). If we schedule more routines, apply §3 caching to them and keep their
prompts scoped like the rewrite above.

---

## 8. Staying current (re-run this, don't re-read it)

This space moves weekly. A standing low-cost way to keep up:

- **Anthropic release notes** (`releasebot.io/updates/anthropic`, the docs changelog) — scan
  monthly for pricing, caching, and tool-use changes. The big recent ones: Tool Search Tool,
  mid-conversation system messages, 200K+ premium removed, Agent SDK separate metering.
- **Re-run the audit quarterly**, not continuously — the inputs (model IDs, cache economics,
  routing tooling) change on that cadence, and a scoped quarterly pass beats a daily routine
  that mostly finds nothing.
- Track our own numbers: turn on the dispatcher's reflection log and `/context` spot-checks so
  next quarter's audit has data, not just best-practice citations.

---

## Sources

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Advanced tool use (Tool Search Tool)](https://www.anthropic.com/engineering/advanced-tool-use)
- [Anthropic release notes — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic)
- [Claude API prompt-caching & token-efficiency guide (hidekazu-konishi)](https://hidekazu-konishi.com/entry/anthropic_claude_api_prompt_caching_and_token_efficiency.html)
- [7 practical ways to reduce Claude Code token usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Best practices for Claude Code (docs)](https://code.claude.com/docs/en/best-practices)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [LLM gateways & model routing cost optimization (Lushbinary)](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [LiteLLM routing docs](https://docs.litellm.ai/docs/routing)
- [NadirClaw — local/cloud router proxy for Claude Code](https://github.com/NadirRouter/NadirClaw)
- [Anthropic subscription/metering changes, June 2026 (DevToolPicks)](https://devtoolpicks.com/blog/anthropic-splits-claude-subscriptions-agent-sdk-credit-june-2026)
