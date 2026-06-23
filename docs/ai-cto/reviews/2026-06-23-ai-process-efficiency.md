# NARF — review — 2026-06-23 — AI process efficiency

Founder asked a standing question: where are the inefficiencies in our **process between the
human and the AI**, and what would cut token spend — better prompting, leveraging other models,
a hybrid local-LLM + Claude split, anything. This is that review. It's scoped to *how we use the
AI*, not the funnel. Findings are newest-relevance-first per house style.

Pricing and feature facts below were re-verified against the Anthropic platform on 2026-06-23
(current model table + prompt-caching/batch economics) and current third-party best-practice
write-ups. Keep this file dated — the model/pricing picture moves weekly.

---

## 0. Time-sensitive — a cost event lands TODAY (2026-06-23)

**Claude Fable 5 stops being free inside Pro/Max/Team/Enterprise plans today.** Through Jun 22 it
was bundled at no extra cost; from Jun 23 continued use bills at **API rates — $10 / $50 per MTok
input/output, exactly 2× Opus 4.8** ($5 / $25). If anyone in the guild has been doing Claude
Code or chat work on Fable 5, their per-token cost just doubled silently. **Action:** default
back to Opus 4.8 for day-to-day work; reserve Fable 5 for genuinely hardest long-horizon tasks
and only deliberately. Nobody should be on the most expensive model by accident.

---

## 1. The biggest lever we control: Claude Code session hygiene

We run Claude Code on the web across seven repos. The dominant cost there isn't the prompt — it's
**context that re-ships every turn**. Two concrete drains, both fixable today with no tooling:

**a. The CLAUDE.md tax.** Every repo's `CLAUDE.md` is injected into *every* request in that repo,
before anyone types a word. Current sizes (measured today):

| Repo | CLAUDE.md words | ≈ tokens/turn tax |
| ---- | ---------------: | ----------------: |
| `localDNS` | 2,728 | ~3,550 |
| `DESIGN-…` (this repo) | 2,608 | ~3,400 |
| `MARKETING` | 1,445 | ~1,900 |
| `customers` | 562 | ~730 |

The community rule of thumb is **keep CLAUDE.md under ~200 lines**; `localDNS` (326) and `DESIGN`
(295) are well over. These files are *good* — but a chunk of each is reference detail that belongs
in `README.md` / `*-context.md` and gets read on demand, not preloaded every turn. **Action:**
move stage-by-stage detail, deploy-path tables, and long known-issues lists out of `CLAUDE.md`
into the files they already cross-link, leaving CLAUDE.md as the briefing it claims to be. A 40%
trim on the two big ones saves ~3K tokens on *every* turn of *every* session in those repos.

**b. One task per session; compact aggressively.** A fresh session ships ~20K tokens/turn; a
200-turn session ships ~200K/turn because the whole history re-sends each turn — cost grows with
the square of session length. The cheap wins, in order of impact:
- **One task = one session.** Don't carry a finished task's history into the next one.
- **`/compact`** at natural breakpoints instead of letting a session sprawl.
- **Point at specific files** ("read `08-client-list-and-crm/schema.md`"), not "look at the repo."
- **`/cost`** to see what a session is actually spending; it makes the geometric growth visible.
- **Keep MCP servers minimal.** Each connected MCP server's tool definitions load every turn
  (can be ~18K tokens for a heavy one). We have the GitHub MCP server wired in — fine, it earns
  its keep; just don't accumulate more without checking the per-turn cost.

Heads-up worth knowing: there was a March 2026 Anthropic prompt-caching bug that inflated billed
tokens 10–20× with no warning. It's resolved, but the lesson stands — **spot-check `/cost`
periodically**; don't assume the meter is honest forever.

---

## 2. We already have the hybrid local/cloud rig — use more of it (and fix the leak)

This is the big strategic answer to "leverage other AI / run hybrid local + Claude." We are
**ahead of the curve here** — `localDNS/10-ai-orchestration/` already runs LiteLLM + Open WebUI on
the t630 with a reasoning ladder (`local-reason` deepseek-r1:1.5b on the box for light work,
`cloud-gpu-reason` / `cloud-overflow` for heavy). The industry pattern everyone is writing up in
2026 — route routine work to a local model, escalate only the hard stuff to a frontier API — is
literally the rig we already own. Reported savings for that pattern run **60–90% vs all-cloud**.

What we're *not* doing yet is **routing enough work to it.** Candidates that local distills handle
fine and that we currently (or will) hand to Claude:
- statement-copy first drafts and "Handled For You" log phrasing,
- lead/intent classification and call-note summarization (stage 04→08),
- marketing-email variants, FAQ drafting,
- embeddings / dedupe on the master list.

Reserve the Claude API for what actually needs frontier reasoning: the playbook edits, code, the
honesty-sensitive number-checking on a Statement. Rule of thumb: **draft local, finalize cloud.**

**Two guardrails before we lean on this harder:**
- **TD-14 is a blocker, not a footnote.** The 2026-06-19 review flagged that `config.yaml` fails
  *open* — a `sensitive`-tagged task pinned to `local-reason` falls back to `cloud-overflow`
  (Claude cloud) if the local model is down. If we route *more* personal/customer data through
  the local tier, that fail-open becomes a privacy leak, not a theoretical one. Fix TD-14 (fail
  closed: `local-reason → ["local-smart","local-fast"]`) *before* expanding local routing.
- **Pin LiteLLM ≥ 1.83.0.** Versions 1.82.7–1.82.8 had a supply-chain compromise (March 2026).
  Check what `~/llm-router` is actually running on the box and pin it.

---

## 3. If/when statements call the Claude API: caching + batch are free money

The Statement generator runs "at about a penny a home" and is the highest-*volume* AI-ish
workload we have. If any part of it calls the Claude API (composing copy, validating figures),
two API features apply directly and we should design them in from the start:

- **Prompt caching** — a stable prefix (system prompt, templates, the honesty/voice rules, shared
  reference) cached once costs **~0.1× on reads** after a **1.25× write** (5-min TTL). For a
  monthly run over many homes that all share the same instruction prefix, that's a **70–90% cut**
  on the repeated portion. Put the stable stuff first, the per-home data last, one `cache_control`
  breakpoint at the boundary. Verify with `usage.cache_read_input_tokens` — if it's 0 across
  homes, a per-request timestamp/UUID is silently busting the cache.
- **Batch API** — **50% off all tokens** for non-latency-sensitive work, results within ~1h
  (24h max). Monthly statement generation is the textbook batch case: it's a scheduled nightly
  job, nobody's waiting on it live. **Caching + batch stack** — cache the shared prefix *and*
  submit the run as a batch.

Model ladder for these workloads (don't reflexively reach for the top): Haiku 4.5 ($1/$5) for
classification/extraction, Sonnet 4.6 ($3/$15) for high-volume copy, Opus 4.8 ($5/$25) for the
honesty-sensitive finalize pass. Fable 5 ($10/$50) almost never — see §0.

---

## 4. Critique of the founder's prompt (he asked — here it is)

The standing prompt is broad and open-ended: "locate inefficiencies… is there a better way…
ANYTHING that could help… search the web… keep UP TO DATE… check the news." Honest read:

- **It's expensive by construction for an unattended routine.** "ANYTHING" invites maximal
  fan-out — every run re-researches the whole field. Ironically, the prompt asking how to save
  tokens is itself a high-token prompt. For a *recurring* routine, scope each run to **one axis**
  ("this week: audit CLAUDE.md sizes and report deltas") so it's cheap and the output is
  comparable run-to-run.
- **No success criterion / no "skip if nothing changed."** A good recurring-routine prompt says
  *when to stay silent* (nothing material changed) and *what threshold is worth a notification*.
  Without that, every run feels obligated to produce a wall of text.
- **It mixes a one-time audit with a standing monitor.** Split them: (1) a one-shot "audit our AI
  process" (this doc), and (2) a lean recurring "tell me only if model pricing/availability
  changed, a cost spiked, or a routine couldn't run."

Suggested rewrite for the recurring version:

> "Weekly: check for Anthropic model/pricing/availability changes and any LiteLLM CVE since the
> last run. If something changed that affects our cost or privacy posture, notify with the
> specific change and the one action it implies. If nothing changed, don't notify. Don't
> re-derive the whole strategy each time — diff against last week."

That keeps it cheap, makes the output actionable, and respects the "silence when all's well" rule.

---

## 5. Top 3 actions

1. **Trim `localDNS` and `DESIGN` CLAUDE.md by ~40%** (push detail to README/context files). Saves
   ~3K tokens on every turn in the two repos we work in most. No risk, do it today.
2. **Fix TD-14 (fail closed) and pin LiteLLM ≥ 1.83.0** — preconditions for routing more work to
   the local tier, which is the real 60–90% cost lever.
3. **Design statement-generation API calls around prompt caching + Batch API** (and the Haiku/
   Sonnet/Opus ladder) before the pipeline scales past HH-0001. Bake it in now, not later.

— NARF
