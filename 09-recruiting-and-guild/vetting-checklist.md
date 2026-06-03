# Operator vetting checklist — the gate to `active`

Vetting **is** the trust pitch — the thing cheap-tech competitors can never copy. An
operator goes into people's home networks, so this gate is heavy on purpose and is *not*
optional ([LAUNCH-NOTES #12](../LAUNCH-NOTES.md#12-operator-onboarded-without-vetting)).

> **Status:** first draft, not a finalized legal standard. "Guild-certified" must be
> defined with counsel before scaling (open decision, `MARKETING`). Treat the items below
> as the intended bar, and confirm the legal specifics (what checks are permissible in
> the jurisdiction, bonding/insurance requirements) before relying on them.

---

## The gate (`status: vetting → active`)

- [ ] **Identity verified** — government ID matches the application.
- [ ] **Background check** — passed (scope/provider `CHANGE_ME`, confirm with counsel).
- [ ] **Bond / liability insurance** — active (a service entering homes; `CHANGE_ME` limits).
- [ ] **References** — at least two checked (a converted customer has the best reference:
      their own operator and their Statement history).
- [ ] **Technical competency** — can follow `localDNS`'s setup guide and pass its
      verification block unaided (DNSSEC `ad` flag, DoT split, services up).
- [ ] **Contractor agreement e-signed** (stage 10) — relationship + scope + data handling.
- [ ] **W-9 on file** (stage 10) — *before* any payout.
- [ ] **Data-handling briefing** — the honesty rule (no invented figures), the privacy
      note (aggregate-only; categories never domains — see the live Statement), and PII
      discipline.

## Writes to the record (08 → `operator.vetting`)

```json
{ "background_check": "passed", "bond": "active",
  "references": ["ref-1", "ref-2"], "agreement_signed_ts": "..." }
```

Only when every box is checked does `status` flip to `active` and the operator may be
assigned a route and paid.

## Why it's the product, not overhead

The whole moat argument: Tailscale + NextDNS replicate most of the *tech* for ~$30/yr;
they cannot replicate **a vetted, bonded, local human you trust in your home.** Every hour
spent on vetting buys defensibility the competition can't.
