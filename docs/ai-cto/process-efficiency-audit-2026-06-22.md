# Process-efficiency audit — user ↔ AI loop (2026-06-22)

NARF (AI CTO) review of how we spend tokens working with Claude across the A777ance
repos, with current best practice (June 2026) and a plan that uses the hybrid LLM stack
we **already built** but don't yet point Claude at. Ordered by impact, biggest lever first.

> One-line answer: the largest recurring cost isn't any single session — it's the
> **CLAUDE.md files we re-pay on every session in every repo**, and the fact that our
> own LiteLLM router (stage 10, localDNS) sits *beside* Claude Code instead of *under* it.

---

## A. CLAUDE.md bloat — the single biggest lever

**What's happening.** CLAUDE.md loads in full before Claude reads a line of code, on
**every** session and **every** scheduled-routine run, in **every** repo. A 300-line
CLAUDE.md costs ~300 lines whether the session sends 2 messages or 200. Current sizes:

| Repo | CLAUDE.md lines | Est. tokens/session |
| ---- | --------------: | ------------------: |
| localDNS | 326 | ~4,800 |
| DESIGN (this repo) | 295 | ~4,300 |
| MARKETING | 214 | ~3,100 |
| customers | 80 | ~1,200 |
| claude-code-homelab | 75 | ~1,100 |
| Azure-lab | 50 | ~700 |
| **Total across portfolio** | **~1,040** | **~15K tokens, re-paid per session** |

The ~25-line **House style** block is duplicated verbatim in 6 of 7 repos. The big files
also carry *rationale and walkthrough prose* (the "why", the deploy-path tables, the
robotics analogy) that Claude rarely needs up front — that belongs in README/linked docs
it reads **on demand**, not in the always-on header.

**Fix (keeps the playbook, cuts the always-on cost ~40–60%):**
1. Treat CLAUDE.md as a **lookup table, not a brain dump** (the 2026 consensus). Keep:
   the one-paragraph "what this repo is", the hard invariants, the pointers. Move:
   deploy-path tables, rationale, walkthroughs → README/`network-context.md`/`workflow-context.md`,
   which Claude already opens when a task needs them.
2. **De-duplicate the house style.** Put it once in a `STYLE.md` (or the public localDNS),
   and in each CLAUDE.md replace the 25 lines with a one-line pointer. House style rarely
   changes; it doesn't need to ride in context on every routine tick.
3. **Keep CLAUDE.md byte-frozen.** Prompt caching gives ~90% off the repeated prefix —
   but only if the prefix doesn't change between calls. Don't interpolate dates or
   per-run state into CLAUDE.md (the harness already injects today's date separately).

---

## B. Wire the LiteLLM router *under* the work, not beside it

We built a genuinely good hybrid stack — `10-ai-orchestration/` (LiteLLM front door,
local-first tiers, the deterministic dispatcher, the Odin supervisor, the reasoning
ladder). It is the textbook 2026 cost architecture (local for the 60–70% simple work,
cloud only for the ~10% that needs a frontier model). **But it only serves Open WebUI
and bespoke scripts — none of our actual Claude Code usage flows through it.**

Two concrete moves:
1. **Route the deterministic / cheap routine work locally.** Link-checking is already
   non-LLM (`tools/check-docs.py` — good, keep that pattern). Log triage, "is everything
   healthy", changelog summarising, "does this read like a real Handled-For-You entry" —
   these are `local-smart` (qwen2.5:7b) or `local-reason` jobs, not Opus jobs. Run them
   through `ai.home.lan:4040` with the dispatcher's privacy gate, and they cost ~$0 and
   never leave the house.
2. **Reserve the Claude API for what only it can do** — implementation, hard reasoning,
   review, anything touching real customer data that still needs frontier quality. The
   dispatcher's existing `sensitive → local-only, allow_cloud=False` lock is exactly the
   right boundary; extend the rule table to cover the routine catalog.

This is the highest-leverage *unrealized* asset we have: the infra exists, it's just not
on the critical path of the day-to-day loop.

---

## C. Model selection on scheduled routines

Routines appear to default to Opus 4.8 (this very audit ran on `claude-opus-4-8[1m]`).
Opus is right for *this* one-off analysis; it's overkill for a daily watchman.

- **Match the model to the job.** Opus $5/$25 per Mtok, Sonnet 4.6 $3/$15, Haiku 4.5
  $1/$5. A "watch for N new errors / anything changed" routine is Haiku or a local tier.
  Start sessions on the cheapest model that can do the job; escalate to Opus only for
  architecture/implementation.
- **`DISABLE_NON_ESSENTIAL_MODEL_CALLS=1`** in the routine environment — kills the
  background suggestion/tip model calls that add nothing to an unattended run.
- **Scope, don't sweep.** A routine that greps for a condition and reads only the matching
  lines beats one that reads whole files/logs into context (tool output is appended in
  full and re-paid on every later turn). Use Explore/sub-agents for fan-out so the file
  dumps stay in the sub-agent and only the conclusion returns to the main context — that
  alone kept *this* audit's context lean.

---

## D. Session hygiene (applies to interactive use too)

- `/clear` between unrelated tasks; `/compact` when a long session has earned it.
- `/context` to see where the window is going; trim the worst offender (usually a big
  file read or a verbose command output, not the prompt).
- Read from files rather than pasting large blocks into the prompt — pasted text is
  re-processed on every subsequent turn for the rest of the session.

---

## E. Your prompt, critiqued (you asked)

The triggering prompt was effective at *intent* but expensive at *execution*. It was a
stream of maximalist, open-ended asks ("ANYTHING that could help", "Search the web",
"Keep UP TO DATE", "Check the news") with no scope or success criterion, which pushes the
agent to load everything it might conceivably need (here: a ~40K-token API skill + five
full CLAUDE.md files) before it can tell what matters.

A tighter version would name the goal, the constraint, and the shape of the answer:

> "Audit token spend on our Claude Code routines across the A777ance repos. We already run
> a local LiteLLM router (localDNS stage 10). Give me a prioritised, quantified list of
> the top 5 levers and the one change with the best payoff. Skip background; cite sources."

That single rewrite removes the guesswork, narrows the research, and gets the same answer
for a fraction of the tokens.

Second, structural: **this audit is a one-off, not a daily watchman.** A process-efficiency
review run on a frequent schedule re-pays a large context (skill + 5 CLAUDE.mds) every
tick to mostly re-derive the same findings. Run it quarterly, or when token spend visibly
moves — not daily. The best routines watch for a *condition* and stay silent otherwise;
"think hard about everything" is a poor fit for a recurring trigger.

---

## Priority order

1. **A — trim & de-dup CLAUDE.md** (cheapest to do, pays on every session forever).
2. **B — route routine/cheap work through the local LiteLLM tiers** (infra already built).
3. **C — right-size the model per routine + `DISABLE_NON_ESSENTIAL_MODEL_CALLS=1`.**
4. **D — session hygiene; scope reads, use sub-agents for fan-out.**
5. **E — tighten routine prompts; downgrade this audit from daily to quarterly.**

## Sources (June 2026)

- [12 Ways to Cut Token Consumption in Claude Code — Firecrawl](https://www.firecrawl.dev/blog/claude-code-token-efficiency)
- [Claude Code Token Optimization (2026 Guide) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [23 Tips for Smart Claude Code Token Saving — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM gateway configuration — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Hybrid Cloud-Local AI Workflows / Cost Optimization — BuildMVPfast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
