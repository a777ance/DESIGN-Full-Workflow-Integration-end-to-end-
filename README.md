# A777ance — Full Workflow Integration (end-to-end)

> **Private / internal repo.** The end-to-end business workflow that surrounds the
> A777ance Statements: marketing → sales → delivery → receivables, and the
> customer→operator guild flywheel. The product itself (the monthly Statement) and the
> technical stack live in the public **[`localDNS`](https://a777ance.github.io/localDNS/)**
> repo; the business model lives in the private **`MARKETING`** repo. This repo is the
> *how* that connects them.

The thesis in one line: **the Statement is the product, and this repo is the machine
that earns it, delivers it, bills it, and turns recipients into the operators who
produce the next ones.** Read **[CLAUDE.md](CLAUDE.md)** first for the condensed
briefing; this README is the stage-by-stage operations guide.

---

## Contents

- [Thesis](#thesis)
- [The funnel topology](#the-funnel-topology)
- [Operational notes](#operational-notes)
- [The stages](#the-stages)
  - [00 — Brand & identity](#00--brand--identity)
  - [01 — Web presence](#01--web-presence)
  - [02 — Demand generation](#02--demand-generation)
  - [03 — Funnels & capture](#03--funnels--capture)
  - [04 — Phone & comms](#04--phone--comms)
  - [05 — Sales & onboarding](#05--sales--onboarding)
  - [06 — Statements delivery](#06--statements-delivery)
  - [07 — Payments & receivables](#07--payments--receivables)
  - [08 — Client list & CRM](#08--client-list--crm)
  - [09 — Recruiting & the guild](#09--recruiting--the-guild)
  - [10 — Gig workers & compliance](#10--gig-workers--compliance)
  - [11 — Automations](#11--automations)
- [How a record flows](#how-a-record-flows)
- [Known issues & open decisions](#known-issues--open-decisions)
- [Further reading](#further-reading)

---

## Thesis

A777ance is a **two-sided guild**, not a software product: it runs a managed
home-network stack and charges two subscriptions — one to the **homeowner**, one to the
**operator** who services homes — while the homeowner pays the operator directly, like
hiring a tradesperson through a trade guild. The full model lives in `MARKETING`.

The **moat is the human guild; the stack is the delivery vehicle.** That single fact
sets the order of everything in this repo:

- **Liquidity before app, trust before tech.** A two-sided marketplace is worthless
  without enough homes and operators in the same area to match. So spend goes into
  proof, local density, and operator supply first — not surface. Right now **the
  monthly Statement *is* the app**: value receipt, salesperson, and referral engine at
  once.
- **Pest control, not lawn care.** The value is the quiet — a blocked tracker, an
  encrypted lookup, a patched appliance — none of it visible. So the product must make
  the invisible visible every month. That is the entire job of the Statement, and the
  entire job of this repo is to surround it: fill the funnel that earns the first one,
  bill for it, deliver it, and spin the flywheel out of it.
- **Design the network to be dull.** A flat operator retainer makes every incident a
  cost, not revenue — so operator and customer both want a boring, unbreakable network.
  Keep the stack simple; keep the proof vivid.

**What this repo is not.** It is not a re-implementation of the Statement generator
(that is `localDNS/docs/statements/`), and not the pricing/strategy rationale (that is
`MARKETING`). It is the integration layer: specs, templates, schemas, checklists, and
the map of which live tool owns each stage and how a record moves between them.

---

## The funnel topology

The whole workflow on one page. Follow a **household** down the left as it travels
stranger → lead → customer → Statement, then follow a **customer** as it converts into
an operator and re-enters the machine at fleet scale. `NN` tags map each piece to its
stage folder.

```
RE-ENTRY TARGETS — what the machine ultimately produces (more Statements, at scale)
   ▲                                                                              ▲
   │  an operator now produces Statements for a whole book of homes               │
   │                                                                              │
 ┌─┴───────────────────────────────────────────────────────────────────────────┐│
 │ 09 recruiting/guild — customer→operator flywheel · vetting · onboarding        ││
 │ 10 compliance       — W-9 · contractor agreement · 1099-NEC (gig workers)      ││
 └─▲──────────────────────────────────────────────────────────────────────────▲─┘│
   │  the Statement raises a hand: "Connect in the Alliance"                    │  │
══ │ ════════════════════════════════════════════════════════════════════════ │ ═╪══ pay-for-value line
   │                                                                            │  │
 ┌─┴────────────────────────────────────────────────────────────────────────┐ │  │
 │ 06 STATEMENTS — the product · localDNS/docs/statements                      │ │  │
 │    • client  Network Activity Statement  (the "sticker on the door")        │─┘  │
 │    • operator Alliance Member Portfolio   (earning the keep)                │    │
 │    delivered: email · printed/mailed · scrollable by QR                     │────┘
 └─▲────────────────────────────────────────────────────────────────────────┘
   │  monthly, from the roster record — gated on a paid account (07)
   │
 ┌─┴── the path to the first Statement ──────────────────────────────────────────┐
 │                                                                                 │
 │  STRANGER                                                                       │
 │     │  02 demand-gen — "pest control for your network" · local SEO ·           │
 │     │                  geo-targeted ads · email lists                          │
 │     ▼                                                                           │
 │  LEAD ─► 03 funnel — landing page → intake form → Setmore booking → demo       │
 │     │  04 phone & comms — answer, qualify, confirm the visit (human touch)     │
 │     ▼                                                                           │
 │  CUSTOMER ─► 05 sales — consult · quote · setup fee · CLOSE                    │
 │     │            └─► provision the stack ───────────────►  localDNS (t630)     │
 │     │  07 payments — one-time setup fee + monthly retainer (Stripe)            │
 │     ▼                                                                           │
 │  (now receives a Statement every month — back up to 06)                        │
 └─────────────────────────────────────────────────────────────────────────────┘

 UNDERLIES EVERYTHING:
   00 brand-identity — logo · slogans · jingle · intro video · the voice every surface inherits
   01 web-presence   — Squarespace · WordPress · Google Business Profile · the published gallery
   08 client/CRM     — the system of record every stage reads & writes (one record per home/operator/route)
   11 automations    — the glue that carries a record stage→stage so nothing is ever retyped
```

**Legend:** `NN` → stage folder · `─►`/`▲` flow direction · `═══` the pay-for-value
line (above it the flywheel, below it the path that earns the first Statement).

---

## Operational notes

- **The CRM record is the single source of truth.** Every stage reads and writes the
  same household / operator / route record (`08-client-list-and-crm/schema.md`). If two
  tools disagree, the CRM wins and the seam that let them drift is an automation bug.
- **Statements are generated, not written.** The monthly run renders from the roster
  via `localDNS/docs/statements/tools/` (~$0.01/home). This repo schedules and delivers;
  it does not hand-author Statements.
- **Delivery is gated on payment.** A Statement goes out only for a paid account; the
  gate lives in stage 07 and is enforced by an automation in stage 11.
- **Nothing is retyped between tools.** Every stage→stage hand-off is an automation
  (stage 11). A manual copy-paste between tools is a bug, not a process.
- **Secrets and PII never land in git.** API keys, passwords, and real client records
  are `CHANGE_ME`/`.env` placeholders. Committed sample data is fictional.
- **Honesty of the kept document.** A Statement prints only figures the box measured —
  the discipline is inherited from `localDNS`'s "Data sourcing" table.

---

## The stages

Each stage has its own `README.md` (the full spec) plus the concrete templates,
schemas, and checklists beside it. The summaries below orient you; open the folder for
the detail.

### 00 — Brand & identity
The foundation every downstream surface inherits: logo, color, type, voice, slogans, a
jingle brief, the intro video, and the Figma source of truth. Held in Figma + an asset
host; linked (not duplicated) from every other stage. → [`00-brand-identity/`](00-brand-identity/)

### 01 — Web presence
The storefront: Squarespace (Circle) and/or WordPress for the marketing site, the
Google Business Profile for local discovery, and the GitHub-Pages-published Statement
gallery (served from `localDNS`). The site's only job is to move a stranger into the
funnel (stage 03). → [`01-web-presence/`](01-web-presence/)

### 02 — Demand generation
The top of the funnel: own the category ("pest control for your network"), rank locally
(SEO), run geo-targeted third-party campaigns clustered into profitable routes, and run
a consent-clean email list off the system of record. Density is the unit of efficiency.
→ [`02-demand-generation/`](02-demand-generation/)

### 03 — Funnels & capture
Where attention becomes a record: landing page → **intake form** → **Setmore**
self-booking → optional demo app. The intake form is the contract between marketing and
the CRM — every field maps to a schema field. → [`03-funnels-and-capture/`](03-funnels-and-capture/)

### 04 — Phone & comms
The human touch that a trust business runs on: a business line with set hours, a
greeting, call routing, and a logging discipline that writes every call back to the CRM
record. → [`04-phone-and-comms/`](04-phone-and-comms/)

### 05 — Sales & onboarding
Lead → customer: discovery consult, a scoped quote (setup fee + retainer), e-sign, and
the clean handoff to **provisioning** — at which point `localDNS` deploys the stack on
the household's t630. → [`05-sales-and-onboarding/`](05-sales-and-onboarding/)

### 06 — Statements delivery
The center. Not a re-build — a delivery runbook around `localDNS/docs/statements/`: the
monthly generate-from-roster run, the email + print/mail + QR delivery, and the
"Handled For You" sidecar discipline that gives each Statement its personal, named
proof of work. → [`06-statements-delivery/`](06-statements-delivery/)

### 07 — Payments & receivables
Getting paid: the one-time setup fee, the monthly retainer plan, dunning on failed
charges, reconciliation, and the **delivery gate** (no Statement to an unpaid account).
Held in Stripe + accounting. → [`07-payments-receivables/`](07-payments-receivables/)

### 08 — Client list & CRM
The system of record — one normalized schema for households, operators, and routes that
every stage reads and writes, and that feeds the Statement generator. The business
analog of `localDNS`'s one-JSON-per-home source of truth. → [`08-client-list-and-crm/`](08-client-list-and-crm/)

### 09 — Recruiting & the guild
The flywheel: turn a Statement's "Connect in the Alliance" hand-raise into a vetted,
onboarded operator. The operator-supply funnel, the vetting standard, and the dual-hat
(customer↔operator) onboarding. → [`09-recruiting-and-guild/`](09-recruiting-and-guild/)

### 10 — Gig workers & compliance
The back office for a gig workforce: W-9 collection, the contractor agreement, payout
records, and 1099-NEC filing by Jan 31 — with worker classification flagged as the real
risk to confirm with counsel. → [`10-gig-workers-compliance/`](10-gig-workers-compliance/)

### 11 — Automations
The glue: the map of every stage→stage hand-off and the automation (Zapier/Make + the
`localDNS` pipeline) that carries the record so nothing is ever retyped. → [`11-automations/`](11-automations/)

---

## How a record flows

One fictional household, end to end — the path the [Verification](CLAUDE.md#2-verification)
checklist walks:

```
02 ad / SEO page ─► 01 landing page ─► 03 intake form
                                          │  (11 automation)
                                          ▼
                                  08 CRM: lead created
                                          │  03 Setmore books consult · 04 call logged
                                          ▼
                                  05 consult → quote → e-sign → CLOSE
                                          │
                          ┌───────────────┼────────────────┐
                          ▼               ▼                ▼
                 07 setup fee +    05 provision      08 status:
                 retainer charged  the t630 ─► localDNS   lead → customer
                          │                                  │
                          └──────────────┬───────────────────┘
                                         ▼
                              06 monthly Statement generated from the
                                 roster record (localDNS pipeline),
                                 gated on paid (07), delivered email/mail/QR
                                         │
                                         ▼
                              "Connect in the Alliance" tap
                                         │  (11 automation)
                                         ▼
                              09 operator-interest record ─► vetting ─► onboard
                                         │
                                         ▼
                              10 W-9 collected · agreement e-signed · 1099-NEC at year end
```

Every arrow is an automation (stage 11). If one needs a human to retype data between
tools, that seam is the bug to fix next.

---

## Known issues & open decisions

The full table — pricing still unvalidated, the cohort dataset still a placeholder,
member dues still TBD, worker classification to confirm with counsel — lives in
**[CLAUDE.md § 1](CLAUDE.md#1-known-issues--open-decisions)**. The short version: the
*workflow* is formalized, but several *inputs* it consumes (price points, dues, the
benchmark dataset) are hypotheses owned by `MARKETING`, and the committed data is
fictional sample data.

---

## Further reading

- **[CLAUDE.md](CLAUDE.md)** — the authoritative briefing and stage map.
- **[console/](console/README.md)** — the **Operator Console**: this whole workflow as
  one installable app — the Statement-Gallery format applied to every stage, runnable
  and offline-capable. Internal only; never published.
- **[workflow-context.md](workflow-context.md)** — why each tool, why this order, the
  economics.
- **[LAUNCH-NOTES.md](LAUNCH-NOTES.md)** — fresh-launch break points and their fixes.
- **[SKILLS.md](SKILLS.md)** — the skills this workflow exercises, mapped to artifacts.
- **`MARKETING`** (private) — the business model and pricing this workflow executes.
- **[`localDNS`](https://a777ance.github.io/localDNS/)** (public) — the stack and the
  Statement artifacts this workflow surrounds.
