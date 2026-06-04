# The 1099 checklist

The steps, in order, from onboarding an operator to filing their 1099-NEC. It writes to the
operator's record (`operator.tax`). **This isn't tax advice** — confirm the current thresholds,
forms, and the contractor-vs-employee question with a CPA or lawyer
([LAUNCH-NOTES #14](../LAUNCH-NOTES.md#14-worker-misclassification)).

---

## 1. At onboarding — before the first payment (hard stop)

- [ ] **Get the W-9** (legal name, taxpayer ID, address). Store it securely — **never in git**,
      it's sensitive personal info.
- [ ] On the record, mark the W-9 on file, the date, and the **last 4** of the tax ID only — the
      full number lives in the payroll tool, not on the customer list.
- [ ] **Sign the contractor agreement** ([`contractor-agreement-outline.md`](contractor-agreement-outline.md));
      save the signed-on date (09).
- [ ] Confirm they're **active** (09). **No W-9 → no payment.**

## 2. Through the year — every payment

- [ ] Record each payment in the payroll/1099 tool.
- [ ] Add it to their year-to-date total on the record (reconcile to the tool monthly).
- [ ] Keep operator payments **separate** from customer income (07).

## 3. Year-end

- [ ] For each operator paid at or above the threshold (`CHANGE_ME`; it's been $600), prepare a
      **1099-NEC**.
- [ ] **File by January 31** — both to the operator and to the IRS.
- [ ] Save the filed date on the record.
- [ ] Handle any state filings too (varies by state — check).

## Handling the sensitive stuff

- W-9s and full tax IDs live in the payroll tool (locked down), **not** on the customer list and
  **not** in git. The record keeps only the last-4 and the dates.
- `.gitignore` already excludes `*-private.*` and `secrets/` — treat any tax document as one of
  those.

## Why the rules are what they are

- W-9-first turns January's filing into a button instead of a scramble.
- The threshold check keeps you from over- or under-filing.
- Separate ledgers keep customer income and operator expense from contaminating each other at
  tax time.
