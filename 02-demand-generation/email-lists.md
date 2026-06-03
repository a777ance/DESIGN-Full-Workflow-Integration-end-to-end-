# Email lists — consent-clean lifecycle

A trust business cannot afford a spam complaint. The list is **segmented off the system
of record (08)**, every contact carries a consent record, and we never import a scraped
or purchased list. Lives in Mailchimp (or equivalent); the CRM is the truth, the email
tool is a sync target.

---

## The consent record (non-negotiable)

Every contact stores, on its CRM record:

| Field | Why |
| ----- | --- |
| `email` | the address |
| `consent` | explicit opt-in (`true`/`false`) — no pre-checked boxes |
| `consent_source` | where it was given (intake form, GBP, event) |
| `consent_ts` | timestamp of opt-in |
| `unsubscribed_ts` | set on opt-out; suppresses forever |

See [LAUNCH-NOTES #5](../LAUNCH-NOTES.md#5-email-list-collected-without-consent-record).
No consent record → not mailable. Period.

## Segments (derived from the CRM, not maintained by hand)

| Segment | Source filter | Gets |
| ------- | ------------- | ---- |
| **Leads** | status = lead, consent = true | Nurture: category education, the real Statement, one CTA |
| **Customers** | status = customer | The monthly Statement notification (06) + occasional tips |
| **Operator-curious** | hand-raised in a Statement (09) | The guild/dual-hat sequence |
| **Dormant** | no activity 90d | A single gentle re-engage, then suppress |

## Sequences

- **Lead nurture:** 3–4 touches built on the category-education pillars (links to the
  live gallery), each ending in the intake CTA.
- **Customer monthly:** "your Statement is ready" — links to the online scrollable
  Statement; reinforces the referral CTA.
- **Operator nurture:** triggered by the "Connect in the Alliance" hand-raise.

## Hygiene rules

- One-click unsubscribe in every send; honor it instantly (write `unsubscribed_ts`).
- Never email an account the kept-document way: no invented stats, no fear bait.
- Bounce/complaint > threshold → pause and clean before the next send.
- CAN-SPAM basics: real physical address in the footer, honest subject lines.

## Hand-offs

- **← 08 CRM:** the source of truth for every address, consent flag, and segment.
- **→ 03 / 06 / 09:** sequences route clicks to the intake form, the live Statement,
  and the operator funnel respectively.
