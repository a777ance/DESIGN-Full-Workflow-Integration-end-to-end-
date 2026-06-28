# Human ↔ AI Process Efficiency Review — 2026-06-28

A NARF (AI CTO) review of how we work *with* the AI across the seven A777ance repos:
where tokens leak, where prompting can be tightened, and how to use the local-LLM
stack we already built. Findings are ordered by leverage (biggest win first).

> Voice note: this is an internal engineering doc, so it's allowed to talk like an
> IT person. Customer-facing surfaces still follow the plain-English rule.

---

## TL;DR — the five biggest levers

1. **Trim the memory files.** `localDNS/CLAUDE.md` (~5.4K tokens) and
   `DESIGN/CLAUDE.md` (~5K tokens) are loaded on *every* turn and both blow past
   Anthropic's ~200-line guideline. Cutting each to a lean briefing + linked detail
   is the single highest-ROI change.
2. **Stop paying the reversed-ordering tax.** The "alphabetical Z→A" and
   "reverse the walkthrough blocks" house-style rules fight the model's priors,
   so every write/edit burns extra reasoning tokens and re-work. Keep
   newest-first logs (standard); drop the two unusual reversals.
3. **Use the hybrid stack you already own.** `localDNS` has a LiteLLM router
   (`:4040`), Open WebUI, and a local reasoning ladder (deepseek-r1:1.5b → rented
   GPU). It's wired for *chat*, not for *work*. Route bulk/cheap tasks to the
   local model; reserve the Claude API for the hard 10%.
4. **Match the model to the task.** Don't run Opus on link-checking. Use
   Haiku/Sonnet or Claude Code's `opusplan` alias (Opus reasoning in plan mode,
   Sonnet for the edits).
5. **Offload determinism to code, not the LLM.** `tools/check-docs.py` is exactly
   the right pattern — extend it (SessionStart hooks, pre-edit greps) so the model
   never burns tokens on things a script does for a penny.

Industry baseline: teams report **40–70% token reduction** from context hygiene
alone, and **60–90% cost reduction** from local/cloud hybrid routing on the
60–70% of requests that are "simple." We are leaving most of both on the table.

---

## 1. Memory files are oversized and duplicated (highest ROI)

Measured today:

| Repo | CLAUDE.md lines | chars | ~tokens/turn |
| ---- | --------------: | ----: | -----------: |
| `localDNS` | 326 | 20,472 | ~5,400 |
| `DESIGN-…` | 295 | 17,987 | ~5,000 |
| `MARKETING` | 214 | 10,660 | ~2,900 |
| `customers` | 80 | 4,135 | ~1,100 |
| `claude-code-homelab` | 75 | 2,896 | ~800 |
| `Azure-lab` | 50 | 2,294 | ~600 |

Anthropic's own guidance: keep `CLAUDE.md` **under ~200 lines**. `localDNS` and
`DESIGN` are 60–65% over. A CLAUDE.md is re-sent on every turn — a 5K-token file
costs 5K tokens whether the session is 2 turns or 200.

**Two compounding problems:**

- **Bloat.** The big files carry full tables (deploy paths, every known issue,
  every WireGuard peer) that belong in `README.md` / `network-context.md` and can
  be *linked*, not inlined. The CLAUDE.md should be the one-screen briefing that
  says "here's the shape of the system and where to look," not the reference manual.
- **Duplication.** The entire ~30-line **House-style: ordering & typography**
  block is copy-pasted verbatim into **all six** active CLAUDE.md files
  (confirmed). That's ~180 lines of identical text the model re-reads per repo,
  and six places to edit when the rule changes.

**Action:**
- Cut `localDNS/CLAUDE.md` and `DESIGN/CLAUDE.md` to ≤200 lines: keep the
  mental model + the "where things live" pointers; move exhaustive tables to the
  README and link them. The deploy-path and known-issues tables are reference
  material, not briefing material.
- Factor the house-style block into one canonical file (e.g. `localDNS`, the
  public repo) and have each CLAUDE.md carry a 2-line summary + a link, instead of
  the full copy. (Claude Code's `@path` import can pull a shared file in where the
  repo layout allows.)
- Net: roughly **a third off the per-turn memory tax** on the two heaviest repos,
  plus less attention dilution (long context measurably degrades focus on the
  actual task).

Prompt caching softens the *dollar* cost of re-reading a stable prefix (cache
reads ≈ 0.1× input price), but it does **not** fix attention dilution, and the
5-minute cache TTL means any >5-min pause re-pays the full write. Smaller is still
better.

---

## 2. The reversed-ordering house style is a self-inflicted tax

The 2026-06-05 house style mandates three orderings:

- ✅ **Newest-first logs / changelogs / decision logs** — this is standard and
  fine. Keep it.
- ⚠️ **"Alphabetical lists run Z→A (descending)."**
- ⚠️ **"Walkthroughs: reverse the blocks, keep the steps."**

The two ⚠️ rules invert conventions the model (and every future human reader) has
deeply ingrained. Every time the AI generates or edits an alphabetical list or a
guide, it has to consciously override its default ordering, *then* self-check it —
that's extra thinking tokens on every such edit, plus a real error/rework rate when
it slips and produces A→Z and has to redo it. The walkthrough-block reversal is the
worst offender: it makes step-by-step docs harder to author *and* harder to read,
which is the opposite of what a playbook is for.

**This is a process-design choice, not a model limitation** — so it's squarely in
scope for this review. Recommendation: **keep newest-first for time-based content;
retire the Z→A alphabetical rule and the walkthrough-block reversal.** If there's a
brand/identity reason to keep them, at least confine them to customer-facing
artifacts and let internal docs use conventional ordering, where the cost is pure
overhead with no audience benefit. This is a `MARKETING`/founder decision; flagging
it as an ADR candidate.

---

## 3. Use the hybrid local+cloud stack you already built

`localDNS` stage 10 already runs the exact architecture the 2026 guides recommend:
**LiteLLM gateway** (`:4040`) + **Open WebUI** (`:3000`) + a **reasoning ladder**
(`local-reason` deepseek-r1:1.5b on the t630 CPU → `cloud-gpu-reason` full R1 on a
rented GPU → `cloud-overflow`). Today it's pointed at *interactive chat*. The
opportunity is to point it at *work*:

- **Route the cheap 60–70% locally.** Most repo chores are "simple" by the
  standard taxonomy — reformatting a doc to house style, drafting a "Handled For
  You" entry from notes, classifying a lead, first-pass link/anchor summaries,
  bulk find-and-describe. Run these through the local model via LiteLLM; they don't
  need a frontier model and they don't need to leave the box (a privacy win that
  fits the repo's whole ethos).
- **Keep Claude for the hard 10%** — architecture, multi-file refactors, the
  honesty-sensitive Statement logic, anything where being wrong is expensive.
- **LiteLLM gives you fallback + budgets for free.** Configure a Claude fallback
  so a local miss escalates automatically (an unexpected cloud call is far cheaper
  than a dropped task), and set per-tier budget caps.
- **Claude Code can sit behind an LLM gateway too** (`code.claude.com/docs/en/llm-gateway`)
  — useful for centralizing keys, spend tracking, and rate-limit handling across the
  repos, even if the heavy lifting stays on the Claude API.

Caveat from the repo's own known-issues: don't run `deepseek-r1:7b`+ on the t630
CPU — the local-reason ladder already accounts for this. Keep local routing to the
1.5b tier or the rented GPU.

**Concrete first step:** add 2–3 LiteLLM model aliases for "bulk doc work" pointed
at the local model, and adopt a rule of thumb — *if a task is mechanical and the
data is ours, try local first; escalate to Claude on a bad result.*

---

## 4. Model & effort selection on the Claude side

- This very session is running **Opus 4.8** (`claude-opus-4-8`, $5/$25 per MTok).
  Opus is correct for design/architecture/this review; it's overkill for
  classification, extraction, reformatting, and short edits.
- For high-volume mechanical work that *does* go to Claude, use
  **Sonnet 4.6** ($3/$15) or **Haiku 4.5** ($1/$5).
- In Claude Code specifically, the **`opusplan`** alias gives Opus-grade reasoning
  during plan mode, then drops to Sonnet for code generation — Opus judgment without
  Opus rates on every line.
- Use **`effort`** deliberately: `high`/`xhigh` for hard agentic work, `low`/`medium`
  for routine edits. Lower effort = fewer tool calls, less preamble, terser output.
- Enter **plan mode before expensive operations** (Shift+Tab twice). Planning first
  prevents the costly rewrite loop.

---

## 5. Offload determinism to code — extend the check-docs.py pattern

`tools/check-docs.py` (link/anchor verification) is the model of what to do: a
penny-cost script doing what would otherwise be thousands of tokens of LLM reading
and a worse result. Do more of it:

- **SessionStart hooks.** `Chronikomicon` already has a SessionStart hook wired in
  `.claude/settings.json` — the other repos don't. A hook can run `check-docs.py`,
  surface current git status, or pre-load the small set of files that matter, so the
  model starts grounded without spending a turn orienting.
- **Pre-process before the model sees data.** Instead of having Claude read a long
  file to find the relevant bit, a hook/grep can hand it just the matching lines —
  the classic "10,000-line log → 20 ERROR lines" reduction.
- **Verification stays deterministic.** Doc-integrity, schema checks (the
  `08-client-list-and-crm/schema.md` rules), and the stage-11 "no hand-retyping"
  invariant are all things a script should assert, not the model re-reason each time.

---

## 6. Prompt caching

The big stable CLAUDE.md/README prefixes are ideal cache candidates (cache reads
≈ 0.1× input price; ~90% saving on the cached span). Claude Code caches
automatically, but two habits maximize hits:

- **Keep the stable stuff stable.** Don't interpolate timestamps/IDs/"current date"
  into the top of a memory file — any byte change in the prefix invalidates the
  cache for everything after it. (The house-style adoption date is fine; a *live*
  date would not be.)
- **Bundle related work into a session** rather than spreading it across many
  >5-minute-apart one-off turns — the cache TTL is 5 minutes, so clustered work
  reuses the warm cache instead of re-paying the write each time.

---

## 7. Critique of the request that triggered this review

The prompt was, paraphrased: *"Locate inefficiencies in our PROCESS… reduce token
use… better prompting… leverage other AI… hybrid local + Claude… ANYTHING that
could help. Search the web. Keep UP TO DATE. Check the news. Thanks!"*

**What it did well:** it named the real goal (process efficiency), explicitly
opened the door to web research and to the hybrid-LLM angle, and asked for a
self-critique — all genuinely useful framing.

**Where it cost efficiency:**
- **No scope or success criterion.** "PROCESS" and "ANYTHING" leave the agent to
  guess the boundary, so it has to either over-explore (expensive) or pick a lane
  and risk missing the intended one. A good brief says what *done* looks like.
- **No priority or budget.** "Anything that could help" invites an unbounded
  survey. "Give me the top 5 by ROI, ≤2 pages" gets a sharper, cheaper answer.
- **Scattershot + filler.** The enthusiasm ("ANYTHING… Thanks!… Check the news!")
  is friendly but adds tokens without adding constraints.

**A tighter version of the same request:**

> *Review how we use Claude across the A777ance repos and find the top ways to cut
> token cost without hurting quality. Cover: (1) memory-file / context hygiene,
> (2) prompting habits, (3) using the local LLM stack in localDNS for cheap tasks.
> Web-check current best practices. Give me a prioritized list (biggest ROI first)
> with a concrete first action for each. Keep it under ~2 pages.*

Same intent, bounded scope, explicit deliverable shape — cheaper to run and easier
to act on. **General rule for prompting the AI: state the goal, the scope, the
constraints, and what the finished answer should look like.** Specific beats vague
every time ("optimize readability in `src/auth.js`, extract constants" >>
"make this better").

---

## Prioritized action checklist

| # | Action | Owner | Effort | Payoff |
| - | ------ | ----- | ------ | ------ |
| 1 | Trim `localDNS` + `DESIGN` CLAUDE.md to ≤200 lines; move tables to README | NARF | M | High |
| 2 | De-duplicate the house-style block into one linked source | NARF | S | Med |
| 3 | ADR: drop Z→A alphabetical + walkthrough-block reversal (keep newest-first) | Founder | S | Med-High |
| 4 | Add LiteLLM aliases for local bulk-doc work; "local-first, escalate to Claude" rule | NARF | M | High |
| 5 | Use Sonnet/Haiku/`opusplan` + `effort` for mechanical Claude work | All | S | Med |
| 6 | Add SessionStart hooks (run check-docs.py, surface git state) to the main repos | NARF | S | Med |
| 7 | Adopt the structured-prompt habit (goal/scope/constraints/deliverable) | All | S | Med |

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [LLM gateways — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Code Token Optimization (2026 guide)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [7 Practical Ways to Reduce Claude Code Token Usage — KDnuggets](https://www.kdnuggets.com/7-practical-ways-to-reduce-claude-code-token-usage)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Hybrid Cloud-Local AI Workflows | Cost Optimization Guide — BuildMVPFast](https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026)
- [Run Local AI Models with Claude Code to Cut Costs — MindStudio](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [LLM Gateways & Model Routing: Cut AI Costs 2026 — Lushbinary](https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/)
- [Code with Claude 2026: new agent features — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)

*Model facts (IDs, pricing, caching economics, effort/model tiers) verified against
the in-session Claude API reference, June 2026.*
