# AI Process Efficiency — token spend & human↔AI workflow — 2026-06-21

**Scope:** founder asked (scheduled routine) to find inefficiencies in *how we use AI* —
token spend between the human and the model, better prompting, leveraging the existing
local-LLM + Claude hybrid, and anything else current. This is an advisory review, not a
code change. Newest-first per house style.

> **Delivery note:** this routine's notification tool was not available in the session, so
> the findings were committed here (the AI-CTO hub) instead of pinged. If routine pings are
> meant to fire, the notification tool needs to be wired into the routine's environment.

---

## TL;DR — the five that matter

1. **The CLAUDE.md files are the single biggest standing token cost.** Seven repos,
   ~8,600 words of project instructions (~11–12k tokens) — the two big ones (`localDNS`
   2,728 w, `DESIGN` 2,608 w) load *every session, every turn*, whether the task touches
   them or not. A 5k-token CLAUDE.md costs 5k tokens on turn 1 **and** turn 200. Trim to a
   lookup table; push detail into the linked READMEs the model can open on demand.
2. **Prompt caching is almost certainly not being exploited.** Stable prefixes
   (CLAUDE.md, tool list, system prompt) cached at ~0.1× read vs 1× fresh = up to ~90% off
   the repeated input. This is the highest-leverage, zero-risk lever and needs no new infra.
3. **The hybrid router already exists but isn't carrying load.** `10-ai-orchestration`
   (LiteLLM on `:4040`, Ollama tiers, `dispatcher.py`, the Odin supervisor) is built and
   wired, but cloud tiers are still the default path for real work. Industry hybrids report
   **60–80% cost cuts** by sending the 60–70% of routine traffic local and reserving Claude
   for the ~10% that needs frontier reasoning. The plumbing is done; the routing discipline isn't.
4. **Model tiering is inverted in practice.** Default to Sonnet 4.6 ($3/$15) for most
   work and Haiku 4.5 ($1/$5) for classification/extraction; reserve Opus 4.8 ($5/$25) for
   genuinely hard reasoning. Paying Opus rates for routine edits is the quiet majority of waste.
5. **Batch the non-interactive work.** The nightly NARF/ZORT reviews, statement builds,
   and any cron-driven generation are not latency-sensitive → **Message Batches API = 50% off**.

---

## A. Token spend — concrete levers (ranked by leverage ÷ effort)

| Lever | Saving | Effort | Notes |
| ----- | ------ | ------ | ----- |
| **Prompt caching** on the stable prefix (CLAUDE.md + tools + system) | up to ~90% of repeated input tokens | low | `cache_control: {type:"ephemeral"}` on the last stable block. Keep the prefix byte-identical — no `datetime.now()`, no per-session IDs ahead of the cache point, deterministic tool order. Verify with `usage.cache_read_input_tokens` > 0. |
| **Trim CLAUDE.md** to a lookup table | flat cut on every turn | low | Move stage-by-stage detail, rationale, and history into the READMEs already linked. The model opens them only when the task needs them. Target: each CLAUDE.md ≤ ~1k tokens of *load-bearing* rules. |
| **Right-size the model** (Sonnet/Haiku default, Opus on demand) | 40–80% per call | low | Sonnet 4.6 is the speed/intelligence sweet spot; Haiku 4.5 for classify/extract/format. Config already lists all three — make Sonnet the cloud default, escalate deliberately. |
| **Route routine traffic local** (the hybrid already built) | 60–80% of cloud spend | medium | Make `dispatcher.py`'s rule table the front door for batch/agentic jobs; cloud is overflow, not default. Privacy gate already deterministic. |
| **Batch API** for cron jobs (reviews, statements, embeddings) | 50% | low | Non-interactive by definition. `client.messages.batches.create(...)`. |
| **Context editing / compaction** on long agent runs | caps runaway growth | medium | `clear_tool_uses_20250919` prunes stale tool output (the biggest silent drain in long threads); compaction summarizes near the window limit. |
| **`effort` parameter** tuned down for routine work | fewer thinking + output tokens | low | Default `high` is often overkill; `medium`/`low` for simple edits, `high`/`xhigh` only for hard agentic/coding. |
| **Terse-output instruction** | ~30–65% of *output* tokens | low | One CLAUDE.md line: lead with the answer, drop filler/preamble/recaps. Output is billed 5× input — this is real money. |

**The trap to avoid:** a fat CLAUDE.md *only* pays off when it saves more output than it
costs in repeated input. Today the files lean encyclopedic (full stage maps, rationale,
known-issues tables). That's great documentation and a poor *always-loaded context*. Split
the two roles.

## B. Tool-output discipline (the silent drain)

Every file read, shell run, and MCP call appends its full output to context and stays there
for every subsequent turn. A 10k-line log read once is paid for on every later message. Habits
that help: read the slice you need (offset/limit), prefer `grep`/`Glob` over dumping whole
files, and clear tool results on long runs. This is behavioral, not infrastructural.

## C. Leverage the hybrid you already built

`ORCHESTRATION-BLUEPRINT.md` + `config.yaml` are further along than they're being used:

- **Front door exists** (`ai.home.lan:4040`, OpenAI-compatible). Point batch/agentic jobs at
  it so the deterministic dispatcher picks the tier — local-first, cloud as overflow.
- **The reasoning ladder is right**: small distill local (cool on the t630), heavy R1 on the
  rented GPU, Claude as overflow. The gap is *defaulting* to cloud for ordinary work.
- **Embeddings/RAG already local** (`nomic-embed-text`) — index + query never leave the walls
  and cost nothing. Use it to *retrieve* the relevant repo slice instead of pasting whole files
  into prompts (doubles as a token cut).
- **Decision still open (BLUEPRINT §4.1):** which tier hosts heavy specialists. The cheapest
  honest answer for the current volume is: local for routine, Claude (Sonnet) for code/hard
  reasoning, rented-GPU R1 only when a privacy class forbids cloud.

## D. On the prompt that triggered this review

The founder asked whether *this* prompt is itself inefficient — yes, mildly, and the fixes
generalize to how to brief the model:

- **It's a broad sweep** ("ANYTHING that could help… search the web… check the news"). Broad
  prompts make the model fan out wide and burn tokens exploring. Tighter scoping ("audit our
  CLAUDE.md token cost and propose a caching plan") gets a sharper answer for less.
- **Bundled asks** (token use + prompting + hybrid + news) in one turn → one long
  context-heavy response. Splitting into separate, scoped tasks caches better and reads cleaner.
- **State the constraint up front.** For long-horizon/agentic work, give the full task spec in
  one well-specified first turn rather than dribbling it across turns — it's both cheaper and better.
- **What was good:** it named the goal (reduce token use), the assets (local LLM + Claude API),
  and gave permission to act. Keep that; just narrow the blast radius.

## E. Recommended next actions (smallest first)

1. Add a terse-output rule + trim the two large CLAUDE.md files to lookup tables. *(1 sitting)*
2. Turn on prompt caching for the stable prefix; verify cache reads land. *(1 sitting)*
3. Make Sonnet 4.6 the cloud default; document when to escalate to Opus. *(config + 1 note)*
4. Move the nightly reviews/statement builds onto the Batch API (50%). *(small script change)*
5. Route batch/agentic jobs through `dispatcher.py` so local carries routine load. *(the BLUEPRINT Phase 3–4 work, already specced)*

## Sources (current as of 2026-06)

- Anthropic prompt-caching economics, Batch API (50%), model pricing/`effort`, context
  editing/compaction — `claude-api` skill reference (authoritative, this session).
- [How to Reduce Claude Code Token Usage (agensi.io)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [12 Ways to Cut Token Consumption in Claude Code (Firecrawl)](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [7 Practical Ways to Reduce Claude Code Token Usage (KDnuggets)](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows — Cost Optimization (buildmvpfast)](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026) — cites 60–80% / 83% reductions
- [LLM Request Routing: GPT-4 vs Claude vs Local (buildmvpfast)](https://www.buildmvpfast.com/blog/llm-request-routing-gpt4-claude-local-models-2026)
