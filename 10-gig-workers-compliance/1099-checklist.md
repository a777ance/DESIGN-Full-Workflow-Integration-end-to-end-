# 1099 contractor checklist

The ordered steps from onboarding an operator to filing their 1099-NEC. Writes to the
record at `operator.tax` (`../08-client-list-and-crm/schema.md`). **Not tax advice** —
confirm current thresholds, forms, and worker classification with counsel/CPA
([LAUNCH-NOTES #14](../LAUNCH-NOTES.md#14-worker-misclassification)).

---

## 1. At onboarding (before the first payout — hard gate)

- [ ] **Collect Form W-9** from the operator (legal name, TIN, address). Store securely —
      **never in git** (it's PII).
- [ ] Set `operator.tax.w9_on_file = true`, `w9_ts`, and `tin_last4` (last 4 only on the
      record; the full TIN lives in the payroll platform, not the CRM).
- [ ] E-sign the **contractor agreement** ([`contractor-agreement-outline.md`](contractor-agreement-outline.md));
      set `operator.vetting.agreement_signed_ts` (09).
- [ ] Confirm the operator is `status = active` (09). **No W-9 → not payable.**

## 2. Through the year (every payout)

- [ ] Record each payout in the payroll/1099 platform.
- [ ] Increment `operator.tax.ytd_paid` (keep it reconciled to the platform monthly).
- [ ] Keep operator-payout records **separate** from customer receivables (07).

## 3. Year end

- [ ] For each operator with `ytd_paid ≥` the IRS threshold (`CHANGE_ME`; historically
      $600), prepare a **1099-NEC**.
- [ ] **File by Jan 31** (to the contractor and the IRS).
- [ ] Set `operator.tax.form_1099_filed_ts`.
- [ ] Issue any state filings required (varies by state — confirm).

## Data-handling rules

- W-9s and full TINs live in the payroll platform (access-controlled), **not** the CRM
  and **not** git. The CRM stores only `tin_last4` and the booleans/timestamps above.
- `.gitignore` already excludes `*-private.*` and `secrets/`; treat any tax document as
  one of those.

## Why these gates exist

- W-9-first makes January's filing a button, not a scramble.
- The threshold check prevents both over- and under-filing.
- The separate ledger keeps customer revenue and contractor expense from contaminating
  each other at tax time.
