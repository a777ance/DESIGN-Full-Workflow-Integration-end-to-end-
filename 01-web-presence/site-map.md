# Site map & CTA routing

The page inventory across the storefront surfaces, and where each call-to-action points.
**Rule:** every page terminates in exactly one primary CTA → the intake form (stage 03).
No dead ends, no competing CTAs.

---

## Squarespace (marketing site) — primary funnel host

| Page | Purpose | Primary CTA → |
| ---- | ------- | ------------- |
| `/` (home) | Category line + the real Statement as proof | Intake form (03) |
| `/how-it-works` | Pest-control analogy; what's installed; the monthly Statement | Intake form (03) |
| `/the-statement` | Embeds/links the **live gallery** (`a777ance.github.io/localDNS/`) | Intake form (03) |
| `/pricing` | Setup fee + retainer (defaults from `MARKETING`, `CHANGE_ME`) | Intake form (03) |
| `/become-an-operator` | The guild pitch + dual-hat story | Operator funnel (09) |
| `/contact` | Phone (04) + form | Intake form (03) |

## WordPress (content / SEO engine)

- Category-education posts (see [`../02-demand-generation/category-education.md`](../02-demand-generation/category-education.md)):
  "is your smart TV spying on you?", "why grandma's tablet is a target", etc.
- Each post ends with the same single CTA → intake form (03).
- Internal-links into the Squarespace funnel pages for authority flow.

## Google Business Profile

| Field | Value |
| ----- | ----- |
| Name / category | `CHANGE_ME` (e.g. "Computer support / network service") |
| Service area | The active route zips (see `../02-demand-generation/geo-targeting.md`) |
| Tagline | The winning slogan from `../00-brand-identity/slogans-and-jingles.md` |
| Website | The Squarespace home |
| Reviews | The local-SEO flywheel — request one after the first Statement lands |

## The gallery (read-only, served from localDNS)

- URL: `https://a777ance.github.io/localDNS/`
- Source: `localDNS/docs/statements/`, published by `localDNS/.github/workflows/pages.yml`.
- This repo **links** to it; it is never copied or rebuilt here.

---

**Consistency check:** every CTA above resolves to the intake form (03) or, for the
operator path, the recruiting funnel (09) — nowhere else. A page with two competing CTAs
is a conversion bug.
