# AI Process Efficiency Review — 2026-06-26

**Question asked:** Where is the user↔AI process wasting tokens or effort? What's the better
way — better prompting, leveraging other AI, a hybrid local-LLM + Claude setup? Keep it
current.

**Short answer:** The single biggest, most fixable waste is **context weight you pay on every
turn** — your seven `CLAUDE.md` files total ~14.6K tokens and the big two are the worst
offenders. After that: making sure prompt caching is actually landing, routing cheap work off
Opus, subagent discipline, and session hygiene. You already own the hardest piece of a hybrid
setup (the LiteLLM reasoning ladder on the t630) — it's just not pointed at this workflow yet.

---

## 1. The context tax — measured, not guessed

Every turn, before you type a word, Claude reads the project instructions. Measured today:

| Repo CLAUDE.md | ~Tokens |
| -------------- | ------- |
| `localDNS` | 5,118 |
| `DESIGN-…` (this repo) | 4,496 |
| `MARKETING` | 2,665 |
| `customers` | 1,033 |
| `claude-code-homelab` | 724 |
| `Azure-lab` | 573 |
| **All loaded together** | **~14,600** |

A 5K-token CLAUDE.md costs 5K input tokens *every turn* before your prompt, before any file
read. In a multi-repo session like this one, all of them load — ~14.6K/turn of pure overhead.

**This is mostly recoverable.** The `localDNS` and `DESIGN` files carry a lot that is reference,
not standing instruction — full deploy-path tables, the entire nftables deploy checklist, every
known issue with full prose. A CLAUDE.md should be the *briefing* (the rules Claude must never
forget); the *reference* belongs in README/linked files that get read **on demand**.

**Action (high value, low effort):**
- Trim each CLAUDE.md to standing rules + a table of contents that links out. Target: `localDNS`
  and `DESIGN` under ~2K tokens each. Move the deploy-path and nftables tables into the README
  they already cite (the CLAUDE.md can say "deploy paths: see README §C").
- The house-style block (ordering/typography/Gill Sans) is duplicated verbatim in all six files
  — ~150 words × 6. Put it in one file and link to it; don't reprint it in every briefing.
- Net effect: ~14.6K → ~6-7K per multi-repo turn. On caching, the first turn's cache *write* also
  shrinks proportionally.

## 2. Prompt caching — make sure it's actually landing

Claude Code caches the stable prefix (system prompt + CLAUDE.md + early context). Cache **reads
cost ~10%** of normal input; cache **writes cost ~25% more** than normal. So the economics only
work if the prefix stays *byte-stable* across turns.

- **Anything that changes the prefix re-bills the whole thing at the write rate.** Editing a
  CLAUDE.md mid-session, or tools that inject changing content high in the context, bust the
  cache. Keep churn low during a working session.
- For long sessions, the 1-hour cache TTL (`ENABLE_PROMPT_CACHING_1H`) avoids paying the write
  again every 5 minutes when you step away — worth it for the way you work (t630-access cadence
  means long gaps mid-session).
- **How to verify it's working:** watch the cache-read vs cache-write token counts. A healthy
  session is mostly reads after turn one. Turn-after-turn *writes* mean something upstream is
  mutating the prefix — that's the leak to hunt.

## 3. Route cheap work off Opus

You're on Opus 4.8 ($5/$25 per M in/out standard; fast mode $10/$50 but 2.5× speed and now ~3×
cheaper than on older models). Opus is the right tool for architecture, the workflow reasoning,
and the honesty-on-the-kept-document judgement calls. It is the wrong tool for:

- Doc-link checking (`tools/check-docs.py` already does this deterministically — no model needed).
- Mechanical edits, renames, reformatting, link fixes, changelog appends.
- Field extraction / classification over roster or stats data.

**Action:** push routine/mechanical work to a cheaper tier (Haiku/Sonnet) or to a script. Reserve
Opus for the genuinely hard calls. The daily-review cadence in this folder, for instance, is
largely templated — a cheaper model can draft it and Opus only reviews exceptions.

## 4. Subagent discipline

Subagents are powerful but **Anthropic measures subagent-heavy workflows at ~7× the tokens of a
single thread.** The rule that holds up: use a subagent when the clutter it keeps *out* of your
main context is worth more than its startup cost — and have it **return a small summary, not its
raw search output.** Good for "go read across 7 repos and tell me X." Bad as a reflex for every
step. For a single known-file lookup, just read the file.

## 5. Session hygiene

- **`/compact` when a thread has done its exploring.** After Claude has chased files and false
  leads, the dead weight rides along in every subsequent turn. Compact once the useful facts are
  established, then continue light.
- **One job per session.** Don't carry an exhausted 80-turn context into an unrelated task — the
  whole history re-bills every turn. Start fresh; CLAUDE.md re-establishes the rules cheaply.
- **Prefer the dedicated tools** (Grep/Glob/Read) over shelling out to `cat`/`grep` — the harness
  formats them tighter and they're easier to cache around.

## 6. The hybrid local-LLM angle — you've already built the hard part

You have LiteLLM (stage 10) on the t630 with a reasoning ladder: `local-reason`
(deepseek-r1:1.5b, CPU, cool) for light work, `cloud-gpu-reason` for heavy, `cloud-overflow`
fallback. The industry pattern for 2026 is exactly this: an intelligent gateway routing on
*task complexity, data sensitivity, and availability* — reported 60-80% cost cuts when ~60-70%
of traffic is simple (classify/extract/format) and only ~10% needs a frontier model.

**Where it's underused:** that router serves the *homelab's* LLM features, not your **build
process**. The high-leverage moves:

- **Privacy-routing the customer data.** The `customers` repo is real PII. Field extraction,
  roster validation, and stats summarization over it are a textbook fit for the *local* model —
  the data never leaves the box, and it's cheap. Reserve the Claude API for the work that
  genuinely needs frontier reasoning. This also tightens your "this repo stays private" rule:
  fewer real records cross the wire.
- **Local model as first-pass drafter.** Daily reviews, changelog entries, link-fix PRs — let
  the local model draft, Claude review. Cuts API tokens on the high-frequency, low-stakes work.
- **Keep Claude for what it's best at:** the cross-repo judgement, the architecture decisions,
  the "is this number honest enough to print" calls. Don't route those to a 1.5B model.

Caveat from the benchmarks: a $500-GPU local model is *not* at Claude's coding level — use it for
narrow, well-specified, low-stakes tasks, always with a cloud fallback. Don't expect it to run
the workflow.

## 7. Your prompt, specifically (you asked)

The prompt that triggered this review was, honestly, **inefficient — and you flagged it, which is
the right instinct.** What made it expensive:

- **Unbounded scope.** "Anything you could possibly think of… ANYTHING that could help" forces a
  wide, exploratory sweep — many searches, long output — when you likely wanted the *few highest-
  leverage* changes. Open scope = maximum tokens by construction.
- **No success criterion or output contract.** Nothing told me when "done" is done or what shape
  the answer should take, so I have to guess (and over-produce to be safe). 2026's #1 prompting
  practice is: **state success criteria and an output contract up front.**
- **Two requests in one** (analyze the process + critique this prompt) — fine, but each deserves
  its own bounded ask.

**A tighter version of the same request:**

> Review our user↔AI process for token waste. Give me the **top 5** changes ranked by
> (impact ÷ effort), each with: the problem in one line, the concrete fix, and the rough token
> saving. Focus on CLAUDE.md weight, caching, model routing, and the local-LLM hybrid. Skip
> anything that saves <5%. One page max. Cite current best practice.

That version is ~1/4 the tokens to state, caps my output, and gets you the actionable core
without the survey. **General rule for this workflow:** lead with the verb and the deliverable,
bound the scope ("top N", "one page"), and say what "done" looks like. Save the open-ended
"think of anything" prompts for when you genuinely want a brainstorm and are willing to pay for
breadth.

---

## Prioritized actions (impact ÷ effort)

1. **Trim `localDNS` + `DESIGN` CLAUDE.md to briefing-only**, reference tables linked from README.
   (~7-8K tokens/turn saved in multi-repo sessions; ~1 hour of editing.)
2. **De-duplicate the house-style block** into one linked file. (Small, trivial, compounding.)
3. **Verify caching is landing** — check read/write token ratio in a normal session; turn on the
   1-hour TTL given your work cadence.
4. **Route mechanical/PII work to the local LiteLLM model**; keep Opus for judgement calls.
5. **Adopt the bounded-prompt template** above as the default for this workflow.

## Sources (current as of 2026-06-26)

- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [Best practices for Claude Code — Docs](https://code.claude.com/docs/en/best-practices)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Claude Code Subagents: A Practical 2026 Guide — Nimbalyst](https://nimbalyst.com/blog/claude-code-subagents-guide/)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Local LLM vs Claude for Coding: $500 GPU Benchmark — kunalganglani.com](https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8)
- [Best practices for prompt engineering — Claude](https://claude.com/blog/best-practices-for-prompt-engineering)
- [Stop trying to one-shot: How to prompt Claude better — LogRocket](https://blog.logrocket.com/stop-one-shot-prompt-claude-better/)
