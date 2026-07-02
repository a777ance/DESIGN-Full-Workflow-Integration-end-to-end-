# Token-efficiency rollout playbook

Turnkey execution of the 2026-07-02 audit
([`reviews/2026-07-02-ai-process-efficiency.md`](reviews/2026-07-02-ai-process-efficiency.md),
TD-15). Each fix is self-contained. Blocks are presented **last-fix-first** per house style
(reverse the blocks, keep the steps); the numbering below is fixed to the audit's ranking, so
do them **Fix 1 → Fix 6** for best return, reading up this page.

## Contents (reversed-block order)

- [Fix 6 — Batch API for async jobs](#fix-6--batch-api-for-async-jobs)
- [Fix 5 — model tiering](#fix-5--model-tiering)
- [Fix 4 — route chores to the local LLM router](#fix-4--route-chores-to-the-local-llm-router)
- [Fix 3 — trim CLAUDE.md to lookup-table size](#fix-3--trim-claudemd-to-lookup-table-size)
- [Fix 2 — de-dupe the house-style block](#fix-2--de-dupe-the-house-style-block)
- [Fix 1 — per-repo sessions](#fix-1--per-repo-sessions)

---

## Fix 6 — Batch API for async jobs

Move workloads nobody is waiting on to the Batch API (50% off, stacks with prompt caching).

1. Identify the batchable jobs: the **monthly statement generation** (DESIGN stage 06 → the
   `localDNS` generator) and any **bulk doc-lint / CI sweep**.
2. For statement generation, submit the month's households as one Message Batches request
   rather than N real-time calls; collect results within 24h (the job already runs on a
   schedule, so latency is free).
3. Keep the batch request's shared prefix (system prompt, templates) stable so prompt caching
   also applies on top of the 50%.

## Fix 5 — model tiering

1. Default new sessions to Sonnet; escalate to Opus deliberately for architecture or hard
   refactors only.
2. Reserve the 1M-context tier for genuinely large cross-repo reads — not for editing a
   150-line `CLAUDE.md`.

## Fix 4 — route chores to the local LLM router

The router already exists (`localDNS` stage 10: LiteLLM :4040, Open WebUI, reasoning ladder).

1. **First, fix TD-14** — give `local-reason` a local-only fallback so a `sensitive`-tagged task
   can never fail over to `cloud-overflow`. Do not route any PII until this is fail-closed.
2. Point cheap, high-volume chores at the local model: link/anchor checking, commit-message
   drafts, diff summaries, lead classification, templated statement copy, the newest-first /
   Z→A reordering chores.
3. Keep code changes, architecture, and anything touching real customer data on Claude. The
   t630's `deepseek-r1:1.5b` is fine for lint/summarize/classify, not for code.

## Fix 3 — trim CLAUDE.md to lookup-table size

Biggest offender: `localDNS/CLAUDE.md` (326 lines) carries narrative rationale that already
lives in `network-context.md` (the DNS split, host-resolver root cause, IPv6 black hole).

1. For each rationale paragraph in a `CLAUDE.md`, confirm the same content exists in the linked
   context file (`network-context.md`, `workflow-context.md`, etc.).
2. Replace the paragraph with the one-line invariant + the existing link. Keep the tables and
   the pointers; drop the prose.
3. Run `python3 tools/check-docs.py` (DESIGN) after editing to confirm no anchor/link broke.
4. Target: `localDNS` and `DESIGN` `CLAUDE.md` under ~150 lines each.

## Fix 2 — de-dupe the house-style block

The ~20-line block is inlined in all six `CLAUDE.md` (identical in DESIGN/localDNS/MARKETING/
claude-code-homelab; `customers` and `Azure-lab` each add one line — see
[`HOUSE-STYLE.md`](../../HOUSE-STYLE.md) "Repo-specific addenda"). Canonical copy now lives in
`HOUSE-STYLE.md`.

> **Order matters — do step 1 before step 2, or the convention silently stops loading.** The
> single loaded copy must be in `~/.claude/CLAUDE.md` *first*; only then remove the inline
> copies. Skipping step 1 while doing step 2 drops house style from context on every machine.

1. Create `~/.claude/CLAUDE.md` on each machine you run Claude Code from, containing exactly:

   ```markdown
   ## House style: ordering & typography
   These conventions apply across **every** A777ance repo — current and future. (Adopted 2026-06-05.)

   - **Time-based content reads newest-first (reverse-chronological).** Logs, changelogs,
     decision logs (ADR / FIN), known-issues and issue trackers, FAQs, metrics and review
     logs, and "Handled For You" entries all lead with the most recent item. Apply this
     within the time-based *section* even when the whole file isn't time-based.
   - **Alphabetical lists run Z → A** (descending).
   - **Walkthroughs: reverse the blocks, keep the steps.** Present the major sections/blocks in
     reverse order (last block first) but keep the numbered steps *within* each block in forward
     order. A walkthrough's TOC mirrors the reversed block order. **Never renumber.**
   - **Font: Gill Sans MT everywhere.** Web/CSS stack:
     `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

   Prefer opening Claude Code with the working directory set to a single repo, not the parent
   (see Fix 1). Full convention + repo addenda: each repo's HOUSE-STYLE.md / CLAUDE.md.
   ```

2. In each repo's `CLAUDE.md`, replace the inline `## House style` block with a 2-line pointer
   (keep the heading so the file's own table-of-contents anchor still resolves):

   ```markdown
   ## House style: ordering & typography
   Canonical conventions live in [`HOUSE-STYLE.md`](HOUSE-STYLE.md) and load once from your
   user-level `~/.claude/CLAUDE.md`. Repo-specific addenda are noted in `HOUSE-STYLE.md`.
   ```

3. Preserve the two addenda in each repo's `HOUSE-STYLE.md` (`customers`, `Azure-lab`).
4. Respect each repo's push rule: DESIGN/customers/MARKETING/Azure-lab commit to their
   designated `claude/*` branches; `localDNS` and `claude-code-homelab` are "push to `main`,
   no branches" per their own `CLAUDE.md` — reconcile with the founder before landing there.
5. Run `check-docs.py` where present after each edit.

## Fix 1 — per-repo sessions

Zero-cost, biggest single saving (~9–13k tokens/session): sessions opened at `/home/user` merge
all six `CLAUDE.md`. Open Claude Code with the working directory set to the specific repo so
only that repo's memory loads.

1. Start sessions from inside the repo (`cd localDNS && claude`), not from the parent.
2. For genuine cross-repo work (portfolio reviews), scope to DESIGN and let its links pull the
   others on demand rather than pre-loading all six.
3. Glance at the context meter / run `/context` at session start to confirm only one repo's
   memory is loaded.
