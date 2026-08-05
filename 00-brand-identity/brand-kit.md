# Brand kit — the one place the look lives

Every surface (website, forms, emails, the phone greeting) points back to this file. Nobody
hard-codes a color or re-uploads the logo somewhere else. Change the brand here, re-export
from Figma, done. Anything marked `CHANGE_ME` is a decision we haven't locked yet — see
[CLAUDE.md § 1](../CLAUDE.md#1-known-issues--open-decisions).

> For *what to say* (the words, the pitch, the price talk), go to
> [`the-pitch.md`](the-pitch.md). This file is the *look*.

---

## Where the files live (binaries aren't in git)

| Asset | Format | Link |
| ----- | ------ | ---- |
| Figma master | Figma | `CHANGE_ME` (project URL — the source everything exports from) |
| Logo (primary) | SVG | `CHANGE_ME` |
| Logo (one-color / reversed for dark backgrounds) | SVG | `CHANGE_ME` |
| Favicon / app icon | PNG 512² | `CHANGE_ME` |
| Intro video | MP4 | `CHANGE_ME` (≤60s; brief in `slogans-and-jingles.md`) |
| Jingle | MP3/WAV | `CHANGE_ME` |
| Press kit (zip of the above) | — | `CHANGE_ME` |

## Color

**The palette is not decided here.** It is extracted from the Statements that already ship
and lives in `localDNS/design-system/tokens/tokens.css` — the full set, with a note on each
token saying what it is for. See [`design-system.md`](design-system.md) for how that works.
This table is the working subset; take any value not listed here from the tokens file rather
than sampling it off a screenshot.

| Where it's used | Token | Hex | Notes |
| --------------- | ----- | --- | ----- |
| Logo, headers, links, figures | `--navy` | `#13314f` | the one brand color |
| The human hand — an operator's name, the rule under the header | `--bronze` | `#a9803f` | spend it sparingly or it stops meaning anything |
| Body text | `--ink` | `#1f2733` | running prose drops to `--ink-body` `#3a4553` |
| Backgrounds | `--paper` | `#fbfaf7` | warm, **not** `#ffffff` — it reads as paper |
| "All clear / good" | `--pos` | `#3f7a4d` | the calm green the statement uses for good news |
| "Worth a look" | `--amber` | `#c08a2e` | attention — never alarm-red unless something's actually wrong |
| "A real problem" (rare) | `--alert` | `#b4542a` | high severity on the operator portfolio |

> **Corrected 2026-08-05.** This table previously carried `--ink: #1a1a1a`,
> `--paper: #ffffff`, and `CHANGE_ME` for the brand color — none of which matched what the
> live Statements actually print. The values above are the shipped ones. A brand kit that
> disagrees with the document in the customer's hand is worse than no brand kit.

> Color carries meaning, not decoration: green = good, amber = keep an eye on it, red = a
> real problem (rare). **Never carry state by color alone** — every status on a Statement is
> also spelled out in words, because these documents get printed and photocopied.

## Type

**Gill Sans MT everywhere** — house style (see [CLAUDE.md](../CLAUDE.md#house-style-ordering--typography)).
Web/CSS stack: `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

| Where | Family | Notes |
| ----- | ------ | ----- |
| Headlines | Gill Sans MT | a warm, human sans — calm, not techy |
| Body | Gill Sans MT | easy to read small (statements get printed and mailed) |
| Numbers / IDs | Gill Sans MT | tabular figures (`font-feature-settings: "tnum"`) for figures and account numbers |

## Logo do's and don'ts

- Give it room: clear space all around equal to the height of the logo mark.
- Don't go smaller than 24px tall on screen / 0.4in in print.
- Don't recolor it outside the palette, add shadows, stretch it, or drop it on a busy photo.

## Voice & tone

Four rules. They're the whole brand.

1. **Pest control, not lawn care.** We sell the quiet — the absence of trouble — not fear.
   Calm and reassuring beats dramatic every time. Fear converts once and churns; calm keeps
   people for years.
2. **Your home, by name.** "*Your living-room TV.*" "*Your appliance was patched while you
   slept — Jose.*" Never "the endpoint," never "the device fleet."
3. **Honest.** We never print a number we can't stand behind. If we didn't measure it, it
   doesn't go on the statement. (More in [CLAUDE.md § 1](../CLAUDE.md#1-known-issues--open-decisions).)
4. **Plain.** A grandparent should understand every customer-facing sentence. The
   plain-English swap table is in [`the-pitch.md`](the-pitch.md) — use it everywhere.

The canonical voice sample is the "Handled For You" log on the live Statement
(`localDNS/docs/statements/`). Read one before you write anything customer-facing.
