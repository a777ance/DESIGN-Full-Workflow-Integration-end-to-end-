# Fresh-Launch Simulation — Known Break Points

What we found when we walked the whole funnel from an empty start — no customers, no
operators — all the way to a first paying household (and a first customer who became an
operator). Every place a customer can get stuck, a hand-off can drop, or money or compliance
can go wrong is listed below with how bad it is and how to fix it. Items are numbered in the
order you'd hit them going down the funnel (stages 00–11).

Each `Location:` points at the stage folder where the fix lives, so a fixed item is one click
away. Think of it as the business version of a pre-flight check: not "does the code run," but
"can a real household get from a stranger to a paid statement without falling through a gap."

Severity tags: `BLOCKER` (no revenue until it's fixed) · `HIGH` · `MEDIUM` · `MINOR` ·
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
With no single brand kit, the website, the Google listing, the booking form, and the statement
each pick their own logo, voice, and color — and a trust business that looks mismatched reads
"amateur," which is fatal here.
**Fix:** the brand kit is stage 00, and every surface links to it instead of re-pasting its own.
**--RESOLVED--** by `brand-kit.md`.

### 2. Statement gallery link points at a mockup, not the live Pages site
**Severity:** `MINOR` · **Location:** [`01-web-presence/`](01-web-presence/)
Linking the website to a screenshot of a statement instead of the live gallery loses the
scan-and-scroll, and it drifts out of date the moment a real statement changes.
**Fix:** link to `https://a777ance.github.io/localDNS/`, served live from `localDNS`.
**--RESOLVED--** in `01-web-presence/site-map.md`.

---

## Demand → capture (02–03)

### 3. Intake form fields do not map to the CRM schema
**Severity:** `BLOCKER` · **Location:** [`03-funnels-and-capture/`](03-funnels-and-capture/)
If the booking form asks for things the customer list can't hold (or skips things it needs), the
lead is born malformed and the whole rest of the funnel stalls on it.
**Fix:** every form question maps one-to-one to `08-client-list-and-crm/schema.md`; change them
together. **--RESOLVED--** — the form is annotated with where each answer lands.

### 4. Geo-targeting buys reach instead of route density
**Severity:** `HIGH` · **Location:** [`02-demand-generation/`](02-demand-generation/)
Buying broad reach scatters customers across the metro; the operator burns the day driving and
the math never closes. **Fix:** buy one neighborhood's ZIPs at a time and track *homes on the
route* as the number that matters (`geo-targeting.md`). **Open** until a real block hits the
density target.

### 5. Email list collected without consent record
**Severity:** `HIGH` `COMPLIANCE` · **Location:** [`02-demand-generation/`](02-demand-generation/)
A trust business can't afford a spam complaint, and the consent rules (CAN-SPAM) are real.
**Fix:** consent + where + when are recorded on the customer's record at opt-in, and the list is
built off the master list, never a bought import (`email-lists.md`).

---

## Sales → provision (04–05)

### 6. Call not logged to the CRM — consult starts cold
**Severity:** `MEDIUM` · **Location:** [`04-phone-and-comms/`](04-phone-and-comms/)
If the inbound call isn't written down, the consult repeats questions the prospect already
answered — exactly the kind of small disrespect that sinks a trust pitch. **Fix:** every call
gets jotted onto the record; the consult picks up from there. **--RESOLVED--** via the
call-logging habit in `call-scripts.md` + an automation (11).

### 7. Close → provision hand-off is undocumented
**Severity:** `HIGH` · **Location:** [`05-sales-and-onboarding/`](05-sales-and-onboarding/)
The riskiest gap: a deal that closes and then nobody sets up the box — a refund waiting to
happen. **Fix:** the onboarding checklist makes "set up the box, per `localDNS`'s guide" a real,
checked-off step triggered on "yes." **--RESOLVED--** in `onboarding-checklist.md`.

---

## Deliver → bill (06–07)

### 8. Statement forked/edited in this repo instead of generated from localDNS
**Severity:** `BLOCKER` · **Location:** [`06-statements-delivery/`](06-statements-delivery/)
Hand-editing a copy of the statement here creates a second version that drifts from the real
one — the exact problem stage 00 exists to prevent — and it can print a stale or made-up figure.
**Fix:** stage 06 is *delivery only*; the statement is always built by `localDNS`'s tool.
**Open as a standing rule** — enforced by review, not code.

### 9. Statement delivered to an unpaid account
**Severity:** `HIGH` · **Location:** [`07-payments-receivables/`](07-payments-receivables/)
Sending the proof of value to someone who stopped paying gives away the goods and teaches
non-payment. **Fix:** delivery (06) only happens for a paid-up account (07), checked
automatically (11). **--RESOLVED--** — the gate is specified in
`07-payments-receivables/README.md`.

### 10. Statement prints figures the box did not measure
**Severity:** `HIGH` `ONGOING CAUTION` · **Location:** [`06-statements-delivery/`](06-statements-delivery/)
The by-category gigabyte breakdown and the neighbor comparison aren't built yet (per `localDNS`).
Printing them on a document people keep is dishonest. **Fix:** keep each statement to the figures
we actually measure until those datasets are real. **Ongoing** — inherited from `localDNS`.

---

## Flywheel → compliance (08–11)

### 11. Shadow spreadsheet becomes a second source of truth
**Severity:** `MEDIUM` · **Location:** [`08-client-list-and-crm/`](08-client-list-and-crm/)
An operator's private "my homes" spreadsheet drifts from the master list and quietly breaks
billing and statements. **Fix:** one entry per home/operator/route on the master list; a fact
exists only if it's in `schema.md`. **Open** — it's cultural, reinforced by making the master
list the only thing that feeds the statement tool.

### 12. Operator onboarded without vetting
**Severity:** `HIGH` `SECURITY` · **Location:** [`09-recruiting-and-guild/`](09-recruiting-and-guild/)
Vetting *is* the trust pitch; putting an unvetted operator onto people's home networks torches
the whole moat in one bad incident. **Fix:** the vetting checklist gates onboarding;
background-check + bonding is mandatory, not optional. **Open** until the "guild-certified"
standard is finalized with a lawyer.

### 13. Contractor paid without a W-9 on file
**Severity:** `BLOCKER` `COMPLIANCE` · **Location:** [`10-gig-workers-compliance/`](10-gig-workers-compliance/)
Paying an operator before collecting a W-9 makes the year-end 1099 impossible (or triggers
backup withholding). **Fix:** the W-9 is collected at onboarding, before the first payment —
step 1 of `1099-checklist.md`. **--RESOLVED--** as a documented gate.

### 14. Worker misclassification
**Severity:** `HIGH` `COMPLIANCE` `ONGOING CAUTION` · **Location:** [`10-gig-workers-compliance/`](10-gig-workers-compliance/)
If the platform dictates *how* operators work too tightly, a 1099 contractor can be reclassified
as an employee — back taxes, penalties, the lot. **Fix:** document the 1099 path and **confirm
the classification with a lawyer before scaling.** It's a legal call, not a repo setting.
**Ongoing.**

### 15. A stage hand-off requires a human to retype data
**Severity:** `MEDIUM` · **Location:** [`11-automations/`](11-automations/)
Any manual copy-paste between tools is slow, drifts, and doesn't scale past a handful of homes.
**Fix:** every hand-off on the automation map has an automation; a manual step is logged as a bug
to close. **Open** — the map exists; the individual automations get switched on as each tool
goes live.

### 16. Real credentials or client PII committed to git
**Severity:** `BLOCKER` `SECURITY` · **Location:** [`.gitignore`](.gitignore)
This is an internal repo; a leaked key or a real customer record is a serious breach.
**Fix:** `.gitignore` excludes `.env`/secrets/real-roster files; every committed value is a
`CHANGE_ME` placeholder and all sample data is made up. **--RESOLVED--**.

---

## Audit Log

- **Initial walkthrough** — walked the funnel end to end from an empty start. Found 16 break
  points; fixed the ones fixable in the repo (1, 2, 3, 6, 7, 9, 13, 16) and left the rest open
  with an owner and a direction. Items 4, 8, 11, 12, 15 are operational/cultural and close as
  each live tool gets stood up; items 5, 10, 14 carry ongoing compliance/honesty caution
  inherited from `MARKETING` and `localDNS`.

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
