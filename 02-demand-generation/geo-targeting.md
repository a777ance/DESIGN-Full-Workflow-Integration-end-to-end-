# Fill the block, not the metro

The single most important marketing habit in the whole business: **buy density, not reach.**
A book of scattered homes burns the operator out; a full block is profitable and sells
itself. The number we live by is **homes on the route** — never impressions, never clicks.

---

## A "route" is just a neighborhood Jose can cover in an afternoon

One subdivision, one HOA, one apartment complex, a tight cluster of streets — close enough
that Jose can swing by three homes in an hour, not three homes in a day. It's a real entry
on the master list (see [`../08-client-list-and-crm/schema.md`](../08-client-list-and-crm/schema.md) →
`route`), because the operator's monthly portfolio is organized by route and we buy ads by
route.

Here's Jose's map today:

```
MAPLE GROVE (the metro)
  ├─ Maple HOA        ZIPs 78701, 78702   ·  Jose  ·  4 homes  ·  building toward 8 ✓ on track
  ├─ Oak Street strip ZIP  78701          ·  Jose  ·  2 homes  ·  too thin to be worth a trip ⚠
  └─ Riverside        ZIPs 78745          ·  nobody yet ·  0 homes  ·  a candidate ◦
```

A route "goes live" — becomes genuinely profitable for the operator — at about **8 homes
within a ten-minute drive** (our working target; `CHANGE_ME` in the data). Below that, every
visit costs more in windshield time than it's worth.

## The campaign loop (one neighborhood at a time)

1. **Pick a candidate** — a cluster where you already have a home or two, or a strong reason
   to believe demand is there (an HOA that just had a scam scare, say).
2. **Aim everything at its ZIPs** — the Google/Meta radius, the business-listing service
   area, the HOA-newsletter ad — all bounded to that handful of ZIP codes.
3. **Land it on the homepage** (01) → the booking form (03).
4. **Count homes, not clicks.** The route is "live" once it hits the density target.
5. **Then let neighbors do the selling.** Once a block has a few happy homes, the "refer a
   neighbor" ask inside the monthly statement (06) brings the next ones in for almost nothing.
6. **Only then move to the next block over.**

## Why this beats chasing reach

- **The operator actually makes money.** A full block turns homes #2 through #20 from
  exhausting into profitable (the math is in `MARKETING`).
- **Referrals snowball.** Density feeds itself — one happy street sells the next.
- **Cheaper customers.** A neighbor referred over the fence costs roughly nothing next to a
  paid lead from a stranger across town.

## The mistake to avoid

A metro-wide "get the word out" campaign that brings in 30 leads spread across 30 ZIP codes.
Jose can't possibly serve them, the bookings fall through, and the ad money is gone
([LAUNCH-NOTES #4](../LAUNCH-NOTES.md#4-geo-targeting-buys-reach-instead-of-route-density)).
**If a campaign can't name the block it's filling, don't run it.**

## Hand-offs

- **→ 08 customer list:** updates the route record and tags every new lead with its route.
- **→ 09 recruiting:** a block that hits density with no operator to serve it is a signal to
  go find one.
