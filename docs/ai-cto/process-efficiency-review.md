# Process efficiency review — user ↔ AI workflow

*Prepared 2026-06-14 by the AI CTO routine. Time-based sections newest-first per house style.*

The brief: find inefficiencies in how we work with Claude (and other AI), cut token
use, sharpen prompting, and consider a hybrid local-LLM + Claude API split. Findings
are ranked by payback (effort vs. tokens/dollars saved). Web sources are listed at the
end; the landscape moves weekly, so re-check before acting on the dated claims.

---

## TL;DR — the five highest-payback moves

1. **The CLAUDE.md tax is the biggest leak.** ~14.6K tokens of CLAUDE.md load on
   *every* session (measured across the 6 repos in this container). The identical
   "House style" block is copy-pasted into all 7 repos — ~1.5K tokens of pure
   duplication re-read every time. **Trim + dedupe → save ~40–50% of that prefix.**
2. **Turn on / lean into prompt caching.** Cache reads cost 10% of base input; for a
   static prefix like our CLAUDE.md + ai-cto/ai-cfo session-start reads, that's an
   ~88–95% cut on the repeated portion. Break-even is one cache hit (5-min) or two
   (1-hour). This is the single biggest dollar lever and needs no doc rewrite.
3. **Route bulk/cheap work off Opus.** We already own a reasoning ladder on the t630
   (deepseek-r1:1.5b local → rented-GPU R1 → cloud overflow). Extend the *same* LiteLLM
   router so mechanical jobs (link-checking, house-style reformatting, summarizing logs,
   first-pass drafts) hit the local box or **Haiku 4.5**, and reserve **Opus 4.8** for
   reasoning. Hybrid setups report 60–90% cost cuts at equal quality.
4. **Use subagents/Explore for fan-out, Batch API for bulk.** Read-only sweeps across
   many files belong in a subagent (isolated context, returns only the conclusion) so
   they don't bloat the main window. Non-interactive bulk runs (monthly statement prose,
   doc-integrity passes) belong on the Batch API — a flat 50% discount.
5. **Prompt tighter.** Name the file/function and the done-condition. Scope beats
   cleverness for token spend. (Includes a critique of the prompt that started this — see
   the last section.)

---

## 1. The CLAUDE.md / session-start tax (measured)

Per-repo CLAUDE.md sizes in this container:

| Repo | ~Tokens |
| ---- | ------- |
| localDNS | ~5,100 |
| DESIGN (this repo) | ~4,500 |
| MARKETING | ~2,665 |
| customers | ~1,033 |
| claude-code-homelab | ~724 |
| Azure-lab | ~573 |
| **Total loaded / session** | **~14,600** |

On top of that, our own instructions tell every session to *also* read
`docs/ai-cto/*.md` and `docs/ai-cfo/*.md` at start — easily another several thousand
tokens before a single task token is spent.

**What's wasteful, concretely:**

- **Duplicated house-style block.** The ~250-word "ordering & typography" section is
  byte-identical in all 7 repos. Re-authored once and *referenced*, that's ~1.3–1.5K
  tokens saved on every multi-repo session.
- **Over-long briefings.** DESIGN and localDNS CLAUDE.md are ~4.5–5.1K each. A CLAUDE.md
  is config, not narrative — the funnel ASCII art, the prose rationale, and the full
  deploy-path tables are reference material that belongs in README/network-context and
  can be *linked*, not inlined. Target: a CLAUDE.md under ~1.5K tokens that says what to
  do and points to where the detail lives.

**Fixes (in payback order):**

1. Hoist the shared house-style block into one canonical file (e.g.
   `localDNS/docs/house-style.md`, since it's the public repo) and replace the copies
   with a one-line link + the adoption date. Keep the rule, drop the repetition.
2. Cut each CLAUDE.md to a navigation layer: the rules that change behavior + links to
   the deep docs. Move tables/diagrams/rationale down into the README they summarize.
3. Make the `docs/ai-cto` / `docs/ai-cfo` session-start reads *conditional* — "read
   these when doing CTO/CFO work," not "every session." Most coding tasks don't need the
   portfolio snapshot.

> Caveat before deleting: these files are the playbook. Trim by *relocating* detail into
> linked docs, not by dropping it. The "new reader can follow a household end-to-end"
> rule still has to hold.

## 2. Prompt caching — the dollar lever

Anthropic prompt caching prices cache *reads* at 0.1× base input and cache *writes* at
1.25× (5-min TTL) or 2× (1-hour TTL). For our workload — a large, stable prefix
(CLAUDE.md + session-start docs) followed by varying task text — this is close to
ideal: reported savings of 88–95% on the cached portion, break-even after a single hit.

- Claude Code applies caching automatically to the system/context prefix; the win is
  making that prefix *stable and contiguous* (don't interleave volatile content), and
  keeping sessions warm (cache goes cold after ~5 min idle on the default TTL; a 1-hour
  TTL exists for spread-out work).
- Stacking caching **with** the Batch API can push effective spend down 95%+ on bulk
  jobs.
- `/recap` (added Apr 2026) summarizes where a session left off instead of replaying the
  whole transcript on resume — use it instead of re-paste-the-context.

## 3. Hybrid local + cloud routing (we're 70% there already)

Our `10-ai-orchestration` LiteLLM router + the Odin/langgraph supervisor already do the
hard part: a tiered ladder with a cool local model, a rented-GPU tier, and a cloud
overflow. The gap is that this ladder is aimed at *reasoning depth*; it isn't yet the
default front door for everyday A777ance doc work.

**Recommended routing policy (by task, not just by model size):**

| Task class | Route to | Why |
| ---------- | -------- | --- |
| Link/doc-integrity checks, reformatting to house style, lint-style fixes | local (t630) or Haiku 4.5 | mechanical, no judgment, high volume |
| Summaries, first-draft prose, log triage, classification | Haiku 4.5 / local-reason | cheap, good enough, privacy-friendly local |
| Customer data (roster, real statements) | **local only** | privacy — never send real PII to cloud |
| Architecture, multi-file refactors, financial/strategy reasoning, this kind of review | Opus 4.8 (Sonnet 4.6 as mid-tier) | frontier judgment is where the spend earns out |

Industry split is ~60–70% simple / 20–30% moderate / ~10% frontier — so most volume
*should* be leaving Opus. LiteLLM gives per-route cost tracking so we can measure the
actual mix and tune. Note the customers-repo privacy rule already forbids real PII to
cloud — the local tier is the natural home for any task touching `roster.json` or
rendered statements.

## 4. Structural token hygiene

- **Subagents / the Explore agent for fan-out reads.** A cross-repo "where is X" sweep
  run in a subagent returns only the answer; the main context never sees the file dumps.
- **Batch API for the monthly cadence.** Statement prose generation and the
  `tools/check-docs.py` companion narrative are non-interactive and predictable — 50%
  off via batch.
- **Model tier per Claude Code session.** Opus 4.8 Fast Mode dropped to $10/$50 per MTok
  (from $30/$150 on 4.7); Sonnet 4.6 and Haiku 4.5 remain the cheaper tiers. Don't run
  Opus for a typo fix.
- **Headless/SDK note (eff. 2026-06-15):** headless SDK usage draws from a *separate
  weekly token pool* on Pro/Max plans — relevant if we automate these routines via the
  SDK; budget that pool separately from interactive use.

## 5. A process friction worth flagging (not a token issue)

`localDNS` and `customers` CLAUDE.md carry a standing founder instruction: **"push to
main, no branches."** This routine, by contrast, is *required* by its harness config to
develop on per-repo `claude/*-gqu7rl` feature branches. That's a live contradiction:
either the no-branch rule should be relaxed for AI routines (and the CLAUDE.md updated to
say so), or the routine config should target `main` for those two repos. Pick one and
write it down, so future sessions don't waste turns rediscovering the conflict. (This
review was committed to the feature branch per the harness rule.)

## 6. Is *this* request inefficient? Yes — here's the fix

The prompt that triggered this review ("Locate inefficiencies… Is there a better way…
Perhaps also better prompting… Anything you could possibly think of… Search the web…
Check the news… ANYTHING that could help.") is maximally open-ended. That's expensive:
it forces broad web fan-out and a long, unscoped exploration, and it makes "done"
undefinable — the model can't tell when to stop.

A tighter version of the same ask, ~80% cheaper to serve:

> "Audit our Claude usage for token waste. Specifically: (1) measure the CLAUDE.md +
> session-start load per session and propose cuts; (2) recommend a prompt-caching and
> local-vs-cloud routing policy for our LiteLLM stack; (3) flag the 3 highest-payback
> changes. Use web search only for 2026 pricing/feature facts. Output: a ranked list
> with effort/impact. Skip anything you can't tie to a concrete saving."

Prompting principles this illustrates, for reuse:
- **Name the deliverable and its shape** ("ranked list, effort/impact") so output is
  bounded.
- **Scope the research** ("web only for pricing facts") instead of "check the news."
- **Give a stop condition** ("skip anything not tied to a saving").
- **Numbered sub-asks** beat "anything you could think of" — they let the model (or a
  cheaper model) parallelize and let *you* verify coverage.
- **Put stable instructions in CLAUDE.md, volatile task detail in the prompt** — so the
  cache prefix stays stable and only the cheap tail changes.

---

## Sources (2026-06-14 — verify before relying; this space moves weekly)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How to Reduce Claude Code Token Usage (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Prompt Caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-token-savings)
- [Anthropic API Pricing in 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude API Pricing 2026: Opus 4.8 / Sonnet 4.6 / Haiku 4.5 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Prompt Caching Cost Optimization (2026) — Web2MD](https://web2md.org/blog/prompt-caching-cost-optimization-guide-2026)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Sub-Agents Explained — MindStudio](https://www.mindstudio.ai/blog/claude-code-sub-agents-explained)
- [Structuring Claude Code for Multi-Repo Workspaces — karun.me](https://karun.me/blog/2026/03/26/structuring-claude-code-for-multi-repo-workspaces/)
- [8 Claude Code Tips for Large Monorepo Projects — Medium](https://diptendud.medium.com/8-claude-code-tips-for-large-monorepo-projects-1f84a34316dd)
