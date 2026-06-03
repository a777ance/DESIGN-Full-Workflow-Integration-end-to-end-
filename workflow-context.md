# Workflow Context

Documents the rationale behind the workflow that the Statements depend on. This is not
reproduced by README.md — README is the stage-by-stage operations guide; this file
explains the non-obvious *why*: why this tool at each stage, why the funnel runs in
this order, and where the economics force a decision. Sections follow the same order as
README's "stages," so each "Stage NN" here lines up with the matching folder.

The one idea everything else falls out of: **the moat is the human guild, not the
software; the stack is the delivery vehicle.** Re-derive any decision from that and you
will land where this repo landed.

---

## Contents

- [Stage order — why the funnel runs this way](#stage-order--why-the-funnel-runs-this-way)
- [Stage 00. Brand & identity — why a single inherited kit](#stage-00-brand--identity--why-a-single-inherited-kit)
- [Stage 01. Web presence — why three surfaces, not one](#stage-01-web-presence--why-three-surfaces-not-one)
- [Stage 02. Demand generation — why category + density before spend](#stage-02-demand-generation--why-category--density-before-spend)
- [Stage 03. Funnels — why the intake form is the contract](#stage-03-funnels--why-the-intake-form-is-the-contract)
- [Stage 04. Phone & comms — why a human answers](#stage-04-phone--comms--why-a-human-answers)
- [Stage 05. Sales — why a setup fee that is never discounted](#stage-05-sales--why-a-setup-fee-that-is-never-discounted)
- [Stage 06. Statements — why we deliver, not rebuild](#stage-06-statements--why-we-deliver-not-rebuild)
- [Stage 07. Payments — why delivery is gated on paid](#stage-07-payments--why-delivery-is-gated-on-paid)
- [Stage 08. CRM — why one schema, no shadow spreadsheets](#stage-08-crm--why-one-schema-no-shadow-spreadsheets)
- [Stage 09. Recruiting — why the customer is the operator pipeline](#stage-09-recruiting--why-the-customer-is-the-operator-pipeline)
- [Stage 10. Compliance — why 1099, and the classification risk](#stage-10-compliance--why-1099-and-the-classification-risk)
- [Stage 11. Automations — why the glue is its own stage](#stage-11-automations--why-the-glue-is-its-own-stage)
- [On the DoorDash-style toggle app](#on-the-doordash-style-toggle-app)

---

## Stage order — why the funnel runs this way

The folders are numbered in **funnel order**, not priority order, for the same reason
`localDNS`'s folders are numbered in *install* order: it lets a new reader follow one
unit (there, a DNS query; here, a household) through the whole system in sequence.

The order is forced by the dependency chain: you cannot capture a lead (03) without a
storefront to land on (01), which inherits a brand (00); you cannot sell (05) what
demand-gen (02) has not surfaced; you cannot deliver a Statement (06) to an account
that has not paid (07); and you cannot recruit an operator (09) from a customer who has
not yet received the Statement that raises their hand. The two cross-cutting stages —
the CRM (08) and automations (11) — are numbered *after* the linear path because they
are the substrate the path runs on, not steps in it.

---

## Stage 00. Brand & identity — why a single inherited kit

A trust business is judged on consistency. If the logo, voice, and color drift between
the Squarespace site, the WordPress blog, the Google Business Profile, the intake form,
and the Statement itself, the household reads "amateur" — fatal for a service you let
inside the home network. So brand is **stage 00**: defined once, in Figma, and *linked*
(never re-pasted) by every downstream surface. The brand kit is to this repo what
`tuning.conf` is to `localDNS` — the single place a value lives so it cannot diverge.

The voice is set by the category analogy ("pest control, not lawn care"): calm,
specific, never alarmist. The Statement's "Handled For You" copy is the canonical
sample of that voice, which is why the brand kit points at it.

---

## Stage 01. Web presence — why three surfaces, not one

Squarespace, WordPress, and a Google Business Profile look redundant; they are not, they
serve three different intents:

- **Google Business Profile** catches *local high-intent* discovery ("network help near
  me") and is the single biggest local-SEO lever — it is free and most competitors
  neglect it.
- **Squarespace (Circle)** is the fast, low-maintenance brochure + funnel host: dull to
  run, which matches the "keep everything dull" rule. Circle is the partner/agency tier
  that lets one operator manage multiple client sites.
- **WordPress** is the content/SEO engine for the category-education play (stage 02) —
  long-form "is your smart TV spying on you?" content ranks better and is more
  ownable than locked-platform pages.

The published **Statement gallery** is the fourth surface, and it is deliberately *not*
rebuilt here: it is served by GitHub Pages straight from `localDNS/docs/statements/`,
so the marketing site links to the real artifact rather than a mockup of it.

---

## Stage 02. Demand generation — why category + density before spend

Two non-obvious choices, both from the business model:

1. **Category education before lead-gen.** Nobody wakes up wanting encrypted DNS; they
   do understand "someone's watching so the bad stuff stays out." Spending on
   bottom-funnel lead-gen before the market understands the *category* burns money
   teaching one prospect at a time. Content + local SEO around the analogy teaches the
   market at scale, and it compounds — the DoorDash lesson applied to awareness.
2. **Geo-clustering over reach.** A scattered customer exhausts the operator; a dense
   route is profitable and makes referrals compound (a happy neighbor refers the next
   neighbor). So campaigns are bought *zip-code-at-a-time* and the unit metric is
   **homes per route**, not impressions. This is why the referral CTA is surfaced
   *inside the Statement* — the cheapest density you can buy is a customer's word to the
   house next door.

Email lists are run off the system of record (08) with strict consent, because a trust
business cannot afford a spam complaint.

---

## Stage 03. Funnels — why the intake form is the contract

The intake form is the single most important integration seam in the funnel: it is
where unstructured attention becomes a **structured CRM record**. So every field on the
form maps one-to-one to a field in `08-client-list-and-crm/schema.md`. If the form asks
something the schema cannot store, the data dies on submit; if the schema needs
something the form never asks, the record is born incomplete. Treat the form and the
schema as two views of one contract — change them together.

Setmore (self-booking) is chosen over "we'll call you" because letting the prospect pick
the slot removes the phone-tag that kills local-service conversion, and it writes the
appointment straight onto the record.

---

## Stage 04. Phone & comms — why a human answers

Every instinct in a software product says automate the phone away. A guild built on
*trust* does the opposite: a real human answering "is this safe to let into my house?"
*is* the product at the moment of highest doubt. The phone stage is therefore small in
tooling (one business line, set hours, a greeting) and large in discipline: every call
is logged back to the CRM record so the consult (05) starts warm. The scripts exist so
that the human touch is consistent, not improvised.

---

## Stage 05. Sales — why a setup fee that is never discounted

The setup fee (~$150–200, a `MARKETING` hypothesis) is deliberately **not** discounted,
for two reasons that are about psychology, not margin: it covers real install labor, and
it sets the expectation that this is a professional service, not a free app. A prospect
who balks at the setup fee is a prospect who will balk at the retainer — better to learn
that before the truck rolls. The quote is *scoped* (it names the homes/devices) so the
retainer is anchored to delivered value, not a round number.

Provisioning is the clean hand-off point between this repo and `localDNS`: the moment
the deal closes, the household's t630 is deployed by following `localDNS`'s setup guide.
This repo does not document the deploy — it points at the one that does.

---

## Stage 06. Statements — why we deliver, not rebuild

The strongest temptation in this whole repo is to "improve" the Statement here. Resist
it. The Statement is the gold standard precisely because it has *one* source of truth
(`localDNS/docs/statements/`), is JSON-driven, self-contained, and honest about which
figures are real. Forking it into this repo would create exactly the drift stage 00
exists to prevent. So stage 06 is a **delivery runbook**, not a generator: it schedules
the monthly run, assembles the operator sidecar ("Handled For You" log + Alliance match),
delivers by email / print-mail / QR, and stops there. The only seam stage 06 owns that
`localDNS` flags as a future swap is `compose_prose()` — the point where a Claude (Haiku)
call can write richer copy at ~$0.01/home once wanted.

---

## Stage 07. Payments — why delivery is gated on paid

The Statement is the value receipt; sending it to an unpaid account inverts the
incentive — it hands over the proof-of-value for free and trains churned customers that
they keep getting the goods. So delivery (06) is **gated on a paid account** in stage
07, enforced by an automation (11), not by an operator remembering. Dunning is gentle
(the model is retention, not collections) but the gate is firm. Setup fee and retainer
are separate line items because they answer different objections (labor vs. ongoing
value) and should be visible as such.

---

## Stage 08. CRM — why one schema, no shadow spreadsheets

This is the direct analog of `localDNS`'s "all tuning in one file" rule. The instant a
second source of truth appears — an operator's personal spreadsheet of "their" homes —
the Statement generator can render stale data, the receivables can bill the wrong plan,
and the 1099 can miss a contractor. So there is exactly **one record per household, per
operator, per route**, and a field exists only if it is in `schema.md`. The route record
is first-class (not just an address tag) because density is the core unit of the
business (stage 02) and the operator portfolio rolls up *by route*.

---

## Stage 09. Recruiting — why the customer is the operator pipeline

DoorDash had to recruit dashers and diners separately. A777ance does not: **a happy
customer is a latent operator** — they like the stack, they are handy, they want gig
income. That dual-hat conversion flywheel is the growth loop and the moat, so the
operator funnel is wired to start *inside the Statement* (the "Connect in the Alliance"
hand-raise), not as a separate cold-recruiting effort. Vetting is heavy on purpose:
background-checked and bonded members *are* the trust pitch competitors with cheaper
tech can never copy — vetting is the product, not overhead.

---

## Stage 10. Compliance — why 1099, and the classification risk

Operators are independent businesses billing customers directly; that is structurally a
**1099-NEC** relationship, not employment, which is what keeps the platform light. The
documented flow is therefore W-9 on onboarding → payout records through the year →
1099-NEC filed by Jan 31 for anyone paid ≥ the IRS threshold.

The honest risk, flagged loudly: if the platform starts *directing how* operators work
(routes, scripts, pricing) heavily enough, a worker-classification challenge could
reclassify them as employees. This is a legal judgment, not a config value — the repo
documents the 1099 path and tells the reader to **confirm classification with counsel
before scaling.** Better to flag it than to pretend the line is obvious.

---

## Stage 11. Automations — why the glue is its own stage

In `localDNS`, the components are useless until DNS *flows* between them; the analog
here is that the stages are useless until a *record* flows between them. Making
automation its own stage (rather than a footnote on each) forces a single map of every
hand-off and a single owner for the seams. The rule mirrors the network one: if moving a
record from tool A to tool B requires a human to retype it, that is a dropped packet —
a bug in stage 11 — not an acceptable manual step. The `localDNS` Statement pipeline is
itself the largest automation in the map: roster → generator → rendered Statement.

---

## On the DoorDash-style toggle app

The customer↔operator **toggle app** (one login, two modes) is the right long-term
product idea — *more* right than DoorDash's, because here the customers *are* the
operator pipeline. But it is **stack, not moat**, and a marketplace app is worthless
without liquidity. The three screens of that app already exist as artifacts: the client
Statement, the operator portfolio, and the Alliance match card. So the standing
guidance (from `MARKETING`'s roadmap) is: **do not build the app to manufacture
liquidity — build it once the funnel in this repo proves liquidity exists**, and build
it as a dull PWA, not a native app, because "easy to debug at 11pm" is the real
constraint for a small operator team.
