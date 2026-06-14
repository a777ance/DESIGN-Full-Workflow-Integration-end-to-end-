# Process efficiency — user ↔ AI workflow (review 2026-06-14)

How we spend tokens and attention working with Claude across the A777ance repos, where
the waste is, and what to change. Ranked by impact. Time-based sections newest-first per
house style.

> **Scope note.** This is a NARF (AI CTO) operational review, not a product change. Nothing
> here touches a Statement or customer data. Findings are advisory until adopted via the
> portfolio hub.

---

## TL;DR — the five moves that matter, biggest lever first

| # | Move | Effort | Payoff |
| - | ---- | ------ | ------ |
| 1 | **Trim the `CLAUDE.md` tax.** Get each under ~200 lines; push detail into on-demand `README`/reference files. | Low | ~10.5K tokens off *every turn* of a multi-repo session |
| 2 | **Right-size the model per task.** Default to Sonnet/Haiku; reserve Opus for hard reasoning. | Low | 5–15× cost on routine edits |
| 3 | **Route routine work to the local LLM we already run** (LiteLLM + Ollama on the t630, stage 10). | Medium | 60–80% off the easy 60–70% of requests |
| 4 | **Use subagents for fan-out** (search, research, multi-file reads) so the main context stays lean. | Low | Keeps the costly main thread short; parallel = faster |
| 5 | **Scope prompts; drop the ALL-CAPS.** Specific task + deliverable + format beats "ANYTHING that helps." | Low | Fewer retries, fewer wasted explore-everything passes |

Teams combining these report **40–85% token reductions** without quality loss.

---

## 1. The `CLAUDE.md` tax — our single biggest, most fixable cost

`CLAUDE.md` is injected into context on **every request**. A 5,000-token file is a
5,000-token tax on every turn — paid whether or not the turn needs it. Current sizes:

| File | Lines | ~Words |
| ---- | ----: | -----: |
| `localDNS/CLAUDE.md` | 326 | 2,728 |
| `DESIGN-…/CLAUDE.md` | 295 | 2,608 |
| `MARKETING/CLAUDE.md` | 214 | 1,445 |
| `customers/CLAUDE.md` | 80 | 562 |
| `claude-code-homelab/CLAUDE.md` | 75 | 371 |
| `Azure-lab/CLAUDE.md` | 50 | 316 |
| **Total** | **1,040** | **~8,030 (~10.5K tokens)** |

In a **single-repo** session you pay only that repo's file (plus parents). But in a
**multi-repo workspace** like a portfolio session opened at `/home/user/`, *all of them*
load — ~10.5K tokens on top of the harness system prompt, on every turn. The community
benchmark is **keep `CLAUDE.md` under ~200 lines.** Three of ours blow past it.

**What to do:**
- Each `CLAUDE.md` should be a *router*, not the manual: the briefing + a table of "for X,
  read file Y." The detail already lives in `README.md` / `network-context.md` /
  `workflow-context.md` — let Claude read those *on demand* instead of pre-loading them.
- Move the long reference tables (e.g. localDNS's full Deploy-paths table, DESIGN's stage
  map) into a linked `reference.md`; keep a one-line pointer in `CLAUDE.md`.
- For portfolio (cross-repo) work, prefer opening **one repo at a time** rather than the
  `/home/user/` parent, so only the relevant `CLAUDE.md` loads.
- This doesn't fight the house-style/honesty rules — those are short. It's the *encyclopedic*
  middle of each file that should graduate to on-demand reading.

## 2. Right-size the model — stop paying Opus for typo fixes

Opus 4.8 is the heavy model. Sonnet 4.6 and Haiku 4.5 cost a fraction and clear the bar for
most of our work (doc edits, link-checks, schema tweaks, commit messages, `check-docs.py`
runs). Rule: **cheapest model that clears the bar.** Use `/model` to drop to Sonnet for
routine sessions; keep Opus for genuine reasoning (architecture, this kind of review, gnarly
debugging). Note: *this very task* ran on Opus 4.8 1M — appropriate for open-ended research,
but it would be waste for "fix the broken anchor in README."

## 3. Hybrid local-LLM routing — we are already built for this

We already run the gateway (stage `10-ai-orchestration`: LiteLLM on **:4040**, Ollama,
Open WebUI, the deepseek reasoning ladder). Most production workloads are ~**60–70% simple**
(classify, extract, format, first-draft), ~20–30% moderate, ~10% true frontier reasoning.
Hybrid routing cuts cost **60–80%** on the simple slice with minimal quality hit. Route by
three dimensions: **data sensitivity, task complexity, availability.**

Good fits for the **local** tier (no API spend, and private by default — relevant for the
**private** `customers` repo and roster data):
- Drafting "Handled For You" log entries / statement prose from measured stats
- Classifying or de-duplicating roster/CRM rows
- First-pass summaries, reformatting, Z→A re-sorting to house style
- Linting/extraction over docs

Keep on **Claude API**: cross-repo reasoning, architecture/ADR decisions, anything
customer-facing where the honesty rule bites, security-sensitive review.

**Next step:** add a routing policy doc + a couple of LiteLLM model aliases (`local-draft`,
`cloud-reason`) so the choice is one config line, not a habit. The infra exists; only the
*routing discipline* is missing.

## 4. Subagents & context offloading

Subagents run in their own context window and return only the conclusion — the main thread
never sees the file dumps. As of June 2026 they can nest up to 5 deep. Use them for the
fan-out shape: "search these repos for X," "research these 4 questions," "read these 10
files and report the one fact." This review used parallel web searches in that spirit. The
2026 "control stack" pattern: **project rules → reusable skills → bounded subagents →
deterministic tools** around the model.

## 5. Prompt caching — mostly automatic, one caveat for us

Claude Code already prompt-caches the system prompt + `CLAUDE.md`. Cache **reads cost 0.1×**
(90% off); a write is 1.25× and breaks even after one hit. **Caveat for scheduled routines:**
the cache expires after **5 min idle**. A routine that fires, sits, then fires again pays the
write each time with no reads to amortize it — so batch routine work into one active session
rather than many cold starts. (Opus 4.8 also now lets us update instructions mid-task via
`system` entries in the messages array *without* breaking the cache — useful if we script
the API directly.)

## 6. Skills + effort levels

Package repeating workflows (build-a-statement, add-a-customer, run check-docs + commit) as
**skills** so the procedure isn't re-explained in prose each time. Skills can pin a low
**effort level** for mechanical work (formatting, linting, simple review), cutting tokens
with no quality loss on tasks that don't need deliberation.

---

## On the prompt that triggered this review

The request worked, but it's a textbook example of the pattern that *costs* the most:

- **Open-ended scope.** "ANYTHING that could help," "Anything you could possibly think of"
  invites an explore-everything pass — maximal tokens, and the model has to guess what
  "done" means. 2026 guidance: a **focused task with clear boundaries** beats a broad one,
  and *specificity* (a named deliverable, a format, a length cap) measurably improves output.
- **ALL-CAPS emphasis.** "PROCESS," "ANYTHING," "UP TO DATE." Newer Claude models do *worse*
  with aggressive emphasis ("CRITICAL!", "YOU MUST") than with calm, direct instruction —
  it's noise that buys nothing.
- **No output contract.** No format, length, or destination specified, so the model picks —
  and tends to over-deliver to be safe.

**A tighter rewrite (same intent, ~1/3 the ambiguity):**

> Review how we work with Claude across the A777ance repos for cost/efficiency. Cover:
> (1) token waste in our setup, (2) model/prompt choices, (3) routing routine work to our
> local LLM, (4) anything from current best practice (search the web; cite sources, 2026).
> Deliver a ranked, ≤2-page findings doc committed to `docs/ai-cto/`, plus a one-paragraph
> summary. Flag the single highest-impact change.

That version names the scope, the deliverable, the format, the destination, and the success
signal — so there's nothing to guess and little to redo.

---

## Sources (2026)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog) — nested subagents (Jun 10), usage attribution
- [23 Tips for Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [How to Reduce Claude Code Token Usage — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization (2026 Guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Anthropic API Pricing 2026 — Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Prompt Caching Cost Optimization (2026) — Web2MD](https://web2md.org/blog/prompt-caching-cost-optimization-guide-2026)
- [Hybrid Cloud-Local LLM Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows Cost Optimization — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Sub-Agents for Context Management — MindStudio](https://www.mindstudio.ai/blog/sub-agents-claude-code-context-management)
- [Best practices for prompt engineering — Claude](https://claude.com/blog/best-practices-for-prompt-engineering)
- [Context Engineering Guide 2026 — The AI Corner](https://www.the-ai-corner.com/p/context-engineering-guide-2026)
- [Introducing Claude Opus 4.8 — Anthropic](https://www.anthropic.com/news/claude-opus-4-8) — mid-task `system` entries don't break cache
