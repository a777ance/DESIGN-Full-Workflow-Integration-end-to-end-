# The booking form — every question, and where the answer goes

The form is the handshake between marketing and the customer list. **Every question maps to
exactly one field on the customer record** ([`../08-client-list-and-crm/schema.md`](../08-client-list-and-crm/schema.md)) —
that's the right-hand column. Only add a question here if you also add the field there.

A sample filled-in submission is in [`data/sample-intake.json`](data/sample-intake.json).

---

## The questions

| Question on the form | Required | Lands on the record as | Why we ask |
| -------------------- | :------: | ---------------------- | ---------- |
| Full name | ✓ | `name` | |
| Email | ✓ | `email` | |
| Phone | ✓ | `phone` | so we can call them back (04) |
| Street address | ✓ | `address.street` | |
| City / State / ZIP | ✓ | `address.city/state/zip` | **the ZIP picks their route** (02) |
| "Roughly how many things are on your Wi-Fi?" | – | `home_profile.devices_est` | sets expectations for the visit |
| "What's your main worry?" (pick any) | – | `home_profile.concerns[]` | e.g. kids' safety, privacy, an elderly parent, the smart-home gear |
| "Who's your internet provider?" | – | `home_profile.isp` | |
| "How'd you hear about us?" | ✓ | `source` | Google / a neighbor / an ad / a post |
| "A neighbor send you?" (name or address) | – | `referred_by` | this is the referral flywheel (02) |
| Email opt-in box (starts **un**-checked) | – | `consent` (+ source + timestamp) | **never pre-check it** |
| Best time for a visit | – | `booking.requested` | Setmore handles the actual slot |

## What happens the instant they hit submit (automatic — stage 11)

1. Create a lead on the customer list — `status = lead`, a new `id`, timestamped.
2. Turn their ZIP into a route (an existing one, or a new candidate route).
3. If they opted in, record the consent and add them to the Leads email list.
4. If a neighbor referred them, link the two records so the neighbor gets credit.
5. Hand the time slot to Setmore; write the confirmed appointment back onto the record.
6. Ping the operator who covers that route (or the founders) to make the call (04).

## The rules

- **Keep it short.** Every extra required field loses you a booking. Ask only what the visit
  genuinely needs; everything else comes up naturally in the consult (05).
- **The form and the record move together.** A question with nowhere to land, or a required
  record field the form never asks about, is the bug in
  [LAUNCH-NOTES #3](../LAUNCH-NOTES.md#3-intake-form-fields-do-not-map-to-the-crm-schema).
- **Only what we need, and none of it in git.** The committed sample is fake.
