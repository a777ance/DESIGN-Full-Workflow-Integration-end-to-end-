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

| Where it's used | Name | Hex | Notes |
| --------------- | ---- | --- | ----- |
| Logo, buttons, links | `--brand` | `CHANGE_ME` | the one brand color |
| Body text | `--ink` | `#1a1a1a` | |
| Backgrounds | `--paper` | `#ffffff` | |
| "All clear / good" | `--good` | `CHANGE_ME` (green) | the calm green the statement uses for good news |
| "Worth a look" | `--watch` | `CHANGE_ME` (amber) | attention — never alarm-red unless something's actually wrong |

> Color carries meaning, not decoration: green = good, amber = keep an eye on it, red = a
> real problem (rare). Keep these in step with the live statement's palette so the postcard
> and the statement feel like the same family.

## Type

**Gill Sans MT everywhere** — house style (see [house-style.md](../docs/house-style.md)).
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
