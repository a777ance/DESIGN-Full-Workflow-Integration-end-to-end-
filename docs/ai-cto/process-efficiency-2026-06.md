# Process efficiency review — user ↔ AI (2026-06-20)

A NARF (AI CTO) review of how we work *with* Claude across the A777ance repos: where
tokens and money leak, where prompting can be tighter, and how to actually use the
hybrid local/cloud LLM rig we already built. Findings are ordered by leverage (biggest
first), per house style they are not — biggest-first beats newest-first when the point
is "do this one thing."

**TL;DR — the one thing:** our `CLAUDE.md` files are the largest recurring cost, and
every scheduled routine pays for *all* of them. Trim them under 200 lines, move the
deploy/verify/checklist blocks into on-demand Skills, and scope each routine to the
fewest repos. That alone should cut steady-state token use materially, before we touch
models or prompts.

---

## 1. `CLAUDE.md` bloat is the #1 lever (P1)

**What's happening.** Anthropic's own cost guidance says *"Aim to keep CLAUDE.md under
200 lines"* and *"move specialized instructions into skills"* because the whole file is
loaded into context at **every** session start. Ours:

| File | Lines | Over budget |
| ---- | ----- | ----------- |
| `localDNS/CLAUDE.md` | 326 | +126 |
| `DESIGN-…/CLAUDE.md` | 295 | +95 |
| `MARKETING/CLAUDE.md` | 214 | +14 |
| (plus `customers`, `Azure-lab`, `claude-code-homelab` — smaller, but still loaded) | | |

A scheduled routine like the one that generated this report had **all seven repos'**
`CLAUDE.md` injected up front — that is paid on every run, before any work happens.

**Fixes (in order):**

1. **Move reference blocks to Skills.** The `localDNS` CLAUDE.md embeds the full
   deploy-path table, the "nftables volume layer — deploy checklist," and a block of
   verification commands. None of that is needed unless you're deploying. Put each in a
   Skill (`deploy-paths`, `nftables-accounting`, `verify-stack`) that loads only when
   invoked. Same for the DESIGN repo's stage-by-stage tables — keep the funnel diagram,
   move the per-stage detail to README/skills.
2. **De-duplicate the house-style block.** The identical ~18-line "ordering & typography"
   section is copy-pasted verbatim into every CLAUDE.md (~126 lines of the same tokens
   across 7 files, every multi-repo session). Keep one canonical copy (a skill or a
   single linked file) and a one-line pointer in each repo.
3. **Target:** every CLAUDE.md under 200 lines of essentials only. Expect the rest to be
   reachable on demand, not resident.

This is logged as **TD-15** in `tech-debt.md`.

## 2. Scope each routine to the fewest repos (P1)

Routines pay the full `CLAUDE.md` + setup tax for **every repo in session scope**, even
when the task touches one. This session carried all seven. Make routine scope minimal and
widen on demand with the `add_repo` tool. A "review process efficiency" routine needs
the DESIGN hub only; a "check the box" routine needs `localDNS` only.

## 3. Use the hybrid rig we already built (P1, ties to TD-14)

We are *ahead* of the industry pattern here — `localDNS` stage 10 already runs LiteLLM as
a gateway with a reasoning ladder: `local-reason` (deepseek-r1:1.5b on the t630, cool),
`cloud-gpu-reason` (full R1 on a rented GPU), `cloud-overflow` (Claude cloud). Industry
benchmarks put hybrid local/cloud routing at **60–80% cost reduction** with minimal
quality loss when routine work goes local and only hard reasoning hits the cloud.

But two gaps stop us from banking that:

- **TD-14 (privacy + correctness):** `local-reason` fails over to `cloud-overflow`, so a
  `sensitive`-tagged prompt can leak to Claude cloud if the local model is down. Fail
  closed first (local-only fallback), *then* lean on local routing — otherwise routing
  more work local increases the blast radius of that bug.
- **We don't actually route the cheap work local yet.** Candidate work that does **not**
  need Claude and could run on the local tier: first-pass marketing-copy drafts, statement
  composition QA, link/anchor checking (`tools/check-docs.py` triage), log triage, commit-
  message drafting, roster lint. Reserve the Claude API for: architecture decisions,
  customer-facing copy final passes, anything touching real customer data judgment.

Note Claude Code itself can be pointed at a custom gateway/model, so the same LiteLLM
front door can sit in front of *both* local models and Claude with one endpoint.

## 4. Routine-level token tactics (P2)

Concrete, low-effort levers from Anthropic's current cost guidance:

- **Subagents for verbose ops.** Running `check-docs.py`, fetching pages, scanning logs —
  delegate to a subagent so the verbose output stays in *its* context and only a summary
  returns. (This report's web research could have been a subagent.)
- **Hooks to pre-filter.** A `PreToolUse` hook that greps test/lint/log output to just the
  failing lines turns tens of thousands of tokens into hundreds. Good fit for
  `check-docs.py` and any `make` output.
- **Prompt caching on the stable blocks.** The big CLAUDE.md/system content is identical
  run-to-run — cache it (cached input is ~90% cheaper; a **1-hour TTL** is now available,
  added Jan 2026, good for back-to-back routines).
- **`/clear` between unrelated tasks; plan mode for big ones.** Plan-mode-first avoids
  paying for a wrong-direction implementation.
- **Right-size the model and thinking.** Sonnet for most coding/coordination, Opus only
  for hard reasoning, Haiku for simple subagents; lower the thinking effort for
  mechanical tasks. (Agent teams cost ~7× a normal session — keep teams tiny.)
- **CLI over MCP where possible.** MCP tool *definitions* are deferred here (good), but CLI
  tools add zero per-tool listing overhead.

## 5. Better prompting (P2)

- **Specific beats broad.** "Add input validation to `login` in `auth.ts`" reads a couple
  files; "improve the codebase" scans everything. Name the file, the function, the
  expected output.
- **Give a verification target.** Paste the expected result / test case so the model can
  self-check instead of round-tripping with us.
- **For recurring routines, write an output contract**, not an open brief (see §6).

## 6. This prompt, critiqued (you asked)

The prompt that launched this run was, deliberately, a wide brainstorm: *"locate
inefficiencies… anything you could possibly think of… leverage other AI… check the
news… thanks!"* That's fine **once**, for discovery. As a **recurring routine** it's
inefficient for three reasons: (a) it bundles ~6 distinct asks, so the model fans out
across all of them every run; (b) it has no stop/notify condition, so it does full work
even when nothing changed; (c) "anything you could think of" invites maximum exploration —
the opposite of token-frugal. It also front-loads a 1,000-line multi-CLAUDE.md context
for a task that only needed the DESIGN hub (see §2).

**A tighter, reusable routine prompt:**

> Review our AI-usage process for **one** named area this run (rotate:
> CLAUDE.md size / routing / prompting). Compare against current Anthropic cost
> guidance (1–2 web searches max). Output: top 3 concrete changes with file paths and
> expected token impact. **Only notify me if you find something that changes a number or
> a config** — otherwise append to `process-efficiency` and stay silent. Scope: DESIGN
> repo only; `add_repo` if needed.

That keeps the value, drops the cost, and respects the "silence when all's well" rule for
unattended routines.

## 7. Keeping current — what changed recently (and the macro trend)

Recent, relevant Claude features (use them):

- **Instant compaction** (Claude Code v2.0.64, Feb 2026) and **server-side compaction**
  (beta, `compact-2026-01-12`) — Anthropic now recommends server-side over SDK compaction.
- **`/recap`** (Apr 2026) — resume a session from a summary instead of replaying it.
- **Memory tool** — cross-session memory file dir, pairs with compaction.
- **1-hour prompt-cache TTL** (Jan 2026) on Haiku/Sonnet/Opus 4.5-class.
- **MCP tool search / deferred tool definitions** — only tool *names* enter context until
  used (already active in our sessions).
- **Code-intelligence plugins** — symbol navigation instead of grep+read for typed langs.

Macro trend the trade press is flagging ("Token Economics 2026 / No More Cheap Claude"):
effective per-task costs are trending **up** as agentic workflows consume more tokens, so
the efficiency work above compounds — it's worth more now than it was six months ago.

---

### Sources

- Manage costs effectively — Claude Code Docs: https://code.claude.com/docs/en/costs
- Effective context engineering for AI agents — Anthropic: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Prompt caching — Claude API Docs: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Context editing / Compaction — Claude API Docs: https://platform.claude.com/docs/en/build-with-claude/compaction
- Hybrid Cloud-Local LLM architecture guide (2026): https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- Hybrid cloud-local AI cost optimization (2026): https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- 23 Tips for Claude Code token saving: https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/
- Token Economics in 2026: https://age-of-product.com/token-economics-2026/
