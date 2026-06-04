# 08 — Client list & CRM

**Lives in:** a CRM / Airtable — **the one master list.**
**Go-live:** keep the list current; everything else reads from it, including the statement tool.

One list, and everyone works off it. The moment there are two — the official list *and* an
operator's private "my homes" spreadsheet — they drift, and then the statement gets built from
stale info, billing charges the wrong plan, and someone's 1099 gets missed at tax time. So:
**one entry per household, one per operator, one per route**, and every stage reads and writes
that same entry.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`schema.md`](schema.md) | What we track on each household, operator, and route — the shared definition the whole funnel agrees on |
| [`data/sample-roster.json`](data/sample-roster.json) | A made-up list: a few households, an operator, two routes |

## The one-list rule

A piece of info exists on a customer only if it's in [`schema.md`](schema.md) — no random
spreadsheet columns, no operator's private tab. If a stage needs to track something new, it
gets **added to the shared definition first**, then to whatever tool fills it in. That keeps
everyone honest about where the truth lives ([LAUNCH-NOTES #11](../LAUNCH-NOTES.md#11-shadow-spreadsheet-becomes-a-second-source-of-truth)).

## Who reads and writes the list

```
02 demand gen ─writes─► the lead, its route, consent      08 ─reads─► to pick the next campaign
03 booking    ─writes─► the lead + the appointment        05 ─reads─► to run a warm consult
04 phone      ─writes─► the call notes                     05 ─reads─► to pick up where the call left off
05 sales      ─writes─► the quote + "now a customer"       06 ─reads─► who to build statements for
07 payments   ─writes─► paid up / behind / canceled        06 ─reads─► who to skip this month
09 recruiting ─writes─► the operator + their interest      10 ─reads─► to file the 1099
```

## A "route" is its own thing, not just an address

A route (a cluster of nearby homes — see `schema.md` → `route`) gets its own entry, because
density is the whole game (02) and the operator's monthly portfolio is organized by route. It's
not just a tag on an address.

## How the list connects to the statement

Each household's entry holds a pointer to that home's **data file** in `localDNS` — the file
the statement is built from. The list here holds the *business* facts (who they are, what they
pay, where they stand); `localDNS` holds the *measured network* facts. The monthly run (06)
joins the two. Keep that line clean: business stuff here, network stuff there.

## Hand-offs

Every stage. This list is the thing the whole funnel runs on — see the read/write map above
and the full hand-off map in [`../11-automations/automation-map.md`](../11-automations/automation-map.md).
