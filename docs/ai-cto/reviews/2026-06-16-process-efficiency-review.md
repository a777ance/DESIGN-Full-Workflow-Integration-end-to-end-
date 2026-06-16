# Process-Efficiency Review — the user↔AI loop — 2026-06-16

Prepared by: NARF (AI CTO), on founder request: *"locate inefficiencies in our PROCESS
between the user and the AI — reduce token use, better prompting, leverage other AI,
run a hybrid local-LLM + Claude API. Keep it up to date; check the news."*

Scope: **how we work with the AI**, not the product. Findings are ranked by leverage
(biggest token/cost win first). Everything here is sourced to current (June 2026)
practice and our own configs — citations at the bottom.

---

## The one headline (timely — landed yesterday)

**On 2026-06-15, Claude Code's programmatic / agentic usage moved out of the flat
subscription compute pool into a dedicated credit system billed at full API rates.**
That is *exactly* the kind of usage we lean on: scheduled routines (this review is one),
PR babysitting, cross-repo reviews, the daily NARF/ZORT session commits. As of yesterday
those stopped being "free inside the Max plan" and started metering at API prices.

**Action this week:** look at the new Claude Code credit/usage dashboard and see what our
agentic usage actually costs now. Every recommendation below is now a dollar number, not
just hygiene. (Sources: Bind AI, UsageBox, jangwook.net — all June 2026.)

---

## Top findings, ranked by leverage

### 1. Our CLAUDE.md files are large and duplicated — and they load every session, every turn
This is the single biggest token lever we fully control.

- CLAUDE.md is injected into context at session start **and re-sent on every turn**. The
  `localDNS` CLAUDE.md is ~400 lines (full deploy-path table, every known issue, the whole
  Unbound drop-in table). It's a brilliant reference — but most of it isn't needed on most
  turns, and we pay for all of it on every turn.
- The **~40-line "House style: ordering & typography" block is byte-for-byte identical
  across all 7 repos** and prepended to all of them. We re-buy it constantly.
- **Recommendation (advisory — not changing your configs unasked):**
  - Trim each CLAUDE.md to a *briefing*: what the repo is, the invariants, and **links** to
    the deep tables. Let Claude `Read` the deploy-path table / known-issues on demand
    instead of carrying them resident. Anthropic's own guidance: keep CLAUDE.md short and
    high-signal; push detail to files read on demand.
  - Factor the house-style block into one `STYLE.md` (or a short shared snippet) and have
    each CLAUDE.md link to it rather than inline the whole thing.
  - Rule of thumb from the field: every 1,000 tokens shaved off CLAUDE.md is ~1,000 tokens
    saved *per turn* — on a 40-turn session that's 40k tokens, now at full API rates.

### 2. Turn on the 1-hour prompt cache (`ENABLE_PROMPT_CACHING_1H`)
Anthropic dropped the default cache TTL to **5 minutes** in early 2026 — which silently
raised effective cost 30–60% for long/slow sessions. The April 2026 Claude Code update
added `ENABLE_PROMPT_CACHING_1H` to buy back the 1-hour window. Our routines and reviews
routinely span more than 5 minutes (this one did), so under the default TTL the stable
prefix (system prompt + tool defs + CLAUDE.md) keeps falling out of cache and getting
**re-billed as a cache *write*** (writes cost *more* than normal tokens). Set the 1h flag
for any session/routine that runs longer than a few minutes. (Sources: dev.to, dsebastien.net.)

### 3. Stop running cheap routines on the most expensive model
This very routine is executing on **Opus 4.8 with a 1M-token context window** — the most
expensive config Anthropic sells — to *check the news and write a summary*. That's a
Haiku/Sonnet job. Match the model to the task:
- **Haiku 4.5** — status checks, "did anything change?", log triage, formatting.
- **Sonnet 4.6** — the daily driver: code, diffs, reviews, most routines.
- **Opus 4.8** — reserve for genuinely hard reasoning / architecture.
For scheduled routines specifically, pin the model in the routine config rather than
inheriting Opus. (Source: Anthropic best-practices; claudefa.st model guide.)

### 4. We already own a hybrid router — we're just not pointing the cheap work at it
`localDNS/10-ai-orchestration` runs a LiteLLM front door (`ai.home.lan:4040`) with local
Ollama tiers (`local-fast` qwen2.5:3b, `local-smart` qwen2.5:7b) and Claude as overflow.
The proven 2026 pattern is **local-first triage, Claude for the hard 20%**:
- Add a `qwen2.5-coder:7b` tier (best-in-class local coder, ~76% HumanEval) for code
  triage and "is this even worth escalating?" gating.
- **Pre-process locally before calling Claude:** have a local model summarize/extract the
  relevant slice of a file or log, and send Claude the slice — not the raw 400-line file.
  Field reports put this at **8–10× cost reduction** on the work that can be offloaded,
  with no quality loss on the reasoning that stays on Claude.
- Concrete homelab fit: log scans, "did the box change?" diffs, draft commit messages, and
  first-pass doc-lint can all run on the t630's local tiers; only the synthesis comes to
  Claude. Watch out for **TD-14** while doing this — the `local-reason` fallback can spill
  a `sensitive` task to cloud; fix that fail-closed before routing anything private local→cloud.

### 5. Use subagents and `Explore` for fan-out, keep the main context clean
When a task means reading across many files (cross-repo reviews are our bread and butter),
delegate to a subagent / the `Explore` agent. The subagent burns its own context window and
returns only a summary — the main thread never ingests the file dumps. This is the highest-
value habit for our multi-repo reviews specifically. (Source: Anthropic costs/subagents docs.)

### 6. Adopt the newer cost features
- `/recap` (April 2026) — resume a session from a summary instead of replaying the whole
  thread on return.
- `microcompact` / auto-compaction — let it summarize history near the context limit rather
  than carrying every turn.
- **Output styles** — set a terse/"concise" output style so routine answers stop padding.
  (A `claude-token-efficient` CLAUDE.md drop-in exists that does exactly this.)
- `/clear` between unrelated tasks instead of one ever-growing session — the biggest hidden
  drain is a long thread re-read on every message.

---

## Better prompting (general + a critique of the request that triggered this)

**General principles that cut tokens without cutting quality:**
- **Scope tightly.** "Refactor the login function in `auth.ts`" beats "refactor the auth
  module." Narrow scope = less context pulled in, fewer tokens, more focused output.
- **Batch.** One complete prompt with all the changes beats five follow-ups, each of which
  re-reads the whole thread.
- **Specify the output and a budget.** "Give me the top 5, one line each" prevents an essay.
- **Say where to look.** Naming the file/dir saves an exploration pass.

**Critique of the prompt that launched this routine** (you asked me to flag it — fair game):
- It was **deliberately unbounded**: *"ANYTHING that could help,"* *"search the web,"*
  *"check the news."* Open-ended invitations make me fan out widely and read broadly — the
  most expensive shape of request. Great for a one-off "blue-sky it" session; expensive as a
  *recurring* routine, because it re-does the wide sweep every run.
- **No output contract.** It didn't say "top 5, ranked, ≤1 line each" or "only flag what
  changed since last run," so I produced a full report. For a *scheduled* routine, that's the
  costly default.
- **It mixes a standing instruction with a one-time ask.** "Keep up to date, check the news"
  is a recurring intent; the deep analysis is a one-time deliverable. Splitting them lets the
  recurring part run cheap.

**A cheaper rewrite for the recurring version:**
> *"Weekly: search only for Claude Code / Anthropic pricing + feature news from the last 7
> days. If nothing material changed for our usage, reply 'no change' and send no
> notification. If something did, give me ≤5 bullets: what changed, the dollar/token impact
> on our routines, and the one action. Run on Haiku; escalate to Sonnet only if you find a
> pricing change."*

That version: bounds the search, sets an output contract, makes silence the default, and pins
a cheap model — turning a full Opus sweep into a near-free check that only spends tokens when
there's actually news.

---

## Suggested follow-ups (not done in this pass — advisory only)

| Leverage | Action | Owner |
| -------- | ------ | ----- |
| High | Audit post-2026-06-15 Claude Code credit spend; tag which routines could move to Haiku/Sonnet or local | ZORT + NARF |
| High | Trim CLAUDE.md files to briefings + on-demand links; extract shared `STYLE.md` | NARF |
| Med | Set `ENABLE_PROMPT_CACHING_1H` for routines/sessions > 5 min | NARF |
| Med | Add `qwen2.5-coder` tier to LiteLLM; route log/diff triage local-first (after TD-14 fail-closed fix) | NARF |
| Low | Add a terse output style + `/recap` to routine workflow | NARF |

I did **not** edit any CLAUDE.md or config in this pass — those are sizeable changes that
should be approved first. This file is the recommendation; say the word and I'll do the
CLAUDE.md trim + `STYLE.md` extraction as a reviewable diff.

---

## Sources (June 2026)
- Anthropic, *Best practices for Claude Code* — https://code.claude.com/docs/en/best-practices
- Anthropic, *Manage costs effectively* — https://code.claude.com/docs/en/costs
- Anthropic, *Prompt caching* — https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Bind AI, *Claude Code Pricing June 2026* — https://blog.getbind.co/claude-code-pricing-changes-june-15-what-youll-actually-pay-2026/
- UsageBox, *What Claude Code Actually Costs in 2026 — two June deadlines* — https://usagebox.com/articles/claude-code-cost-2026-per-token-per-month-june-deadlines
- jangwook.net, *Claude Code June 2026 Update: Safe Mode, Opus 4.8, doubled rate limits* — https://jangwook.net/en/blog/en/claude-code-june-2026-new-features-changelog-developer-guide/
- dev.to, *Claude Prompt Caching in 2026: the 5-minute TTL change* — https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363
- KDnuggets, *Pairing Claude Code with Local Models* — https://www.kdnuggets.com/pairing-claude-code-with-local-models
- MindStudio, *Run Local AI Models with Claude Code to Cut Costs 10x* — https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs
- Analytics Vidhya, *23 Tips for Claude Code Token Saving* — https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/
- claudefa.st, *Every Claude Model* — https://claudefa.st/blog/models
