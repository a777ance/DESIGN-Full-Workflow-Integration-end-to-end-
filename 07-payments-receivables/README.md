# 07 — Payments & receivables

**Lives in:** Stripe (or a similar card processor) + your bookkeeping.
**Go-live:** set up the plan; collect the $175 setup fee + the $32/month; keep the books straight.

Getting paid — and one rule that protects the whole model: **the statement only goes to people
who've paid.** There are two charges, kept separate on purpose because they answer two different
questions in the customer's head.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`receivables.md`](receivables.md) | The billing states, gentle dunning, monthly reconciliation, and the paid-only gate |
| [`data/sample-receivables.csv`](data/sample-receivables.csv) | A few made-up billing rows |

## Two charges

| Charge | When | Working number | Why it's its own line |
| ------ | ---- | -------------- | --------------------- |
| **Setup fee** | Once, when they sign (05) | $175, never discounted | Pays for the real visit + install; answers "is this a serious service?" |
| **Monthly** | Every month | $32 (or $38 for a heavier home) | The ongoing quiet + the statement; answers "is it worth keeping?" |

> Two money flows in the guild (`MARKETING`): the **platform** collects the customer's
> membership and the operator's dues; the **operator** bills the customer for the service
> directly. This stage handles the platform side and the customer's plan. The operator's own
> billing is theirs, and the operator's dues are over in stage 09.

## The paid-only rule (the one that matters)

The statement is the proof of value. Send it to someone who stopped paying and you've handed
over the goods for free and taught them they don't need to pay to keep getting it. So **a
statement only goes out to an account that's paid up**, and that check happens automatically
(11), not by an operator remembering ([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)).
Chasing a missed payment is *gentle* — we're about keeping people, not collections — but the
gate is firm.

## What state an account can be in

```
new ─►(setup fee paid)─► paid up ─►(a charge fails)─► behind ─►(card fixed)─► paid up
                                          │
                                          └─►(no luck after a couple weeks)─► canceled  ──► statements stop
```

The full handling and the monthly reconciliation are in [`receivables.md`](receivables.md).

## Hand-offs

- **← 05 sales:** on "yes," set up the customer + plan and collect the setup fee.
- **→ 06 statements:** tells the monthly run who's paid up and who to skip.
- **↔ 08 customer list:** the billing status lives on the customer's record; Stripe moves the
  money, but the record is the truth.
- **↔ 10 compliance:** paying *operators* (and their taxes) is a separate ledger — keep the two
  from mixing.
