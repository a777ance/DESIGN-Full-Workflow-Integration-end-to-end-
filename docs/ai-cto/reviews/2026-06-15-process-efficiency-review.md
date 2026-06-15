# Process efficiency review — user↔AI workflow & token spend (2026-06-15)

**Scope:** How we work *with* the AI (Claude Code + the local/cloud stack), where tokens
leak, and what to change. Prompted by the founder: "find inefficiencies in our process,
reduce token use, better prompting, leverage other AI / hybrid local+Claude, keep current."

Web best-practice sources are dated June 2026 and cited inline. NARF's bottom line: the
plumbing (Odin/LiteLLM reasoning ladder) is already well-designed — the waste is in
**what we load into every Claude session** and in **routing routine work to a frontier
model**. Both are fixable this week.

---

## TL;DR — ranked by payback

1. **Stop force-reading the CTO/CFO state files on every session.** Make them
   *conditional* ("when doing CTO/CFO work, read…"), not mandatory. Biggest single win.
2. **Right-size the model.** Routine edits/docs on Sonnet, not Opus-4.8-1M. Reserve Opus
   for hard architecture. The 1M context window is a per-token premium we pay even when
   unused.
3. **Deploy the reasoning ladder we already built (Odin/LiteLLM).** Route drafting,
   classification, RAG, commit messages, link-checking to local `qwen2.5`; keep Claude
   for the hard 20%. Industry hybrid setups report **60–80% cost cuts** doing exactly this.
4. **Trim & stabilize CLAUDE.md.** Every line is paid before you type a word. Keep them
   short and *don't edit them mid-session* (edits bust the prompt cache).
5. **Use subagents for verbose/parallel work** so file dumps stay out of the main thread.
6. **Batch the non-interactive jobs** (monthly statements, overnight NARF/ZORT briefs):
   50% off via the Batch API, and they're not latency-sensitive.
7. **Adopt the new platform features** (Sonnet 4.5 context-editing + memory tool, Claude
   Code checkpoints) for long-running agent sessions.

---

## A. The recurring tax: what loads before you say anything

A `CLAUDE.md` "loads before Claude reads your code or your task — a 5,000-token CLAUDE.md
costs 5,000 tokens before you've typed a word" (buildtolaunch, 2026). Our per-repo files:

| Repo | CLAUDE.md lines | ~words |
| ---- | --------------- | ------ |
| localDNS | 326 | ~1,980 |
| DESIGN (this repo) | 295 | ~1,790 |
| Chronikomicon | 236 | ~1,430 |
| MARKETING | 214 | ~1,310 |
| customers | 80 | ~480 |
| claude-code-homelab | 75 | ~460 |
| Azure-lab | 50 | ~300 |

That alone is tolerable. The real leak is the **mandatory session-start reading list**:

- DESIGN CLAUDE.md §5 + §6 tell every session to read **4 CTO files + 6 CFO files**
  (~5,000 words) — `portfolio.md`, `roadmap.md`, `tech-debt.md`, `decisions.md`,
  `ai-cfo/{portfolio,decisions,metrics,runway,budget}.md`, plus a MARKETING spoke.
- Most sessions are *not* CFO sessions. Loading `runway.md` + `budget.md` to fix a DNS
  config or a typo is pure waste, repeated every session.

**Fix (highest payback, lowest effort):** change the wording from "At session start, read…"
to **"When the task is CTO/CFO work, read…"** and let Claude pull the spoke files on
demand. Keep only the *hub* pointer in CLAUDE.md. This is a prompt change, not a code
change, and it cuts the base load of a typical session by ~40%.

**The "House style" block** is duplicated verbatim across all 7 CLAUDE.md files
(~170 words × 7 ≈ 1,200 words). It's an intentional cross-repo standard, so keep it — but
two cheap improvements: (a) compress it to four terse bullets (the rationale prose isn't
needed every load), and (b) since it never changes, it's ideal cache-stable content — keep
it at the *top* of each file and never edit it mid-session.

---

## B. Prompt caching — what's actually true

Claude Code already caches the system prompt, tool definitions, and `CLAUDE.md`
automatically. Anthropic advertises 70–90% savings on cached input, but **developers
report 5–15% in practice** unless prompts are *structured* for it (buildtolaunch; knightli,
2026). The mechanics that matter for us:

- **Stable content first, volatile content last.** CLAUDE.md and tool defs are stable —
  good. Don't interleave changing data into them.
- **Editing CLAUDE.md mid-session busts the cache** for everything after the edit. Batch
  CLAUDE.md edits into their own short sessions.
- **`/compact` shrinks the running prefix** — use it when a session gets long instead of
  carrying the whole transcript.
- Caching stacks with the Batch API (see §E) for ~90% + 50% on eligible jobs.

---

## C. Model right-sizing

We default to `claude-opus-4-8[1m]`. Opus 4.8 is ~$5/Mtok in, $25/Mtok out; the **1M
context tier carries a premium** even when the window sits empty. Most of our work —
edits, doc updates, link fixes, statement composition — is Sonnet-grade.

**Fix:** default Claude Code to **Sonnet 4.6** for routine work; switch to Opus only for
genuinely hard architecture/research turns (`/model`). The `config.yaml` ladder already
encodes this intent (`cloud-code: sonnet`, escalate to opus for the hardest) — mirror it
in the interactive default, don't just leave it in the router config.

---

## D. The hybrid local+cloud play we've designed but not shipped

We already built the right architecture — `localDNS/10-ai-orchestration/`: LiteLLM gateway
+ Ollama locals + Claude cloud tiers, with the **Odin/Heimdall** deterministic privacy
gate and a graceful reasoning ladder. The 2026 best-practice stack is *exactly* this:
"LiteLLM as the unified gateway, Ollama for local serving, Anthropic's Claude API as the
cloud tier" (sitepoint, 2026). The gap is that it's **designed + self-tested, not deployed
on the t630.**

What to push through local (`qwen2.5:3b/7b`, `deepseek-r1:1.5b`) — high-volume, low-stakes,
privacy-relevant:

- Commit-message drafting, changelog tidying, doc-link triage.
- First-pass classification/extraction (lead triage, "Handled For You" log phrasing).
- RAG/embedding over the repos (`nomic-embed-text` + Huginn) so Claude gets *retrieved
  snippets*, not whole-file dumps.
- The routine, templated parts of the **overnight NARF/ZORT briefs**.

Keep on Claude: cross-repo architecture, the hard reasoning, anything customer-facing that
must be exactly right, vision. Reported hybrid savings: **60–80%** for setups that run
simple tasks locally and reserve Claude for complex work (buildmvpfast; sitepoint, 2026) —
and the privacy gate means sensitive lookups (bank/tax/medical) never leave the box, which
is a correctness/compliance win on top of the cost win.

**Action:** schedule the deploy from `localDNS` §F-style checklist; it's the single
highest-leverage *infrastructure* item and it's already paid for.

---

## E. Batch the non-interactive jobs (50% off)

The Batch API is half price and we have perfect candidates — none are latency-sensitive:

- Monthly statement composition/rendering across the roster.
- The daily/overnight NARF & ZORT briefs.
- Bulk doc passes (e.g. house-style sweeps across repos).

Stacks with caching. Don't pay interactive rates for work that runs while you sleep.

---

## F. Newer features worth adopting (June 2026)

- **Context editing + memory tool** (shipped with Sonnet 4.5): lets long agent sessions
  prune stale context and persist state across runs — directly relevant to our
  long-running NARF/ZORT sessions that currently reload everything each time
  (anthropic; s3p-studios, 2026).
- **Claude Code checkpoints**: save/rollback progress — safer long edits, less re-work
  (and less re-prompting after a bad turn).
- **Subagents**: each has its own context window; verbose output (searches, log dumps)
  stays isolated and only a summary returns to the main thread (smartscope; alexop, 2026).
  Use for the wide "map the repos" / research fan-outs — keeps the main session lean.
- **Skills over re-explaining**: turn our repeated procedures (build-a-statement,
  add-a-customer, the doc-link check) into Skills so we stop spending tokens re-describing
  them each time. "Use a skill when there is real domain logic or helper files" (alexop).

---

## G. About the prompt that triggered this review

The founder asked: *if this prompt is inefficient, say so.* It is — usefully so, but
inefficient. "Anything you could possibly think of… ANYTHING that could help" maximizes
breadth, which forces wide, unfocused exploration and a long answer (more output tokens,
more tool calls). A tighter version gets the same value for less:

> *"Audit our user↔AI process for token waste. Focus on: (1) per-session context load
> (CLAUDE.md + the CTO/CFO read-list), (2) model right-sizing, (3) deploying the local
> reasoning ladder. For each, give the change, the rough % saving, and the effort. Cite
> any 2026 best-practice sources. One page max."*

General prompting hygiene that compounds: state the *goal + constraints + output format +
length cap*; point at specific files instead of "the codebase"; prefer one scoped ask over
an open-ended sweep; add a terse-output instruction for heavy workflows (cf. the
`claude-token-efficient` CLAUDE.md pattern). Keep a `/efficiency-audit` slash command so
this recurring review is one keystroke, not a fresh essay each time.

---

## Sources

- https://buildtolaunch.substack.com/p/claude-code-token-optimization
- https://code.claude.com/docs/en/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://knightli.com/en/2026/05/18/claude-code-prompt-cache-token-optimization/
- https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/
- https://www.buildmvpfast.com/blog/hybrid-cloud-local-ai-workflow-cost-optimization-2026
- https://www.kunalganglani.com/blog/local-llm-vs-claude-coding-benchmark
- https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/
- https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/
- https://www.marktechpost.com/2026/06/14/claude-code-guide-2026-25-features-with-examples-demo/
- https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features
- https://s3p-studios.com/blog/anthropic-memory-tool-context-engineering-agents/
- https://www.finout.io/blog/anthropic-api-pricing
- https://github.com/drona23/claude-token-efficient
