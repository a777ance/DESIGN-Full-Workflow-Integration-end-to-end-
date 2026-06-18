# NARF — review — 2026-06-18 — AI process & token efficiency

Special pass, by request: *"Locate inefficiencies in our PROCESS — between the user
and the AI. Reduce token use. Better prompting. Hybrid local LLM + Claude. Keep it
current — check the news."* Findings below, ordered by payoff. Web-sourced best
practices are cited at the bottom; I grounded every recommendation against our actual
files (`*/CLAUDE.md`, `localDNS/10-ai-orchestration/config.yaml`, this reviews/ cadence).

---

## The headline

**Our biggest token leak isn't the API — it's the always-loaded context.** Every
session re-pays for whatever sits in the loaded `CLAUDE.md`(s). The fix that beats
everything else is *shrinking what loads on every turn*, then *running the cheap work
on cheap models*. We already own the hardware for the second half (the LiteLLM router)
— it just isn't pointed at this workflow yet.

The 2026 consensus from the cost write-ups: most teams cut spend **40–70%** with
context hygiene + model tiering + caching, and a single CLAUDE.md trim has been
benchmarked at **~92% context reduction with no quality loss**. We're leaving most of
that on the table.

---

## Top findings, in order of payoff

### 1. Trim the always-loaded `CLAUDE.md` files — biggest, cheapest win (do today)
- **The numbers:** our seven `CLAUDE.md` files total **1,040 lines** (`localDNS` 326,
  `DESIGN` 295, `MARKETING` 214; the rest small). In a single-repo session only that
  repo's file loads — but **this very session has all seven in scope = ~1,040 lines
  (~12k tokens) prepended to every turn**, and any multi-repo work pays that tax.
- **What's bloating them:** reference material that Claude can read on demand is pinned
  in the always-on file instead. Examples: `localDNS/CLAUDE.md` inlines the full
  deploy-path table **and** the nftables deploy checklist (those belong in
  README/INSTALL-NOTES, fetched when needed). The **"House style" block is duplicated
  near-verbatim across 6 files** (~30 lines each ≈ 180 redundant lines).
- **The rule from the field:** *if Claude can infer it from the code, or a senior dev
  could find it in 20 min of reading, cut it.* Keep decisions and non-obvious
  conventions; push narrative/rationale to README/context files.
- **Action:** (a) lift the shared House-style + the three-repo table into one short
  canonical doc and have each `CLAUDE.md` link to it; (b) move the deploy-path table and
  nftables checklist out of `localDNS/CLAUDE.md` into README (they're already partly
  there); (c) target each `CLAUDE.md` at **≤120 lines of "can't-infer-it" facts.**
  Realistic outcome: 1,040 → ~350 lines. *This is a docs edit, no box access needed.*

### 2. Stop running routine days on a frontier model — tier the model to the task
- **The mismatch:** this daily review runs on **Opus 4.8 (1M ctx)**. Most days the
  honest output is "nothing shipped, still blocked on t630 access" (see 06-15…06-17).
  Paying frontier + 1M-context rates for a no-change status check is the textbook
  over-spend the 2026 cost guides flag ("no more cheap Claude").
- **Action:** run the *routine* daily pass on **Haiku 4.5** (or local `local-smart`),
  and **escalate to Opus only when something material changed** since the last review
  (new commit, closed tech-debt item, a decision landed). A cheap "did anything change?"
  gate in front of the expensive reviewer. Reserve Opus/1M for the genuinely hard,
  wide-context calls (architecture, cross-repo reasoning).

### 3. Point the LiteLLM router we already built at this workflow
- We already run a hybrid stack (`localDNS/10-ai-orchestration/config.yaml`): local
  Ollama tiers (`local-fast`/`local-smart`/`local-reason`) as default, Claude as
  overflow. **It's wired to the homelab chat UI, not to our dev/CTO process.** That's a
  built asset sitting idle for the task that asked for it.
- **The field split:** ~60–70% of agent requests are "simple" (classify, extract,
  format, lint), ~20–30% moderate, ~10% need a frontier brain. Route accordingly.
- **Action — concrete handoffs to local/cheap:**
  - `tools/check-docs.py` link audits, doc reformatting, Z→A list sorting, "summarize
    what changed" → **local model**, zero API cost.
  - Drafting/first-pass prose on `MARKETING`/`DESIGN` → `local-smart`, Claude only to polish.
  - Keep **anything touching real customer data local-only** anyway (matches the privacy
    posture and TD-14). 
  - ⚠️ **Tie-in to TD-14 (still open):** the `local-reason` fallback chain still spills
    to `cloud-overflow`, so a "sensitive" task fails *open* to Claude cloud. Before we
    lean on local routing for privacy, fix that fallback to fail **closed** (local-only).

### 4. Prompt caching — know why it *won't* save us yet, and what would
- Caching gives ~90% off repeated input — **but the TTL dropped to 5 min in early 2026.**
  Our daily routines run ~24h apart, so they **never hit a warm cache.** Caching helps
  *within* a burst of activity, not across once-a-day runs.
- **Action:** don't count on caching for the scheduled routines; the real lever for them
  is finding #1 (less to load = less to pay, cached or not). *Do* lean on caching for
  interactive sessions where you're hammering the same repo for an hour.

### 5. Subagents — use surgically, not by default
- Subagents isolate heavy reads (file dumps, search noise stay in the child; only the
  conclusion returns) — great for big fan-out. **But a subagent-heavy run can burn ~7×
  the tokens** of a single thread. For our small repo set, the daily review does **not**
  warrant fan-out. Keep subagents for genuine multi-location searches; don't reach for
  them reflexively.

---

## On the prompt that triggered this (you asked me to flag it)

**It is itself an inefficient prompt — and a good teaching example of the #1 cost
pattern.** "Locate inefficiencies… *ANYTHING* that could help… *anything you could
possibly think of*… search the web… check the news" is maximally open-ended, which
forces broad scanning and broad web research — exactly what the guides say to avoid.
It cost far more than a scoped version would.

**A tighter version of this same routine** (drop-in replacement, scoped + capped):

> *Weekly AI-cost pass. Check: (1) total line count of all `*/CLAUDE.md` vs last week;
> (2) whether `config.yaml` routes routine work to local models; (3) any model/pricing
> change in the last 7 days (one web search, Anthropic + LiteLLM only). Output ≤10
> bullets: what changed, what to do, est. token impact. If nothing changed since last
> run, reply "no change" and stop. Don't rewrite files unless I say so.*

Why it's cheaper: bounded checklist (no open scanning), capped web research (one
targeted search, not a sweep), explicit output ceiling, an early-exit on "no change",
and a no-edit default. **General rule for our routine prompts:** name the inputs, cap
the output, give an exit condition, and forbid side-effects unless asked.

---

## What I'd do this week (no t630 access required for any of it)
1. **Trim the `CLAUDE.md` set** to ≤120 lines each; de-dupe the House-style block into one linked doc. (Finding #1 — biggest win, pure docs.)
2. **Add a model-tier rule** to these routines: Haiku/local for the daily pass, Opus only on a real change. (Finding #2.)
3. **Fix TD-14's fail-open fallback**, *then* route doc/link/format chores to the local router. (Findings #3 + the standing TD-14.)
4. **Rewrite the routine prompts** to the scoped/capped template above. (The meta-fix.)

Expected combined effect, on the 2026 field numbers: **40–70% lower token spend on this
workflow**, most of it from #1 and #2 alone.

*I did not edit any `CLAUDE.md`, `config.yaml`, or routine config in this pass — those
are judgment calls with cross-repo blast radius, so they're recommendations pending your
go-ahead, not changes.*

---

### Sources (checked 2026-06-18)
- Manage costs effectively — Claude Code Docs: https://code.claude.com/docs/en/costs
- Best practices for Claude Code: https://code.claude.com/docs/en/best-practices
- Prompt caching — Claude API Docs: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude Code Token Optimization (2026 guide): https://buildtolaunch.substack.com/p/claude-code-token-optimization
- CLAUDE.md trim benchmark (~92% reduction): https://systemprompt.io/guides/claude-code-cost-optimisation
- Hybrid Cloud-Local LLM architecture guide (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- LiteLLM auto-routing docs: https://docs.litellm.ai/docs/proxy/auto_routing
- Token Economics 2026 ("no more cheap Claude"): https://age-of-product.com/token-economics-2026/
- Claude Code Subagents practical guide (2026): https://nimbalyst.com/blog/claude-code-subagents-guide/
- Anthropic release notes (June 2026): https://releasebot.io/updates/anthropic/claude-code
