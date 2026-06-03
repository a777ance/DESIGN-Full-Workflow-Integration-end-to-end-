# Automation map — every stage→stage hand-off

The connective tissue of the whole funnel. Each row is a record moving from one stage to
the next; the **Automation** column is the zap/pipeline that carries it so no human
retypes data ([LAUNCH-NOTES #15](../LAUNCH-NOTES.md#15-a-stage-hand-off-requires-a-human-to-retype-data)).
`Status` reflects whether the seam is specified (here) vs. stood up in the live tool.

---

## The map

| # | From → To | Trigger | Automation (carries the record) | Status |
| - | --------- | ------- | ------------------------------- | ------ |
| 1 | 03 → 08 | Intake form submitted | Create `household` lead; resolve ZIP→route; set consent | Spec'd |
| 2 | 03 → 08 | Setmore booking confirmed | Write `booking.setmore_id` + `consult_ts` to record | Spec'd |
| 3 | 04 → 08 | Call ends | Append to `call_log[]`; notify owning operator | Spec'd |
| 4 | 02 → 08 | Email opt-in / opt-out | Write/clear `consent*`; sync the email segment | Spec'd |
| 5 | 05 → 07 | Quote e-signed (close) | Create customer + plan; charge setup fee; flip `status=customer` | Spec'd |
| 6 | 05 → localDNS | Close | Trigger the provisioning checklist; create the home-JSON pointer | Spec'd |
| 7 | 07 → 06 | Billing status change | Set the **delivery gate** (`active` ⇒ deliverable) | Spec'd |
| 8 | 06 (localDNS) | Monthly schedule | Run `collect → compose → generate`; render Statements | Spec'd |
| 9 | 06 → 02 | Statement rendered | Send "your Statement is ready" to the customer segment | Spec'd |
| 10 | 06 → 08/09 | "Connect in the Alliance" tap | Set `operator_interest`; create operator-interest record | Spec'd |
| 11 | 09 → 10 | Operator → `active` | Request W-9 + contractor agreement (gate before payout) | Spec'd |
| 12 | 10 → 08 | Payout recorded | Increment `operator.tax.ytd_paid` | Spec'd |
| 13 | 02 → 09 | Route hits target density, no operator | Flag a recruiting trigger | Spec'd |

## Invariants

- **No row is "done" until the live tools enact it without a human retype.** "Spec'd"
  means the contract is defined here; "Live" means the zap/pipeline runs.
- **The CRM (08) is the hub.** Most rows read or write the household/operator/route record;
  the CRM is the truth, every other tool is a spoke.
- **Seam #7 is load-bearing for revenue integrity** — the paid/unpaid delivery gate must
  never be a manual check.
- **Seam #1 is load-bearing for the whole funnel** — if intake→CRM doesn't fire, every
  downstream stage starves. Build and verify it first.

## Verification (mirrors CLAUDE.md § 2)

Walk a fictional household (e.g. `archetype-prime-time`) through rows 1→9 and confirm each
field appears on the CRM record **without anyone typing it twice**. Any arrow that needs a
human to move data between tools is the next bug to close.
