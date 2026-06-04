# Skills demonstrated

A map from the go-to-market, revenue-ops, and small-business skills this workflow exercises to
the actual files that prove them. Nothing here is aspirational — every line points at a file you
can open.

It's the business-side companion to `localDNS`'s engineering skills doc: that one proves the
tech; this one proves the machine that sells, delivers, and bills it.

---

## Contents

- [0. Go-to-market & growth](#0-go-to-market--growth)
- [A. Sales, onboarding & customer ops](#a-sales-onboarding--customer-ops)
- [B. Revenue operations & integration](#b-revenue-operations--integration)
- [C. Finance, compliance & the gig workforce](#c-finance-compliance--the-gig-workforce)
- [1. Professional background (beyond this repo)](#1-professional-background-beyond-this-repo)

---

## 0. Go-to-market & growth

- **Category design** — owning one analogy ("pest control for your internet") so a market that
  doesn't know it has a problem can be taught that it does, in words anyone gets.
  → `02-demand-generation/category-education.md`, `00-brand-identity/the-pitch.md`
- **Local / geo demand gen** — filling one neighborhood at a time into a profitable route;
  density as the unit of marketing, not reach.
  → `02-demand-generation/geo-targeting.md`
- **Funnel design & conversion** — website → booking form → self-booking → demo, with the
  refer-a-neighbor loop built into the monthly statement.
  → `03-funnels-and-capture/README.md`, `03-funnels-and-capture/intake-form.md`
- **Brand systems & messaging** — one brand kit every surface inherits, plus the actual pitch
  (the one-liner, the elevator, the price talk) a rep can use today.
  → `00-brand-identity/brand-kit.md`, `00-brand-identity/the-pitch.md`
- **Web presence** — a multi-surface storefront (website, blog, Google Business listing) plus a
  live gallery of the real product.
  → `01-web-presence/README.md`, `01-web-presence/site-map.md`
- **Email & lifecycle marketing** — list hygiene, segmentation off the master list, consent
  discipline, and the copy written and ready to send.
  → `02-demand-generation/email-lists.md`

---

## A. Sales, onboarding & customer ops

- **Consultative selling** — a discovery consult → scoped quote → setup fee → close, with a real
  objection bank and a worked example quote.
  → `05-sales-and-onboarding/discovery-call.md`, `05-sales-and-onboarding/quote-template.md`
- **Phone & front-desk ops** — a business line, hours, greeting, routing, and a call-logging
  habit that writes back to the customer list, with the actual scripts.
  → `04-phone-and-comms/README.md`, `04-phone-and-comms/call-scripts.md`
- **Recurring service delivery** — turning a one-off install into a monthly artifact (the
  statement) sent by email, mail, and QR.
  → `06-statements-delivery/README.md`, `06-statements-delivery/monthly-run.md`
- **Self-service scheduling** — Setmore self-booking wired into both the customer funnel and the
  operator-interview funnel.
  → `03-funnels-and-capture/README.md`, `09-recruiting-and-guild/operator-funnel.md`

---

## B. Revenue operations & integration

- **One master list** — a single shared definition for households, operators, and routes that
  every stage reads and writes; no shadow spreadsheets.
  → `08-client-list-and-crm/schema.md`, `08-client-list-and-crm/data/sample-roster.json`
- **Workflow automation** — mapping every stage-to-stage hand-off to an automation so a
  customer's info is never retyped between tools.
  → `11-automations/automation-map.md`
- **Billing & receivables** — setup fee + monthly plans, gentle dunning, reconciliation, and
  gating delivery on a paid account.
  → `07-payments-receivables/README.md`, `07-payments-receivables/receivables.md`
- **Data-driven documents** — reusing `localDNS`'s data-file → statement tool as the delivery
  engine instead of rebuilding it.
  → `06-statements-delivery/README.md`, `06-statements-delivery/monthly-run.md`
- **Docs that check themselves** — the whole workflow is a version-controlled playbook where
  every cross-link is checked automatically, so the map can't quietly rot.
  → `tools/check-docs.py`, `CLAUDE.md`, `11-automations/automation-map.md`

---

## C. Finance, compliance & the gig workforce

- **1099 contractor lifecycle** — W-9 collection, the agreement, payment tracking, and filing
  the 1099-NEC by the Jan 31 deadline.
  → `10-gig-workers-compliance/1099-checklist.md`,
  `10-gig-workers-compliance/contractor-agreement-outline.md`
- **Classification awareness** — documenting the 1099 path while flagging misclassification as
  the real risk to confirm with a lawyer.
  → `10-gig-workers-compliance/README.md`
- **Trust as infrastructure** — operator vetting, background checks, and bonding as the
  headline, not overhead.
  → `09-recruiting-and-guild/vetting-checklist.md`
- **The conversion flywheel** — the customer→operator path that turns a statement recipient into
  a dues-paying member, with the recruit's-eye view and the earnings math.
  → `09-recruiting-and-guild/operator-funnel.md`, `09-recruiting-and-guild/operator-day-one.md`

---

## 1. Professional background (beyond this repo)

Skills from prior work that inform this workflow but aren't directly exercised by it:
PensionPro; Salesforce (custom dashboards, validated reports, workflow automation); advanced
Excel (XLOOKUP, macros, pivot tables); ESOP administration; TValue 6 (amortization); Microsoft
Access; SharePoint; the Office suite. REST and Claude API integration for compliance and
document workflows (also exercised in `localDNS`).
