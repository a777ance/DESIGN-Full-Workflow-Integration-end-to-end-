# Quote template

A **scoped** quote — it names what's delivered, so the retainer is anchored to value,
not a round number. Figures are `MARKETING` hypotheses (`CHANGE_ME` until validated);
the setup fee is never discounted. Written to the CRM as `quote.*` on the record.

---

## Quote — `[Household name]` · `[date]`

**Prepared by:** `[operator name]` · A777ance guild
**For:** `[address]` · route `[RT-####]`

### What you get
- A managed home-network appliance (DNS filtering, encrypted DNS, VPN, monitoring, QoS)
  installed on your network.
- Network-wide ad/tracker blocking and DNSSEC — every device, no app to install.
- A **monthly Network Activity Statement** — the plain-language proof of what we handled,
  by email and (optionally) mailed on paper, scrollable from a QR code.
- A real person — your operator — you can call.

### Scope (this is what anchors the price)
| Item | This home |
| ---- | --------- |
| Homes / locations | `[1]` |
| Approx. devices covered | `[from intake home_profile.devices_est]` |
| Mailed paper statement? | `[yes/no]` (+~$1/mo if mailed) |
| Special concerns addressed | `[from intake concerns[]]` |

### Investment
| Line | Amount | Note |
| ---- | ------ | ---- |
| One-time setup | `$CHANGE_ME` (~$150–200) | Real install labor — **not discounted** |
| Monthly retainer | `$CHANGE_ME` (~$25–40/mo) | The ongoing quiet + the Statement |

> No long-term contract. Cancel anytime; the value is the monthly proof, not a lock-in.

### Next step
Sign below (e-sign) → we schedule the install → your first Statement lands the following
month.

---

**Notes for the operator (not shown to customer):**
- Pull `devices_est` and `concerns[]` from the intake (03) so the scope reads as
  *personal*, not boilerplate.
- On signature: write `quote.signed_ts`, flip `status → customer`, trigger setup-fee
  collection (07) and the onboarding checklist.
- Statement-cost reality: ~$0.01/home to generate + ~$1 if mailed (`MARKETING`).
