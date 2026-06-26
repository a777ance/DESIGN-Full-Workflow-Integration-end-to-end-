# Process efficiency review — user ⇄ AI token use

*Review date: 2026-06-26. Owner: NARF (AI CTO). Re-run quarterly or after any major Claude Code release.*

This is a standing review of **how we work with the AI**, not what we build. The goal: same
output, fewer tokens, less wall-clock, less hand-holding. Findings are ordered **highest ROI
first**. Each has a concrete action and a rough token/cost impact.

> **How to read the numbers:** ~1.33 tokens per English word. "Per session" means the cost is
> paid once at session start; "per turn" means every single message pays it.

---

## TL;DR — the five moves that matter

1. **Centralize the duplicated house-style block** → saved on every session in every repo. *(do today, 15 min)*
2. **Cut the two big CLAUDE.md files (~3.5k tokens each) to a ~600-token core + linked detail** → the rest loads only when needed. *(do this week)*
3. **Stop defaulting to Opus 1M.** Use `opusplan` (Opus plans, Sonnet executes) and let Haiku triage. *(40–70% off the model bill)*
4. **Gate the MCP servers (Notion, GitHub) per-session** instead of always-on — their tool schemas are a fixed per-session tax. *(a few k tokens/session)*
5. **Offload bulk/cheap work to the t630's own LiteLLM router** (already deployed, stage 10 of localDNS) — link/lint/classify/summarize jobs never need to touch the Claude API.

---

## 1. CLAUDE.md is the single biggest recurring cost — and it's partly duplicated

**What's happening.** Every session injects the project's `CLAUDE.md` *before* any work. Our files:

| Repo | Words | ~Tokens | Paid |
| ---- | ----- | ------- | ---- |
| localDNS | 2,728 | ~3,630 | per session |
| DESIGN-… | 2,608 | ~3,470 | per session |
| MARKETING | 1,445 | ~1,920 | per session |
| claude-code-homelab | 371 | ~490 | per session |
| customers | 562 | ~750 | per session |
| Azure-lab | 316 | ~420 | per session |

That's a **~3,500-token tax before you type a word** in our two main repos, every session. The
2026 guidance is blunt: a 5,000-token CLAUDE.md costs 5,000 tokens on every turn/session — trim
the persistent context aggressively, because it's the most-repeated bill you pay.

**The duplication.** The identical ~171-word "House style: ordering & typography" block is copied
verbatim into **6** CLAUDE.md files. That's ~1,026 words (~1,360 tokens) of pure duplication, and
five of the six copies are dead weight on every session in those repos.

**Actions:**
- **(a)** Move the house-style block to one file — `DESIGN-…/docs/house-style.md` (or keep the
  canonical copy in the public localDNS and link it). Replace the six inline copies with a single
  line: *"House style (ordering, Z→A lists, Gill Sans MT) — see `docs/house-style.md`."* Claude
  reads it on demand only when a styling question actually comes up.
- **(b)** Split each big CLAUDE.md into a **~600-token core** (what's true every session: what the
  repo is, the hard rules, the push-branch policy) and **linked detail** (the stage map, deploy-path
  tables, the full known-issues matrix). The detail files are already there (README, network-context,
  workflow-context) — CLAUDE.md should *point*, not *duplicate*. The localDNS deploy-paths table and
  the DESIGN stage map are reference tables Claude can open with one Read when it needs them, not
  things it needs memorized on every "fix this typo" session.
- **(c)** **Don't let all repos' instructions load at once.** This very review session had **six**
  CLAUDE.md files (~8,000 words / ~10.6k tokens) injected together because the repos are siblings
  under `/home/user`. When you only mean to work in one repo, open the session scoped to that repo's
  directory so you pay one CLAUDE.md, not six.

*Estimated saving: ~2,500–3,000 tokens/session in the main repos, plus the ~1,360-token dedup,
plus avoiding the 6× pile-up on cross-repo sessions.*

---

## 2. Stop defaulting to Opus 1M for everything

**What's happening.** This session runs Opus 4.8 with the **1M context window**. The 1M window
carries premium per-token pricing once context passes ~200k, and Opus is the most expensive tier
regardless. Most of our work — editing markdown playbooks, fixing links, updating logs, rendering
statements — does not need Opus-grade reasoning.

**The 2026 routed-stack pattern: Haiku triages, Sonnet builds, Opus reviews.**
- **Haiku** (~3× cheaper than Sonnet, ~5× cheaper than Opus): link checks, log/CRM edits, "does
  this file follow house style", classification, first-pass drafting.
- **Sonnet** — the right default for ~60–70% of real work; the everyday driver.
- **Opus** — reserve for genuinely hard reasoning or where a wrong answer has real cost
  (architecture/ADR decisions, the honesty-rule statement logic, financial modeling in ZORT).

**Actions:**
- Switch the default to **`/model opusplan`** (Opus does the planning, Sonnet executes the edits) or
  just **Sonnet** for routine doc work. Escalate to Opus only when Sonnet visibly struggles.
- Use **`/model haiku`** for the bulk, mechanical sessions (running `check-docs.py`, reverse-chron
  log inserts, schema field additions).
- For subagents (we now have nested subagents up to several levels), set cheap agents to
  `model: haiku` explicitly — don't let them inherit Opus.

*Estimated saving: teams report 40–85% off the model bill from routing alone; 70% routed to
Haiku/Sonnet cuts the input-token bill ~two-thirds.*

---

## 3. We already own a local LLM — use it as the cheap tier

**What's happening.** localDNS stage 10 already runs a **LiteLLM router (port 4040) + Open WebUI +
a reasoning ladder** (deepseek-r1:1.5b local on the t630; full R1 on a rented GPU via Tailscale).
This is a deployed hybrid stack we're barely leveraging for *our own workflow*.

**The hybrid play:** anything that is high-volume and low-stakes should never hit the paid API.
- **Local (t630 / LiteLLM):** draft-quality summaries, bulk classification, "rewrite this in the
  homeowner voice" first passes, log tidying, extracting fields from call notes into roster.json,
  routine commit-message drafts. The box is on a flat cost — every local inference is effectively free.
- **Claude API:** the final pass, anything customer-facing/kept-document, anything needing current
  knowledge or large-context reasoning.

**Actions:**
- Point a `claude-code-llm-router`-style shim (or just Open WebUI / the existing LiteLLM endpoint)
  at the t630 for the cheap tier, and keep Claude Code on the API for the high-stakes tier. Run them
  side by side; route by task, not by habit.
- Good first candidate: the **monthly statement compose first-draft** and **"Handled For You" log
  phrasing** — generate locally, have Claude do the honesty-rule final review. Keeps the penny-a-home
  economics intact and offloads the verbose part.

---

## 4. MCP servers are an always-on token tax

**What's happening.** Notion MCP is wired into DESIGN, localDNS, and MARKETING via `.mcp.json`, and
GitHub MCP loads in these sessions. **Every connected MCP server's tool schemas occupy context for
the whole session**, whether or not you call them. The GitHub server alone exposes ~60 tools.

**Actions:**
- Don't auto-connect Notion in repos where a given session won't touch Notion. Use
  `claude mcp login/logout <name>` (new in June 2026) or remove it from the per-repo `.mcp.json` and
  connect on demand.
- Lean on the harness's **deferred-tool / ToolSearch** behaviour: tools load only when searched for.
  Fewer always-on servers = smaller fixed per-session overhead.

---

## 5. Prompt caching — protect the 90% discount we're already getting

**What's happening.** Cache reads bill at ~10% of input rate (breaks even after ~1.4 reads); cache
writes cost 1.25×. The cache dies after **5 minutes of inactivity**, and **one changed token before
a cache breakpoint invalidates everything after it**.

**Actions (mostly behavioural):**
- **Work in focused bursts**, not across long gaps. Coming back 30 min later means re-paying the
  full context cold. Batch a repo's edits into one sitting.
- Keep the static stuff static: our newest-first / reverse-chronological house style is actually
  *cache-friendly* for logs (we prepend, the old cached body is unchanged) — but **don't reorder or
  re-upload files mid-session**; that nukes the cache.
- Don't inject volatile content (today's date, run IDs) ahead of stable instructions.

---

## 6. The way we *prompt* — including the prompt that triggered this review

**What's happening.** The request that started this review was, paraphrased: *"Locate inefficiencies
in our PROCESS… Is there a better way… Perhaps better prompting… anything you could possibly think
of… ANYTHING that could help… search the web… check the news. Thanks!"*

It got a good answer, but it's an **expensive shape of prompt**: open-ended ("anything"),
multi-objective, and unbounded on research. That maximizes tokens — the model fans out wide because
no boundary was given. Better-prompting principles that apply to us generally:

- **Bound the scope and the output.** "Find the top 5 token sinks in our Claude Code setup and give
  one action each, < 400 words" returns faster and cheaper than "anything that could help."
- **State the deliverable up front** (a doc? a diff? a number?) so the model doesn't hedge across
  formats.
- **Separate research from action.** "First list what you'd change, then wait" prevents a wide,
  speculative implementation pass.
- **Front-load the constraints** (which repo, which branch, don't touch X) — cheaper than corrections.
- **Drop the politeness padding** in *machine* prompts (the "Thanks!" etc.). Harmless individually,
  but in automated/looped prompts it's tokens with no signal. (Keep being kind to humans.)
- **For recurring research like this,** pin a tight template and a token ceiling, and let a cheap
  model do the first sweep.

A tighter version of the triggering prompt: *"Audit our Claude Code token use across the A777ance
repos. Output a ranked list of the 5 biggest token sinks with one concrete fix and an estimated
saving each. Check current best practices on the web (cite). Scope: don't change code, write the
findings to docs/ai-cto/process-efficiency.md. ≤ 1,200 words."*

---

## 7. Smaller wins (batch them)

- **`/compact` and context hygiene:** compact deliberately at natural breakpoints rather than
  letting long sessions auto-compact mid-task; use `/usage` (now broken down by cache miss / long
  context / subagent / skill / MCP over 24h–7d) to *see* where tokens actually go before guessing.
- **`/clear` between unrelated tasks** so stale context isn't dragged forward and re-billed.
- **Subagents for fan-out, not for everything:** spawning agents multiplies context; use them when
  work is genuinely parallel/independent (e.g. one per repo for a cross-repo sweep), and give the
  cheap ones a cheap model.
- **check-docs.py and other deterministic checks** should run as plain scripts/CI, never as a "ask
  the model to verify links" task — that's paying LLM rates for a regex.

---

## Sources (2026, verify freshness on each re-run)

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude Code changelog](https://code.claude.com/docs/en/changelog)
- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026)](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Prompt Caching in Claude Code — MindStudio](https://www.mindstudio.ai/blog/prompt-caching-claude-code-save-tokens)
- [AI Model Routing in 2026: Fable 5 / Opus / Sonnet / Haiku — MindStudio](https://www.mindstudio.ai/blog/ai-model-routing-fable-5-opus-sonnet-haiku)
- [Best AI Model for Coding Agents in 2026: A Routing Guide — Augment Code](https://www.augmentcode.com/guides/ai-model-routing-guide)
- [How We Cut Claude Code Costs 70% — branch8](https://branch8.com/posts/claude-code-token-limits-cost-optimization-apac-teams)
- [Claude Code June 2026: 10 New Features — SitePoint](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
- [claude-code-llm-router — PyPI](https://pypi.org/project/claude-code-llm-router/1.3.5/)
