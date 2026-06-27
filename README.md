# A777ance — the full workflow, end to end

> **Private / internal.** This is the playbook for the business *around* the product:
> marketing → sales → delivery → getting paid, and the loop that turns happy customers into
> the operators who serve the next block. The product itself — the monthly **Statement** —
> and the tech that powers it live in the public
> **[`localDNS`](https://a777ance.github.io/localDNS/)** repo. The pricing and business model
> live in the private **`MARKETING`** repo. This repo is the *how* that ties them together.

The whole thing in one sentence: **the Statement is what people pay for, and this repo is the
machine that finds the customer, sells them, delivers it every month, bills for it, and turns
some of them into operators.** Read **[CLAUDE.md](CLAUDE.md)** for the short briefing; this
README is the stage-by-stage guide.

---

## Contents

- [Follow one household](#follow-one-household)
- [The whole funnel, one page](#the-whole-funnel-one-page)
- [How the money works](#how-the-money-works)
- [The stages](#the-stages)
- [Follow one customer all the way through](#follow-one-customer-all-the-way-through)
- [The rules we don't break](#the-rules-we-dont-break)
- [Still being figured out](#still-being-figured-out)
- [Further reading](#further-reading)

---

## Follow one household

A homeowner streams every night and hates the idea of their internet company selling their
browsing. One evening they read a post of ours — "Is your smart TV watching you back?" — and
book a free look. Jose, an operator two miles away, calls to confirm, then sits with them,
walks the house, and shows them a real statement on his phone. They sign: $175 to set up,
$35 a month. Jose installs a small box that quietly keeps the junk off every device. A month
later they get their first statement — *"three things happened to your home this month; you
felt none of them"* — and tap "refer a neighbor." Eight months in, they're so into it they
tap "Connect in the Alliance" and start looking after a few homes themselves.

**Every folder in this repo is one chapter of that story.** The numbers are the order they
travel it.

## The whole funnel, one page

Follow a **household** down the page as it goes stranger → lead → customer → statement. Then
follow a **customer** as it becomes an operator and re-enters at the top, now serving a whole
block.

```
What the machine ultimately makes more of: statements, at scale
   ▲                                                                          ▲
   │  an operator now runs statements for a whole block of homes              │
 ┌─┴────────────────────────────────────────────────────────────────────────┴─┐
 │ 09 recruiting — turn a happy customer into a vetted operator                  │
 │ 10 compliance — W-9 · the agreement · the 1099 (they're contractors)          │
 └─▲──────────────────────────────────────────────────────────────────────▲────┘
   │  the statement raises a hand: "Connect in the Alliance"                │
══ │ ══════════════════════ the line where they start paying ══════════════ │ ════
   │                                                                        │
 ┌─┴──────────────────────────────────────────────────────────────────────┴──┐
 │ 06 THE STATEMENT — what they pay for, every month                            │
 │    • the homeowner's Network Activity Statement (the "sticker on the door")  │
 │    • the operator's portfolio (one view of their whole book)                 │
 │    delivered by email · mailed on paper · scrollable from a QR code          │
 └─▲───────────────────────────────────────────────────────────────────────────┘
   │  every month, only to paid-up accounts (07)
 ┌─┴── the path to that first statement ───────────────────────────────────────┐
 │  STRANGER                                                                     │
 │     │  02 demand gen — "pest control for your internet" · local search · ads │
 │     ▼                                                                         │
 │  LEAD ─► 03 booking form → pick a time → the free look                        │
 │     │  04 phone — a real person answers and confirms the visit                │
 │     ▼                                                                         │
 │  CUSTOMER ─► 05 sales — consult · quote · setup fee · YES                     │
 │     │            └─► set up the box ─────────────────►  localDNS              │
 │     │  07 payments — the $175 setup + the $35/month                           │
 │     ▼                                                                         │
 │  (gets a statement every month — back up to 06)                              │
 └───────────────────────────────────────────────────────────────────────────┘

 Underneath all of it:
   00 brand    — the logo, voice, and the words to say (the-pitch.md)
   01 web      — the website, the Google listing, the live statement gallery
   08 the list — the one master customer list every stage reads and writes
   11 glue     — the automations that move a customer stage→stage, so nothing's retyped
```

## How the money works

A **two-sided guild** (full version in `MARKETING`). Both sides subscribe to the platform;
the service money flows from the customer to the operator directly, like hiring a tradesperson
through a guild.

```
Customer ──platform membership──▶ A777ance ◀──member dues── Operator
   │                                                            ▲
   └──────────────── pays directly for the service ────────────┘
```

| Who | Pays | Earns | What this repo does for them |
| --- | ---- | ----- | ---------------------------- |
| **Customer** (a household) | Membership + their operator | — | Stages 02→07: find them, sell them, bill them, deliver the statement |
| **Operator** (like Jose) | Member dues | Bills their customers | Stages 09→10: recruit, vet, onboard, pay as a contractor |
| **Platform** (A777ance) | — | Both subscriptions | Stages 00, 01, 08, 11: brand, storefront, the list, the glue |

**The incentive that keeps everyone honest:** the operator is on a flat monthly, so **every
problem is a cost, not a payday.** Operator and customer both want a boring, unbreakable
network — so we design every stage to make the network *dull* and the *proof of quiet* vivid.
The statement is that proof.

## The stages

Each stage has its own README (the full detail) plus the concrete templates and scripts beside
it. Summaries here; open the folder for the rest.

- **[11 — Automations](11-automations/)** — the glue that carries a customer stage→stage so
  nothing's ever retyped.

- **[10 — Gig workers & compliance](10-gig-workers-compliance/)** — W-9, the agreement, the
  1099, and the contractor-classification risk to confirm with a lawyer.
- **[09 — Recruiting & the guild](09-recruiting-and-guild/)** — turn a happy customer into a
  vetted operator; here's [what the job is](09-recruiting-and-guild/operator-day-one.md).
- **[08 — Client list & CRM](08-client-list-and-crm/)** — the one master list every stage reads
  and writes.
- **[07 — Payments & receivables](07-payments-receivables/)** — the setup fee, the monthly, and
  the rule that the statement only goes to people who've paid.
- **[06 — Statements delivery](06-statements-delivery/)** — the center. We *deliver* the
  statement (built in `localDNS`), we don't rebuild it; and we write the human notes that make
  it personal.
- **[05 — Sales & onboarding](05-sales-and-onboarding/)** — the [consult, start to
  finish](05-sales-and-onboarding/discovery-call.md), a [worked
  quote](05-sales-and-onboarding/quote-template.md), and the steps from "yes" to the first
  statement.
- **[04 — Phone & comms](04-phone-and-comms/)** — a real person answers; here's [what to
  say](04-phone-and-comms/call-scripts.md).
- **[03 — Funnels & capture](03-funnels-and-capture/)** — the booking form that turns interest
  into a real lead, with every question mapped to the list.
- **[02 — Demand generation](02-demand-generation/)** — own "pest control for your internet,"
  fill one block at a time, and run an email list with the [copy ready to
  send](02-demand-generation/email-lists.md).
- **[01 — Web presence](01-web-presence/)** — the website, the Google listing, and the live
  statement gallery. One job: move a stranger to the booking form.
- **[00 — Brand & identity](00-brand-identity/)** — the look, the voice, and **the words to
  say** ([`the-pitch.md`](00-brand-identity/the-pitch.md)). Set once, inherited everywhere.
## Follow one customer all the way through

The same household — this time as the path the [verification walk](CLAUDE.md#2-verification) checks:

```
02 a post / an ad ─► 01 the website ─► 03 the booking form
                                          │  (automatic)
                                          ▼
                                  08 a new lead on the list
                                          │  03 picks a time · 04 the call gets written up
                                          ▼
                                  05 free look → quote → YES
                                          │
                          ┌───────────────┼────────────────┐
                          ▼               ▼                ▼
                 07 setup fee +    05 set up the     08 lead →
                 monthly charged   box ─► localDNS   customer
                          │                              │
                          └──────────────┬───────────────┘
                                         ▼
                              06 a statement built from his data file,
                                 only because he's paid up (07),
                                 sent by email + mail + QR
                                         │
                                         ▼
                              "Connect in the Alliance" tap
                                         │  (automatic)
                                         ▼
                              09 operator lead ─► vetting ─► onboarded
                                         │
                                         ▼
                              10 W-9 collected · agreement signed · 1099 at year-end
```

Every arrow is an automation (stage 11). If one needs a human to retype data between tools,
that seam is the next bug to fix.

## The rules we don't break

- **One master list.** Every stage reads and writes the same customer record (08). If two tools
  disagree, the list wins and the thing that let them drift is a bug.
- **Statements are built, not written by hand.** The monthly run renders from the list via
  `localDNS`'s tool. This repo schedules and delivers; it never hand-edits a statement.
- **No statement to an unpaid account.** The proof of value only goes to people who paid for it
  (the gate is in 07, enforced automatically in 11).
- **Nothing gets retyped between tools.** Every hand-off is an automation (11). A manual
  copy-paste is a bug, not a process.
- **No secrets or real personal info in git.** API keys and real records are `CHANGE_ME` /
  `.env` placeholders. The committed sample data is made up.
- **Never print a number we didn't measure.** A statement carries only figures the box actually
  produced — same honesty rule as `localDNS`.

## Still being figured out

The full list — pricing still a working test, the neighbor-comparison data not built yet,
operator dues a ~$50/mo ballpark, contractor classification to confirm with a lawyer — is in
**[CLAUDE.md § 1](CLAUDE.md#1-known-issues--open-decisions)**. Short version: the *workflow* is
settled, but a few *inputs* it uses (prices, dues, the comparison data) are still open and owned
by `MARKETING`, and all committed data is fictional.

## Further reading

- **[CLAUDE.md](CLAUDE.md)** — the short briefing and the stage map.
- **[workflow-context.md](workflow-context.md)** — why this tool at each stage, why this order.
- **[LAUNCH-NOTES.md](LAUNCH-NOTES.md)** — everything that can break between an empty funnel and
  a paying customer, and the fix.
- **[SKILLS.md](SKILLS.md)** — the skills this workflow exercises, each tied to a real file.
- **`MARKETING`** (private) — the business model and pricing this executes.
- **[`localDNS`](https://a777ance.github.io/localDNS/)** (public) — the tech and the statement
  artifacts this workflow surrounds.

---

## Patch Notes

*Cross-repo daily digest — customers · DESIGN · localDNS · MARKETING · Azure-lab · claude-code-homelab · Chronikomicon. Newest entry first.*

---

### 2026-06-27

**No changes.** No pull requests were merged across any A777ance repository on 2026-06-26.
