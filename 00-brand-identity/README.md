# 00 — Brand & identity

**Lives in:** Figma (source of truth) + an asset host / press-kit folder.
**Go-live / sync:** export assets; update the brand-kit links every other stage inherits.

The foundation every downstream surface inherits. Brand is **stage 00** because a trust
business is judged on consistency: if the logo, voice, and color drift between the
website (01), the intake form (03), and the Statement itself (06), the household reads
"amateur" — fatal for a service you let inside the home network. So brand is defined
**once** and *linked*, never re-pasted. This is the `tuning.conf` rule from `localDNS`
applied to identity: one place a value lives, so it cannot diverge.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`brand-kit.md`](brand-kit.md) | The single source of truth: logo, palette, type, voice, asset links |
| [`slogans-and-jingles.md`](slogans-and-jingles.md) | Approved taglines + the jingle/intro-video brief |

The binaries themselves (logo SVG/PNG, the intro video, the jingle audio) are **not**
committed here — they live in the asset host and are linked from `brand-kit.md`, so this
repo stays text and the heavy files have one home. (`.gitignore` excludes `*.psd`,
`*.ai`, `*.mp4`, etc. for this reason.)

## The deliverables (from the original DESIGN brief)

Intro video · logo · slogans · jingle · the visual system (color/type) · the Figma
source. Each maps to a section of `brand-kit.md` or a line in `slogans-and-jingles.md`.

## The voice, in one rule

Set by the category analogy — **pest control, not lawn care:** calm, specific, never
alarmist. We sell *quiet*, not fear. The canonical sample of this voice is the
Statement's "Handled For You" copy in `localDNS` ("*Cloudflare pushed a security update;
your appliance was patched the same day — Jose*") — always *your home*, *your
appliance*, attributed by name. When in doubt about tone, match that line.

## Who inherits this

| Stage | Inherits |
| ----- | -------- |
| 01 web-presence | Logo, palette, type on Squarespace / WordPress / GBP |
| 03 funnels | Form styling + confirmation-page voice |
| 04 phone & comms | Greeting + voicemail script tone |
| 06 statements | Visual alignment with the `localDNS` Statement (which owns its own CSS) |

**Invariant:** a downstream surface links to the brand kit; it never hard-codes a hex
value or re-uploads a logo. A brand change is a one-file edit here plus a re-export.
