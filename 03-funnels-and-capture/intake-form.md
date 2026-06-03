# Intake form — field schema

The contract between marketing and the CRM. **Every field maps one-to-one to a field in
[`../08-client-list-and-crm/schema.md`](../08-client-list-and-crm/schema.md)** — the
`→ household.x` column is that mapping. Add a field here only if you add it there too.

A sample submission is in [`data/sample-intake.json`](data/sample-intake.json).

---

## Fields

| Form field | Required | → maps to (household record) | Notes |
| ---------- | :------: | ---------------------------- | ----- |
| Full name | ✓ | `name` | |
| Email | ✓ | `email` | |
| Phone | ✓ | `phone` | drives the call-back (04) |
| Street address | ✓ | `address.street` | |
| City / State / ZIP | ✓ | `address.city/state/zip` | **ZIP assigns the route** (02) |
| "How many connected devices, roughly?" | – | `home_profile.devices_est` | sets expectations for the consult |
| "What's your main concern?" (multi-select) | – | `home_profile.concerns[]` | e.g. kids' safety, privacy, elderly relative, IoT |
| "Who's your internet provider?" | – | `home_profile.isp` | |
| "How did you hear about us?" | ✓ | `source` | gbp / referral / ad / content |
| "Referred by a neighbor?" (name/addr) | – | `referred_by` | feeds the density flywheel (02) |
| Email opt-in checkbox (un-checked) | – | `consent` + `consent_source=intake` + `consent_ts` | **never pre-checked** (05/email rules) |
| Preferred consult time | – | `booking.requested` | Setmore handles the actual slot |

## On submit (the automation, stage 11)

1. Create a `household` record, `status = lead`, `id = HH-####`, `created_ts = now`.
2. Resolve `address.zip` → `route_id` (existing route, or create a `candidate` route).
3. If `consent`, write `consent_source` + `consent_ts`; add to the Leads email segment.
4. If `referred_by`, link the referrer's record (credit the referral).
5. Hand the booking to Setmore; write `booking.setmore_id` + `consult_ts` back on confirm.
6. Notify the assigned/owning operator (or the founders) for the call (04).

## Rules

- **Minimal field set.** Every extra required field costs conversion; ask only what the
  consult genuinely needs. Depth comes during the consult (05), not the form.
- **One-to-one or it doesn't ship.** A form field with no schema target, or a required
  schema field with no form source, is the bug in
  [LAUNCH-NOTES #3](../LAUNCH-NOTES.md#3-intake-form-fields-do-not-map-to-the-crm-schema).
- **No PII beyond what's needed**, and none of it committed to git — the sample is fake.
