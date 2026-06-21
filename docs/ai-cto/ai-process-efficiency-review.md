# AI process efficiency review

> Routine output — NARF (AI CTO). Reviews how we work *with* the AI: token spend, the
> user↔AI loop, prompting, and the local+Claude hybrid. Reflects practice current to
> **2026-06-21**. Newest entry first, per house style.

---

## 2026-06-21 — Baseline review

**Verdict: the expensive decision is already made correctly.** The local-first dispatcher
(`localDNS/10-ai-orchestration`) — deterministic routing, local models as default, Claude
as overflow-only — is exactly the architecture the 2026 hybrid playbooks converge on, and
it's where the 60–80% of cost savings live. There is no big structural win left to find.
The remaining gains are **token hygiene** and **the human↔AI loop**, not architecture.

The items below are ranked by payoff ÷ effort.

### A. Token-reduction wins (ranked)

1. **Trim the two large `CLAUDE.md` files — paid on every session.**
   `DESIGN/CLAUDE.md` is ~2,600 words (~3.5k tokens) and `localDNS/CLAUDE.md` ~2,700
   (~3.6k). In Claude Code these load into *every* prompt in the session; the weight is
   paid on every turn, not once. 2026 guidance is explicit: keep project instructions
   short. Target: cut each to a ~1-page briefing + links to the detail files (README,
   network-context, workflow-context already hold the depth). Likely ~40–50% off the
   per-session fixed cost on the two hub repos. *Effort: low. Payoff: high (recurs every session).*

2. **Persist NARF context across runs so prompt caching actually hits.**
   `DESIGN/tools/ai-cto.py` already sets `cache_control: ephemeral` on the portfolio block
   (good), but `load_context()` re-reads the 5+ context files every run and the ephemeral
   cache only lives ~5 min — so a weekly run never reuses it. Either (a) batch the
   weekly NARF + ZORT calls into one session so the cache is warm, or (b) accept it's a
   weekly cold start and don't over-engineer. The real fix is #1 (smaller context) more
   than caching here. *Effort: low. Payoff: low–med.*

3. **Deploy the Haiku 4.5 tier — it's configured but "not deployed."**
   60–70% of real LLM traffic is classify / extract / format work. Those should never
   touch Opus. Add `cloud-cheap: claude-haiku-4-5` ($1/$5 per MTok vs Opus $5/$25) and
   route short, low-reasoning cloud tasks there. For privacy-safe simple tasks the local
   `qwen2.5:3b` already handles this for free — Haiku is for the simple-but-must-be-cloud
   slice. *Effort: low. Payoff: med.*

4. **Use the Batch API (50% off) for non-interactive jobs.**
   The weekly NARF/ZORT review and any bulk statement generation (stage 06) are not
   latency-sensitive. The Message Batches API is half price on all tokens, most batches
   finish in <1h. Wire NARF's weekly run and statement builds through it. *Effort: med.
   Payoff: med (recurring).*

5. **Cache GitHub fetches and the embedding index in the router.**
   `langgraph-router/tools.py` re-downloads files from the GitHub API on every
   `gather_context()`, and `rag.py` re-embeds all chunks on every index rebuild. Add a
   short-TTL local cache for fetches (invalidate on push) and only rebuild the index on
   detected git change. Saves latency and GitHub quota more than tokens, but it's cheap to
   do. *Effort: low–med. Payoff: low (tokens) / med (latency+quota).*

6. **Tune the `effort` parameter instead of defaulting high.**
   `high` is the quality/cost sweet spot for hard work, but `medium` is often
   indistinguishable on routine cloud tasks and `low` is right for sub-agents and simple
   calls. Set per-tier in the dispatcher rather than one global value. *Effort: low.
   Payoff: low–med.*

7. **Context editing / compaction for the Odin multi-turn loop.**
   The LangGraph supervisor stores full message history in its SQLite checkpoint and
   resends it. For long loops, enable server-side context editing (`clear_tool_uses`) or
   compaction so stale tool output stops riding along on every turn. Beta, but cheap to
   adopt where loops get long. *Effort: med. Payoff: situational.*

### B. The human↔AI loop (process, not tokens)

- **The portfolio-hub pattern is the right call** — keep leaning on
  `docs/ai-cto/portfolio.md` as the single re-entry point so cross-repo sessions don't
  re-derive state from scratch. The biggest *human* time sink in a 7-repo setup is
  re-establishing context each session; one canonical state file is the fix, and it
  already exists. Keep it current; that's the highest-leverage habit.
- **Add a short `SESSION-STATE.md` / "where we left off" note** (or use it inside
  portfolio.md) so a new session starts from "here's the open thread" instead of
  re-reading everything. Cheaper than re-exploration every time.
- **House-style ordering carries a real cost.** "Reverse the blocks / Z→A / newest-first"
  is fine for *humans skimming logs*, but it adds re-orientation cost for the model on
  every read and the "reverse blocks, keep step numbers" walkthrough rule is genuinely
  error-prone to author and to follow. Not arguing to drop it — just logging that it's a
  measurable tax, and worth confining to genuinely time-based sections (logs/changelogs)
  rather than applying repo-wide.

### C. Prompting

- Current Anthropic guidance (2026): *minimum necessary structure*; curate the smallest
  set of high-signal tokens; use a system/role prompt; give explicit permission to express
  uncertainty (cuts hallucination); use **adaptive thinking** for agentic/tool loops. The
  NARF system prompt and dispatcher are already close to this.
- Aggressive "CRITICAL: YOU MUST" phrasing over-triggers on current Claude models — they
  follow instructions far more literally than older ones. Audit any such language in tool
  descriptions and system prompts and dial it back.

### D. Critique of the request that generated this review

The prompt that kicked this off ("Locate inefficiencies in our PROCESS … ANYTHING that
could help … Thanks!") is itself a good example of an inefficient prompt — not wrong, just
expensive to act on well:
- **No scope or success metric** — "anything that could help" forces a broad, speculative
  sweep instead of a targeted answer. Cost scales with ambiguity.
- **No output contract** — format, length, and where the answer should land are unstated.
- **Stream-of-consciousness + filler** ("Perhaps also…", "ANYTHING", "Thanks!") adds tokens
  without signal.

A tighter version, same intent: *"Review our AI process (Claude Code across the 7 repos +
the LiteLLM router) for token-cost and workflow inefficiencies. Rank the top 5 fixes by
payoff/effort, with concrete file references. Web-search to confirm 2026 best practice.
Write findings to `docs/ai-cto/`. Skip our architecture — assume the local-first hybrid is
settled."* — scoped, measurable, with an output target and an explicit out-of-scope.

### E. Track these dated items

- **Pricing is hardcoded for March 2026** in `hoard.py`. Re-baseline against live rates
  periodically (or fetch from the Models API at startup); the conservative over-estimate is
  safe but drifts.
- **Model IDs current as of this review:** Opus 4.8 `claude-opus-4-8` ($5/$25), Sonnet 4.6
  `claude-sonnet-4-6` ($3/$15), Haiku 4.5 `claude-haiku-4-5` ($1/$5). Fable 5 exists
  ($10/$50) for the hardest long-horizon work — not worth it for this workload.
- Token-counting and tokenizer shift with model generation — use `count_tokens`, never a
  `chars/4` estimate, when a number needs to be right.

### Sources
- [Claude Code: manage costs](https://code.claude.com/docs/en/costs) ·
  [LLM gateway config](https://code.claude.com/docs/en/llm-gateway)
- [Prompt caching in Claude Code (MindStudio)](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [Reduce Claude Code token usage — 8 methods (Agensi)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Hybrid cloud-local LLM architecture guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local models with Claude Code to cut costs (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Effective context engineering for agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude 4 prompting best practices (Anthropic)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
