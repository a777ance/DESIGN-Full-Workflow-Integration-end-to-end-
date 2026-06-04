# 05 — Sales & onboarding

**Lives in:** the customer list + a proposal/e-sign tool → then the hand-off to set up the box.
**Go-live:** send the quote; when they say yes, set up the box and collect the setup fee (07).

Where a lead becomes a customer. It's a consult, not a hard sell: you sit with someone like
David, walk his house, show him a real statement, put a fair number on it, and — if it's a
fit — get him set up. The whole thing should feel like hiring a good tradesperson, because
that's what it is.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`discovery-call.md`](discovery-call.md) | **The consult, start to finish** — how to open, what to ask, how to present the number, and how to handle the pushback |
| [`quote-template.md`](quote-template.md) | The quote — David Allum's worked end-to-end, plus a blank to copy |
| [`onboarding-checklist.md`](onboarding-checklist.md) | The steps from "yes" to their first statement, in order |

## The path

```
warm consult (04 wrote it up) ─► look at the home ─► quote ($175 setup + $32/mo)
        ─► they sign ─► collect the setup fee (07) ─► set up the box ─► first statement (06)
```

## Why the setup fee never gets discounted

The $175 setup fee (a working number — see `MARKETING`) is **never** discounted, and that's
about psychology, not margin. It pays for a real visit and a real install, and it sets the
tone that this is a professional service, not a free app. Someone who balks at the setup fee
is someone who'll balk at the monthly too — better to find that out before you drive out
there. And the quote is **specific to their house** (it names their devices and their worry),
so the monthly is anchored to real value, not a number you pulled from the air. Fuller reasoning
in [`../workflow-context.md`](../workflow-context.md#stage-05-sales--why-a-setup-fee-that-is-never-discounted).

## Setting up the box (the hand-off to localDNS)

The riskiest moment in the whole funnel is a deal that closes and then nobody sets up — that's
a refund waiting to happen ([LAUNCH-NOTES #7](../LAUNCH-NOTES.md#7-close--provision-hand-off-is-undocumented)).
So "set up the box" is a real, checked-off step on the [onboarding checklist](onboarding-checklist.md).
The actual install — putting the appliance on their network and confirming it's working —
follows **`localDNS`'s install guide**; we don't repeat those steps here, we point at the guide
that has them. When it's done, the customer's data file exists in `localDNS` and their record
is stamped "customer."

## Hand-offs

- **← 03/04:** a booked, warmed-up, written-up consult is the input.
- **→ 07 payments:** on "yes," set up the plan and collect the setup fee.
- **→ localDNS:** install the box per its guide; create the customer's data file.
- **→ 06 statements:** a set-up, paid-up customer is in line for the next monthly run.
- **→ 08 customer list:** writes the quote, the signature, and the "lead → customer" flip.
