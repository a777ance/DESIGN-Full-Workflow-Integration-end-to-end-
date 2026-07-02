# A777ance house style — ordering & typography

Canonical, single source of truth for the house-style conventions that apply across **every**
A777ance repo — current and future. (Adopted 2026-06-05.) Each repo's `CLAUDE.md` currently
inlines a copy of this block; the token-efficiency rollout
([`docs/ai-cto/token-efficiency-rollout.md`](docs/ai-cto/token-efficiency-rollout.md)) moves
the single loaded copy into machine-local `~/.claude/CLAUDE.md` and points the repos here.

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

## Repo-specific addenda

Two repos append one line to the shared block. Preserve these when rolling out:

- **`customers`** — after the reverse-chronological bullet: *"(The personal job tracker and
  writing log here already work this way — newest at the top.)"*
- **`Azure-lab`** — after the intro line: *"They are documentation conventions, not
  infrastructure, so they apply even while this repo is a stub."*
