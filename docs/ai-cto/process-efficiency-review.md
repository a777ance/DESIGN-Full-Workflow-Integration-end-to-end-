# Process efficiency review — human ↔ AI workflow

A standing review of how we spend tokens and attention across the A777ance repos, and
where the human↔AI loop can be made cheaper, faster, or better. Newest review at the top
(per house style).

Verified against the live Claude API reference on the date noted. Pricing and model facts
move week to week — re-run this review monthly and update the date.

---

## Review — 2026-06-16

### TL;DR

We are **already doing the two hardest things right**: a real hybrid stack (LiteLLM
reasoning ladder on the t630, local-first with cloud overflow) and one cached briefing per
repo. The cheap wins left are mostly **discipline, not architecture**: keep the cache from
silently breaking, push bulk work to the Batch API, right-size the model per task, and stop
feeding the whole 300-line CLAUDE.md into jobs that only touch one stage. Estimated blended
saving if all of the below land: **roughly 60–80% on API spend** for the agentic/automation
workloads, with no quality loss.

### Where our tokens actually go

1. **Per-session repo briefings.** `localDNS/CLAUDE.md` is 326 lines, `DESIGN/CLAUDE.md`
   295. Every Claude Code session re-sends the whole thing. Cached, this is ~0.1× cost on
   repeat turns — **but only if the prefix is byte-stable** (see cache hygiene below). If it
   isn't cached, we pay full input price for ~3–4K tokens on every single turn.
2. **Long agentic loops** (statement generation, the stage-11 automations once wired):
   tool-result history accumulates and is re-sent each turn unless trimmed.
3. **Cloud-overflow fallback** from the LiteLLM ladder: the expensive path, used when the
   t630/rented-GPU tier is unavailable.

### Highest-leverage fixes (ranked by saving ÷ effort)

| # | Fix | Why it pays | Effort |
| - | --- | ----------- | ------ |
| 1 | **Push bulk/non-interactive work to the Batch API** (50% off in + out). Monthly statement generation, any classification/summarization sweep over the customer list, demand-gen copy variants — none of these are latency-sensitive. Batch + caching stacks to ~95% off vs. uncached real-time. | Biggest single lever for our shape of work (scheduled batches, not chat). | Low–med |
| 2 | **Cache hygiene audit.** Confirm `cache_read_input_tokens > 0` on repeat calls. The #1 silent cache-killer is a timestamp/UUID/`datetime.now()` near the *front* of a prompt — it invalidates everything after it. Keep CLAUDE.md frozen; inject "today's date" etc. at the *end*, never in the system prefix. | A broken cache quietly turns 0.1× into 1.0× on our largest, most-repeated payload. | Low |
| 3 | **Right-size the model per task.** Default mix for a shop like ours: ~Haiku 40% / Sonnet 50% / Opus 10%. Use Haiku 4.5 ($1/$5) for classification, extraction, "is this paid?", short rewrites; Sonnet 4.6 ($3/$15) for most drafting; reserve Opus 4.8 ($5/$25) for genuine multi-step reasoning. We currently lean Opus-heavy by habit. | 5× price spread between Haiku and Opus on the same token. | Low (routing rules) |
| 4 | **Scope the briefing to the stage.** A job that only edits `06-statements-delivery/` does not need the full 295-line funnel map. Consider a short per-folder `CLAUDE.md` (or a "minimal" briefing variant) so single-stage tasks don't drag the whole playbook into context. | Cuts the fixed per-turn cost on the most common narrow edits. | Med |
| 5 | **Context editing / compaction on long loops.** For the stage-11 automations and statement runs, enable server-side compaction (summarizes old context) or context editing (prunes stale tool results) so hour-long agent runs don't re-send a growing transcript every turn. | Keeps long-horizon jobs from ballooning. | Med |
| 6 | **Tune the hybrid ladder we already have.** Two concrete items: (a) **fix TD-14 first** — a `sensitive` task must fail *closed* to a local-only chain, never to `cloud-overflow`; that's a privacy bug, not just cost. (b) Add **semantic caching** in front of the router (near-duplicate prompts return a stored answer, hitting no model) — reported 15–30% request-volume cut on classification-heavy traffic, which is exactly the "is this paid / what stage is this lead" work. | We built the router; these are the next two turns of the screw. | Med |

### Hybrid / local routing — we're ahead here

The `10-ai-orchestration` LiteLLM ladder (local-reason on t630 CPU → cloud-gpu-reason on a
rented GPU → cloud-overflow to Claude) is the right architecture and most teams never get
this far. Tuning, not rebuilding:

- **Route by task, not by reflex.** Light extraction/classification → local Haiku-class or
  the t630. Drafting → Sonnet. Only true reasoning → Opus/cloud.
- **Fail closed on privacy** (TD-14). Cost and privacy point the same way here: keep
  sensitive household data on the local tier.
- **Semantic cache** before the model call (see #6).
- Industry case studies in 2026 report 50–88% cost reduction from exactly this local-first
  pattern — we should be measuring our actual local-hit ratio to confirm we're capturing it.

### Current model & pricing facts (2026-06-16)

- **No more long-context surcharge.** The 1M context window on Opus and Sonnet is now
  standard per-token pricing — large-document prompts no longer carry a premium. (Mind that
  1M of *anything* is still 1M tokens billed; big ≠ free.)
- Opus 4.8 $5 / $25 per MTok · Sonnet 4.6 $3 / $15 · Haiku 4.5 $1 / $5 (in / out).
- **Fable 5** sits *above* Opus (≈$10 / $50) — reserve strictly for the hardest long-horizon
  jobs; it is not the default. For "use the best model" we mean Opus 4.8.
- Prompt-cache economics: read ≈0.1×, write 1.25× (5-min TTL) / 2× (1-hr TTL). Break-even is
  ~2 reads at 5-min, ~3 at 1-hr. Target a **cache-read : cache-write ratio ≥ 5×**.

### Prompting improvements (for us, the humans driving it)

- **State the goal and constraints up front in one well-specified turn**, rather than
  dribbling context over many turns. On the current Opus generation this is both cheaper
  (fewer round-trips, more cache reuse) and higher quality. Ambiguous multi-turn prompts are
  the most expensive way to work.
- **Ask for the answer, not a survey.** "Recommend one" beats "lay out all options" — less
  output, which is the expensive half ($25 vs $5 on Opus).
- **Don't paste; point.** Reference files by path and let the agent read what it needs,
  rather than pasting large blobs into the prompt every turn.
- **Drop aggressive instruction language.** `CRITICAL: YOU MUST…` overtriggers on current
  models and wastes tokens; plain "Do X when Y" works and is cheaper.
- **Match output length to the surface.** Our house style already values plain, concrete
  prose — extend that to AI output: a "Handled For You" log line, not an essay.

### Critique of the meta-prompt that triggered this review

The standing prompt ("Locate inefficiencies… Is there a better way… Search the web… Keep UP
TO DATE…") is **good for a human kickoff but inefficient as a recurring routine**:

- **It's open-ended ("ANYTHING that could help").** That maximizes exploration cost every
  run. For a scheduled routine, narrow it to a checklist: *"Re-verify model IDs/pricing,
  re-run the cache-hit and local-hit-ratio checks, flag any regression vs. last review,
  notify only on change."* That turns an expensive essay into a cheap diff.
- **"Search the web… check the news" on every run** is costly and usually returns nothing
  new day-to-day. Gate it: only deep-search when a model launch or pricing change is
  plausible, or monthly — not every run.
- **It mixes two jobs** (audit our process *and* critique the prompt). Fine once; for a
  routine, split them so each run has one cheap, well-scoped objective.
- **Better recurring form:** *"Monthly: confirm pricing/model facts against the live API
  ref; verify cache-read ratio ≥5× and local-hit ratio on the t630; list anything that
  changed since the last entry in process-efficiency-review.md; push a notification only if
  something is actionable. Silence if nothing changed."*

### Action checklist

- [ ] Audit cache hits — confirm `cache_read_input_tokens > 0` on repeat Claude Code turns
- [ ] Move statement generation + any list-wide sweeps onto the Batch API
- [ ] Write per-task routing rules (Haiku/Sonnet/Opus) into the LiteLLM config
- [ ] Fix TD-14 (sensitive → local-only fallback) — privacy + cost
- [ ] Prototype a short/minimal per-stage CLAUDE.md for single-folder edits
- [ ] Add a semantic cache in front of the router; measure local-hit ratio
- [ ] Rewrite this review's trigger prompt into the narrow monthly checklist above

### Sources

- [Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic pricing docs](https://platform.claude.com/docs/en/about-claude/pricing) ·
  [Finout 2026 pricing guide](https://www.finout.io/blog/anthropic-api-pricing) ·
  [The New Stack — million-token pricing change](https://thenewstack.io/claude-million-token-pricing/)
- [Claude API cost optimization (caching + batching, 60% reduction)](https://dev.to/whoffagents/claude-api-cost-optimization-caching-batching-and-60-token-reduction-in-production-3n49)
- [Hybrid cloud-local LLM architecture guide 2026](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/) ·
  [Ollama + LiteLLM routing](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
