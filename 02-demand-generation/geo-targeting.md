# Geo-targeting — density as the unit of efficiency

The single most important marketing discipline in the guild: **buy density, not reach.**
A scattered book of homes exhausts the operator; a dense route is profitable and makes
referrals compound. The unit metric is **homes per route**, never impressions.

---

## The route — a first-class object

A **route** is a geographic cluster of homes one operator can service efficiently (one
neighborhood, one HOA, one apartment complex, a tight set of zips). It is a real record
in the CRM (`../08-client-list-and-crm/schema.md` → `route`), because the operator
portfolio rolls up *by route* and campaigns are bought *per route*.

```
metro  ─┬─ route A  (zips 1xxxx, 1xxxy)   ── operator: Jose   ── 12 homes  ✓ profitable
        ├─ route B  (zip  1xxxz)          ── operator: Jose   ──  3 homes  ⚠ below density
        └─ route C  (zips 2xxxx…)         ── unassigned       ──  0 homes  ◦ candidate
```

## The campaign loop (zip-code-at-a-time)

1. **Pick a candidate route** — a cluster with a few existing/likely homes.
2. **Scope the campaign to its zips** — Meta/Google radius + GBP service area + any
   local print/HOA channel, all bounded to those zips.
3. **Land traffic on the storefront** (01) → intake form (03).
4. **Measure homes per route**, not clicks. A route is "live" at the target density
   (`CHANGE_ME`, e.g. ≥8 homes within a ~10-min drive).
5. **Harvest referrals** — once a route has happy homes, the in-Statement referral CTA
   (06) drives the cheapest density there is: neighbor → neighbor.
6. **Only then expand** to the next adjacent route.

## Why this beats reach

- **Operator economics:** a dense route turns homes #2–#20 from exhausting into
  profitable (the unit-economics argument in `MARKETING`).
- **Referrals compound:** density is self-reinforcing; one happy block sells the next.
- **CAC drops:** a referred neighbor costs ~nothing vs. a paid scattered lead.

## The anti-pattern

A metro-wide "reach" campaign that produces 30 scattered leads in 30 zips. The operator
can't service them, conversion craters, and the CAC is wasted. See
[LAUNCH-NOTES #4](../LAUNCH-NOTES.md#4-geo-targeting-buys-reach-instead-of-route-density).
If a campaign can't name the route it's filling, don't run it.

## Hand-offs

- **→ 08 CRM:** writes/updates the `route` record and tags each lead with its route.
- **→ 09 recruiting:** a route at density without an operator is a recruiting trigger.
