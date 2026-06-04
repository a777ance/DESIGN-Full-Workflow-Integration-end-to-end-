# CLAUDE.md

Briefing for Claude Code. Read this first — it is the authoritative summary of
the whole workflow. README.md is the complete operations guide and stage-by-stage
reference. workflow-context.md has detailed rationale for non-obvious decisions.

This repo is the **business machine that surrounds the Statements.** The product is
the monthly Statement (see [Section E](#e-the-statements--the-center)); everything
here exists to get a household to its first Statement, keep producing and delivering
it, get paid for it, and convert some recipients into operators who produce Statements
for others. The Statements themselves — the gold standard — live in the public
**[`localDNS`](https://a777ance.github.io/localDNS/)** repo under `docs/statements/`.

---

## Contents

- [0. What this repo is](#0-what-this-repo-is)
- [A. The funnel at a glance](#a-the-funnel-at-a-glance)
- [B. Roles & money flow](#b-roles--money-flow)
- [C. Stage map](#c-stage-map)
- [D. The system of record](#d-the-system-of-record)
- [E. The Statements — the center](#e-the-statements--the-center)
- [1. Known issues & open decisions](#1-known-issues--open-decisions)
- [2. Verification](#2-verification)
- [3. Working philosophy](#3-working-philosophy)
- [4. Further reading](#4-further-reading)

---

## 0. What this repo is

The end-to-end operating system for the A777ance guild: how a stranger becomes a
**customer** (a household receiving a monthly Statement), and how a customer becomes
an **operator** (a guild member producing Statements for a book of homes). Every
folder maps to a stage of that lifecycle and to the live tool where the work actually
happens (see "Stage map" below). Edits here are specs, templates, schemas, and the
integration map — they do not take effect until deployed into the live tool.

**Three repos, one business:**

| Repo | Holds | Visibility |
| ---- | ----- | ---------- |
| **[`localDNS`](https://a777ance.github.io/localDNS/)** | The technical stack **and** the Statement artifacts (`docs/statements/`) — the product | **Public** |
| **`MARKETING`** | The business model, pricing, and guild mechanics — the *why* | **Private** |
| **`DESIGN-…` (this repo)** | The end-to-end workflow that surrounds the Statements — the *how* | **Private / internal** |

**This repo is internal.** Public-facing artifacts (brand, website, the Statements)
are *published from here into* public surfaces; the workflow integration itself —
client list, receivables, recruiting economics, contractor records — is not. Never
commit real credentials or PII: use `CHANGE_ME` placeholders and keep secrets in
`.env` (git-ignored). The sample data committed here is fictional.

---

## A. The funnel at a glance

```
STRANGER  (a household that doesn't know it has a problem)
   │   02 demand-gen — "pest control for your network" · local SEO · geo-targeted · email
   ▼
LEAD ─────► 03 funnel — landing page → intake form → Setmore self-booking → demo
   │   04 phone & comms — answer the call, confirm the visit, the human touch
   ▼
CUSTOMER ─► 05 sales — consult · quote · setup fee · CLOSE
   │            └──► provision the stack ───────────────►  localDNS  (deploy the t630)
   │   07 payments — one-time setup fee + monthly retainer
   ▼
══════════ THE PRODUCT — what they pay for, every month ════════════════════════════
   06  STATEMENTS   ◄── the gold standard · localDNS/docs/statements
       • client  Network Activity Statement   — the "sticker on the door"
       • operator Alliance Member Portfolio    — earning the keep
   delivered by email · printed & mailed · scrollable by QR code
═════════════════════════════════════════════════════════════════════════════════════
   │   the Statement raises a hand:  "Connect in the Alliance"
   ▼
SOME CUSTOMERS ─► 09 recruiting — the customer→operator flywheel · vetting · onboarding
   │   10 compliance — W-9 · 1099-NEC · contractor agreement (gig workers)
   ▼
OPERATOR  (now produces Statements for a book of homes) ──┐
                                                          └─► back to 06, at fleet scale

   00 brand-identity underlies all of it   ·   01 web-presence is the storefront
   08 client-list / CRM is the system of record every stage reads & writes
   11 automations is the glue that moves a record from one stage to the next
```

**Legend:** `NN` → numbered stage folder · `─►` flow direction · `═══` the
pay-for-value boundary — everything above earns the first Statement, everything below
spins the flywheel from it.

---

## B. Roles & money flow

A **two-sided guild** (full rationale in `MARKETING`). Both sides subscribe to the
platform; the service money flows customer→operator directly, like hiring a tradesperson
through a guild.

```
Customer ──platform subscription──▶ A777ance ◀──member dues── Operator
   │                                                              ▲
   └──────────────── pays directly for service ──────────────────┘
```

| Role | Pays | Earns | This repo's job for them |
| ---- | ---- | ----- | ------------------------ |
| **Customer** (household) | Platform membership + their operator, directly | — | Stages 02→07: find them, close them, bill them, deliver the Statement |
| **Operator** (e.g. Jose) | Member dues to the platform | Bills customers directly | Stages 09→10: recruit, vet, onboard, pay as a 1099 contractor |
| **Platform** (A777ance) | — | Both subscriptions | Stages 00, 01, 08, 11: brand, storefront, system of record, automations |

**Incentive invariant:** the operator is on a flat retainer, so **every incident is a
cost, not revenue.** Operator and customer both want a boring, unbreakable network — so
design every stage to make the network *dull* and the *proof of quiet* vivid. The
Statement is that proof.

---

## C. Stage map

Folders are numbered by **funnel order** — the path a household travels from stranger
to Statement, then the path a customer travels from Statement to operator. A folder's
number is its lifecycle position, not a priority ranking. This table maps repo path →
the live tool where the work happens → the action that puts a change live (the analog
of localDNS's deploy-path reload commands).

| Repo path | Lives in (live tool) | Go-live / sync |
| --------- | -------------------- | -------------- |
| `00-brand-identity/` | Figma + brand asset host / press kit | Export assets; update the brand-kit links everything inherits |
| `01-web-presence/` | Squarespace (Circle) · WordPress · Google Business Profile · GitHub Pages (Statements gallery) | Publish site; verify GBP listing; Pages deploys from `localDNS` |
| `02-demand-generation/` | Meta/Google Ads · local SEO · Mailchimp (email lists) | Launch campaign; sync the geo-targeted audience |
| `03-funnels-and-capture/` | Landing pages + intake form + Setmore (self-booking) + demo app | Publish funnel; wire form → CRM (08) via automations (11) |
| `04-phone-and-comms/` | Business line / VoIP (Google Voice / OpenPhone) | Set hours, greeting, call routing; log every call to the CRM |
| `05-sales-and-onboarding/` | CRM + proposal / e-sign → handoff to `localDNS` deploy | Send quote; on close, provision the stack and collect setup fee |
| `06-statements-delivery/` | `localDNS` generator (`docs/statements/`) + email + print/mail + QR | Monthly run; email + mail the Statement; QR codes go live |
| `07-payments-receivables/` | Stripe / payment processor + accounting | Create the plan; collect setup fee + monthly retainer; reconcile |
| `08-client-list-and-crm/` | CRM / Airtable — the **system of record** | Maintain the roster; it feeds the Statement generator and every stage |
| `09-recruiting-and-guild/` | Operator funnel + vetting + Setmore (interviews) | Open applications; run vetting; onboard into the guild |
| `10-gig-workers-compliance/` | 1099 / payroll platform (Gusto / Track1099) + e-sign | Collect W-9; pay contractors; file 1099-NEC by Jan 31 |
| `11-automations/` | Zapier / Make + the `localDNS` pipeline | Enable the zaps that carry a record stage→stage; never hand-copy |

Each folder's own `README.md` is the spec for that stage; the concrete templates,
schemas, and checklists sit beside it (the analog of the live config files in
`localDNS`'s numbered folders).

---

## D. The system of record

`08-client-list-and-crm/` is the single source of truth — the business analog of
`localDNS`'s data-driven generator, where one JSON file per home is the truth a
Statement renders from. **One record per household; one record per operator; one
record per route (a geographic cluster of homes).** Every other stage reads and writes
this record:

```
02 demand-gen ─writes─► lead          08 reads to segment the next campaign
03 funnel     ─writes─► lead + intake  05 reads to run the consult
05 sales      ─writes─► customer       06 reads the roster to generate Statements
07 payments   ─writes─► billing status 06 reads to gate delivery on a paid account
09 recruiting ─writes─► operator        10 reads to file the 1099
```

The schema is defined in `08-client-list-and-crm/schema.md`. **Invariant:** a field is
either in the schema or it does not exist — no stray spreadsheet columns. If a stage
needs a new field, add it to the schema first, the same way `localDNS` keeps all cache
tuning in one `tuning.conf`.

---

## E. The Statements — the center

Everything in this repo surrounds two artifacts, and **this repo does not own them** —
it reverse-engineers the business that delivers them. They are the gold standard, built
and published in `localDNS`:

| Statement | Audience | What it is | Source |
| --------- | -------- | ---------- | ------ |
| **Network Activity Statement** | The homeowner | A 1–2 page monthly value receipt — the "sticker on the door" that proves the quiet was earned | `localDNS/docs/statements/client/*.html` |
| **Alliance Member Portfolio** | The operator | One fleet view over a whole book of homes — fleet KPIs, the attention queue, the work log that carries the dues | `localDNS/docs/statements/operator/*.html` |

The model is **pest control, not lawn care:** the value is the quiet, and the Statement
is what makes the invisible work visible. Both are rendered by a JSON-driven generator
(`localDNS/docs/statements/tools/`) at ~$0.01/home. **This repo's only job around them**
is the surround: fill the funnel that earns the first one (00–05), bill for it (07),
deliver it on cadence (06), and turn its "Connect in the Alliance" hand-raise into the
next operator (09–10).

**Invariant — honesty of the kept document:** never print a figure the data does not
support. `localDNS`'s own "Data sourcing" table marks which numbers are real today
(Pi-hole / Uptime Kuma / `wg`) versus buildable (per-category volume) versus needing a
real cohort dataset. Stages 06 and 08 inherit that discipline: a Statement goes out for
money only with figures the box actually measured.

---

## 1. Known issues & open decisions

| Issue | Action |
| ----- | ------ |
| Real cohort dataset for "How You Compare" | Still a placeholder — do not print invented peer averages on a kept document. Carried from `localDNS`/`MARKETING`. |
| Per-category traffic volume (GB) | Flow-accounting layer is scaffolded in `localDNS`, not yet stood up — scope statements to Pi-hole/Kuma figures until it is real. |
| Member dues amount + what they unlock | Open in `MARKETING`; stage 09 onboarding assumes a flat monthly figure (`CHANGE_ME`). |
| Pricing is unvalidated | `$25–40/mo` retainer + `~$150–200` setup fee are hypotheses (`MARKETING`); stage 05 quote template uses them as defaults, not gospel. |
| Operator vetting standard | "Guild-certified" is not yet defined concretely — `09-recruiting-and-guild/vetting-checklist.md` is a first draft, not a legal standard. |
| Worker classification (1099 vs W-2) | `10-gig-workers-compliance/` documents the 1099-NEC path; confirm classification with counsel before scaling — misclassification is the real risk. |
| Credentials & PII | Every API key, password, and real client record is a `CHANGE_ME`/`.env` placeholder here. Do not commit the real thing. |
| Liquidity before app | The DoorDash-style toggle app is **stack, not moat** — do not build it to manufacture liquidity. Phase gates live in `MARKETING`'s roadmap. |

---

## 2. Verification

The funnel is "live end-to-end" when a fictional household can travel every stage
without a manual hand-off. Walk it the way `localDNS` walks a DNS query:

```
1.  A geo-targeted ad / local-SEO page resolves to a landing page      (02 → 01)
2.  The intake form submits and creates a CRM lead record               (03 → 08)
3.  Setmore books a consult and the call is logged to that record       (03, 04 → 08)
4.  The quote sends, e-sign closes, status flips lead → customer         (05 → 08)
5.  Setup fee + retainer plan are created and the first charge clears    (07)
6.  The stack is provisioned                                            (05 → localDNS)
7.  A Statement generates from the roster record and is emailed + mailed (06 → localDNS)
8.  A "Connect in the Alliance" tap creates an operator-interest record  (06 → 09)
9.  A W-9 is collected and the contractor agreement is e-signed          (10)
10. Every step above was carried by an automation, not a copy-paste      (11)
```

If any arrow requires a human to retype data from one tool into another, that seam is a
**bug in stage 11**, not a feature. Spot-check: open the CRM record for the fictional
`archetype-prime-time` household and confirm it carries fields written by stages
02, 03, 05, and 07.

**Doc integrity:** `python3 tools/check-docs.py` confirms every internal file link and
cross-file anchor in this repo resolves — the analog of `localDNS`'s `tools/check-docs.py`,
extended to recurse the stage folders. Run it before a commit; it exits non-zero on a
broken link so it can gate CI.

---

## 3. Working philosophy

- **The Statement is the product; this repo is the machine.** Every change must make
  it cheaper or more reliable to earn, produce, deliver, or get paid for a Statement —
  or to turn a recipient into an operator. If it does none of those, it does not belong.
- **Liquidity before app, trust before tech.** The moat is the human guild, not the
  software. Spend on proof, density, and operator supply before building surface.
- **Design the network to be dull.** A flat retainer makes every incident a cost; the
  whole stack should be boring so the Statement can be vivid.
- **Honesty of the kept document.** Never print what the data does not support.
- **One source of truth per concern.** The CRM record (08) for business data; the home
  JSON in `localDNS` for Statement data. No shadow spreadsheets, no stray fields.
- **Every commit leaves a coherent workflow.** A new reader should be able to follow a
  household from stranger to Statement using only this repo. Use feature branches for
  half-finished stages.

---

## 4. Further reading

- **README.md** — complete operations guide; the funnel stage-by-stage, with the
  topology diagram and per-stage detail.
- **[console/](console/README.md)** — the **Operator Console**: this whole workflow as
  one installable (PWA) launcher — the Statement-Gallery format pointed at every stage,
  with honest status chips and live links across all three repos. Generated from
  `console/data/console.json`. **Internal only — never published.**
- **workflow-context.md** — design rationale: why this tool at each stage, why the
  funnel order, the economics, and the trust-first sequencing.
- **LAUNCH-NOTES.md** — fresh-launch simulation: every break point between an empty
  funnel and a paying customer, severity-tagged with its fix.
- **SKILLS.md** — the go-to-market / RevOps / compliance skills the workflow
  exercises, each mapped to the artifact that proves it.
- **`MARKETING`** (private) — the business model, pricing, and guild mechanics this
  workflow executes.
- **[`localDNS`](https://a777ance.github.io/localDNS/)** (public) — the technical stack
  and the Statement artifacts (`docs/statements/`) this workflow surrounds.
