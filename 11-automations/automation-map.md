# The hand-off map — what moves, and what moves it

Every place a customer's info passes from one stage to the next. The **how** column is the
automation that carries it, so nobody retypes anything
([LAUNCH-NOTES #15](../LAUNCH-NOTES.md#15-a-stage-hand-off-requires-a-human-to-retype-data)). The
**status** says whether it's just written down here or actually switched on in the live tools.

---

## The map

| # | From → To | When it fires | What it does | Status |
| - | --------- | ------------- | ------------ | ------ |
| 1 | 03 → 08 | Booking form submitted | Make a new lead; turn the ZIP into a route; record consent | Planned |
| 2 | 03 → 08 | Appointment booked | Drop the appointment onto the record | Planned |
| 3 | 04 → 08 | Call ends | Add the call notes; ping the route's operator | Planned |
| 4 | 02 → 08 | Email opt-in / opt-out | Record (or clear) consent; sync the email list | Planned |
| 5 | 05 → 07 | Quote signed | Set up the customer + plan; charge the setup fee; mark "customer" | Planned |
| 6 | 05 → localDNS | They sign | Kick off the "go set up the box" reminder; note the data-file location | Planned |
| 7 | 07 → 06 | Paid status changes | Flip the **paid-only gate** (paid up ⇒ gets a statement) | Planned |
| 8 | 06 (localDNS) | Monthly schedule | Run the statement job; build the statements | Planned |
| 9 | 06 → 02 | Statement built | Send "your statement's ready" to that customer | Planned |
| 10 | 06 → 08/09 | "Connect in the Alliance" tap | Mark them interested; create an operator lead | Planned |
| 11 | 09 → 10 | Operator goes active | Ask for the W-9 + agreement (the gate before any payment) | Planned |
| 12 | 10 → 08 | A payment goes out | Add it to the operator's year-to-date total | Planned |
| 13 | 02 → 09 | A block hits density with no operator | Flag it: go recruit one | Planned |

## The rules

- **Nothing's "done" until the live tools do it without a human retyping.** "Planned" means it's
  defined here; switch it on and it's live.
- **The customer list (08) is the hub.** Most rows read or write a household/operator/route
  entry; the list is the truth, every other tool is a spoke off it.
- **Row #7 protects the revenue** — the paid-only gate must never be a human eyeballing a list.
- **Row #1 holds up the whole funnel** — if the booking form doesn't create a lead, every stage
  after it starves. Build and test it first.

## How to check it works

Walk one customer — David Allum — through rows 1→9 and confirm each fact lands on his record
**without anyone typing it twice.** Any arrow that needs a human to move data between tools is
the next bug to close. (This is the same walk-through as [CLAUDE.md § 2](../CLAUDE.md#2-verification).)
