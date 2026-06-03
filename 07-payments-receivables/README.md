# 07 — Payments & receivables

**Lives in:** Stripe (or equivalent processor) + accounting.
**Go-live / sync:** create the plan; collect the setup fee + monthly retainer; reconcile.

Getting paid, and the **delivery gate**: a Statement (the value receipt) goes out only to
a paid account. Two line items — the one-time setup fee and the monthly retainer —
because they answer different objections (labor vs. ongoing value).

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`receivables.md`](receivables.md) | Billing states, dunning, reconciliation, the delivery gate |
| [`data/sample-receivables.csv`](data/sample-receivables.csv) | Fictional example billing rows |

## Two line items

| Charge | When | Default (`MARKETING`, `CHANGE_ME`) | Why separate |
| ------ | ---- | ---------------------------------- | ------------ |
| **Setup fee** | Once, on close (05) | ~$150–200, never discounted | Covers real install labor; sets "professional service" expectation |
| **Monthly retainer** | Recurring | ~$25–40/mo | The ongoing quiet + the Statement |

> Note the two money flows in the guild (`MARKETING`): the **platform** collects the
> customer membership and operator dues; the **operator** bills the customer for service
> directly. This stage handles the platform-side collection and the customer plan; the
> operator's direct billing is theirs, and the operator's *dues* are in stage 09.

## The delivery gate (the key invariant)

Sending the Statement to an unpaid/churned account gives away the proof of value for free
and trains non-payment. So **delivery (06) is gated on `billing.status = active`**,
enforced by an automation (11) — not by an operator remembering
([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)). Dunning
is gentle (the model is retention, not collections), but the gate is firm.

## Billing states (on the CRM record, `billing.status`)

```
none ─►(setup paid)─► active ─►(charge fails)─► past_due ─►(recovered)─► active
                                     │
                                     └─►(dunning exhausted)─► canceled  ──► Statement gate CLOSES
```

Full state handling and reconciliation in [`receivables.md`](receivables.md).

## Hand-offs

- **← 05 sales:** on close, create the customer + plan; collect the setup fee.
- **→ 06 statements:** supplies the paid/unpaid gate for the monthly run.
- **↔ 08 CRM:** `billing.*` lives on the household record; Stripe is the processor, the
  CRM is the truth.
- **↔ 10 compliance:** operator payouts and the 1099 trail are the contractor side; this
  stage is the customer side. Keep them distinct.
