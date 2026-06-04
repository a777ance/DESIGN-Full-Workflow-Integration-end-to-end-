# The monthly run + writing the "Handled For You" notes

The repeatable steps of the monthly statement cadence, and a guide to the one thing you
actually write each month — the human notes. Everything else is `localDNS`'s tool, run as-is.
This is a routine, not a rebuild: you never edit the statement itself.

---

## The monthly checklist

Do this per route, for every household that's paid up (07).

**The parts localDNS does (just run them)**
- [ ] Refresh each box's real numbers (the measured stuff — lookups, blocks, uptime). There's
      a practice mode too, for a dry run with no box attached.
- [ ] Build the statements from those numbers plus your notes.

**The parts this stage does**
- [ ] **Write the human notes** for each home (below) *before* you build.
- [ ] **Honesty check:** every number on the finished statement is one the box really measured.
      Leave off anything that isn't built yet (the by-category gigabytes, the neighbor
      comparison) until it's real — [LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure).
- [ ] **Paid check:** skip anyone who isn't paid up (07). It's supposed to happen
      automatically (11), but confirm it actually did this month.
- [ ] **Send it:** email everyone the link; mail paper to whoever asked for it; check the QR
      codes open the right pages.
- [ ] **Note it on the record (08):** mark when each statement was generated and sent.

**After the run**
- [ ] Check the operator's portfolio rolled up right (the totals, the to-do list, the work log).
- [ ] Scan one statement's QR on an actual phone, start to finish, to be sure.

---

## Writing the "Handled For You" notes

This is the only part of the statement written by a person each month, and it's the part that
makes the whole thing feel human. Three pieces:

| Piece | What goes in it | How it should read |
| ----- | --------------- | ------------------ |
| **Handled For You** | The real work you did this month, signed by name | Like a friendly note: *"Cloudflare pushed a security update; your box was patched the same day — Jose."* Always *your home / your TV / your box*, never "the endpoint." |
| **A neighbor to meet** (optional) | An Alliance member who matches their setup | A warm intro, not an ad. *"Marco, two miles over, is great with home-theater and Plex — thought you two would hit it off."* |
| **Last month / this year** | The simple period-over-period and year-to-date totals | Plain, like a bank statement. Only numbers the box measured. |

**The rules**
- Calm voice (00). Sell the quiet. *"Three things happened to your home this month. You felt
  none of them — that's the point."*
- **Be honest.** Every line is real work that actually happened; every number is measured. A
  quiet month is a *win* — say *"nothing to change this month, beautifully boring."* Never
  invent work or an upsell to fill space.
- **Sign it by name.** The named operator *is* the trust. That signature is the product.

---

## What this stage never does

- Edit the statement or the tool that builds it (`localDNS` owns those).
- Put a number on a statement that the box didn't measure ([LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure)).
- Send a statement to someone who hasn't paid ([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)).
- Keep a separate, hand-edited copy of the statement ([LAUNCH-NOTES #8](../LAUNCH-NOTES.md#8-statement-forkededited-in-this-repo-instead-of-generated-from-localdns)).
