# Process efficiency — token & workflow audit (NARF, 2026-06-27)

How we (founder ↔ Claude) actually spend tokens across the seven repos, where that
spend is wasted, and what to change. Grounded in the live repos and in current
(June 2026) Anthropic pricing/feature facts — sources at the bottom. Ranked by
**impact ÷ effort**, biggest lever first.

This is a self-audit; the ecosystem half (the "What changed in 2026" section) ages
fast — re-check it monthly, not daily.

---

## TL;DR — the levers, ranked

| # | Lever | Where the waste is now | Est. saving | Effort |
| - | ----- | ---------------------- | ----------- | ------ |
| 1 | **Trim the per-turn context tax** | `CLAUDE.md` files are 18–20 KB; injected on *every* turn | 15–30% of every session | Low — edit 3 files |
| 2 | **Kill the "read N files at session start" ritual** | NARF reads 4, ZORT reads 6, every spoke reads 2 — most unchanged day-to-day | A few K tokens × every session × 2 personas × daily | Low — reword CLAUDE.md |
| 3 | **Default to Sonnet, reserve Opus** | Opus 4.8 is 1.7× Sonnet in / 1.7× out; only ~10% of tasks need it | 30–50% on model cost | Low — `/model` habit |
| 4 | **Lazy-load MCP tools; prefer `gh` CLI** | GitHub MCP = ~60 tool defs, up to ~18 K tokens/turn of pure overhead | up to ~18 K tokens/turn | Low–med |
| 5 | **Session hygiene: one task, then `/compact`** | Long sessions re-read all prior turns — cost grows geometrically | 40–70% on focused tasks | Free — habit |
| 6 | **Route bulk NL chores to the local LLM we already run** | LiteLLM router (port 4040) + local R1 exist but only feed Open WebUI chat | 60–80% on the offloaded slice | Med — wire it up (fix TD-14 first) |
| 7 | **Deterministic checks → scripts/CI, never tokens** | `check-docs.py` already in CI (good); generalize the pattern | small but recurring | Low |

Items 1–3 and 5 are habit/edit changes available **today** at near-zero effort and
together plausibly halve routine spend. Item 6 is the bigger build and the one the
homelab is uniquely set up to do.

---

## 1. The per-turn context tax (biggest, cheapest win)

`CLAUDE.md` is injected into **every request**, so its size is a tax on every turn of
every session. Anthropic/community guidance: keep it lean (~200 lines / a few K tokens);
document decisions and conventions, not narrative.

Measured today:

| Repo | `CLAUDE.md` | ≈ tokens/turn |
| ---- | ----------- | ------------- |
| localDNS | 326 lines / 20.5 KB | ~5,000 |
| DESIGN-… | 295 lines / 18.0 KB | ~4,500 |
| MARKETING | 214 lines / 10.7 KB | ~2,700 |
| customers / homelab / azure | 2–4 KB each | small |

A cross-repo session that touches the big three pays **~12 K tokens before any work
starts** — on every turn. Prompt caching softens this (Claude Code auto-caches the
prefix; a cache hit is ~10% of input price) but a cache hit still costs, and any edit to
the file busts the cache and forces a full re-write at 1.25×.

**Fix:** move the *reference* material (deploy-path tables, the full service/port table,
peer lists, the funnel ASCII art) out of `CLAUDE.md` and into README/`network-context.md`,
leaving `CLAUDE.md` as a thin index of pointers + the load-bearing invariants. The
RECOMMENDED-CHANGES audit already flagged the localDNS `CLAUDE.md ↔ README` table
duplication and the 6× house-style block — collapsing those is the same work. Target:
each big `CLAUDE.md` under ~150 lines.

## 2. The "read these files at session start" ritual

The DESIGN `CLAUDE.md` tells NARF to read 4 files at session start and ZORT to read 6;
every spoke repo says "read `context.md` + the portfolio hub." That's 10+ file reads
before a single line of work, **every session, for both personas, daily** (the git log
shows a NARF + ZORT commit every day). Most of those files are unchanged from yesterday.

**Fix:** make the reads *lazy and conditional* — "read the hub `portfolio.md`; read a
spoke's context file *only when working in that spoke*." Better: keep one small
`state.md` per persona (the 10-line "what changed since last session") that's cheap to
read every time, and reach for the big logs only when the task needs them. Don't make the
model re-ingest the whole decision log to write a one-line status update.

## 3. Model selection — default Sonnet, reserve Opus

Current API prices (per Mtok): **Opus 4.8 $5 / $25**, **Sonnet 4.6 $3 / $15**, **Haiku
4.5 $1 / $5**. Opus is ~1.7× Sonnet on both sides. Guidance that holds up in 2026: Sonnet
handles ~80% of coding/agentic work; switch to Opus only for deep analysis or gnarly
refactors. Daily status-update commits (NARF/ZORT) and doc edits do **not** need Opus.

**Fix:** default sessions to Sonnet; `/model opus` only when a task is genuinely hard.
For the lightest mechanical passes, Haiku. Check live spend mid-session with `/cost`
(per-model breakdown + cache-hit rate).

## 4. MCP overhead — lazy-load tools, prefer CLI

Every connected MCP server injects its tool definitions into every turn. A large server
like GitHub's (~60 tools here) can be ~18 K tokens/turn of pure overhead. Note this very
environment already uses **deferred tool loading** (tools surfaced via search, schemas
fetched on demand) — that's the fix in action.

**Fix:** (a) enable deferred/lazy MCP tool loading in the local Claude Code config so
schemas load only when needed; (b) for routine git/PR work, prefer the `gh` CLI over the
MCP server (CLI calls cost only the command, not 60 always-on schemas); (c) disable MCP
servers you're not actively using in a given session.

## 5. Session hygiene

A 200-turn session re-sends the whole transcript every turn — message 50 silently re-reads
the 49 before it, so cost grows geometrically. Behavioral fixes give the most durable
reductions: **one task per session**, `/compact` (or a fresh session) between tasks, and
scope each request to named files ("add the privacy fallback to `config.yaml`'s
`local-reason` block", not "fix the router"). Vague asks trigger broad scanning; specific
asks let Claude work with minimal reads.

## 6. Use the local LLM we're already paying to run

The homelab already runs the thing most "cut your AI bill" posts tell you to build: a
**LiteLLM gateway on :4040** with a local tier (`local-reason`, deepseek-r1:1.5b on the
t630), an on-demand rented-GPU tier (`cloud-gpu-reason`), and Claude as `cloud-overflow`.
Today it only backs Open WebUI chat. The industry pattern (RouteLLM et al.) routes the
~60–70% of requests that are classification/extraction/formatting/first-draft to local
models and reserves the frontier model for the ~10% that need real reasoning — reported
60–85% cost cuts at ~95% of frontier quality.

**Candidates to offload to local, keeping Claude Code for agentic coding:**
- NotebookLM "Rainbow Bridge" summarization in MARKETING (bulk, low-stakes).
- First-draft marketing copy / lead classification (stages 02, 05) — Claude edits, doesn't draft from zero.
- "Read this long doc and give me the 5-line gist" pre-work before a Claude session.

**Blocker, do this first:** **TD-14** — `local-reason` currently has a cloud fallback
chain, so a `sensitive`-tagged prompt can fail *over* to Claude cloud if the local model is
down, breaking the privacy guarantee. Give `local-reason` a **local-only, fail-closed**
fallback before routing any sensitive work through it.

Optional: point Claude Code's `ANTHROPIC_BASE_URL` at the LiteLLM gateway so all spend,
caching, and rate limits are tracked in one place — weigh the extra hop vs. the
single-pane-of-glass benefit.

## 7. Deterministic work doesn't need a token

`tools/check-docs.py` validates every internal link/anchor and is now wired into CI
(TD-11, resolved) — that's the model: anything deterministic (link checks, schema
validation, `roster.json` shape, lint) belongs in a script/CI, not in a prompt asking
Claude to eyeball it. Keep generalizing this; it's the cheapest token — the one never spent.

---

## On the prompt that generated this audit

The triggering request was, paraphrased: *"Find inefficiencies in our process, reduce
token use, better prompting, leverage other AI, hybrid local+Claude — anything — search
the web, check the news, keep up to date."* Honest critique:

- **Unscoped → broad scan.** "Anything that could help" forces a wide sweep and a sprawling
  answer (more tokens both directions). Naming the target — "the top 3 token-cost drivers
  in our Claude Code usage, each with a fix and a rough % saving" — gets a tighter, cheaper,
  more actionable result.
- **Bundles ~6 questions in one turn.** Token-cost, prompting, other-AI, hybrid, web
  research, and self-critique are distinct. One turn answers all shallowly; separate scoped
  turns answer each well.
- **Unbounded web research.** "Search the web, check the news, keep up to date" with no
  bound invites many searches. Bound it: "use web search only to confirm 2026 pricing/feature
  changes since the Jan knowledge cutoff."
- **Retyped, not saved.** This runs as a scheduled routine, so the prompt should be a saved,
  parameterized job — and its two halves have different clocks: the **self-audit** changes
  when our repos change (run on demand / after big edits); the **ecosystem scan** changes
  slowly (run monthly). Splitting them stops us re-researching a stable field daily.

A leaner version of this prompt:

> *Audit our Claude Code usage across the repos for the top token-cost drivers. For each:
> the waste, a concrete fix, and a rough % saving. Cover context size, model choice, session
> hygiene, MCP overhead, and offload-to-local opportunities. Use web search only to confirm
> 2026 Anthropic pricing/feature facts. Output a ranked table + short sections to
> `docs/ai-cto/process-efficiency.md`.*

---

## What changed in 2026 (re-check monthly; newest first)

- **2026-06-15** — Anthropic *paused* the announced Agent SDK credit-split billing change;
  the prior structure stands for now.
- **2026-06-09** — Claude **Fable 5** released ($10/$50), but customer access was suspended
  2026-06-12 — not a dependable option today.
- **2026-05-28** — **Opus 4.8** launched at $5/$25 (the model this routine runs on).
- **2026-02-05** — Prompt caching moved to **workspace-level isolation**; cache hit ≈ 10%
  of input price, 5-min TTL (1.25× write) or 1-hr TTL (2× write). Caching pays off after a
  single 5-min re-read.
- **Ongoing** — Sonnet/Haiku 4.x carry **context awareness** (the model tracks its own
  remaining window), which makes `/compact`-style hygiene more effective.

---

## Sources

- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [How Claude Code uses prompt caching — Claude Code Docs](https://code.claude.com/docs/en/prompt-caching)
- [LLM gateways — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [Pricing — Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [How to Reduce Claude Code Token Usage: 8 Proven Methods (2026) — Agensi](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
- [Claude Code Token Optimization: Stop the $1,600 Bill (2026) — Build to Launch](https://buildtolaunch.substack.com/p/claude-code-token-optimization)
- [Hybrid Cloud-Local LLM: The Complete Architecture Guide (2026) — SitePoint](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [RouteLLM — lm-sys/RouteLLM (GitHub)](https://github.com/lm-sys/routellm)
- [Claude Code Agents in 2026 — CloudZero](https://www.cloudzero.com/blog/claude-code-agents/)
- [Anthropic Claude API Pricing 2026 — aipricing.guru](https://www.aipricing.guru/anthropic-pricing/)
- [Anthropic June 15 2026 billing change paused — Digital Applied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
