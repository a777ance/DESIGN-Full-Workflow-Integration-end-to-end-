# 03 — Funnels & capture

**Lives in:** landing pages (01) + the **intake form** + **Setmore** (self-booking) +
an optional demo app.
**Go-live / sync:** publish the funnel; wire the form → CRM (08) via an automation (11).

Where attention becomes a **record**. This is the single most important integration seam
in the funnel: unstructured interest in, structured CRM record out.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`intake-form.md`](intake-form.md) | The field schema — every field maps to the CRM (08) |
| [`data/sample-intake.json`](data/sample-intake.json) | A fictional example submission |

## The funnel path

```
landing page (01) ─► intake form ─► Setmore booking ─► [optional demo] ─► consult (05)
                         │                  │
                    (11) writes        (11) writes the
                    a LEAD record      appointment onto
                    to the CRM (08)    that same record
```

## The intake form is the contract

Every field on the form maps **one-to-one** to a field in
[`../08-client-list-and-crm/schema.md`](../08-client-list-and-crm/schema.md). If the form
asks for something the schema can't store, the data dies on submit; if the schema needs
something the form never asks, the record is born incomplete. **Change the form and the
schema together** — they are two views of one contract. See
[LAUNCH-NOTES #3](../LAUNCH-NOTES.md#3-intake-form-fields-do-not-map-to-the-crm-schema).

## Why Setmore self-booking

Letting the prospect pick the consult slot removes the phone-tag that kills local-service
conversion, and it writes the appointment straight onto the record. "We'll call you" adds
a hop where leads go cold. The same Setmore pattern is reused for **operator interviews**
in stage 09.

## The demo app (optional)

The "demo apps / app stack" from the original DESIGN brief. Today the **live Statement
gallery is the demo** — point the prospect at `a777ance.github.io/localDNS/` and let them
scroll a real Statement on their phone. A bespoke interactive demo is a Phase-2 build
(see `MARKETING` roadmap and `workflow-context.md` → toggle app); don't build it to
manufacture liquidity.

## Hand-offs

- **← 01/02:** receives traffic; inherits brand voice on the form + confirmation page.
- **→ 08 CRM:** the form submission *is* a new lead record (via automation, stage 11).
- **→ 04 phone:** booked consults appear for the human to confirm.
- **→ 05 sales:** a booked, qualified record is the input to the consult.
