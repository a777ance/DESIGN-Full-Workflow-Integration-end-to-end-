# Process & Token-Efficiency Review — 2026-06-14

Requested by the founder: *"Locate inefficiencies in our PROCESS — between the user and
the AI. Reduce token use. Better prompting. Leverage other AI / hybrid local+Claude.
Keep up to date."* This is a one-off audit of **how we run the AI**, not of the product.
Newest-first per house style; the ranked fixes lead.

The numbers below are measured against this very session, which had 6–7 repos in scope.

---

## TL;DR — the five highest-leverage fixes, ranked by tokens saved

1. **Gate the daily NARF/ZORT reviews on "did anything change?"** — biggest single waste.
2. **Stop loading all 7 CLAUDE.md files into one session** (~14.6K tokens/turn baseline).
3. **De-duplicate the house-style block** (~1.5K tokens copied 7×).
4. **Right-size the model + actually use the local LLM router we already built.**
5. **Tighten the prompts** (scope + output contract + token budget + "stay silent if nil").

---

## 1. Our own process — measured inefficiencies

### 1.1 The daily review re-derives the same answer (the big one)

`docs/ai-cto/reviews/` holds a NARF portfolio review for **every day** 2026-06-04 → 06-14
(11 files), plus a parallel ZORT cadence. Reading them in sequence, the conclusion barely
moves: 06-10, 06-11, 06-13 and 06-14 all land on the same headline —
*"nothing material has shipped since the 2026-06-07 LLM-router landing; everything real is
downstream of t630 access; close TD-14."* Each run re-reads the same 4–6 source files
(CHANGELOG, tech-debt, the collect runbook, config.yaml) on a full Opus context to
regenerate a paragraph we already have.

That is exactly the failure mode the routine guidance warns about: **a scheduled run that
finds nothing new should stay silent, not produce a full artifact.** Cost today ≈ a daily
Opus session (tens of thousands of input tokens re-reading unchanged files + a fresh
write) for near-zero new signal.

**Fix (cheap, today):**
- Make the review **diff-gated**. Step 1 of the routine: read only the CHANGELOG's top
  entry + `git log --since` for the spoke repos. If nothing changed since the last review,
  **exit and send no notification / write no file.** Only do the full read-and-write when
  the cheap check shows movement.
- Run the *gate* check on **Haiku 4.5** ($1/$5 per M), not Opus ($5/$25). Escalate to
  Opus only when there's something to actually reason about. ~5× cheaper on the 9-out-of-10
  days nothing shipped.
- Consider Anthropic's new **"Dreaming"** feature (shipped at Code with Claude 2026): a
  scheduled process that reviews past sessions, curates memory, and surfaces *patterns*
  across runs — purpose-built to replace "re-read everything daily" with "tell me what
  changed." This is the native answer to our daily-review cadence.

### 1.2 Seven CLAUDE.md files load into one session — ~14.6K tokens before a word is typed

Measured this session:

| Repo | ~tokens in CLAUDE.md |
| ---- | -------------------- |
| localDNS | ~5,100 |
| DESIGN (this hub) | ~4,500 |
| MARKETING | ~2,700 |
| customers | ~1,000 |
| claude-code-homelab | ~720 |
| azure-lab | ~570 |
| **Total loaded every turn** | **~14,600** (+ Chronikomicon if present) |

CLAUDE.md loads *before* Claude reads the task — it's a constant baseline carried on every
turn of every session. A multi-repo session pays the **sum of all of them** whether or not
the task touches that repo.

**Fix:**
- **Scope each session/routine to the one repo it works on.** A localDNS task should not
  carry the MARKETING + customers + azure-lab briefings. This alone roughly halves the
  baseline for most tasks.
- **Trim each CLAUDE.md to a lean "router."** The current files mix a true briefing with
  long reference tables (e.g. localDNS's full deploy-path table, the nftables runbook).
  Reference material that isn't needed *every* turn belongs in README/linked docs that
  Claude reads **on demand**, not in the always-loaded CLAUDE.md. Target a CLAUDE.md under
  ~1.5–2K tokens; link out for the rest.

### 1.3 The house-style block is duplicated 7× verbatim

The identical ~350-word "House style: ordering & typography" section is pasted into all 7
CLAUDE.md files (~1,500 tokens, copied seven times = it's in context multiple times in any
multi-repo session, and it's seven files to edit when the rule changes — exactly the kind
of edit that busts the prompt cache everywhere at once).

**Fix:** keep the canonical copy in **one** place (e.g. `DESIGN/docs/house-style.md` or a
shared skill) and have each CLAUDE.md carry a one-line pointer to it. One source of truth —
the same rule we apply to business facts (roster) and network facts (the box).

### 1.4 We re-read whole files we just read

The review transcripts show each run re-reading the full `config.yaml`, the collect README,
the CHANGELOG, etc. Every read appends the full file to context for the rest of the session.

**Fix:** read **ranges/heads** not whole files when checking state (`head`, line offsets,
`git diff` instead of full re-read); prefer `git log`/`git diff --stat` to detect change
before reading content.

---

## 2. Token-reduction levers (mapped to our setup)

Current Claude pricing (per M tokens, Jun 2026): **Opus 4.8 $5/$25 · Sonnet 4.6 $3/$15 ·
Haiku 4.5 $1/$5.** Long-context surcharge was removed in March 2026 — a 900K request costs
the same per-token as a 9K one.

- **Right-size the model.** Routine classification/extraction/formatting/state-checks →
  **Haiku**. Drafting/summaries → **Sonnet**. Only genuine cross-repo reasoning → **Opus**.
  Industry split is ~60–70% simple / 20–30% moderate / ~10% frontier — we're running Opus
  for nearly all of it.
- **Batch API = flat 50% off** for anything not interactive. The nightly reviews, statement
  composition, bulk doc checks are perfect batch candidates (results within 24h). Opus drops
  to $2.50/$12.50, Haiku to $0.50/$2.50.
- **Prompt caching cuts cached input ~90%.** Caveat that *bit us structurally*: editing
  CLAUDE.md or changing the tool set mid-session invalidates the whole cached prefix and
  forces full re-processing. So **batch CLAUDE.md edits**, keep the tool set stable within a
  session, and put volatile context (git status, file contents) in messages, never in the
  system prompt. The cache default TTL is now 5 min; for a long returning session use the
  **1h TTL** — but only when the same prefix is reused many times (one-shot subagents should
  stay 5m).
- **Fast mode** (Opus, faster output at lower price — toggled with `/fast`) is now cheaper;
  use it for the interactive work where it qualifies.
- **`/compact` and microcompact** to shed stale turns mid-session instead of carrying a
  10,000-line log forever.

### 2.1 Hybrid local + Claude — we already built the router; we're underusing it

We have **LiteLLM on the t630** (stage 10) with a reasoning ladder (`local-reason` =
deepseek-r1:1.5b on CPU; cloud tiers for heavy work) and Open WebUI. The published
playbooks for exactly this stack report **60–90% cost reduction** by serving the
simple/sensitive 60–70% of requests locally and reserving Claude for the ~10% that needs
frontier reasoning.

Concretely for us:
- Route **state-checks, link-checks (`check-docs.py` summaries), classification, "did
  anything change?" gates, and any `sensitive`-tagged household data** to the **local**
  model. This is both cheaper *and* the privacy-correct default (sensitive data never
  leaves the box — which is the promise printed on every Statement).
- Reserve the **Claude API** for the cross-repo synthesis and the customer-facing copy.
- **But fix TD-14 first.** The router's privacy boundary currently *fails open*:
  `local-reason`'s fallback chain includes `cloud-overflow` (Claude cloud), so a sensitive
  prompt can leak to the cloud if the local model is down. Before we lean on the local tier
  for sensitive routing, make that fallback **local-only / fail closed.** (Already tracked;
  this review reinforces it as a prerequisite for the hybrid cost play.)

---

## 3. Prompting improvements (how we talk to the AI)

The reviews are well-prompted for *reasoning* but unbounded for *cost*. Standard upgrades:

- **State the output contract.** "≤400 words, this structure, write to `<path>`, no full
  file re-reads." An open-ended ask invites an open-ended (expensive) answer.
- **Set a token/scope budget** in the routine itself ("check X with `git diff`; only if
  changed, do the full pass").
- **Make 'stay silent if nothing changed' explicit** in every scheduled routine — most of
  ours should no-op most days.
- **Incremental over wholesale.** "Update the top tech-debt row," not "re-audit all repos."
- **One repo per task.** Don't put the AI in a 7-repo session for a 1-repo job.
- **Pin the model per task** so routine work doesn't silently run on Opus.

---

## 4. Is *this* prompt (the request that triggered this review) inefficient? Yes — a bit.

The request was: *"Locate inefficiencies… Is there a better way… Perhaps better prompting…
Leveraging other AI… ANYTHING that could help. Search the web… Check the news… Keep UP TO
DATE… Thanks!"*

What it does well: clear intent, gives permission to use the web, asks for current info.

Where it costs more than it needs to:
- **"ANYTHING that could help"** is unbounded — it licenses unlimited search and writing.
- **No output contract** (length, format, where to put the answer).
- **No scope** (which repos / which process — billing? reviews? statement gen?).
- **"Check the news… day by day"** implies open-ended browsing; better to name the 2–3
  sources or sites worth checking.
- Ran in a **7-repo session**, so it paid the full ~14.6K CLAUDE.md baseline for a question
  that only needed this hub.

**A leaner version:**

> *Audit how we run the AI for token waste (process, prompting, model choice, local vs
> Claude). Scope: the NARF/ZORT review cadence + CLAUDE.md load. Web-check current Claude
> pricing/features only if it changes a recommendation. Output: ranked fixes with est.
> savings, ≤600 words, write to `DESIGN/docs/ai-cto/reviews/<date>-process-efficiency.md`.
> Skip anything you can't tie to a concrete token saving.*

Same answer, a fraction of the spend, and a defined place for it to land.

---

## 5. Current-as-of-2026-06 facts behind the above

- **Models/pricing:** Opus 4.8 $5/$25 · Sonnet 4.6 $3/$15 · Haiku 4.5 $1/$5 per M.
  Batch −50%. Caching −90% on cached input. Long-context surcharge removed (Mar 2026).
- **Cache TTL** defaults to 5 min (down from 60); 1h TTL available, worth it only on
  reused prefixes. Changing tools/CLAUDE.md mid-session busts the whole cache.
- **Claude Code shipped (2026):** Dreaming (scheduled memory curation across past
  sessions), multi-agent orchestration (lead delegates to specialist subagents, each its
  own model/prompt/tools), expanded Skills, agent view, faster+cheaper fast mode, Opus 4.8
  as default.
- **Hybrid local+cloud:** published architectures (LiteLLM gateway + local Ollama + Claude
  cloud tier) report 60–90% cost cuts by routing the simple/sensitive majority locally.

### Sources

- [Best practices — Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [How Claude Code uses prompt caching — Docs](https://code.claude.com/docs/en/prompt-caching)
- [What's new — Claude Code Docs](https://code.claude.com/docs/en/whats-new)
- [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Token Efficiency for Claude Code in the Enterprise (Medium, Jun 2026)](https://dave-c.medium.com/token-efficiency-for-claude-code-in-the-enterprise-525f6d8123ea)
- [23 Tips for Claude Code Token Saving (Analytics Vidhya, May 2026)](https://www.analyticsvidhya.com/blog/2026/05/tips-for-claude-code-token-saving/)
- [Claude Prompt Caching in 2026: the 5-min TTL change (dev.to)](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Hybrid Cloud-Local LLM: Complete Architecture Guide 2026 (SitePoint)](https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/)
- [Run Local AI Models with Claude Code to Cut Costs 10x (MindStudio)](https://www.mindstudio.ai/blog/run-local-ai-models-with-claude-code-cut-costs)
- [Code with Claude 2026: New Agent Features (MindStudio)](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [Anthropic API Pricing in 2026 (Finout)](https://www.finout.io/blog/anthropic-api-pricing)
