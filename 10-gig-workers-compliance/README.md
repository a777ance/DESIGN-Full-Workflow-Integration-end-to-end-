# 10 — Gig workers & compliance

**Lives in:** a 1099 / payroll platform (Gusto / Track1099) + e-sign.
**Go-live / sync:** collect the W-9; pay contractors; file 1099-NEC by Jan 31.

The back office for a gig workforce. Operators (and any sub-contracted "workers") are
independent businesses billing customers directly — structurally a **1099-NEC**
relationship, which is what keeps the platform light.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`1099-checklist.md`](1099-checklist.md) | W-9 → payout tracking → 1099-NEC filing, in order |
| [`contractor-agreement-outline.md`](contractor-agreement-outline.md) | The agreement's required sections |

## The 1099 path (the documented flow)

```
onboarding (09) ─► collect W-9  ─► e-sign contractor agreement  ─► [now payable]
       │                                                              │
       └─ status active (09) ───────────────────────────────────────►│
                                                                      ▼
   through the year: track every payout on operator.tax.ytd_paid (08)
                                                                      │
                                          year end ─► 1099-NEC by Jan 31 for anyone ≥ threshold
```

## The two hard gates

1. **No payout without a W-9 on file.** Paying before collecting the W-9 makes the
   year-end 1099-NEC impossible (or triggers backup withholding) — it's a `BLOCKER`
   ([LAUNCH-NOTES #13](../LAUNCH-NOTES.md#13-contractor-paid-without-a-w-9-on-file)). W-9 is
   step 1 of [`1099-checklist.md`](1099-checklist.md).
2. **File 1099-NEC by Jan 31** for every contractor paid ≥ the IRS threshold
   (`CHANGE_ME` — confirm the current-year figure; historically $600).

## The honest risk — worker classification

If the platform starts directing *how* operators work — mandated routes, scripts,
pricing — heavily enough, a worker-classification challenge could reclassify them as
employees (back taxes, penalties). This is a **legal judgment, not a config value**: this
repo documents the 1099 path and tells you to **confirm classification with counsel before
scaling** ([LAUNCH-NOTES #14](../LAUNCH-NOTES.md#14-worker-misclassification)). Better to
flag it loudly than to pretend the line is obvious.

## Distinct from customer billing (07)

Customer money (membership, retainer, setup fee) is stage 07. **Contractor money**
(operator payouts, dues offsets) is here, and the two ledgers stay separate because they
feed different tax treatments. Keep them from mixing in reconciliation.

## Hand-offs

- **← 09 recruiting:** an operator entering `active` triggers W-9 + agreement collection.
- **↔ 08 CRM:** the 1099 trail lives on `operator.tax`.
- **↔ 07 payments:** distinct ledger; reconciled separately.
