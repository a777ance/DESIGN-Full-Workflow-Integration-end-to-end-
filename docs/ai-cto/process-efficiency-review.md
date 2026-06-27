# Process efficiency review — the user↔AI loop

*Review date: 2026-06-27. Scope: how we work with Claude Code across the A777ance
repos — token cost, prompting, and where to lean on the local-LLM stack we already
own (Odin). Findings are current as of June 2026; this space moves weekly, so treat
the "News" section as perishable.*

This is a process doc, not a product change. Nothing here touches a Statement, the
box, or a customer record — it's about making the **machine that builds the machine**
cheaper to run.

---

## TL;DR — ranked by impact ÷ effort

| # | Lever | Effort | Why it pays |
| - | ----- | ------ | ----------- |
| 1 | **Stop loading all 7 CLAUDE.md files every session** | Low | ~58 KB (~15K tokens) loads before you type a word. Scope sessions to one repo. |
| 2 | **Trim + de-duplicate the CLAUDE.md files** | Low | All 6 repeat the same ~20-line house-style block. Anthropic's own guidance: keep CLAUDE.md lean. |
| 3 | **Default to Sonnet; reserve Opus for hard reasoning** | Trivial | This very session is Opus 4.8. Most edits/docs don't need it. Biggest single $ lever. |
| 4 | **Use subagents for verbose exploration** | Low | Reading/searching stays in the subagent's context; only the summary returns. |
| 5 | **Turn repeated workflows into slash-commands / skills** | Medium | "Build a statement", "add a customer", "session-end portfolio update" get re-derived each time. |
| 6 | **Point Claude Code's dev loop at Sonnet/Haiku tiers; point the *bulk NL* work at Odin (local)** | Medium | We already own the hybrid stack — we just aren't using it for the dev loop or for first-pass drafting. |
| 7 | **SessionStart hooks that print a 5-line digest (not dump files)** | Low | We have the pattern in Chronikomicon. Extend it carefully. |
| 8 | **Session hygiene: `/compact` per phase, `/clear` on topic switch** | Trivial | Long threads re-process the whole history every turn. |

---

## 1. The biggest single drain: context, not conversation

When Claude Code is launched from a directory that *contains all the repos*
(`/home/user`), the harness loads **every repo's `CLAUDE.md` into context at session
start.** Measured today:

```
Azure-lab            50 lines
claude-code-homelab  75
customers            80
MARKETING           214
DESIGN-…            295
localDNS            326
Chronikomicon       236 (when mounted)
-----------------------------
~58 KB total ≈ ~15,000 tokens, paid on every session before the first instruction
```

Two fixes, both cheap:

- **Scope the session to one repo.** Open Claude Code *inside* `localDNS/` (or
  whichever repo the work is in), not the parent folder. Then only that repo's
  `CLAUDE.md` loads — you go from ~15K tokens of preamble to ~3–8K. The cross-repo
  pointers already in each file (the "AI CTO state" sections) let Claude pull the hub
  on demand instead of carrying all of it always.
- **De-duplicate the house-style block.** The identical ~20-line "House style:
  ordering & typography" section is copied into **all six** `CLAUDE.md` files (~120
  duplicated lines). Put it in one file — e.g. `docs/house-style.md` in the DESIGN hub
  — and replace each copy with a one-line pointer: *"House style: see DESIGN/docs/
  house-style.md (ordering newest-first, lists Z→A, Gill Sans MT)."* The one-liner is
  enough to act on; the full rules are a click away when needed.

**Then trim.** Anthropic's guidance is to keep `CLAUDE.md` short — it's the most
expensive file in the repo because it's read first, every time. `localDNS` (326) and
`DESIGN` (295) carry a lot that belongs in `README.md`/`network-context.md` and can be
*referenced* rather than *inlined*. Rule of thumb: `CLAUDE.md` is the index and the
non-obvious rules; the manuals are the READMEs. Target ~120–150 lines each.

> Caching caveat in our favour: because these files are stable, prompt caching means
> the *second+* session in a 5-min/1-hr window pays ~10% for them. The trim still
> matters for the first read of each session and for the cache-write cost — and most
> of our sessions are cold.

---

## 2. Model & subagent routing (the $ levers)

- **Sonnet by default, Opus on demand.** Day-to-day editing, doc work, link-fixing,
  CRM/schema edits — Sonnet 4.6 handles fine at a fraction of Opus cost. Switch to
  Opus 4.8 only for genuinely hard reasoning (architecture, gnarly debugging, the
  pricing/compliance thinking). `/model` toggles it; this session running on Opus for
  a process review is exactly the kind of mismatch to avoid.
- **`fallbackModel` chains** (shipped 2026): set an ordered model list so a
  rate-limit/outage falls through to the next model instead of stalling you.
- **Subagents for verbose work.** When a task means reading lots of files or sweeping
  the tree, delegate it — the file dumps stay in the subagent's window and only the
  conclusion returns to your main context. (This review used one for exactly that.)
  Mechanical subagent tasks can run on **Haiku** to cut cost further; per-agent cost
  attribution now exists so you can see which agents burn tokens.
- **Cap tool output.** Large command/log outputs flood context — keep a tight output
  budget and pipe through `head`/filters rather than dumping whole files.

---

## 3. The hybrid play — we already own the stack, we're just not pointing it here

We run **Odin** (LiteLLM router on the t630, `ai.home.lan:4040`) with local Ollama
models (`qwen2.5:3b/7b`, `deepseek-r1:1.5b`, `nomic-embed-text`), a rented-GPU R1 tier
over Tailscale, and Claude Opus as fail-closed cloud overflow. Today that serves the
**product** (Open WebUI, the langgraph dispatcher). It does **not** serve our dev loop
or our content drafting. Two realistic moves:

**a) Offload bulk natural-language work to local models — keep Claude Code for code.**
Don't try to run the *agentic coding loop* on a 3B/7B CPU model on the t630 — it's too
weak and too slow for tool-use coding, and you'd spend more human time babysitting it
than you'd save. But a lot of what we ask Claude for *isn't* coding:

- First-pass marketing copy / blog drafts (stage 02) → `qwen2.5:7b` locally, Claude
  only polishes. (Privacy-safe and free.)
- Summarizing logs, "Handled For You" entries, call notes → local.
- Classifying/triaging leads, tagging the master list → `local-fast`.
- **RAG over the repos:** `nomic-embed-text` is already in the stack — index the repos
  locally so questions like "where did we decide X" get answered from an embedding
  search instead of Claude re-reading files. This is the highest-value local use and
  it's already half-built.

**b) Route Claude Code itself *through* LiteLLM for instrumentation.** Point
`ANTHROPIC_BASE_URL` at the Odin gateway. You still hit real Claude for the dev loop,
but now every request flows through one place with **per-model token + cost logging** —
which the AI-CTO context notes we currently lack. That turns "I think we're spending a
lot" into a number per repo, per session, per model. Pair it with the new per-agent
cost attribution.

> Cost note for the reasoning ladder: when you *do* need heavy reasoning, compare the
> rented-GPU R1 pod (spin-up + GPU-hour) against just paying Claude/Sonnet tokens for
> the same task. For short bursts, Claude tokens are often cheaper than a pod you spin
> up and forget to spin down. Track it; don't assume local = cheaper.

---

## 4. Stop re-deriving the same workflows

Several procedures live as prose in CLAUDE.md/README and get re-explained to Claude
each time. Codify them so the steps aren't re-reasoned (and re-tokenized) every run:

- **Slash commands / skills** for: "build a statement for HH-X" (the `make statement`
  flow), "add a customer", "run `check-docs.py` and fix broken links", "session-end:
  update portfolio.md + tech-debt.md". A skill carries the steps so the prompt is one
  line, not a paragraph.
- **SessionStart hook (carefully).** Chronikomicon's hook is a good model. For the
  DESIGN hub, a hook that prints a **5-line digest** — top 3 open blockers, current
  phase gate, last portfolio update date — saves Claude from opening 4 files to orient.
  *Do not* have the hook cat whole files into context; that re-introduces the very bloat
  in §1. Digest, not dump.
- **`fewer-permission-prompts` / allowlist.** Add the routine read-only Bash + GitHub
  MCP calls to `.claude/settings.json` so sessions stop stalling on approvals (saves
  wall-clock and round-trips, not tokens, but it's free).

---

## 5. Session hygiene (free, habitual)

- `/compact` after each discrete phase (finished a stage → compact before the next).
- `/clear` when switching repos/topics — don't drag localDNS context into a MARKETING task.
- **Batch your asks.** A string of "now fix this… also change that…" re-processes the
  whole thread each turn. One message with the full change set is markedly cheaper.
- **Scope the ask.** "Refactor the booking-form handler in 03-…" beats "refactor the
  funnel" — smaller scope = less context pulled = fewer tokens.

---

## 6. News / what changed recently (June 2026 — perishable)

- **Headless billing split (eff. 2026-06-15):** Agent SDK and `claude -p` usage now
  bills against a separate API-credit pool ($20 Pro / $100 Max5x / $200 Max20x). If we
  script any automation, watch which pool it draws.
- **Nested subagents** (up to 3 levels) and **fallback model chains** shipped — useful
  for the langgraph/Odin orchestration and for resilience.
- **Per-agent cost attribution** is now available — the instrumentation gap in §3b is
  partly closed out of the box.
- **Agent Skills + plugins** are now packageable/shareable — relevant to our PLUGINS.md
  discipline; our per-repo plugin scoping is already the right instinct.
- **Checkpoint/resume** keeps the pending task queue, so resumed sessions don't
  re-evaluate finished work — good for our ephemeral remote containers.

---

## 7. The prompt that triggered this review — critique + template

The originating prompt ("Locate inefficiencies in our PROCESS… Anything you could
possibly think of… ANYTHING that could help… Keep UP TO DATE… Check the news") was
**rich in intent but unscoped**, which is itself a (minor) token inefficiency — open
superlatives invite an unbounded sweep. What worked: it named the domain, explicitly
asked for web/news currency (right call for a fast-moving topic), and asked to check
its own efficiency (good instinct). What to tighten:

- **No success criterion / output contract** — "done" was undefined (a report? a number?
  changes pushed?). Claude has to guess the deliverable.
- **No scope boundary** — it conflates two different "processes": the *human↔Claude-Code
  dev loop* and the *product's own LLM routing*. They have different fixes; say which.
- **Unbounded language** ("ANYTHING", "anything you could possibly think of") maximizes
  breadth — the opposite of the token frugality being requested.

A tighter version (≈same intent, structured the way Claude 4.x parses best — labeled
blocks, explicit contract, scope, and definition of done):

```
ROLE: You're our AI-CTO reviewing how we work with Claude Code.

TASK: Find the top inefficiencies in our user↔Claude-Code workflow and propose fixes
that reduce token spend without losing quality.

SCOPE: The dev/authoring loop across our repos. Include the option of offloading work
to our local Odin LLM stack. Exclude product-side LLM routing unless it changes dev cost.

USE: Web search for current (June 2026) best practices and any Claude Code release news;
flag anything likely to change soon.

OUTPUT: A ranked table (lever / effort / impact), each with one concrete next action.
Then critique this prompt. Commit the report to docs/ai-cto/; notify me with the top 3.

DONE = the report is pushed and I have a 3-line summary I can act on without opening it.
```

That's ~40% shorter, removes the guesswork, and bounds the sweep — which is the whole
point of the exercise.

---

## Sources

- [Best practices for Claude Code — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Manage costs effectively — Claude Code Docs](https://code.claude.com/docs/en/costs)
- [LLM gateways — Claude Code Docs](https://code.claude.com/docs/en/llm-gateway)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Prompt caching — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Claude prompting best practices — Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Optimizing Claude Code for Cost, Speed, and Productivity (Medium, Jun 2026)](https://medium.com/@ramakrishna.sanikommu/optimizing-claude-code-for-cost-speed-and-productivity-5122fb9ce1de)
- [How to Run Local AI Models with Claude Code to Cut Costs (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Hybrid Cloud-Local LLM: Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Claude Code June 2026: 10 New Features (SitePoint)](https://www.sitepoint.com/claude-code-june-2026-10-new-features-devs-need-to-know/)
- [How to Reduce Claude Code Token Usage: 8 Methods (Agensi)](https://www.agensi.io/learn/how-to-reduce-claude-code-token-usage)
