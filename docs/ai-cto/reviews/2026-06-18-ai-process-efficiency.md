# AI process efficiency review — 2026-06-18

NARF (AI CTO), prepared as a scheduled routine. Scope: the **user ↔ AI process** —
how we drive Claude (Claude Code on the web, the API, the scheduled routines) and the
hybrid local/cloud stack on the t630 — looking for token waste, better prompting, and
ways to lean on cheaper compute. Findings are ordered highest-leverage first.

> The field moves weekly; treat dated claims as of 2026-06-18 and re-check the linked
> docs before acting. Sources at the bottom.

---

## TL;DR — the five that matter

1. **Trim the `CLAUDE.md` files. This is the biggest, most certain win.** Across the six
   repos they total ~58 KB (~15k tokens) and **all of them load into context on every
   turn**, never evicted. The DESIGN one is 18 KB, localDNS 20 KB — each far past the
   "lean lookup table" line. Target ≤ ~1.5–2 KB each; push rationale into the
   already-existing `*-context.md` / README files that are read on demand.
2. **Turn on prompt caching for any repeated API work** (statement runs, the routines,
   the LiteLLM cloud tiers). 90% off cached input tokens. Single highest-leverage API
   lever in 2026.
3. **Move non-interactive work to the Batch API.** Monthly statement generation and
   these scheduled routines are async by nature → unconditional 50% off, and it *stacks*
   with caching (~10× cheaper combined).
4. **Right-size the model.** Default Claude Code to Sonnet; reserve Opus for genuinely
   hard reasoning. The cloud failover tiers currently pin Opus 4.8 for everything —
   expensive for a fallback.
5. **Actually route bulk/low-sensitivity work through the local LiteLLM gateway** you
   already built. Today it sits beside the Claude Code workflow, not in front of it, so
   the t630 isn't offsetting day-to-day spend.

---

## A. Token waste we can measure right now

- **`CLAUDE.md` bloat (certain).** Numbers above. These files are persistent context, so
  every byte is paid on every request of every session. Keep each to: how to run/verify,
  the house-style rules, the deploy-path table, hard invariants. Everything narrative
  (the funnel story, the Norse-named orchestration lore, design rationale) belongs in a
  read-on-demand file. Rule of thumb from Anthropic's own guidance: CLAUDE.md is a lookup
  table, not a brain dump.
- **MCP tool surface.** The GitHub MCP server exposes ~60 tools; each tool schema is
  context. Where a CLI exists it's cheaper than an MCP server (no per-tool listing). In
  this sandbox `gh` isn't available so MCP is the right call here — but on a normal Claude
  Code workstation, prefer `gh`/`aws`/`gcloud` CLIs and only enable the MCP servers a
  given repo actually needs.
- **Long threads.** Every message re-sends the whole conversation. Use `/clear` between
  unrelated tasks and `/compact` at phase boundaries. For the 1M-context Opus we're on,
  the big window is a temptation, not a license — discipline saves more than the window
  buys.
- **Verbose tool output.** Cap tool output (~8k chars) and prefer a `Grep`/hook that
  returns only matching lines over reading whole logs/files. We already have
  `tools/check-docs.py`; a `SessionStart` hook that runs checks and greps instead of
  Claude reading files wholesale would keep the cheap work off the model.

## B. API-level cost levers (for the statement pipeline + routines)

- **Prompt caching (90% off cached input).** Put static content first (system prompt,
  tool defs, the statement template, any large doc), dynamic content last. Min 1,024
  tokens per cached block; pays for itself after ~1.4 reads. **Pitfall:** never put a
  live timestamp inside the cached prefix — it busts the cache every call; truncate to
  the day or move it after the breakpoint. As of 2026-02-05 caches are workspace-isolated.
- **Batch API (50% off, unconditional).** Use it whenever no human is staring at the
  screen: monthly statement generation, lead enrichment, log triage, and these routines.
  Discount applies even to a 10-request batch. Stacks with caching.
- **Server-side compaction & context editing (2026 betas).** For long-running agents,
  server-side compaction auto-summarizes history near the window limit (beta header
  `compact-2026-01-12`); context editing clears stale tool results/thinking blocks
  (`context-management-2025-06-27`). The **memory tool** lets an agent persist a summary
  to files and learn across sessions — a fit for the recurring CTO/CFO state updates we
  already do by hand.
- **Right-size models.** Opus ≈ 5× Sonnet per token. Sonnet 4.6 is the code/diff sweet
  spot; Haiku 4.5 (1-hour cache TTL) is ideal for classification/extraction/triage.

## C. The hybrid stack — good design, one gap

The LiteLLM + Ollama setup (`localDNS/10-ai-orchestration/`) is genuinely well thought
through: capability-named tiers, a deterministic privacy gate that pins sensitive tasks
local, graceful local→cloud fallback, and the reasoning ladder (light distill local →
full R1 on a rented GPU → cloud overflow). Industry reports put hybrid local/cloud
savings at 60–88% for the right workload mix. Two refinements:

1. **Put the gateway in the path of real work.** Right now Claude Code (web/API) doesn't
   call `ai.home.lan:4040`, so the t630 isn't offsetting our actual usage. Pipe the
   bulk/low-sensitivity, non-coding tasks — draft generation, classification, log/lead
   triage, embeddings for RAG — through the local gateway first; reserve the Claude API
   for the hard reasoning and the customer-facing prose. That is exactly the
   data-sensitivity / complexity / availability split the README already describes.
2. **Don't pin Opus on every cloud tier.** `cloud-overflow`, `cloud-explore`, and
   `cloud-vision` all map to `claude-opus-4-8`. A fallback path that's always the most
   expensive model defeats the point of having tiers — point overflow at Sonnet (or
   Haiku for the light ones) and escalate deliberately.

## D. Prompting — including the prompt that triggered this review

The meta-prompt that launched this routine was effective at intent but loose in form:
open-ended ("ANYTHING that could help"), a little redundant ("Thanks!" twice), and it
mixed the ask with the meta-ask. That's fine for a human-to-human brief; for a *recurring
automated* routine it's worth tightening, because a vague prompt makes the agent read
more widely (more tokens) to guess scope. A tighter version:

> *Audit our AI usage process (Claude Code, the API, the t630 LiteLLM stack) for token
> waste and cost. Return: (1) the 3–5 highest-leverage fixes with rough $/token impact,
> (2) any prompting or config changes, (3) one current best-practice we're not using.
> Check the web for 2026 updates. Skip anything already in place. Be concise.*

General prompting practices that save tokens and rework: be specific about files/symbols
("add validation to `login()` in auth.ts", not "improve the codebase"); use **plan mode**
before big changes so we approve the approach before expensive edits; delegate verbose
*searching* to subagents so only the conclusion returns to the main thread; and tell the
model the output format and length you want up front.

## E. Suggested next actions (cheap → impactful)

- [ ] Trim all six `CLAUDE.md` to lean lookup tables; relocate narrative to `*-context.md`.
      (Pure win, no downside, recoups ~15k tokens/turn.)
- [ ] Add prompt-caching breakpoints to the statement generator and the cloud LiteLLM tiers.
- [ ] Move statement generation + routines onto the Batch API.
- [ ] Repoint `cloud-overflow`/`cloud-explore`/`cloud-vision` off Opus where Sonnet/Haiku suffice.
- [ ] Route bulk/non-sensitive tasks through `ai.home.lan:4040` before hitting the Claude API.
- [ ] Add a `SessionStart` hook that runs `check-docs.py` + greps, instead of Claude reading files.
- [ ] Adopt `/clear` between unrelated tasks and `/compact` at phase boundaries as habit.

---

## Sources (as of 2026-06-18)

- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Pricing — Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Context editing — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Automatic context compaction — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction)
- [Context engineering: memory, compaction, tool clearing — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude Batch API cost optimization](https://claudeapi.com/en/blog/dev-guides/claude-batch-api-cost-optimization/)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Implementing LLM Model Routing with Ollama and LiteLLM](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
