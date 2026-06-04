# Workflow Context

The *why* behind the workflow — the non-obvious calls, explained. README.md tells you what
each stage does; this file tells you why it's built that way: why this tool, why this order,
and where the money forces the decision. Sections line up with README's stages.

The one idea everything falls out of: **the moat is the human guild, not the software; the
software just delivers it.** Whenever a decision is unclear, reason from that and you'll land
where this repo landed.

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

The folders are numbered in the order a household actually travels them — stranger first,
operator last — so a new reader can follow one family through the whole thing in sequence
instead of jumping around.

The order isn't arbitrary; each step needs the one before it. You can't capture a lead (03)
without a website to land on (01), which needs a brand (00). You can't sell (05) what marketing
(02) hasn't surfaced. You can't deliver a statement (06) to someone who hasn't paid (07). And
you can't recruit an operator (09) out of a customer who hasn't yet gotten the statement that
makes them want in. The two stages that touch everything — the master list (08) and the
automations (11) — are numbered last because they're the ground the whole path runs on, not
steps along it.

## Stage 00. Brand & identity — why a single inherited kit

A trust business gets judged on whether it looks like it has its act together. If the logo,
the voice, and the colors don't match between the website, the booking form, the postcard, and
the statement, a homeowner reads "amateur" — and amateur is fatal for someone you're asking to
let onto their home network. So the brand is settled once, here, and every other surface points
back to it instead of inventing its own. One place the value lives, so it can't drift.

The voice comes straight from the analogy — "pest control, not lawn care": calm, specific,
never alarmist. The statement's "Handled For You" copy is the gold-standard sample of that
voice, which is why the brand kit points at it.

## Stage 01. Web presence — why three surfaces, not one

The website, the blog, and the Google listing look redundant. They're not — they catch three
different kinds of person:

- **The Google listing** catches the *local, ready-to-act* searcher ("network help near me").
  It's the single biggest free local-search lever, and most competitors can't be bothered with
  it.
- **The website (Squarespace)** is the fast, low-fuss brochure and booking flow: boring to run,
  which is exactly the point. Its agency tier lets one person manage several customers' sites.
- **The blog** is the engine for teaching the category — long "is my smart TV spying on me?"
  posts rank well over time and are ours to keep, unlike a locked platform.

The statement **gallery** is the fourth surface, and on purpose it's *not* rebuilt here: it's
served straight from `localDNS`, so the website links to the real, live artifact instead of a
screenshot that goes stale.

## Stage 02. Demand generation — why category + density before spend

Two non-obvious calls, both straight from the business model:

1. **Teach the problem before selling the fix.** Nobody wakes up wanting "encrypted DNS." They
   do get "something's watching the kids' tablets, and we keep it out." Running "buy now" ads
   before people understand the *problem* means paying to educate them one at a time. Teaching
   the category — posts and local search built on the analogy — educates the whole market at
   once, and it compounds.
2. **Fill a block, don't chase the metro.** Scattered customers wear the operator out; a full
   block is profitable, and a happy neighbor sells the next one. So ads are bought one
   neighborhood's ZIPs at a time, and the number we watch is **homes on the route**, not
   impressions. The cheapest new customer there is is a current one's word over the fence —
   which is exactly why the "refer a neighbor" ask lives *inside* the monthly statement.

The email list runs off the master list (08) with strict consent, because a trust business
can't afford a spam complaint.

## Stage 03. Funnels — why the intake form is the contract

The booking form is the most important connection in the funnel: it's where loose interest
becomes a real, structured lead. So every question on the form lines up one-to-one with a field
on the customer record (08). Ask for something the record can't hold and the answer dies on
submit; leave out something the record needs and the lead is born half-finished. Treat the form
and the record as two views of one thing, and change them together.

Self-booking (Setmore) beats "we'll call you to schedule" because letting people grab their own
slot kills the phone-tag that murders local-service bookings — and it writes the appointment
straight onto the record.

## Stage 04. Phone & comms — why a human answers

Every software instinct says automate the phone away. A business built on *trust* does the
opposite: a real person answering "is it safe to let you onto my Wi-Fi?" *is* the product, right
at the moment of biggest doubt. So this stage is small in gear (one line, set hours, a greeting)
and big in discipline: every call gets written onto the record so the consult (05) starts warm.
The scripts exist so the calm voice is consistent, not improvised.

## Stage 05. Sales — why a setup fee that is never discounted

The $175 setup fee (a working number — `MARKETING`) is deliberately **not** discounted, and
it's about psychology, not margin: it pays for a real visit and install, and it sets the
expectation that this is a professional service, not a free app. Someone who balks at the setup
fee will balk at the monthly — better to find that out before the truck rolls. The quote is
*specific to their house* (it names their devices and their worry), so the monthly is anchored
to real value, not a round number.

Setting up the box is the clean hand-off between this repo and `localDNS`: the moment the deal
closes, the box gets installed by following `localDNS`'s guide. This repo doesn't repeat that
guide — it points at the one that has it.

## Stage 06. Statements — why we deliver, not rebuild

The biggest temptation in this whole repo is to "improve" the statement here. Don't. The
statement is the gold standard precisely *because* it has one home (`localDNS`), gets built the
same way every time, and is honest about which numbers are real. Hand-editing a copy here would
create exactly the drift stage 00 exists to prevent — and could put a stale or made-up number on
a document people keep. So stage 06 is a *delivery routine*, not a builder: it schedules the
monthly run, writes the human "Handled For You" notes, sends the statement, and stops there.

## Stage 07. Payments — why delivery is gated on paid

The statement is the proof of value; sending it to someone who stopped paying hands over the
goods for free and teaches them they don't need to pay to keep getting it. So a statement only
goes out to a paid-up account, and that check is automatic (11), not an operator remembering.
Chasing a missed payment is gentle — we're about keeping people, not collections — but the gate
is firm. The setup fee and the monthly are separate lines because they answer two different
questions in the customer's head (is this serious? is it worth keeping?).

## Stage 08. CRM — why one schema, no shadow spreadsheets

The instant a second source of truth shows up — an operator's private spreadsheet of "their"
homes — the statement can get built from stale info, billing can charge the wrong plan, and a
1099 can miss a contractor. So there's exactly **one entry per household, per operator, per
route**, and a fact exists only if it's in the shared definition. The route gets its own entry
(not just an address tag) because density is the whole game (02) and the operator's portfolio is
organized by route.

## Stage 09. Recruiting — why the customer is the operator pipeline

DoorDash had to recruit drivers and diners separately. We don't: **a happy customer is an
operator waiting to happen** — they trust the box, they're a little handy, and they want the side
income. That customer→operator conversion is the growth loop and the moat, so the operator funnel
starts *inside the statement* (the "Connect in the Alliance" tap), not as a separate cold-hiring
effort. Vetting is heavy on purpose: background-checked, bonded local people *are* the trust
pitch a cheaper-tech competitor can never copy — the vetting is the product, not overhead.

## Stage 10. Compliance — why 1099, and the classification risk

Operators are independent businesses billing their own customers; that's structurally a
**1099-NEC** relationship, not employment, which is what keeps the platform light. So the flow
is: W-9 at onboarding → track payments through the year → file the 1099-NEC by January 31 for
anyone paid at or above the IRS threshold.

The honest risk, flagged loudly: if the platform starts dictating *how* operators work (routes,
scripts, prices) hard enough, a regulator can reclassify them as employees. That's a legal call,
not a setting — so the repo documents the contractor path and tells you to **confirm the
classification with a lawyer before scaling.** Better to flag it than pretend the line is
obvious.

## Stage 11. Automations — why the glue is its own stage

The stages are useless until a customer's info *flows* between them without anyone retyping it.
Making the glue its own stage forces a single map of every hand-off and a single person
responsible for the gaps. The rule: if moving a customer's info from one tool to the next means
someone types it twice, that's a bug here — not an acceptable manual step. The biggest piece of
glue is the statement run itself: the master list → `localDNS`'s tool → a finished statement.

## On the DoorDash-style toggle app

The customer↔operator **toggle app** (one login, two modes) is the right long-term product idea
— *more* right than DoorDash's, because here the customers *are* the operator pipeline. But it's
**tech, not moat**, and a marketplace app is worthless without people on both sides to match.
The three screens of that app already exist as real artifacts: the customer statement, the
operator portfolio, and the "Connect in the Alliance" card. So the standing guidance (from
`MARKETING`'s roadmap) is: **don't build the app to manufacture demand — build it once the funnel
in this repo proves the demand is real**, and build it as a dull, simple web app, because "easy
to fix at 11pm" is the real constraint for a small operator team.
