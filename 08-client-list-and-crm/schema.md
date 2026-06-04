# What we track on each customer — the shared definition

The whole funnel agrees on one set of facts to keep about each **household**, each
**operator**, and each **route**. If it's not listed here, we don't track it (no stray
spreadsheet columns). The booking form (03) fills in the household basics; billing (07) owns
the money fields; recruiting (09) owns the operator; compliance (10) owns the tax bits. A
made-up filled-in example is in [`data/sample-roster.json`](data/sample-roster.json).

> This is the one genuinely technical page in the repo — it's a field list, by necessity. The
> "Filled in by" column tells you which stage is responsible for each fact.

---

## A household

| Fact | Looks like | Filled in by | Notes |
| ---- | ---------- | ------------ | ----- |
| `id` | `HH-####` | 03 | their unique number |
| `created_ts` | a date | 03 | |
| `status` | `lead` · `qualified` · `customer` · `churned` | 03/05/07 | where they are in the funnel |
| `route_id` | `RT-####` | 02 | their neighborhood, from their ZIP |
| `name` | text | 03 | |
| `email` | text | 03 | |
| `phone` | text | 03 | |
| `address` | street/city/state/zip | 03 | the ZIP decides the route |
| `home_profile` | devices, worries, internet provider | 03 | sizes up the consult + quote |
| `source` | `gbp`·`referral`·`ad`·`content` | 03 | how they found us |
| `referred_by` | a `HH-####` or nothing | 03 | the refer-a-neighbor flywheel (02) |
| `consent` | yes/no | 02/03 | email opt-in, never pre-checked |
| `consent_source` / `consent_ts` | text / date | 02/03 | where and when they opted in |
| `unsubscribed_ts` | a date or nothing | 02 | set on opt-out; we never email again |
| `call_log` | a running list of call notes | 04 | every call, jotted down |
| `booking` | the appointment | 03 | from Setmore |
| `quote` | setup fee, monthly, what's covered, signed-on date | 05 | |
| `billing` | plan, paid up / behind / canceled, payment dates | 07 | Stripe moves money; this is the truth |
| `operator_id` | `OP-####` | 05/09 | who looks after this home |
| `statement` | where the data file is, last built, last sent, how it's delivered | 05/06 | the data file lives in `localDNS` |
| `operator_interest` | yes/no | 06/09 | flips on when they tap "Connect in the Alliance" |

## An operator

| Fact | Looks like | Filled in by | Notes |
| ---- | ---------- | ------------ | ----- |
| `id` | `OP-####` | 09 | |
| `name` / `email` / `phone` | text | 09 | |
| `status` | `applicant`·`vetting`·`active`·`suspended` | 09 | |
| `converted_from` | a `HH-####` or nothing | 09 | the customer they used to be (the dual-hat flywheel) |
| `routes` | a list of `RT-####` | 09 | their book of homes, by neighborhood |
| `dues` | their platform membership | 09 | ~$50/mo, a working number — not final (`MARKETING`) |
| `vetting` | background check, bond, references, signed agreement | 09 | the gate to going active |
| `tax` | W-9 on file, last-4 of their TIN, paid this year, 1099 filed | 10 | the year-end 1099 trail |

## A route

| Fact | Looks like | Filled in by | Notes |
| ---- | ---------- | ------------ | ----- |
| `id` | `RT-####` | 02 | |
| `name` | text | 02 | e.g. the neighborhood or HOA |
| `zips` | a list of ZIP codes | 02 | what a campaign targets |
| `operator_id` | `OP-####` or nothing | 02/09 | empty = nobody's covering it yet (go recruit) |
| `home_count` | a number | (counted) | live customers on the route |
| `target_density` | a number | 02 | `CHANGE_ME` (e.g. 8) — the "now it's profitable" line |
| `status` | `candidate`·`building`·`live` | 02 | |

---

## The rules

- **One entry per real thing.** No duplicate households, no operator's private "my homes" tab
  ([LAUNCH-NOTES #11](../LAUNCH-NOTES.md#11-shadow-spreadsheet-becomes-a-second-source-of-truth)).
- **Add it here first**, then to the form or tool that fills it in.
- **Business facts here; network facts in `localDNS`.** The two meet only at the pointer to
  the home's data file.
- **No real personal info in git here.** The samples in this repo are fictional. For the
  pilot, the **live** roster lives in the private `customers` repo (see
  [ADR-006](../docs/ai-cto/decisions.md)) — out of this repo and out of public `localDNS`.
