# From "yes" to their first statement

The steps, in order, from a signed quote to a household scrolling its first monthly statement.
Each one updates the customer's record. The one step you never hand-wave is setting up the
box — that's the moment the promise becomes real
([LAUNCH-NOTES #7](../LAUNCH-NOTES.md#7-close--provision-hand-off-is-undocumented)).

---

## When they sign

- [ ] Flip the record: lead → **customer**; save the signed quote.
- [ ] **Collect the $175 setup fee** and start the $32/month plan (07). Make sure the first
      charge actually clears *before* you drive out.
- [ ] Lock in the install day (Setmore / a quick call, 04).

## Set up the box (the hand-off to localDNS)

- [ ] Install the box by following **`localDNS`'s install guide** — we don't repeat those
      steps here, we use the guide that has them.
- [ ] Run `localDNS`'s built-in check that everything's working before you leave. A home isn't
      "set up" until that check passes.
- [ ] Create the customer's **data file** in `localDNS` — that's the file each monthly
      statement is built from.
- [ ] Note where that data file lives on the customer's record.

## Turn on the monthly statement

- [ ] Confirm how they want it delivered — email, mailed paper, or both.
- [ ] Write the **first month's "Handled For You" opener** — it starts at the install:
      *"Set up and checked over your box — [operator]."*
- [ ] Add the household to the monthly run (06).

## Check the whole loop once

- [ ] Generate a **practice statement** from their data file and eyeball it: is every number
      one we actually measured? (No made-up figures — [LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure).)
- [ ] Scan the QR codes and confirm they open the right pages.
- [ ] Add them to the monthly-statement email list (02).

## Done when

They're marked **customer**, the $175 cleared and the monthly plan is **active** (07), their
data file exists in `localDNS`, and a practice statement renders honestly. The first real one
goes out on the next monthly run — and don't forget to ask for that Google review (01) once
it lands.
