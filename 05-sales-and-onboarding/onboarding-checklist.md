# Onboarding checklist — close → first Statement

The owned, ordered steps from a signed quote to a household receiving its first monthly
Statement. Each step writes to the CRM record. The provisioning step is the seam between
this repo and `localDNS` — never skip or hand-wave it
([LAUNCH-NOTES #7](../LAUNCH-NOTES.md#7-close--provision-hand-off-is-undocumented)).

---

## On close (quote signed)

- [ ] Flip CRM `status`: `qualified → customer`; stamp `quote.signed_ts`.
- [ ] **Collect the setup fee** and create the monthly retainer plan (07). Confirm the
      first charge clears *before* the truck rolls.
- [ ] Confirm install appointment (Setmore / phone, 04).

## Provision the stack (handoff → localDNS)

- [ ] Deploy the t630 by following **`localDNS`'s setup guide** (README Sections/Steps).
      This repo does not duplicate the deploy.
- [ ] Run `localDNS`'s verification block (DNSSEC `ad` flag; DoT split; Pi-hole + Uptime
      Kuma up; `wg show`). A home isn't "provisioned" until verification passes.
- [ ] Create the household's **home-JSON** in `localDNS/docs/statements/data/clients/`
      (the single source of truth a Statement renders from).
- [ ] Record the home-JSON path on the CRM record (`statement.home_json_path`).

## Set up the recurring artifact

- [ ] Confirm delivery channels on the record (`statement.delivery_channels`: email,
      mail, or both).
- [ ] Seed the operator **sidecar** for month 1 (the "Handled For You" log starts at
      install — "set up and verified your appliance — `[operator]`").
- [ ] Schedule the household into the monthly run (06).

## Verify the loop

- [ ] Generate a **dry-run Statement** from the home-JSON (06 → `localDNS` generator) and
      eyeball it for honesty (no unmeasured figures — [LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure)).
- [ ] Confirm the QR codes resolve (status page + online statement).
- [ ] Add the customer to the monthly-Statement email segment (02/email-lists).

## Done when

The household is `status = customer`, billing is `active` (07), the home-JSON exists in
`localDNS`, and a dry-run Statement renders honestly. The first real Statement goes out
on the next monthly run.
