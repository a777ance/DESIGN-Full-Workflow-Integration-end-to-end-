# 01 — Web presence

**Lives in:** Squarespace (Circle) · WordPress · Google Business Profile · GitHub Pages
(the Statement gallery, served from `localDNS`).
**Go-live / sync:** publish the site; verify the GBP listing; the gallery deploys from
`localDNS` via its `pages.yml`.

The storefront. Its **only job is to move a stranger into the funnel** (stage 03) — every
page ends in a path to the intake form. It inherits everything visual from stage 00 and
never hard-codes brand values.

---

## Three surfaces, three intents — why not one

| Surface | Intent it catches | Why it earns its place |
| ------- | ----------------- | ---------------------- |
| **Google Business Profile** | *Local high-intent* ("network help near me") | The single biggest local-SEO lever, free, and most competitors neglect it |
| **Squarespace (Circle)** | Brochure + funnel host | Fast, low-maintenance, dull to run — matches "keep everything dull"; Circle's agency tier lets one operator manage multiple client sites |
| **WordPress** | Content / category SEO | Long-form education ranks better and is more ownable than locked-platform pages |
| **GitHub Pages gallery** | *Proof* — the live Statement | The real artifact, not a mockup — served straight from `localDNS/docs/statements/` |

See [`site-map.md`](site-map.md) for the page inventory and where each CTA points.

## The published Statement gallery — link it, don't rebuild it

The marketing site links to **`https://a777ance.github.io/localDNS/`** — the live,
QR-scrollable gallery published by `localDNS`'s `pages.yml` workflow on every change to
`docs/statements/`. Never screenshot the Statement into the marketing site: a screenshot
loses the QR/scroll experience and drifts from the real artifact (see
[LAUNCH-NOTES #2](../LAUNCH-NOTES.md#2-statement-gallery-link-points-at-a-mockup-not-the-live-pages-site)).

## What the storefront must do

1. Lead with the category line (00) and the **real Statement** as proof.
2. End every page with one CTA → the intake form (03).
3. Carry the GBP so local search resolves to a real, reviewed listing.
4. Stay dull: low-maintenance, fast, debuggable at 11pm.

## Hand-offs

- **← 00 brand-identity:** logo, palette, type, voice.
- **→ 03 funnels:** every CTA targets the intake form / Setmore booking.
- **↔ 06 statements:** links to the live gallery; the Statement's QR codes point *back*
  to the status page and the online statement.
