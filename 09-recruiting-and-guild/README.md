# 09 — Recruiting & the guild

**Lives in:** an operator-application funnel + vetting + Setmore (interviews).
**Go-live / sync:** open applications; run vetting; onboard into the guild.

The flywheel. This is where a Statement's "Connect in the Alliance" hand-raise becomes a
**vetted, onboarded operator** who produces Statements for a book of homes — closing the
loop that everything above opened.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`operator-funnel.md`](operator-funnel.md) | The customer→operator conversion path (the dual-hat flywheel) |
| [`vetting-checklist.md`](vetting-checklist.md) | The gate to `active` — vetting *is* the trust pitch |

## Why the customer is the operator pipeline

DoorDash recruits dashers and diners separately. A777ance doesn't: **a happy customer is
a latent operator** — they like the stack, they're handy, they want gig income. That
dual-hat conversion is the growth loop and the moat, so the operator funnel is wired to
start *inside the Statement* (the "Connect in the Alliance" hand-raise → `operator_interest`
on the record), not as a separate cold-recruiting effort. Anyone can be a customer, an
operator, or both, whenever they want.

## Why vetting is heavy on purpose

Background-checked and bonded members **are** the trust pitch competitors with cheaper
tech can never copy — vetting is the product, not overhead. Onboarding an unvetted
operator into people's home networks torches the moat in one incident
([LAUNCH-NOTES #12](../LAUNCH-NOTES.md#12-operator-onboarded-without-vetting)). See
[`vetting-checklist.md`](vetting-checklist.md).

## The operator record & money

An operator is a first-class record (`../08-client-list-and-crm/schema.md` → `operator`):
`status` (`applicant`→`vetting`→`active`), `converted_from` (the household they were),
`routes[]` (their book), `dues` (platform member subscription — amount TBD in
`MARKETING`), `vetting`, and `tax` (owned by stage 10). Operators pay the platform **dues**
and bill customers **directly**; the platform takes dues + customer membership, not a cut
of every job.

## Hand-offs

- **← 06 statements:** the "Connect in the Alliance" hand-raise creates the interest record.
- **→ 10 compliance:** an operator can't be paid until W-9 + agreement are on file.
- **↔ 08 CRM:** the operator + route records live there.
- **→ 02 geo:** a route at density with no operator is a recruiting trigger.
