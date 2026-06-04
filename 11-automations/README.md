# 11 — Automations

**Lives in:** Zapier / Make + the `localDNS` statement job.
**Go-live:** switch on the automations that carry a customer from one stage to the next; never
hand-copy.

The glue. Each stage is useless on its own — the magic is a customer's info *moving* from one
tool to the next without anyone retyping it. Making this its own stage forces a single map of
every hand-off and a single person responsible for the seams between tools.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`automation-map.md`](automation-map.md) | Every hand-off, and the automation that carries it |

## The one rule

If moving a customer's info from tool A to tool B means someone retypes it, that's a bug here —
not an acceptable manual step ([LAUNCH-NOTES #15](../LAUNCH-NOTES.md#15-a-stage-hand-off-requires-a-human-to-retype-data)).
Every arrow in [the whole-funnel picture](../README.md#the-whole-funnel-one-page) is either an
automation or a to-do to build one. Retyping is how info gets dropped, gets stale, and stops
scaling past a handful of homes.

## The biggest automation is the statement job

The monthly run itself — the customer list → `localDNS`'s tool → finished statements →
delivery — is the largest piece of automation in the whole map. This stage **schedules and
connects** it (and makes sure it only sends to paid-up accounts); it doesn't touch how the
statement gets built.

## What to build first (as each tool comes online)

1. **Booking form → customer list** (03→08): the most important one — a form submission becomes a
   lead. Until this works, nothing else matters.
2. **Appointments + call notes → customer list** (03/04→08).
3. **"Yes" → billing + a reminder to go set up the box** (05→07 + the localDNS hand-off).
4. **Paid status → who gets a statement** (07→06): the paid-only gate.
5. **The monthly statement run** (06) + the "your statement's ready" email (02).
6. **"Connect in the Alliance" tap → operator lead** (06→09), and **operator goes active → ask
   for the W-9** (09→10).

## Hand-offs

This stage touches **all** of them — it *is* the connective tissue. The full table is in
[`automation-map.md`](automation-map.md).
