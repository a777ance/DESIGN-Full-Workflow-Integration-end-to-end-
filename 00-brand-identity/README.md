# 00 — Brand & identity

**Lives in:** Figma (the master) + a folder of exported logo/audio/video files.
**Go-live:** export the assets, update the links in `brand-kit.md`, and every other stage
picks up the change.

A customer should see the same calm logo, the same plain voice, and the same blue on the
postcard, the website, the booking page, and the monthly statement — and never once
wonder if they're dealing with the same outfit. That consistency *is* the trust pitch. A
service you let onto your home Wi-Fi can't look like it was thrown together. So the brand
is settled **once**, here, and every other surface points back to it instead of inventing
its own.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`the-pitch.md`](the-pitch.md) | **What to actually say** — the one-liner, the elevator, the 2-minute open, the price talk. The most-used page in the repo. |
| [`brand-kit.md`](brand-kit.md) | The look: logo, color, type, voice — and where the asset files live |
| [`slogans-and-jingles.md`](slogans-and-jingles.md) | The taglines we've approved + the jingle and intro-video briefs |

The actual logo files, the jingle, and the video are **not** in this repo — they're big
binaries that live in the asset folder and are linked from `brand-kit.md`. (That's why
`.gitignore` skips `*.psd`, `*.mp4`, and friends.)

## The voice, in one breath

**Pest control, not lawn care.** We sell the quiet, not the fear — calm, specific, and
plain enough that a grandparent gets every word. We talk about *your living-room TV* and
*your kids' tablets*, never "endpoints." We put a real person's name on the work.

The gold-standard sample of this voice is the "Handled For You" log on the live customer
Statement:

> *"Cloudflare pushed a security update to its encrypted-DNS service. Your appliance was
> updated the same day — your private lookups kept flowing, a little faster than before."*
> — Patched on your t630 by Jose

When you're unsure how anything should sound, go read a real one and match it.

## Who picks this up

| Stage | Inherits |
| ----- | -------- |
| 01 web presence | The logo, colors, and type on the website and Google listing |
| 02 demand gen | The voice in every ad, post, and email |
| 03 funnels | The look and tone of the booking form + thank-you page |
| 04 phone | The greeting and voicemail script |
| 06 statements | Visual family resemblance to the live Statement (which sets its own styling) |

**The one rule:** a downstream surface *links* to the brand kit — it never re-types a hex
code or re-uploads a logo. Change the brand here, once, and re-export. That's the whole
job of stage 00.
