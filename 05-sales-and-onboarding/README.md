# 05 — Sales & onboarding

**Lives in:** the CRM + a proposal / e-sign tool → handoff to the `localDNS` deploy.
**Go-live / sync:** send the quote; on close, provision the stack and collect the setup
fee (07).

Lead → customer. A consultative path — discovery consult, a *scoped* quote, e-sign, and
the clean hand-off to provisioning, at which point `localDNS` deploys the stack on the
household's t630.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`quote-template.md`](quote-template.md) | The scoped quote: setup fee + retainer, with default figures |
| [`onboarding-checklist.md`](onboarding-checklist.md) | Close → provision → first Statement, as an owned checklist |

## The path

```
warm consult (04 logged) ─► scope the home ─► quote (setup fee + retainer)
        ─► e-sign ─► CLOSE ─► collect setup fee (07) ─► PROVISION (localDNS) ─► first Statement (06)
```

## Why a setup fee that's never discounted

The setup fee (~$150–200, a `MARKETING` hypothesis, `CHANGE_ME`) is deliberately **not**
discounted — it's about psychology, not margin. It covers real install labor and sets
the expectation that this is a professional service, not a free app. A prospect who
balks at the setup fee will balk at the retainer; better to learn that before the truck
rolls. The quote is **scoped** (it names the homes/devices) so the retainer is anchored
to delivered value, not a round number. Full rationale in
[`../workflow-context.md`](../workflow-context.md#stage-05-sales--why-a-setup-fee-that-is-never-discounted).

## The provisioning hand-off (this repo → localDNS)

The riskiest seam in the funnel is a closed deal nobody provisions — a refund waiting to
happen ([LAUNCH-NOTES #7](../LAUNCH-NOTES.md#7-close--provision-hand-off-is-undocumented)).
So "provision the t630" is an explicit, owned step on the onboarding checklist, and the
actual deploy follows **`localDNS`'s setup guide** — this repo does not duplicate it, it
points at the one that does. On completion, the household's home-JSON exists in
`localDNS` and the CRM record is stamped `status = customer`.

## Hand-offs

- **← 03/04:** a booked, warm, logged consult is the input.
- **→ 07 payments:** on close, create the plan and collect the setup fee.
- **→ localDNS:** provision the stack per its setup guide; create the home-JSON.
- **→ 06 statements:** a provisioned, paid customer is eligible for the monthly run.
- **→ 08 CRM:** writes the quote, signature, and `status` transitions onto the record.
