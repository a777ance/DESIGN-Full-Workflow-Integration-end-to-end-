# AI process efficiency — how we work with Claude & where the waste is

**Owner:** NARF (AI CTO) · **First written:** 2026-06-19 · **Audience:** founder + future operators

A standing note on the *process* between the human and the AI: where tokens (and money,
and attention) leak, what to do about it, and what's worth ignoring. Time-based entries
below read newest-first per house style. **Re-check the "What changed recently" section
roughly monthly — this space moves week to week.**

---

## 0. The one-line answer

We are not short on AI *capability* — stage 10 already gives us a local-first router with
a cloud fallback. We are short on **discipline in the loop**: open-ended prompts, long
unbroken sessions, and re-sending the same context. The cheapest wins are behavioral
(how we ask) and cache-shaped (what we keep stable), not architectural. Build the
dispatcher *later*; fix the habits *now*.

---

## 1. Where the process leaks (ranked by payoff)

| # | Leak | Why it costs | The fix | Effort |
| - | ---- | ------------ | ------- | ------ |
| 1 | **Unbounded prompts** ("anything that could help", "do the whole module") | Invites the model to load and reason over everything; output balloons | Scope every ask to one file/function/decision. "Refactor the login function in `auth.ts`" beats "refactor auth." | Free, today |
| 2 | **One long session for unrelated work** | The whole transcript re-bills as input on every turn; cache goes cold after 5 min idle / fully cold by ~30 min | `/clear` between unrelated tasks; `/compact` with instructions on what to keep; `/recap` instead of re-reading on resume | Free, today |
| 3 | **Verbose exploration in the main thread** | Searching/reading dumps thousands of tokens into the context you pay for on every later turn | Delegate fan-out reads to **subagents** — verbose work stays in their throwaway context, only the conclusion returns | Free, today |
| 4 | **Cold cache / shuffled prompt prefixes** | A cache *read* is ~10% of input price; a miss is full price. Any change at position N busts everything after N | Keep stable content (CLAUDE.md, tool defs, system context) at the *front* and unchanged; put the variable stuff last. Enable 1h caching for long sessions | Low |
| 5 | **Frontier model on trivial work** | Opus-class pricing on classification/formatting/extraction that a 3B local or Haiku does fine | Route the ~60–70% of simple turns down a tier (local-fast / Haiku); reserve Opus for the ~10% that needs it | Medium (this is the dispatcher) |
| 6 | **Sensitive data going to cloud** (privacy *and* cost leak) | TD-14: a `sensitive` task can still fail over to `cloud-overflow` | Give `local-reason` a local-only fallback chain — fail closed | Low; already tracked |

Rule of thumb from the field: **session management beats a bigger window.** A 1M context
window is a tool, not a default — at standard rates now (the 2× long-context premium was
removed March 2026) it's cheap to *have* but still expensive to *fill* every turn.

---

## 2. Critique of the prompt that asked for this

The request that generated this note is itself exhibit A:

> "Locate inefficiencies… Anything you could possibly think of… Leveraging other AI…
> Running a hybrid… ANYTHING that could help. Search the web… Keep UP TO DATE… Check
> the news."

What it does well: states the goal, grants tool latitude (web search), invites a
self-critique. What makes it expensive:

- **No scope ceiling.** "ANYTHING" has no stopping rule, so the agent fans out maximally
  — more searches, more reading, more output than a decision usually needs.
- **Several distinct asks bundled into one** (token use *and* prompting *and* hybrid
  routing *and* news). Each would cache and clear better as its own scoped turn.
- **No output shape named.** "Let me know" leaves format open; the agent guesses long.

A tighter version, same intent:

> "Review our Claude usage for the top 3 token-waste patterns and one prompting fix
> each. Check whether anything shipped in Claude Code in the last 30 days changes our
> stage-10 plan. Output: a ranked list, ≤1 page. Skip the deep web survey unless a
> finding hinges on it."

That keeps the curiosity but bounds the spend and names the deliverable. **The pattern:
goal + scope ceiling + output shape.** (This note is longer than one page only because
it's a *kept* reference doc, not a chat answer — which is itself the right call: write
the durable version once, then point future prompts at it instead of re-deriving.)

---

## 3. Hybrid local + cloud — what we have, and the honest gap

We already designed the right thing. `localDNS/10-ai-orchestration/` is a LiteLLM front
door with local Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` :7b,
`local-reason` deepseek-r1:1.5b), a rented-GPU heavy tier, and Claude as
`cloud-overflow`. The blueprint's instinct is correct and matches 2026 best practice:
**route simple/repetitive/sensitive work local, send the ~10% hard reasoning to a
frontier API.** Reported savings for that pattern run 60–80%.

Two honest gaps:

1. **The dispatcher is "design, not built."** Today a human picks the model in Open
   WebUI. Until the deterministic `dispatcher.py` is wired in front of LiteLLM, the
   routing savings are theoretical. Good news: the rule-table design is right (no LLM in
   the routing decision — free, deterministic, debuggable). It just needs building.
2. **This router does not (and cannot easily) front Claude *Code* itself.** Claude Code
   talks to Anthropic directly; it won't transparently route its own turns through our
   t630. So the hybrid router is for *our apps and chat*, not for cutting Claude Code's
   bill. **Don't conflate the two** — the lever for Claude Code cost is §1 (habits +
   caching + subagents + model choice per task), not the LiteLLM router.

Where the local box genuinely earns its keep: drafting, classification, summarizing
statement data, the privacy-locked `sensitive` lane, and "submit-and-wait" batch jobs
the CPU can chew on overnight. Keep frontier Claude for the hard reasoning and the
final, customer-facing prose.

---

## 4. What changed recently (re-check monthly)

*Newest first. Sourced June 2026 — verify before relying on a figure.*

- **2026-06** — Claude Code added **usage attribution** (Account & usage dialog shows
  cache misses, long-context, subagents, per-skill/agent/MCP breakdown over 24h/7d).
  *Action:* read it before optimizing — measure the actual leak, don't guess.
- **2026-06** — **Subagents matured**: can nest up to 5 deep, run in parallel, each with
  its own fresh context; `/agents` UI to manage them. *Action:* use for fan-out
  exploration; but note the cautionary tale — one runaway 49-subagent parallel session
  was estimated at **$8k–15k**. Parallelism cuts wall-clock, not necessarily cost. Bound it.
- **2026-04** — **`/recap`** command: summary of where you left off without replaying the
  whole transcript on resume.
- **2026-03** — **1M context GA** and the **2× long-context price premium removed** for
  Opus 4.6 / Sonnet 4.6. Big windows are cheaper to hold, still costly to fill.
- Ongoing — **Prompt caching**: cache reads ~10% of input price; one bug-fix task
  measured $0.54 cached vs $1.35 uncached (~2.5×). Largest single config lever for API use.

---

## 5. Recommendations (do in this order)

1. **Adopt the prompt pattern** (goal + scope ceiling + output shape) and stop one-shot
   "do everything" asks. Free, biggest lever. (§2)
2. **`/clear` and `/compact` discipline** between tasks; `/recap` on resume. Free. (§1.2)
3. **Push fan-out reads to subagents**, bounded — keep the main thread lean. (§1.3)
4. **Turn on / verify prompt caching** for long sessions; keep CLAUDE.md and tool defs
   stable at the prompt front. (§1.4)
5. **Close TD-14** — local-only fallback for the `sensitive` lane (privacy + cost). (§1.6)
6. **Build the stage-10 dispatcher** (deterministic Python rule table) so simple/sensitive
   turns actually land local instead of needing a human to pick. Medium effort, real
   recurring savings — but it's for *our apps*, not Claude Code's own bill. (§3)
7. **Read the new usage-attribution panel first** on any future "cut costs" push — measure,
   then cut. (§4)

---

## Sources

- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — agensi.io](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [Claude Code changelog — Claude Code Docs](https://code.claude.com/docs/en/changelog)
- [Claude Code Sub-Agents Explained — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Claude Code 1M Context Window: Cost, Limits, When to Use — claudecodecamp.com](https://www.claudecodecamp.com/p/claude-code-1m-context-window)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide (2026) — buildmvpfast.com](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [The State of Coding Agents Using Local LLMs — Feb 2026 (Medium)](https://medium.com/@rontom/the-state-of-coding-agents-using-local-llms-february-2026-83259140e6ec)
