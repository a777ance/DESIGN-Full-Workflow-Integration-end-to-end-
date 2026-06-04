# 10 — Gig workers & compliance

**Lives in:** a 1099 / payroll tool (Gusto / Track1099) + e-sign.
**Go-live:** collect the W-9; pay operators; file the 1099-NEC by January 31.

The back office for the people doing the work. Operators run their own homes and bill their own
customers — they're independent businesses, not employees. That keeps the platform light, and it
means we pay them as **1099 contractors**, with a couple of rules we don't bend.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`1099-checklist.md`](1099-checklist.md) | W-9 → tracking payments → filing the 1099, in order |
| [`contractor-agreement-outline.md`](contractor-agreement-outline.md) | What the operator agreement has to cover |

## The path

```
onboarding (09) ─► collect W-9 ─► sign the agreement ─► now payable
       │                                                    │
       └─ operator goes active (09) ───────────────────────►│
                                                            ▼
   through the year: track every payment to them
                                                            │
                              year-end ─► file a 1099-NEC by Jan 31 for anyone paid ≥ the threshold
```

## Two rules we don't bend

1. **No payment before the W-9 is in hand.** Pay someone first and you've made January's
   filing a nightmare (or you owe backup withholding). The W-9 is step one — a hard stop
   ([LAUNCH-NOTES #13](../LAUNCH-NOTES.md#13-contractor-paid-without-a-w-9-on-file)).
2. **File the 1099-NEC by January 31** for every operator paid at or above the IRS threshold
   (`CHANGE_ME` — confirm the current number; it's been $600 for years).

## The honest risk — are they really contractors?

If the platform starts dictating *how* operators work — forced routes, scripts, set prices —
hard enough, a regulator can decide they're actually employees, with back taxes and penalties to
match. **This is a legal call, not a setting in a tool.** This repo documents the contractor path
and tells you plainly to **check the classification with a lawyer before scaling**
([LAUNCH-NOTES #14](../LAUNCH-NOTES.md#14-worker-misclassification)). Better to flag it loudly than
pretend the line is obvious.

## Keep it separate from customer money (07)

Money coming **in** from customers (membership, monthly, setup fee) is stage 07. Money going
**out** to operators is here. The two ledgers stay separate, because they're taxed completely
differently and must never get tangled at year-end.

## Hand-offs

- **← 09 recruiting:** an operator going active kicks off collecting the W-9 + agreement.
- **↔ 08 customer list:** the 1099 trail lives on the operator's record (`operator.tax`).
- **↔ 07 payments:** a separate ledger, reconciled on its own.
