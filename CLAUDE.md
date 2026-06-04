# CLAUDE.md

The short briefing — read this first. [README.md](README.md) is the full stage-by-stage guide;
[workflow-context.md](workflow-context.md) explains the *why* behind the non-obvious calls.

This repo is the **business machine around the Statements.** The product is the monthly
Statement (see [Section E](#e-the-statements--the-center)); everything here exists to get a
household to its first one, keep producing and delivering it, get paid for it, and turn some
recipients into the operators who produce the next ones. The Statements themselves — the gold
standard — live in the public **[`localDNS`](https://a777ance.github.io/localDNS/)** repo under
`docs/statements/`.

**The voice rule for this whole repo:** write it the way a good salesperson talks to a
homeowner, not the way an IT person talks to a server. Concrete, named, plain. "Your
living-room TV," not "the endpoint." When in doubt, read a real "Handled For You" log and match
it. The plain-English swap table is in
[`00-brand-identity/the-pitch.md`](00-brand-identity/the-pitch.md).

---

## Contents

- [0. What this repo is](#0-what-this-repo-is)
- [A. The funnel at a glance](#a-the-funnel-at-a-glance)
- [B. Roles & money flow](#b-roles--money-flow)
- [C. Stage map](#c-stage-map)
- [D. The one master list](#d-the-one-master-list)
- [E. The Statements — the center](#e-the-statements--the-center)
- [1. Known issues & open decisions](#1-known-issues--open-decisions)
- [2. Verification](#2-verification)
- [3. Working philosophy](#3-working-philosophy)
- [4. Further reading](#4-further-reading)
- [5. NARF (AI CTO) state](#5-narf-ai-cto-state)

---

## 0. What this repo is

The end-to-end playbook for the A777ance guild: how a stranger becomes a **customer** (a
household getting a monthly Statement), and how a customer becomes an **operator** (a guild
member running Statements for a block of homes). Every folder is a stage of that journey, and
maps to the live tool where the work actually happens (see the [stage map](#c-stage-map)). What
you edit here are the specs, scripts, templates, and the map — they go live when you put them
into the real tool.

**Three repos, one business:**

| Repo | Holds | Who sees it |
| ---- | ----- | ----------- |
| **[`localDNS`](https://a777ance.github.io/localDNS/)** | The tech **and** the Statements (`docs/statements/`) — the product | **Public** |
| **`MARKETING`** | The business model, pricing, guild mechanics — the *why* | **Private** |
| **`DESIGN-…` (this repo)** | The workflow around the Statements — the *how* | **Private / internal** |

**This repo is internal.** The customer-facing stuff (brand, website, the Statements) is
published *from here into* public places; the workflow itself — the customer list, the money,
the recruiting economics — is not. Never commit real passwords or personal info: use
`CHANGE_ME` placeholders and keep secrets in `.env` (git-ignored). The sample data here is made
up.

## A. The funnel at a glance

```
STRANGER  (a household that doesn't know it has a problem)
   │   02 demand gen — "pest control for your internet" · local search · ads · email
   ▼
LEAD ─────► 03 booking form → pick a time → the free look
   │   04 phone — a real person answers and confirms the visit
   ▼
CUSTOMER ─► 05 sales — consult · quote · $175 setup · YES
   │            └──► set up the box ───────────────►  localDNS
   │   07 payments — $175 setup + $32/month
   ▼
══════════ THE PRODUCT — what they pay for, every month ════════════════════════
   06  THE STATEMENT  ◄── the gold standard · localDNS/docs/statements
       • the homeowner's Network Activity Statement — the "sticker on the door"
       • the operator's portfolio — one view of their whole book
   sent by email · mailed on paper · scrollable from a QR code
═════════════════════════════════════════════════════════════════════════════════
   │   the statement raises a hand:  "Connect in the Alliance"
   ▼
SOME CUSTOMERS ─► 09 recruiting — happy customer → vetted operator
   │   10 compliance — W-9 · 1099 · the agreement (they're contractors)
   ▼
OPERATOR  (now runs statements for a block of homes) ──┐
                                                       └─► back to 06, at scale

   00 brand underlies all of it  ·  01 web is the storefront
   08 the master list is what every stage reads & writes
   11 the glue moves a customer from one stage to the next, untouched by hand
```

## B. Roles & money flow

A **two-sided guild** (full version in `MARKETING`). Both sides pay the platform; the service
money flows customer→operator directly, like hiring a tradesperson through a guild.

```
Customer ──platform membership──▶ A777ance ◀──member dues── Operator
   │                                                            ▲
   └──────────────── pays directly for the service ────────────┘
```

| Role | Pays | Earns | This repo's job for them |
| ---- | ---- | ----- | ------------------------ |
| **Customer** (household) | Membership + their operator | — | Stages 02→07: find, sell, bill, deliver |
| **Operator** (e.g. Jose) | Member dues | Bills customers directly | Stages 09→10: recruit, vet, onboard, pay as a 1099 |
| **Platform** (A777ance) | — | Both subscriptions | Stages 00, 01, 08, 11: brand, storefront, the list, the glue |

**The incentive that keeps it honest:** the operator is on a flat monthly, so **every problem
is a cost, not a payday.** Operator and customer both want a boring, unbreakable network — so
make the network *dull* and the *proof of quiet* vivid. The Statement is that proof.

## C. Stage map

Folders are numbered by **funnel order** — the path a household travels. A folder's number is
where it sits in the journey, not how important it is. This maps each folder → the live tool
where the work happens → what makes a change go live.

| Folder | Lives in (the live tool) | Go live |
| ------ | ------------------------ | ------- |
| `00-brand-identity/` | Figma + the asset folder | Export assets; update the brand-kit links everything inherits |
| `01-web-presence/` | Squarespace · the blog · Google Business · the statement gallery (from `localDNS`) | Publish the site; verify the Google listing |
| `02-demand-generation/` | Google/Meta ads · local search · Mailchimp | Launch a campaign on one block's ZIPs; sync the email list |
| `03-funnels-and-capture/` | Landing pages + the booking form + Setmore | Publish the funnel; wire the form → the list (08) via the glue (11) |
| `04-phone-and-comms/` | A business line (Google Voice / OpenPhone) | Set hours, greeting, routing; jot every call onto the list |
| `05-sales-and-onboarding/` | The list + a proposal/e-sign tool → hand-off to set up the box | Send the quote; on "yes," set up the box and collect the setup fee |
| `06-statements-delivery/` | `localDNS`'s statement tool + email + print/mail + QR | Run the monthly job; send the statements; QR codes go live |
| `07-payments-receivables/` | Stripe + bookkeeping | Set up the plan; collect setup + monthly; keep the books straight |
| `08-client-list-and-crm/` | A CRM / Airtable — **the master list** | Keep it current; it feeds the statement tool and every stage |
| `09-recruiting-and-guild/` | An application page + vetting + Setmore | Open applications; run vetting; onboard operators |
| `10-gig-workers-compliance/` | A 1099 / payroll tool (Gusto / Track1099) + e-sign | Collect W-9s; pay operators; file 1099-NECs by Jan 31 |
| `11-automations/` | Zapier / Make + the `localDNS` statement job | Switch on the automations that carry a customer stage→stage |

Each folder's own README is the spec for that stage; the scripts, templates, and checklists sit
beside it.

## D. The one master list

`08-client-list-and-crm/` is the single source of truth. **One entry per household, one per
operator, one per route** (a route = a cluster of nearby homes). Every other stage reads and
writes that same entry:

```
02 demand gen ─writes─► a lead          08 reads it to plan the next campaign
03 booking    ─writes─► lead + booking   05 reads it to run a warm consult
05 sales      ─writes─► customer          06 reads it to build statements
07 payments   ─writes─► paid / not paid   06 reads it to skip the unpaid
09 recruiting ─writes─► operator           10 reads it to file the 1099
```

The full field list is in [`08-client-list-and-crm/schema.md`](08-client-list-and-crm/schema.md).
**The rule:** a fact is either in that list or it doesn't exist — no stray spreadsheet columns,
no operator's private "my homes" tab. If a stage needs a new fact, add it to the list first.

## E. The Statements — the center

Everything in this repo surrounds two artifacts, and **this repo does not own them** — it builds
the business that delivers them. They are the gold standard, built and published in `localDNS`:

| Statement | Who it's for | What it is | Where it lives |
| --------- | ------------ | ---------- | -------------- |
| **Network Activity Statement** | The homeowner | A one-page monthly proof — the "sticker on the door" that shows the quiet was earned | `localDNS/docs/statements/client/*.html` |
| **Alliance Member Portfolio** | The operator | One view across a whole book of homes — totals, the to-do list, the work log | `localDNS/docs/statements/operator/*.html` |

The model is **pest control, not lawn care:** the value is the quiet, and the Statement makes
the invisible work visible. Both are built by a tool that reads the customer's data file at
about a penny a home. **This repo's only job around them** is the surround: fill the funnel that
earns the first one (00–05), bill for it (07), deliver it on schedule (06), and turn its
"Connect in the Alliance" tap into the next operator (09–10).

**The honesty rule:** never print a number the data doesn't support. `localDNS` tracks which
figures are real today (how many lookups, how much got blocked, uptime) versus not-built-yet (a
by-category gigabyte breakdown; how a home compares to its neighbors). Stages 06 and 08 inherit
that discipline: a Statement goes out for money only with numbers the box actually measured.

## 1. Known issues & open decisions

| Issue | What to do |
| ----- | ---------- |
| The "How You Compare" neighbor data | Still a placeholder — don't print made-up neighbor averages on a document people keep. Carried from `localDNS`/`MARKETING`. |
| A by-category gigabyte breakdown | The measuring layer is scaffolded in `localDNS`, not stood up yet — keep statements to the figures we *do* measure until it's real. |
| Member dues amount + what they include | Open in `MARKETING`; stage 09 assumes a flat monthly (`CHANGE_ME`). |
| Pricing isn't validated | $175 setup + $32/mo are a working **price test** (`MARKETING`); stage 05 uses them as confident defaults, not gospel. |
| The vetting standard | "Guild-certified" isn't defined concretely yet — `09-recruiting-and-guild/vetting-checklist.md` is a first draft, not a legal standard. |
| Contractor vs. employee | `10-gig-workers-compliance/` documents the 1099 path; confirm the classification with a lawyer before scaling — misclassification is the real risk. |
| Secrets & personal info | Every key, password, and real record is a `CHANGE_ME`/`.env` placeholder here. Don't commit the real thing. |
| Don't build the app to fake liquidity | The customer/operator toggle app is **tech, not moat** — don't build it to manufacture demand. Phase gates live in `MARKETING`. |

## 2. Verification

The funnel is "live end to end" when a made-up household can travel every stage without anyone
retyping data by hand. Walk it:

```
1.  An ad / a search result lands on the website                          (02 → 01)
2.  The booking form creates a lead on the master list                     (03 → 08)
3.  Setmore books the consult and the call gets written up                 (03, 04 → 08)
4.  The quote sends, they e-sign, lead flips to customer                    (05 → 08)
5.  The setup fee + monthly plan are created and the first charge clears    (07)
6.  The box gets set up                                                    (05 → localDNS)
7.  A statement is built from the data file and is emailed + mailed         (06 → localDNS)
8.  A "Connect in the Alliance" tap creates an operator lead                (06 → 09)
9.  A W-9 is collected and the agreement is signed                          (10)
10. Every step above was carried by an automation, not a copy-paste         (11)
```

If any arrow needs a human to retype data from one tool into another, that seam is a **bug in
stage 11**, not a feature. Spot-check: open the record for the worked-example household
(the sample household, HH-0001) and confirm it carries facts written by stages 02, 03, 05, and 07.

**Doc integrity:** `python3 tools/check-docs.py` confirms every internal link and cross-file
anchor in this repo resolves. Run it before a commit; it exits non-zero on a broken link so it
can gate CI.

## 3. Working philosophy

- **The Statement is the product; this repo is the machine.** Every change should make it
  cheaper or more reliable to earn, produce, deliver, or get paid for a Statement — or to turn a
  recipient into an operator. If it does none of those, it doesn't belong.
- **Liquidity before app, trust before tech.** The moat is the human guild, not software. Spend
  on proof, density, and operator supply before building surface.
- **Make the network dull.** A flat monthly makes every problem a cost — so keep the stack
  boring and let the Statement be the vivid part.
- **Be honest on the kept document.** Never print what the data doesn't support.
- **One source of truth.** The customer list (08) for business facts; the home data file in
  `localDNS` for statement facts. No shadow spreadsheets, no stray fields.
- **Talk like a person.** No IT jargon on any customer-facing surface — and as little as
  possible everywhere else. A grandparent should understand it.
- **Every commit leaves a coherent playbook.** A new reader should be able to follow a household
  from stranger to Statement using only this repo.

## 4. Further reading

- **README.md** — the full stage-by-stage guide, with the funnel diagram.
- **workflow-context.md** — why this tool at each stage, why this order, the economics.
- **LAUNCH-NOTES.md** — every break point between an empty funnel and a paying customer, with
  its fix.
- **SKILLS.md** — the skills this workflow exercises, each tied to a real file.
- **PLUGINS.md** — which Claude Code plugins to turn on for this repo.
- **`MARKETING`** (private) — the business model and pricing this executes.
- **[`localDNS`](https://a777ance.github.io/localDNS/)** (public) — the tech and the Statements
  this surrounds.

---

## 5. NARF (AI CTO) state

This repo is the portfolio hub. At session start, read:

1. `docs/ai-cto/portfolio.md` — cross-repo status, current priorities, phase gate
2. `docs/ai-cto/roadmap.md` — what to build and when
3. `docs/ai-cto/tech-debt.md` — tracked items across all repos
4. `docs/ai-cto/decisions.md` — architecture decisions log

At session end, update `portfolio.md` with any new decisions or status changes.
