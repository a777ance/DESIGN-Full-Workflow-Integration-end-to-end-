# 01 — Web presence

**Lives in:** Squarespace (the website) · the blog (for search) · Google Business Profile
(the local listing) · the live statement gallery (served from `localDNS`).
**Go-live:** publish the site, claim and fill in the Google listing; the gallery updates
itself from `localDNS`.

The storefront. It has exactly **one job: move a stranger to the booking form** (stage 03).
A visitor should land, get the idea in ten seconds, see a real statement, and have one
obvious next step. It wears the brand from stage 00 and never invents its own look.

---

## Three places people find us — and why each one earns its keep

| Where | Who it catches | Why it's worth it |
| ----- | -------------- | ----------------- |
| **Google Business listing** | The person typing "network help near me" at 9pm | The biggest free local-search lever there is, and most competitors don't bother |
| **The website (Squarespace)** | Everyone — the brochure + the booking flow | Fast, low-fuss, easy to run; nothing fancy to break at 11pm |
| **The blog** | The "should I worry about my smart TV" searcher | Plain-language posts rank well and are ours to keep, unlike a locked platform |
| **The statement gallery** | Anyone who wants proof | The *real* artifact — scan-and-scroll on a phone, not a screenshot — served straight from `localDNS` |

Page-by-page CTAs are in [`site-map.md`](site-map.md).

## Show the real statement — never a screenshot

The site links to the live gallery at **`https://a777ance.github.io/localDNS/`**, which
updates on its own whenever the statements change. Never paste a screenshot of a statement
into the site: a picture loses the scan-and-scroll, and it drifts out of date the moment a
real one changes ([LAUNCH-NOTES #2](../LAUNCH-NOTES.md#2-statement-gallery-link-points-at-a-mockup-not-the-live-pages-site)).

## What the storefront has to do

1. Lead with the category line (00) and a **real statement** as proof.
2. End every page with one button → the booking form (03). No dead ends, no competing asks.
3. Keep the Google listing real and reviewed, so local search resolves to a trustworthy spot.
4. Stay boring to run — fast, simple, debuggable at 11pm.

## Hand-offs

- **← 00 brand:** logo, colors, type, voice.
- **→ 03 funnels:** every button points at the booking form.
- **↔ 06 statements:** links out to the live gallery; the QR codes on a statement point
  *back* to the customer's status page and online statement.
