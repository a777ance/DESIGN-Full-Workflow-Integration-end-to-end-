# Receivables — states, dunning, reconciliation

How money is tracked from close to cash, and how the **delivery gate** is enforced. The
processor (Stripe) moves the money; the CRM record (`billing.*`) is the source of truth.

---

## Billing fields (on the household record — see `../08-client-list-and-crm/schema.md`)

| Field | Meaning |
| ----- | ------- |
| `billing.processor_customer_id` | Stripe customer id (`CHANGE_ME` placeholder in samples) |
| `billing.plan` | retainer plan id / amount |
| `billing.status` | `none` · `active` · `past_due` · `canceled` |
| `billing.setup_paid_ts` | when the one-time setup fee cleared |
| `billing.next_charge` | next retainer date |
| `billing.last_payment_ts` | most recent successful retainer |

## State machine

```
none ──(setup fee clears)──► active ──(retainer succeeds, monthly)──► active
  ▲                              │
  │                              └──(charge fails)──► past_due ──(retry succeeds)──► active
  │                                                       │
  └────────────(re-onboard)───── canceled ◄──(dunning exhausted)──┘
```

- **`active`** → the only state where the Statement (06) may be delivered.
- **`past_due`** → dunning runs; the *next* Statement is held until recovered.
- **`canceled`** → the delivery gate is closed; the home-JSON in `localDNS` is retained
  (rollback target) but no new Statements render.

## Dunning (gentle — retention, not collections)

1. Charge fails → automatic retry per processor schedule.
2. Day 1: friendly email — "your card didn't go through, here's the link."
3. Day 3 / Day 7: reminder; offer a quick call (04).
4. Day ~14: pause service conversation; mark `canceled` if unresolved.

Keep the tone calm (00). A churned customer who felt respected refers and returns.

## The delivery gate (enforced in stage 11)

The monthly run (06) reads `billing.status`; only `active` accounts render and send. This
is an automation, not a human check
([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)).

## Reconciliation

- Monthly: processor payout report ↔ CRM `billing.last_payment_ts` for every `active`
  account. Any mismatch is investigated before the next run.
- Setup fees reconciled against closed deals (05) — every `status = customer` should have
  a `billing.setup_paid_ts`.
- Keep customer (this stage) and operator-payout (10) ledgers **separate** — they feed
  different tax treatments.
