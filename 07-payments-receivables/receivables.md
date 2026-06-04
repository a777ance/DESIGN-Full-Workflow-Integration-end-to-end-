# Billing — states, gentle reminders, keeping the books straight

How money gets tracked from "yes" to the bank, and how the paid-only gate gets enforced.
Stripe moves the money; the customer's record is the source of truth for where they stand.

---

## What we track (on the customer record — see [`../08-client-list-and-crm/schema.md`](../08-client-list-and-crm/schema.md))

| On the record | What it means |
| ------------- | ------------- |
| `billing.processor_customer_id` | Their ID in Stripe (`CHANGE_ME` in samples) |
| `billing.plan` | Which monthly plan / amount |
| `billing.status` | new · paid up · behind · canceled |
| `billing.setup_paid_ts` | When the $175 setup fee cleared |
| `billing.next_charge` | When the next monthly runs |
| `billing.last_payment_ts` | The last monthly that went through |

## The states

```
new ──(setup fee clears)──► paid up ──(monthly succeeds)──► paid up
  ▲                            │
  │                            └──(charge fails)──► behind ──(retry works)──► paid up
  │                                                   │
  └──────────(they come back)──── canceled ◄──(no luck after ~2 weeks)──┘
```

- **paid up** → the only state where this month's statement actually goes out.
- **behind** → we send the gentle reminders below; the *next* statement waits until they're
  caught up.
- **canceled** → statements stop. We keep their setup on file (in case they come back), but
  nothing new gets built. *(In the sample data, the Lapsed household is here.)*

## Chasing a missed payment (gently — we want them back, not beaten up)

1. Charge fails → the processor retries automatically on its own schedule.
2. Day 1: a friendly note — "looks like your card didn't go through, here's a quick link."
   (Copy is in [`../02-demand-generation/email-lists.md`](../02-demand-generation/email-lists.md).)
3. Day 3 / Day 7: a reminder; offer a quick call (04).
4. Around day 14: a "let's pause this" conversation; mark canceled if it's not sorted.

Keep the tone calm (00). A customer who churns but felt respected refers people and often
comes back.

## The paid-only gate (handled automatically, stage 11)

The monthly run (06) checks each account's status and only builds + sends for the paid-up
ones. This is automatic, not a human eyeballing a list
([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)).

## Keeping the books straight

- Each month, match the processor's payout report against the record for every paid-up
  account. Anything that doesn't line up gets sorted before the next run.
- Every customer should have a setup-fee date on file — if one's marked "customer" with no
  setup payment, find out why.
- Keep the **customer** money (here) and the **operator-payment** money (10) in separate
  ledgers — they're taxed differently and must never get mixed up at year-end.
