# CRM schema — the single source of truth

Three record types: **household**, **operator**, **route**. A field exists only if it's
here. The intake form (03) maps one-to-one to `household`; billing (07) owns
`household.billing`; recruiting (09) owns `operator`; compliance (10) owns `operator.tax`.
A fictional instance is in [`data/sample-roster.json`](data/sample-roster.json).

---

## `household`

| Field | Type | Owner stage | Notes |
| ----- | ---- | ----------- | ----- |
| `id` | `HH-####` | 03 | primary key |
| `created_ts` | timestamp | 03 | |
| `status` | enum | 03/05/07 | `lead` · `qualified` · `customer` · `churned` |
| `route_id` | `RT-####` | 02 | assigned from ZIP |
| `name` | string | 03 | contact name |
| `email` | string | 03 | |
| `phone` | string | 03 | |
| `address` | `{street,city,state,zip}` | 03 | ZIP drives `route_id` |
| `home_profile` | `{devices_est,concerns[],isp}` | 03 | sets consult + scope |
| `source` | enum | 03 | `gbp`·`referral`·`ad`·`content` |
| `referred_by` | `HH-####`\|null | 03 | the density flywheel (02) |
| `consent` | bool | 02/03 | email opt-in, never pre-checked |
| `consent_source` / `consent_ts` | string / ts | 02/03 | |
| `unsubscribed_ts` | ts\|null | 02 | suppresses forever |
| `call_log[]` | `[{ts,dir,by,summary,next}]` | 04 | every call appended |
| `booking` | `{setmore_id,consult_ts,requested}` | 03 | |
| `quote` | `{setup_fee,monthly_retainer,scope,sent_ts,signed_ts}` | 05 | |
| `billing` | `{processor_customer_id,plan,status,setup_paid_ts,next_charge,last_payment_ts}` | 07 | `status`: `none`·`active`·`past_due`·`canceled` |
| `operator_id` | `OP-####` | 05/09 | who services this home |
| `statement` | `{home_json_path,last_generated,last_delivered,delivery_channels[]}` | 05/06 | `home_json_path` → `localDNS/docs/statements/data/clients/` |
| `operator_interest` | bool | 06/09 | set on "Connect in the Alliance" hand-raise |

## `operator`

| Field | Type | Owner stage | Notes |
| ----- | ---- | ----------- | ----- |
| `id` | `OP-####` | 09 | primary key |
| `name` / `email` / `phone` | string | 09 | |
| `status` | enum | 09 | `applicant`·`vetting`·`active`·`suspended` |
| `converted_from` | `HH-####`\|null | 09 | the dual-hat flywheel (a customer who became an operator) |
| `routes[]` | `[RT-####]` | 09 | the book of homes, by route |
| `dues` | `{subscription_id,status}` | 09 | platform member dues (amount TBD, `MARKETING`) |
| `vetting` | `{background_check,bond,references[],agreement_signed_ts}` | 09 | gate to `active` |
| `tax` | `{w9_on_file,w9_ts,tin_last4,ytd_paid,form_1099_filed_ts}` | 10 | the 1099-NEC trail |

## `route`

| Field | Type | Owner stage | Notes |
| ----- | ---- | ----------- | ----- |
| `id` | `RT-####` | 02 | primary key |
| `name` | string | 02 | e.g. neighborhood/HOA |
| `zips[]` | `[string]` | 02 | the campaign-targeting unit |
| `operator_id` | `OP-####`\|null | 02/09 | null = unassigned (recruiting trigger) |
| `home_count` | int | derived | live customers on the route |
| `target_density` | int | 02 | `CHANGE_ME` (e.g. 8) — "live" threshold |
| `status` | enum | 02 | `candidate`·`building`·`live` |

---

## Invariants

- **One record per real-world entity.** No duplicate households, no operator's private
  spreadsheet ([LAUNCH-NOTES #11](../LAUNCH-NOTES.md#11-shadow-spreadsheet-becomes-a-second-source-of-truth)).
- **Add the field here first**, then to the form/tool that writes it.
- **Business data here; network data in `localDNS`.** The two meet only via
  `household.statement.home_json_path`.
- **No real PII in git.** Samples are fictional; live records stay in the CRM.
