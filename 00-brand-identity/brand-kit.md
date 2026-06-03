# Brand kit — single source of truth

Every downstream surface (web, forms, comms) **links to this file**; it never hard-codes
a value. A brand change is a one-file edit here plus a re-export from Figma. Values
marked `CHANGE_ME` are decisions not yet locked — see [CLAUDE.md § 1](../CLAUDE.md#1-known-issues--open-decisions).

---

## Asset links (the binaries live in the asset host, not git)

| Asset | Format | Link |
| ----- | ------ | ---- |
| Figma source | Figma | `CHANGE_ME` (Figma project URL — the master) |
| Logo (primary) | SVG | `CHANGE_ME` |
| Logo (mono / reversed) | SVG | `CHANGE_ME` |
| Favicon / app icon | PNG 512² | `CHANGE_ME` |
| Intro video | MP4 | `CHANGE_ME` (≤60s; see brief in `slogans-and-jingles.md`) |
| Jingle | MP3/WAV | `CHANGE_ME` |
| Press kit (zip of the above) | — | `CHANGE_ME` |

## Color palette

| Role | Token | Hex | Use |
| ---- | ----- | --- | --- |
| Primary | `--brand` | `CHANGE_ME` | Logo, primary buttons, links |
| Ink | `--ink` | `#1a1a1a` | Body text |
| Paper | `--paper` | `#ffffff` | Backgrounds |
| Quiet (good) | `--good` | `CHANGE_ME` (green) | "all clear" / positive sentiment — matches the Statement's compare-axis green |
| Watch | `--watch` | `CHANGE_ME` (amber) | attention, never alarm-red unless a real incident |

> Sentiment, not decoration: green means *good regardless of direction* (the rule the
> Statement's "How You Compare" axis uses). Keep the palette aligned with the live
> Statement CSS in `localDNS/docs/statements/tools/style.css` — that file owns the
> Statement's own rendering; this kit keeps the *marketing* surfaces in step with it.

## Typography

| Role | Family | Notes |
| ---- | ------ | ----- |
| Headings | `CHANGE_ME` | Humanist sans; calm, not techy |
| Body | `CHANGE_ME` | High legibility at small sizes (statements get printed) |
| Mono | system mono | Only for figures/IDs, sparingly |

## Logo usage

- Clear space: ≥ the height of the logo mark on all sides.
- Minimum size: 24px tall digital / 0.4in print.
- Don't: recolor outside the palette, add effects, stretch, or place on a busy photo.

## Voice & tone

- **Pest control, not lawn care.** We sell the quiet, not the fear. Calm, specific,
  reassuring.
- **Your home, by name.** "*Your living-room TV*," "*your appliance was patched — Jose*."
  Never generic IT-speak.
- **Honest.** Never claim a number the data doesn't support (the kept-document rule).
- **Plain.** A grandparent should understand every customer-facing sentence.

Canonical voice sample: the "Handled For You" log in the live client Statement
(`localDNS/docs/statements/`).
