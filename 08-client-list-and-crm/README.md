# 08 — Client list & CRM

**Lives in:** a CRM / Airtable — the **system of record**.
**Go-live / sync:** maintain the roster; it feeds the Statement generator and every other
stage.

The single source of truth. The business analog of `localDNS`'s data-driven generator,
where one JSON file per home is the truth a Statement renders from. **One record per
household, per operator, per route** — and every other stage reads and writes it.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`schema.md`](schema.md) | The normalized record definitions — the contract for the whole funnel |
| [`data/sample-roster.json`](data/sample-roster.json) | A fictional roster: households, an operator, a route |

## The one-schema rule

A field exists only if it's in [`schema.md`](schema.md) — no stray spreadsheet columns,
no operator's private "my homes" tab. This is `localDNS`'s "all tuning in one file" rule
applied to business data. The instant a second source of truth appears, the generator can
render stale data, billing can charge the wrong plan, and the 1099 can miss a contractor
([LAUNCH-NOTES #11](../LAUNCH-NOTES.md#11-shadow-spreadsheet-becomes-a-second-source-of-truth)).
If a stage needs a new field, **add it to the schema first.**

## Who reads/writes the record

```
02 demand-gen ─writes─► lead + route + consent      08 ─reads─► segments the next campaign
03 funnel     ─writes─► lead + intake + booking      05 ─reads─► runs the warm consult
04 phone      ─writes─► call_log[]                   05 ─reads─► opens from call history
05 sales      ─writes─► quote + status=customer      06 ─reads─► the roster to generate from
07 payments   ─writes─► billing.*                    06 ─reads─► gates delivery on paid
09 recruiting ─writes─► operator + operator_interest 10 ─reads─► files the 1099
```

## The route is first-class

A `route` (a geographic cluster of homes) is its own record, not just an address tag,
because density is the core unit of the business (02) and the operator portfolio in
`localDNS` rolls up *by route*. See `schema.md` → `route`.

## The link to the Statement generator

The household record carries `statement.home_json_path` — the pointer to that home's JSON
in `localDNS/docs/statements/data/clients/`. The CRM holds the *business* truth (status,
billing, contacts); `localDNS` holds the *Statement* truth (the measured network figures).
The monthly run (06) joins them. Keep the boundary clean: business data here, network
data there.

## Hand-offs

Every stage. This is the substrate the funnel runs on — see the read/write map above and
the automation map in [`../11-automations/automation-map.md`](../11-automations/automation-map.md).
