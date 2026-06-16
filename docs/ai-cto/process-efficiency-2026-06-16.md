# Process efficiency review — human ↔ AI workflow (2026-06-16)

A review of how we spend tokens and attention across the A777ance repos, with concrete
fixes. Ordered by impact, biggest lever first. Numbers are measured from this repo set;
treat token figures as ~±15% (word→token estimate).

> **The one-line takeaway:** as of *yesterday* (June 15) Anthropic split autonomous usage
> onto a separate, full-rate credit pool — and our most expensive habit is exactly the
> autonomous one: daily NARF/ZORT routines that each re-read ~14k tokens of standing
> context before doing any work, on Opus. Cache that context, shrink the mandatory reads,
> and push the cheap work to the t630 we already built.

---

## 0. The time-sensitive thing (act this week)

**Anthropic changed billing on 2026-06-15.** Interactive Claude Code (someone at the
keyboard) still draws on the session/weekly subscription limits. **Non-interactive usage —
Agent SDK, headless runs, GitHub Actions, *scheduled routines like the NARF/ZORT reviews
and this very report* — now draws from a separate monthly Agent-SDK credit pool, billed at
full API rates** (Pro $20, Max 5x $100, Max 20x $200 of included credit, then metered).

What this means for us:

- Every autonomous run now has a real dollar cost, separate from the seat we already pay
  for. The daily CTO + CFO review loops are the biggest line item we control.
- On Opus with the 1M window, auto-compact has been firing as early as ~76k tokens and
  resubmitting the whole context to summarize (100–200k tokens, up to 3× a turn). A bloated
  autonomous session can spend more on compaction than on the work.

**Action:** decide *deliberately* which routines run autonomously vs. interactively, and
apply the caching + slimming below before the credit pool does it for us.

---

## 1. Standing-context overhead is our single biggest lever

Every session for this repo starts by paying for context before a useful token is produced:

| What loads at session start | ~tokens |
| --- | --- |
| This repo's `CLAUDE.md` | ~3,500 |
| NARF mandate: portfolio + roadmap + tech-debt + decisions | ~4,300 |
| ZORT mandate: cfo portfolio + decisions + metrics + runway + budget + marketing context | ~7,000+ |
| **Fixed overhead per DESIGN session, before any work** | **~14,500–15,000** |

The other repos add their own: `localDNS` CLAUDE.md is ~3,600 tokens (it carries the full
deploy-path and Unbound tables — that's *reference*, not a briefing). Six CLAUDE.md files
total ~10,700 tokens, and they cross-reference each other, so an agent often pulls siblings too.

**Fixes, in order of payoff:**

1. **Turn on prompt caching for the stable prefix.** CLAUDE.md + the AI-state docs barely
   change between runs. Cached input bills at ~10% of the normal rate (≈90% saving) for hits;
   a 4k system prompt + 2k tool defs alone is a documented ~59% input-token cut. Claude Code
   caches some of this already, but the default cache TTL is ~5 minutes — so **back-to-back
   daily routines miss the window unless we batch them** (see §4) or use the extended-TTL
   option.
2. **Cut the mandatory session-start reads.** "Read these 10 files every session" is the
   costliest standing instruction we have. Replace with: *read the portfolio hub only; pull
   the rest on demand.* Better still, have NARF/ZORT maintain a single ~1-page **state
   digest** they refresh at session end, and read only that at session start. That converts a
   ~11k-token fan-out read into a ~1k one.
3. **Slim the CLAUDE.md files.** A CLAUDE.md is paid *every turn*, not just at start. Keep it
   to the briefing; move the big tables (stage map, deploy paths, Unbound drop-in table) into
   README and link to them. Target: under ~1,500 tokens each.

---

## 2. The review logs are proliferating

`docs/ai-cfo/reviews/` holds **21** files and `docs/ai-cto/reviews/` **13** — roughly one
CTO + one CFO file *per day* over ~12 days, ~900–1,500 words each. The CFO set alone is
~39k tokens. Today nothing reads them all, but any instruction like "review recent decisions"
risks pulling the whole pile, and it's growing daily forever.

**Fix:** collapse daily-per-role files into a **single rolling review log per role**
(newest-first, per house style), or weekly digests with the dailies archived. One append per
day to one file instead of a new file keeps git history and any "read recent reviews" cost
flat instead of linear-in-days.

---

## 3. Use the local LLM we already built — and don't pay an LLM for deterministic work

We have a LiteLLM gateway + reasoning ladder on the t630 (`localDNS/10-ai-orchestration`):
`local-reason` (deepseek-r1:1.5b, cool/free) and `cloud-gpu-reason` for heavy lifts. It's
under-used as a cost lever. Industry rule of thumb: 60–70% of agent tasks are "simple"
(classify / extract / format / draft / summarize), and routing those off the frontier model
cuts total cost 60–90% at the same quality ceiling.

- **Deterministic first.** `tools/check-docs.py` already validates every internal link with
  zero tokens. Link checks, schema validation, the nftables/stats math — these are *scripts*.
  Routines should run the script and only invoke a model on failure. Don't spend tokens on
  what `python3` does for free.
- **Local model for the cheap LLM work.** First-draft prose, log/diff summarization, "is this
  comment actionable?" triage, classification, reformatting to house style → route to the
  t630 `local-reason` rung. Reserve Opus for genuine architecture/financial reasoning.
- **Cheaper Claude tier where local won't do.** Inside Claude Code, mechanical edits, commits,
  and doc checks don't need Opus — Haiku/Sonnet handle them at a fraction of the cost. Let the
  routines name a cheaper model and escalate to Opus only for the hard 10%.

---

## 4. Batch the autonomous runs into one warm session

Right now the process implies separate NARF, ZORT, and process routines, each re-paying the
~15k startup overhead and each starting a cold cache. **Run one daily "portfolio sweep"** that
loads the standing context once and does CTO + CFO + housekeeping in a single warm context:
one startup cost, the prompt cache stays hot across the steps, and Opus never has to compact
because the session stays scoped. This also makes the per-day Agent-SDK spend a single
predictable number.

---

## 5. On the prompt that asked for this review

The request was, paraphrased: *"Locate inefficiencies in our process… better prompting…
leverage other AI… hybrid local + API… ANYTHING that could help… search the web… check the
news."* Honest critique, since it was asked for:

- **It's unbounded by construction.** "ANYTHING you could possibly think of," "search the
  web," "check the news," with no priority and no stopping rule, is the most expensive shape a
  prompt can take — it tells the model to fan out maximally. Great for a one-off brainstorm,
  costly as anything recurring.
- **Six asks, no ranking, no output format, no budget, no destination.** The model has to
  guess what "done" looks like and where findings go.
- **Running *this* as a recurring routine is itself the pattern §0 warns about** — broad
  open-web research is the priciest thing to put on autopilot under the new metered pool.

A tighter version that would cost a fraction and return something more actionable:

> *"In ≤1 session, find the top 3 token/cost inefficiencies in our autonomous routines.
> Measure them against the actual repo (cite token counts). For each: the fix, the effort,
> the expected saving. Write findings to `docs/ai-cto/`. Skip anything you can't measure.
> One web search max, only to confirm current Anthropic pricing/caching behavior."*

That swaps "explore everything" for "measure a few things and write them down," names the
deliverable and its home, and caps the web spend. Keep the open-ended version for the rare
interactive deep-dive; make the recurring version scoped like this.

---

## Scoreboard — do these in order

1. **Decide** which routines run autonomously vs. interactively (post-June-15 billing). *[§0]*
2. **Cache + batch** the daily NARF/ZORT runs into one warm session. *[§1.1, §4]*
3. **Replace** the 10-file session-start mandate with a 1-page state digest. *[§1.2]*
4. **Slim** the CLAUDE.md files; move reference tables to README. *[§1.3]*
5. **Collapse** daily review files into rolling per-role logs. *[§2]*
6. **Route** cheap/deterministic work to scripts + the t630 ladder; Opus for the hard 10%. *[§3]*

---

### Sources (current as of 2026-06-16)

- [Claude Code pricing after June 15 — decision table](https://findskill.ai/blog/claude-code-pricing-after-june-15-decision-table/)
- [Anthropic release notes — June 2026](https://releasebot.io/updates/anthropic)
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Anthropic prompt caching](https://www.anthropic.com/news/prompt-caching)
- [Prompt caching in 2026 — real cost wins](https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins)
- [Hybrid cloud-local LLM architecture guide (2026)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run local AI models with Claude Code to cut costs](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Claude Code Skills — token-light when inactive](https://www.codewithseb.com/blog/claude-code-skills-reusable-ai-workflows-guide)
- [How to reduce Claude Code token usage (2026)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
