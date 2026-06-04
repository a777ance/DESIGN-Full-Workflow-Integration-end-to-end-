# 03 — Funnels & capture

**Lives in:** the website pages (01) + the **booking form** + **Setmore** (so people pick
their own time) + an optional demo.
**Go-live:** publish the funnel; connect the form to the customer list (08) so a submission
becomes a record automatically (11).

This is where a curious visitor turns into a name on a list you can actually follow up with.
It's the most important connection in the whole funnel: interest goes in, a real lead comes
out.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`intake-form.md`](intake-form.md) | Every question on the form, and where its answer lands on the customer record |
| [`data/sample-intake.json`](data/sample-intake.json) | A made-up example submission |

## The path

```
website page (01) ─► booking form ─► pick a time (Setmore) ─► [optional demo] ─► the consult (05)
                         │                    │
                  creates a LEAD        drops the appointment
                  on the customer       onto that same record
                  list (08)             (both automatic, stage 11)
```

## The form is a promise to the customer list

Every question on the form lines up **one-to-one** with a field on the customer record
(08). Ask for something the record can't hold and the answer vanishes when they hit submit;
leave out something the record needs and the lead is born half-finished. So the form and the
record are two views of the same thing — **change them together**
([LAUNCH-NOTES #3](../LAUNCH-NOTES.md#3-intake-form-fields-do-not-map-to-the-crm-schema)).
Keep the form short: every extra required box costs you a booking, and the real depth comes
in the consult (05), not the form.

## Why people pick their own time

Letting someone grab a slot themselves (Setmore) kills the phone-tag that murders
local-service bookings — "we'll call you to schedule" just adds a step where leads go cold.
And it writes the appointment straight onto their record. We reuse the exact same self-booking
for operator interviews later (09).

## The "demo"

The original plan called for a fancy interactive demo. We already have a better one: **the
live statement.** Hand the prospect your phone, scan the code, let them scroll a real
statement at `a777ance.github.io/localDNS/`. That's the demo. A custom-built app is a
someday project — don't build it just to look impressive (see `workflow-context.md`).

## Hand-offs

- **← 01/02:** receives the traffic; wears the brand on the form and thank-you page.
- **→ 08 customer list:** a submission *is* a new lead (automatically, stage 11).
- **→ 04 phone:** booked consults show up for a human to confirm.
- **→ 05 sales:** a booked, warmed-up lead is what the consult starts from.
