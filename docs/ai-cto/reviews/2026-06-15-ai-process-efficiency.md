# 2026-06-15 — AI process efficiency review (user ↔ AI, token & cost)

**Scope:** the *process* between a human operator and the AI across the A777ance repos —
where tokens (and dollars) are spent, where local models could carry the load, what to
change in prompting and tooling. Researched against current (June 2026) best practice;
sources at the bottom. NARF (CTO) + ZORT (CFO) overlap, so this lives in the CTO reviews
and is cross-linked from the CFO portfolio.

> **One-line answer:** you are already ahead of most — local-first LiteLLM + Ollama is the
> right spine. The wins left are (1) stop paying for duplicated *fixed* context every
> session, (2) make the cheap path *automatic* instead of a manual model pick, and (3)
> match the model tier to the job — including the model *this routine* runs on.

---

## A. The biggest levers, ranked (do these first)

| # | Lever | Effort | Saving | Where |
| - | ----- | ------ | ------ | ----- |
| 1 | **Right-size the model per task.** Don't run Opus/Fable for summarize/extract/format/commit-msg work — Haiku 4.5 or Sonnet 4.6 is plenty and 5–20× cheaper. *This very routine runs on Opus 4.8 (1M) to do web research + write a doc — Sonnet would do it for a fraction.* | low | large | routine/model config |
| 2 | **Make the local↔cloud split automatic, not a manual Open WebUI pick.** 60–70% of real traffic (classify, extract, format, short summaries, commit messages, log digests) clears local-model quality bars. Industry hybrid setups report **60–80% cost cut** by routing those to Ollama and reserving Claude for hard reasoning. You have the router (`10-ai-orchestration`) — the routing *decision* is still human. | med | 60–80% of cloud spend | localDNS LiteLLM/dispatcher |
| 3 | **Stop paying for duplicated fixed context.** The ~30-line house-style block is copy-pasted verbatim into all 6+ `CLAUDE.md` files; any multi-repo session loads every copy. Caching softens it, but it's still bytes on every cold session. Factor common house-style to one canonical file and reference it. | low | recurring | every repo's CLAUDE.md |
| 4 | **Lean on prompt caching deliberately.** Claude Code caches automatically; protect it by keeping `CLAUDE.md`/skills/MCP **stable mid-task** (don't hot-swap models, don't use CLAUDE.md as a scratchpad). Real-world: caching saves ~90% of repeated-input tokens; one team cut cost 72% over 3 months. | low | ~90% on repeats | workflow habit |
| 5 | **Subagents for context-heavy reads.** "Read every CLAUDE.md / sweep the portfolio" is the textbook subagent case — ~70% token reduction vs. doing it in the main thread, because the subagent eats the heavy context and returns only the conclusion. | low | ~70% on big reads | Explore/general agents |
| 6 | **Batch the monthly, non-interactive jobs.** Statement generation is templated at ~a penny a home — keep it on the local/template path, not Claude. If any monthly job *does* call Claude, the **Batch API is 50% off** for anything that doesn't need an answer in the next minute. | low | 50% on batch | stage 06 / collect |

---

## B. Inefficiencies observed in *your* setup (specific, not generic)

- **Model selection is manual.** `config.yaml` exposes `local-fast / local-smart /
  cloud-*` and the user picks in Open WebUI. That means the *human* is the router, and
  humans over-reach for the big model "to be safe." The `dispatcher.py` /
  `langgraph-router` (Heimdall gate) is the intended automatic path — finish wiring a
  **complexity + sensitivity** classifier so cheap/sensitive work pins local *without a
  decision*. (Note: **TD-14** already flags that the privacy fallback isn't fail-closed —
  a `sensitive` task can fail over to `cloud-overflow`. Fix that first; a cost-router that
  leaks is worse than a manual one.)
- **Routines should declare a cheap model.** A scheduled "go research and summarize" run is
  exactly the kind of job that should pin Sonnet/Haiku. Running it on Opus 4.8 1M is the
  single most visible spend in this very transcript.
- **Duplicated house-style across repos.** Same ~30 lines in `DESIGN`, `localDNS`,
  `customers`, `MARKETING`, `Azure-lab`, `claude-code-homelab`. Fixed cost, paid per cold
  session, multiplied by repos loaded. Canonicalize once.
- **MCP overhead is handled well — keep it that way.** GitHub MCP exposes ~55 tools; this
  environment defers them behind `ToolSearch` (load-on-demand) rather than dumping all
  schemas into context at start. That's the recommended pattern. The rule to keep:
  **2–3 active MCP servers max**, disconnect what you haven't used in a week.
- **CPU-bound local tier limits how much you can offload.** The t630 Carrizo is
  memory-bandwidth bound; 7B is "submit-and-wait," 3B is interactive. So the realistic
  local catch is short/structured tasks. The rented-GPU reasoning tier is the right escape
  valve — but it's spin-up-on-demand, so it won't catch *interactive* offload. Manage
  expectations: local catches the *bulk-but-simple*, not the *hard-and-fast*.

---

## C. Prompting improvements

- **Front-load the stable, vary the tail.** Put fixed instructions (style, schema, repo
  rules) at the top so they cache; put the changing ask at the end. Avoid editing early
  context mid-task — it busts the cache.
- **Ask for the conclusion, not the corpus.** "Summarize the 3 changes and the one risk,"
  not "read these files and tell me everything." Every token not requested is one you don't
  pay for, wait on, or cache.
- **Bound the work.** Give a tool-call budget, a model, and an output location. Open-ended
  prompts ("anything you can think of") invite unbounded spend (see §E — your own prompt).
- **`/compact` proactively, `/clear` between unrelated tasks.** Compacting *before* you're
  near the limit produces a clean, cacheable summary; clearing stops you dragging a dead
  task's context into the next one.

---

## D. Hybrid local + Claude — the target architecture

You've built the hard part. The model to converge on:

```
request ─► classifier (deterministic: sensitivity + complexity + latency need)
            │
            ├─ sensitive            ─► LOCAL only, fail CLOSED (never cloud)   ← fix TD-14
            ├─ simple & non-sensitive ─► local-fast (qwen 3B)                  ← the 60-70%
            ├─ moderate             ─► local-smart (qwen 7B, async)
            ├─ hard reasoning       ─► rented-GPU R1 (on demand) → cloud overflow
            └─ frontier / vision    ─► Claude (Sonnet for code, Opus/Fable for the hardest)
```

- **The classifier is cheap and can itself be local** (a 3B model or even keyword rules)
  — don't spend a Claude call to decide whether to spend a Claude call.
- **Enable prompt caching on the cloud-overflow path too.** When LiteLLM forwards to
  Anthropic with a stable system prompt, mark it with `cache_control` so repeated calls
  hit the cache (~90% off the repeated portion).
- **Keep statements off Claude.** Templated render at ~1¢/home is already optimal; resist
  "let the LLM write the statement" — it's more expensive and risks the honesty rule.

---

## E. Critique of the routine prompt itself (you asked)

The prompt is **clear in intent but unbounded in scope**, which is itself a token
inefficiency:

- *"ANYTHING that could help… Anything you could possibly think of"* — invites unbounded
  fan-out (more searches, longer output) with no stop condition.
- No **success metric**, no **output format/location**, no **model/tool budget**.
- Several distinct asks bundled (token use, prompting, other AI, hybrid, news) — fine, but
  unranked, so the agent guesses priority.
- **Good parts:** explicit "search the web," "keep up to date," "check the news" — clear,
  and correctly signals this can't be answered from memory alone.

**A tighter version** (drop-in):

> *"Monthly: review our user↔AI process for token/cost waste. Pin Sonnet. Web-search only
> for changes since the last review. Output: append findings (newest-first) to
> `docs/ai-cto/reviews/`, ranked by saving×ease, ≤8 tool calls. Notify only if you find a
> change worth >10% spend or a new capability we don't use yet."*

That version sets the model, the budget, the cadence, the output location, and the
notify-threshold — so the run is cheap, repeatable, and only interrupts you when it matters.

---

## F. What's new since you last looked (June 2026)

- **Fable 5 / Mythos 5** (Jun 9, 2026): Mythos tier above Opus; 1M context, 128K output,
  always-on adaptive thinking. Use it for genuinely hard, long-context work — *not* routine
  summarization.
- **Skills load progressively** — only the ~100-token name+description per skill at start;
  body/scripts load on demand, scripts run out-of-context so only output returns. Prefer
  Skills over MCP for token footprint.
- **Memory tool + context editing** generally available — context auto-prunes stale tool
  results; memory summaries carry across sessions. Reduces manual `/compact` need.
- **Subagents can nest** (up to 5 deep) and run as background workflows — good for the
  portfolio-wide sweeps this repo does.

---

## G. Recommended next actions

1. **Pin a cheap model on every scheduled routine** (this review included). *(ZORT: track
   the before/after on the Anthropic bill.)*
2. **Fix TD-14** (local-only fail-closed for `sensitive`) *before* turning on auto cost-routing.
3. **Finish the deterministic classifier** in `dispatcher.py` so simple/non-sensitive →
   local automatically.
4. **Canonicalize the house-style block** to one file the others reference.
5. **Turn on `cache_control`** on LiteLLM's Anthropic forward path.
6. **Keep MCP servers to 2–3 active**; keep using the deferred-tool (ToolSearch) pattern.

---

## Sources

- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Claude Code Token-Saving Guide: Models, MCP, CLAUDE.md, Skills & cache (knightli.com)](https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Agent Teams, Subagents, and MCP: 2026 Playbook — Developers Digest](https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026)
- [LLM API Cost Comparison 2026 — zenvanriel.com](https://zenvanriel.com/ai-engineer-blog/llm-api-cost-comparison-2026/)
- [Anthropic Claude updates — June 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude)
- [Everything Claude Has Shipped in 2026 — The AI Corner](https://www.the-ai-corner.com/p/everything-claude-shipped-2026-complete-guide)
</content>
</invoke>
