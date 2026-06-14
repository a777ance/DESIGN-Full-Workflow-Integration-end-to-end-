# AI Process Efficiency — how we work with the AI, and where it leaks

**Owner:** NARF (AI CTO) · **Last reviewed:** 2026-06-14

The question this answers: *between the human and the AI, where are we burning tokens
and attention we don't need to — and what's the cheaper, better-prompted, or hybrid-local
way to do the same work?* This is a living file; the AI landscape moves weekly, so the
review log at the bottom leads with the newest pass.

> TL;DR — the three biggest wins, in order of payback:
> 1. **Stop loading all 7 repos' CLAUDE.md on every session** (~11K tokens of fixed
>    overhead per session, most of it irrelevant to the task at hand).
> 2. **Right-size the model per routine** — monitoring/triage routines don't need Opus 4.8;
>    Sonnet 4.6 or Haiku 4.5 do the same job for 40–95% less.
> 3. **Push the cheap first-pass to the local LiteLLM stack** we already run, and call the
>    Claude API only for the synthesis it's actually better at.

---

## A. The single biggest leak: the context preamble

Every session in this workspace mounts all seven repos under `/home/user`, so the harness
injects **every** repo's `CLAUDE.md` as project instructions — on every turn, before any
work happens:

| Repo | CLAUDE.md (words) | ≈ tokens |
| ---- | ----------------: | -------: |
| localDNS | 2,728 | ~3,600 |
| DESIGN (this repo) | 2,608 | ~3,500 |
| MARKETING | 1,445 | ~1,900 |
| customers | 562 | ~750 |
| claude-code-homelab | 371 | ~490 |
| Azure-lab | 316 | ~420 |
| **Total** | **~8,030** | **~10,700** |

That ~10.7K tokens is paid **on every session**, whether the task is "check the news" or
"edit a Statement template." A MARKETING pricing task is carrying Unbound DoT internals and
WireGuard peer tables it will never read. The cost is two-fold: **dollars** (~$0.05/session
of pure preamble on Opus input rates, before a single useful token) and, more importantly,
**relevance dilution** — the model spends attention reconciling instructions for repos it
isn't touching, which is exactly the "messy context" the 2026 guidance blames for runaway
bills.

**Fixes (cheapest first):**

1. **Scope sessions to one repo.** When a routine or task only touches `MARKETING`, start it
   with just that repo mounted. One CLAUDE.md instead of six cuts the preamble ~75%.
2. **Split the house-style block out of every CLAUDE.md into one shared, cached file.** The
   identical ~250-word "House style: ordering & typography" section is duplicated verbatim in
   6 files. Put it once in a `STYLE.md` each CLAUDE.md links to; the model reads it on demand
   instead of six times up front.
3. **Trim CLAUDE.md to the stable, load-bearing 30%.** Current guidance: keep persistent
   context (CLAUDE.md) *short and stable* so it caches well and doesn't drift the session.
   Ours are excellent *documentation* but oversized as *always-on preamble*. Move the
   stage-by-stage prose into README (already the plan) and keep CLAUDE.md to the briefing.
4. **Keep CLAUDE.md stable to win prompt caching.** Cache reads bill at ~10% of input.
   Editing a CLAUDE.md invalidates that prefix for the next session — so batch CLAUDE.md
   edits, don't trickle them.

## B. Right-size the model to the routine

This very session runs on **Opus 4.8 (1M context)** — our most capable, most expensive tier —
to do open-ended research. That's a mismatch. (Good news from the news: as of 2026-03-13
Anthropic **removed the 2× long-context premium**, so the 1M window now bills at standard
rates — the old "stay under 200K" worry is gone. The model-tier choice is where the money is
now, not the context size.)

Rule of thumb for our routines:

| Routine shape | Use | Why |
| ------------- | --- | --- |
| Monitoring / triage / "did anything change?" | **Haiku 4.5** | Cheapest; most of these end in "nothing to report." |
| Doc edits, link-checks, summarizing logs, drafting | **Sonnet 4.6** | The speed/cost sweet spot; ~40% of Opus cost. |
| Cross-repo synthesis, architecture, hard reasoning | **Opus 4.8** | Reserve the expensive brain for work only it does well. |

A "check the news and tell me if it matters" routine is a Haiku/Sonnet job that escalates to
Opus only when it finds something worth deep analysis.

## C. Leverage the hybrid stack we already built

`localDNS/10-ai-orchestration` already runs a LiteLLM gateway with local Ollama tiers
(`local-fast` qwen2.5:3b, `local-smart` 7b, `local-reason`) that fail over to the Claude API.
Current best practice for hybrid local+cloud is exactly this shape and reports **60–90% cost
reduction** by serving the 60–70% of requests that are simple (classification, extraction,
formatting, summarizing) locally and routing only the ~10% that need frontier reasoning to
the cloud. We have the pipes; we under-use them.

**Concrete moves:**

- **Pre-digest before Claude touches it.** Long logs, `git diff`s, Uptime-Kuma exports, doc
  link-check output — summarize locally first, hand Claude the digest, not the raw dump.
- **Local first responder for repo hygiene.** `python3 tools/check-docs.py` already gates
  broken links deterministically (no LLM needed). Let the local model own first-pass
  doc-lint / "does this read in house style" checks; escalate only the ambiguous ones.
- **Keep the privacy gate.** The supervisor's deterministic rule — `sensitive` tasks pin
  local, never reach a cloud tier — is the right invariant; customer/roster data should
  ride the local tier by default.

## D. Prompt hygiene (the human → AI side)

Patterns that quietly cost tokens, and the swap:

- **Give every routine a scope, a format, and a stop condition.** Open-ended prompts
  ("ANYTHING that could help… check the news… thanks!") invite unbounded fan-out. Bound it:
  *"Top 3 changes since last run that affect our token cost; ≤200 words; if none, say so and
  stop."*
- **Say "notify only if it matters."** For unattended routines, the kind thing (and the cheap
  thing) is silence on a no-op. Build that into the prompt so the run ends early when nothing
  changed.
- **Name the model in the routine.** Don't let a triage routine default to Opus.
- **Prefer subagents for fan-out reads, not for one-liners.** A subagent's verbose file
  reading stays in its own context and only the summary returns — worth it when the task
  spans 4+ large files; wasteful overhead for a quick git/shell action.
- **Don't re-read what you just wrote.** Re-reading files to "verify" an edit that already
  succeeded is pure spend.

## E. House-style note (a small, real friction)

Our house style mandates reverse-chronological, Z→A, and reversed walkthrough blocks. It's
great for human scanning, but it runs against the grain of how models are trained (forward
order), so it costs a little extra parsing care and is a frequent source of "the AI put it in
the wrong order" rework. Keep it — but know that machine-read files (the things only the AI
consumes, like a stats sidecar) gain nothing from it and can stay in natural order.

---

## Meta: was the prompt that commissioned this efficient?

No — and it's a useful example. The commissioning prompt was, in essence: *"Find
inefficiencies anywhere. Reduce tokens. Better prompting. Leverage other AI. Run hybrid.
ANYTHING. Search the web. Keep up to date. Check the news. Thanks!"*

What it did well: it set a clear **goal** and explicitly licensed web research.

Where it leaked: **no scope, no output format, no budget, no stop condition.** "ANYTHING that
could help" tells the model to fan out without limit; on an unattended routine that's the
most expensive possible instruction. A tighter version, same intent:

> *"Audit our AI usage for token waste. Deliver the top 5 fixes ranked by payback, each with
> the rough saving and the concrete change to make. ≤1 page. Use the web only to confirm
> current best practice; cite dates. If you've covered this in a prior run, only report
> what's changed since."*

That version is ~3× shorter, caps the output, makes the research bounded and dated, and turns
a repeating routine into a cheap diff instead of a full re-audit each time.

---

## Review log (newest first)

### 2026-06-14 — first pass (NARF)
- Established the three headline wins (preamble, model-sizing, hybrid offload).
- Measured the CLAUDE.md preamble at ~10.7K tokens loaded every session.
- Confirmed from current sources: 1M-context 2× premium **removed** (2026-03-13), so
  model-tier choice — not context size — is now the cost lever; hybrid local+cloud routing
  reports 60–90% savings; prompt caching cuts repeat input cost ~90% on cache hits but needs
  3+ reads inside the 5-min TTL, which spaced-out routines rarely get (a reason to batch
  related runs).
- Sources: Anthropic prompt-caching & pricing docs (platform.claude.com); The New Stack on
  the 1M-token pricing change; KDnuggets / Analytics Vidhya on Claude Code token reduction;
  SitePoint / buildmvpfast on hybrid local+cloud architecture (all accessed 2026-06-14).
