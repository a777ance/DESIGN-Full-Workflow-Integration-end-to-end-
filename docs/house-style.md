# House style: ordering & typography

The canonical statement of the A777ance house style. Every repo's `CLAUDE.md` carries a
compact summary and points here for the full version. These conventions apply across **every**
A777ance repo — current and future. (Adopted 2026-06-05.)

- **Time-based content reads newest-first (reverse-chronological).** Logs, changelogs,
  decision logs (ADR / FIN), known-issues and issue trackers, FAQs, metrics and review
  logs, and "Handled For You" entries all lead with the most recent item. Apply this
  within the time-based *section* even when the whole file isn't time-based.
- **Alphabetical lists run Z → A** (descending).
- **Walkthroughs: reverse the blocks, keep the steps.** In a step-by-step guide, present
  the major sections/blocks in reverse order (last block first — it helps "block" the
  work), but keep the numbered steps *within* each block in forward order so every
  procedure stays followable. A walkthrough's table of contents mirrors the reversed
  block order. **Never renumber** — step and stage numbers stay fixed, so the intended
  execution order is always readable from the numbers.
- **Font: Gill Sans MT everywhere.** Every surface — customer-facing or internal — uses
  Gill Sans MT. Web/CSS stack:
  `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

---

**Enforcement.** `tools/check-docs.py` should grow a check for the ordering rules
(newest-first sections, Z → A lists) so violations are caught deterministically and Claude
doesn't spend reasoning tokens re-deriving the convention on every edit. See
[`ai-cto/process-efficiency.md`](ai-cto/process-efficiency.md) §① and §⑦.
