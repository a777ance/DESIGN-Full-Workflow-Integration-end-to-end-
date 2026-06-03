# Skills demonstrated

This document maps the go-to-market, RevOps, and small-business operations skills
exercised in formalizing this workflow to the concrete artifacts in the repo. Every
claim below points at the file(s) that prove it — nothing here is aspirational.

It is the business-operations companion to `localDNS`'s engineering `SKILLS.md`: that
one proves the stack; this one proves the machine that sells, delivers, and bills it.

---

## Contents

- [0. Go-to-market & growth](#0-go-to-market--growth)
- [A. Sales, onboarding & customer ops](#a-sales-onboarding--customer-ops)
- [B. Revenue operations & integration](#b-revenue-operations--integration)
- [C. Finance, compliance & the gig workforce](#c-finance-compliance--the-gig-workforce)
- [1. Professional background (beyond this repo)](#1-professional-background-beyond-this-repo)

---

## 0. Go-to-market & growth

- **Category design** — owning an analogy ("pest control for your network") so a
  market that doesn't know it has a problem can be taught it does.
  → `02-demand-generation/README.md`, `02-demand-generation/category-education.md`
- **Local / geo-targeted demand gen** — zip-code-at-a-time clustering into profitable
  routes; density as the unit of marketing efficiency (the DoorDash-batching lesson).
  → `02-demand-generation/geo-targeting.md`
- **Funnel design & conversion** — landing page → intake form → self-booking → demo,
  with the referral loop surfaced inside the monthly Statement.
  → `03-funnels-and-capture/README.md`, `03-funnels-and-capture/intake-form.md`
- **Brand systems** — a single brand kit (logo, palette, voice, slogans, jingle brief)
  that every downstream surface inherits.
  → `00-brand-identity/brand-kit.md`, `00-brand-identity/slogans-and-jingles.md`
- **Web presence** — multi-platform storefront (Squarespace, WordPress, Google Business
  Profile) plus a first-party published artifact gallery.
  → `01-web-presence/README.md`, `01-web-presence/site-map.md`
- **Email lifecycle marketing** — list hygiene, segmentation off the system of record,
  consent discipline.
  → `02-demand-generation/email-lists.md`

---

## A. Sales, onboarding & customer ops

- **Consultative sales** — discovery call → scoped quote → setup fee → close, with a
  proposal/e-sign step and a clean handoff to provisioning.
  → `05-sales-and-onboarding/README.md`, `05-sales-and-onboarding/onboarding-checklist.md`
- **Telephony & front-desk ops** — business line, hours, greeting, routing, and a
  call-logging discipline that writes back to the CRM.
  → `04-phone-and-comms/README.md`, `04-phone-and-comms/call-scripts.md`
- **Service delivery on a cadence** — turning a one-off install into a recurring monthly
  artifact (the Statement) delivered by email, print/mail, and QR.
  → `06-statements-delivery/README.md`, `06-statements-delivery/monthly-run.md`
- **Self-service scheduling** — Setmore self-booking wired into both the customer funnel
  and the operator-interview funnel.
  → `03-funnels-and-capture/README.md`, `09-recruiting-and-guild/README.md`

---

## B. Revenue operations & integration

- **System-of-record design** — one normalized schema (household / operator / route)
  that every stage reads and writes; no shadow spreadsheets.
  → `08-client-list-and-crm/schema.md`, `08-client-list-and-crm/data/sample-roster.json`
- **Workflow automation / integration** — mapping each stage→stage hand-off to an
  automation so no record is ever retyped between tools.
  → `11-automations/automation-map.md`
- **Billing & receivables** — setup fee + retainer plans, dunning, reconciliation, and
  gating Statement delivery on a paid account.
  → `07-payments-receivables/README.md`, `07-payments-receivables/receivables.md`
- **Data-driven document generation** — reusing `localDNS`'s JSON→HTML Statement
  pipeline as the delivery engine instead of rebuilding it.
  → `06-statements-delivery/README.md`, `06-statements-delivery/monthly-run.md`
- **Docs-as-system / self-verifying integration map** — the whole workflow is a
  version-controlled spec where every cross-reference is link-checked in CI, so the map
  can't silently rot (the analog of `localDNS`'s infra-as-config discipline).
  → `tools/check-docs.py`, `CLAUDE.md`, `11-automations/automation-map.md`

---

## C. Finance, compliance & the gig workforce

- **1099 contractor lifecycle** — W-9 collection, contractor agreement, payout records,
  and 1099-NEC filing by the Jan 31 deadline.
  → `10-gig-workers-compliance/1099-checklist.md`,
  `10-gig-workers-compliance/contractor-agreement-outline.md`
- **Worker-classification awareness** — documenting the 1099 path while flagging
  misclassification as the real risk to confirm with counsel.
  → `10-gig-workers-compliance/README.md`
- **Trust infrastructure** — operator vetting, background-check and bonding posture as
  the guild's headline, not overhead.
  → `09-recruiting-and-guild/vetting-checklist.md`
- **The conversion flywheel** — instrumenting the customer→operator path that turns a
  Statement recipient into a dues-paying member.
  → `09-recruiting-and-guild/operator-funnel.md`

---

## 1. Professional background (beyond this repo)

Domain skills from prior work that inform this workflow but are not exercised by it
directly: PensionPro; Salesforce (custom dashboards, validated reports, workflow
automation); advanced Microsoft Excel (XLOOKUP, macros, pivot tables); ESOP
administration; TValue 6 (amortization); Microsoft Access; SharePoint; the Microsoft
Office Suite. REST and Claude API integration for compliance and document workflows
(also exercised in `localDNS`).
