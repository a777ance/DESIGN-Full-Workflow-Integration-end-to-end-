# Fresh-Launch Simulation — Known Break Points

Results of a full walkthrough of the workflow, simulating taking the guild from an empty
funnel to a first paying customer (and a first converted operator). Every point where a
record can stall, a hand-off can drop, or money/compliance can go wrong is catalogued
below with its severity and fix. Items are numbered and ordered by where they surface
along the funnel (stages 00–11), mirroring `localDNS/INSTALL-NOTES.md`.

Each `Location:` points at the stage folder where the fix lives, so a resolved-in-repo
item is one click away. This is the business analog of `localDNS`'s install simulation:
there it was "fresh Ubuntu → running stack," here it is "empty funnel → paid Statement."

Severity tags: `BLOCKER` (no revenue until fixed) · `HIGH` · `MEDIUM` · `MINOR` ·
`SECURITY` · `COMPLIANCE` · `ONGOING CAUTION`.

---

## Contents

**Fresh-launch break points** (in funnel order)

**Foundation (00–01)**
- [1. No brand kit means every surface drifts](#1-no-brand-kit-means-every-surface-drifts) `MEDIUM` — **--RESOLVED--**
- [2. Statement gallery link points at a mockup, not the live Pages site](#2-statement-gallery-link-points-at-a-mockup-not-the-live-pages-site) `MINOR` — **--RESOLVED--**

**Demand → capture (02–03)**
- [3. Intake form fields do not map to the CRM schema](#3-intake-form-fields-do-not-map-to-the-crm-schema) `BLOCKER` — **--RESOLVED--**
- [4. Geo-targeting buys reach instead of route density](#4-geo-targeting-buys-reach-instead-of-route-density) `HIGH`
- [5. Email list collected without consent record](#5-email-list-collected-without-consent-record) `HIGH` `COMPLIANCE`

**Sales → provision (04–05)**
- [6. Call not logged to the CRM — consult starts cold](#6-call-not-logged-to-the-crm--consult-starts-cold) `MEDIUM` — **--RESOLVED--**
- [7. Close → provision hand-off is undocumented](#7-close--provision-hand-off-is-undocumented) `HIGH` — **--RESOLVED--**

**Deliver → bill (06–07)**
- [8. Statement forked/edited in this repo instead of generated from localDNS](#8-statement-forkededited-in-this-repo-instead-of-generated-from-localdns) `BLOCKER`
- [9. Statement delivered to an unpaid account](#9-statement-delivered-to-an-unpaid-account) `HIGH` — **--RESOLVED--**
- [10. Statement prints figures the box did not measure](#10-statement-prints-figures-the-box-did-not-measure) `HIGH` `ONGOING CAUTION`

**Flywheel → compliance (08–11)**
- [11. Shadow spreadsheet becomes a second source of truth](#11-shadow-spreadsheet-becomes-a-second-source-of-truth) `MEDIUM`
- [12. Operator onboarded without vetting](#12-operator-onboarded-without-vetting) `HIGH` `SECURITY`
- [13. Contractor paid without a W-9 on file](#13-contractor-paid-without-a-w-9-on-file) `BLOCKER` `COMPLIANCE`
- [14. Worker misclassification](#14-worker-misclassification) `HIGH` `COMPLIANCE` `ONGOING CAUTION`
- [15. A stage hand-off requires a human to retype data](#15-a-stage-hand-off-requires-a-human-to-retype-data) `MEDIUM`
- [16. Real credentials or client PII committed to git](#16-real-credentials-or-client-pii-committed-to-git) `BLOCKER` `SECURITY` — **--RESOLVED--**

**Other**
- [Audit Log](#audit-log)
- [Summary Table](#summary-table)

---

## Foundation (00–01)

### 1. No brand kit means every surface drifts
**Severity:** `MEDIUM` · **Location:** [`00-brand-identity/`](00-brand-identity/)
Without one inherited brand kit, the Squarespace site, the GBP, the intake form, and the
Statement each pick their own logo/voice/color — and a trust business reads "amateur."
**Fix:** the brand kit is stage 00 and every surface links to it rather than re-pasting.
**--RESOLVED--** by `brand-kit.md`.

### 2. Statement gallery link points at a mockup, not the live Pages site
**Severity:** `MINOR` · **Location:** [`01-web-presence/`](01-web-presence/)
Linking the marketing site to a screenshot of the Statement instead of the live gallery
loses the QR/scroll experience and drifts from the real artifact.
**Fix:** link to `https://a777ance.github.io/localDNS/`, served from `localDNS` by Pages.
**--RESOLVED--** in `01-web-presence/site-map.md`.

---

## Demand → capture (02–03)

### 3. Intake form fields do not map to the CRM schema
**Severity:** `BLOCKER` · **Location:** [`03-funnels-and-capture/`](03-funnels-and-capture/)
If the intake form asks for fields the schema cannot store (or omits fields the schema
requires), the record is born malformed and the whole downstream funnel stalls on it.
**Fix:** every form field maps one-to-one to `08-client-list-and-crm/schema.md`; change
them together. **--RESOLVED--** — `intake-form.md` is annotated with its schema target.

### 4. Geo-targeting buys reach instead of route density
**Severity:** `HIGH` · **Location:** [`02-demand-generation/`](02-demand-generation/)
Buying broad reach scatters customers across a metro; the operator burns the day driving
and the unit economics never close. **Fix:** buy zip-code-at-a-time and track *homes per
route* as the unit metric (`geo-targeting.md`). **Open** until a real route shows the
target density.

### 5. Email list collected without consent record
**Severity:** `HIGH` `COMPLIANCE` · **Location:** [`02-demand-generation/`](02-demand-generation/)
A trust business cannot afford a spam complaint, and CAN-SPAM/consent obligations are
real. **Fix:** consent + source + timestamp are captured on the record at opt-in;
list is segmented off the system of record, never a scraped import (`email-lists.md`).

---

## Sales → provision (04–05)

### 6. Call not logged to the CRM — consult starts cold
**Severity:** `MEDIUM` · **Location:** [`04-phone-and-comms/`](04-phone-and-comms/)
If the inbound call is not written to the record, the consult repeats questions the
prospect already answered — corrosive for a trust pitch. **Fix:** every call is logged
to the CRM record; the consult opens from that history. **--RESOLVED--** via the
call-logging discipline in `call-scripts.md` + an automation (stage 11).

### 7. Close → provision hand-off is undocumented
**Severity:** `HIGH` · **Location:** [`05-sales-and-onboarding/`](05-sales-and-onboarding/)
The riskiest seam: a closed deal that nobody provisions is a refund waiting to happen.
**Fix:** the onboarding checklist makes "provision the t630 per `localDNS` setup guide"
an explicit, owned step triggered on close. **--RESOLVED--** in `onboarding-checklist.md`.

---

## Deliver → bill (06–07)

### 8. Statement forked/edited in this repo instead of generated from localDNS
**Severity:** `BLOCKER` · **Location:** [`06-statements-delivery/`](06-statements-delivery/)
Re-creating or hand-editing the Statement here creates a second source of truth and the
exact drift stage 00 exists to prevent — and it can print stale or invented figures.
**Fix:** stage 06 is a *delivery runbook only*; the artifact is always generated from
`localDNS/docs/statements/tools/`. **Open as a standing rule** — enforced by review, not
code.

### 9. Statement delivered to an unpaid account
**Severity:** `HIGH` · **Location:** [`07-payments-receivables/`](07-payments-receivables/)
Sending the value receipt to a churned/unpaid account gives away the proof of value and
trains non-payment. **Fix:** delivery (06) is gated on a paid account in stage 07,
enforced by an automation (11). **--RESOLVED--** — the gate is specified in
`07-payments-receivables/README.md`.

### 10. Statement prints figures the box did not measure
**Severity:** `HIGH` `ONGOING CAUTION` · **Location:** [`06-statements-delivery/`](06-statements-delivery/)
Per-category GB volume and peer-average benchmarks are *not yet real* (per `localDNS`'s
"Data sourcing" table). Printing them on a kept document is dishonest. **Fix:** scope
each Statement to figures Pi-hole/Uptime Kuma/`wg` actually produce until the
flow-accounting + cohort datasets are stood up. **Ongoing** — inherited from `localDNS`.

---

## Flywheel → compliance (08–11)

### 11. Shadow spreadsheet becomes a second source of truth
**Severity:** `MEDIUM` · **Location:** [`08-client-list-and-crm/`](08-client-list-and-crm/)
An operator's private "my homes" spreadsheet drifts from the CRM and quietly breaks
billing and Statement generation. **Fix:** one record per home/operator/route in the
CRM; a field exists only if it is in `schema.md`. **Open** — cultural, reinforced by
making the CRM the only place that feeds the generator.

### 12. Operator onboarded without vetting
**Severity:** `HIGH` `SECURITY` · **Location:** [`09-recruiting-and-guild/`](09-recruiting-and-guild/)
Vetting *is* the trust pitch; onboarding an unvetted operator into people's home networks
torches the moat in one incident. **Fix:** the vetting checklist gates onboarding;
background-check + bonding posture is mandatory, not optional. **Open** until the
"guild-certified" standard is finalized with counsel.

### 13. Contractor paid without a W-9 on file
**Severity:** `BLOCKER` `COMPLIANCE` · **Location:** [`10-gig-workers-compliance/`](10-gig-workers-compliance/)
Paying a contractor before collecting a W-9 makes the year-end 1099-NEC filing
impossible (or triggers backup withholding). **Fix:** W-9 is collected *at onboarding*,
before the first payout — it is step 1 of `1099-checklist.md`. **--RESOLVED--** as a
documented gate.

### 14. Worker misclassification
**Severity:** `HIGH` `COMPLIANCE` `ONGOING CAUTION` · **Location:** [`10-gig-workers-compliance/`](10-gig-workers-compliance/)
If the platform directs *how* operators work too tightly, a 1099 contractor can be
reclassified as an employee — back taxes, penalties, the lot. **Fix:** document the 1099
path and **confirm classification with counsel before scaling.** This is a legal
judgment, not a repo setting. **Ongoing.**

### 15. A stage hand-off requires a human to retype data
**Severity:** `MEDIUM` · **Location:** [`11-automations/`](11-automations/)
Any manual copy-paste between tools is a dropped packet: it is slow, it drifts, and it
does not scale past a handful of homes. **Fix:** every hand-off in the automation map
has an automation; a manual step is logged as a bug to close. **Open** — the map exists;
individual zaps are stood up as each tool goes live.

### 16. Real credentials or client PII committed to git
**Severity:** `BLOCKER` `SECURITY` · **Location:** [`.gitignore`](.gitignore)
This is an internal repo; a leaked API key or a real client record is a serious breach.
**Fix:** `.gitignore` excludes `.env`/secrets/real-roster files; all committed values are
`CHANGE_ME` placeholders and all sample data is fictional. **--RESOLVED--**.

---

## Audit Log

- **Initial formalization** — walked the funnel end-to-end from an empty state, mirroring
  `localDNS`'s install simulation. Catalogued 16 break points; resolved the ones fixable
  in-repo (1, 2, 3, 6, 7, 9, 13, 16) and left the rest open with an owner and a fix
  direction. Items 4, 8, 11, 12, 15 are operational/cultural and close as each live tool
  is stood up; items 5, 10, 14 carry ongoing compliance/honesty caution inherited from
  `MARKETING` and `localDNS`.

---

## Summary Table

| # | Break point | Severity | Status |
| - | ----------- | -------- | ------ |
| 1 | No brand kit → surfaces drift | `MEDIUM` | RESOLVED |
| 2 | Gallery link → mockup not live site | `MINOR` | RESOLVED |
| 3 | Intake fields ≠ CRM schema | `BLOCKER` | RESOLVED |
| 4 | Geo buys reach not density | `HIGH` | Open |
| 5 | Email list without consent | `HIGH` `COMPLIANCE` | Open |
| 6 | Call not logged to CRM | `MEDIUM` | RESOLVED |
| 7 | Close→provision undocumented | `HIGH` | RESOLVED |
| 8 | Statement forked, not generated | `BLOCKER` | Standing rule |
| 9 | Statement to unpaid account | `HIGH` | RESOLVED |
| 10 | Statement prints unmeasured figures | `HIGH` `ONGOING` | Ongoing |
| 11 | Shadow spreadsheet | `MEDIUM` | Open |
| 12 | Operator onboarded unvetted | `HIGH` `SECURITY` | Open |
| 13 | Contractor paid w/o W-9 | `BLOCKER` `COMPLIANCE` | RESOLVED |
| 14 | Worker misclassification | `HIGH` `COMPLIANCE` | Ongoing |
| 15 | Manual retype between tools | `MEDIUM` | Open |
| 16 | Secrets/PII in git | `BLOCKER` `SECURITY` | RESOLVED |
