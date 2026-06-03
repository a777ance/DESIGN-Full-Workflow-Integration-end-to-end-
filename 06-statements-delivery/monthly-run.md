# Monthly run & sidecar authoring

The owned, repeatable steps of the monthly Statement cadence, and the guide for the one
input this stage genuinely authors — the **operator sidecar**. Everything else is
`localDNS`'s pipeline, run as-is. This is a *runbook*, not a generator: it never edits the
Statement HTML or the generator code.

---

## The monthly checklist

Run per route, for every `billing.status = active` household on it.

**Generate (localDNS pipeline — run as-is)**
- [ ] Refresh on-box stats: `collect_stats.py` (Pi-hole / Uptime Kuma / `wg` / nftables)
      — or `--sample` for a dry run with no box.
- [ ] Compose → home-JSON: `compose.py --stats … --sidecar … --out data/clients/<home>.json`.
- [ ] Render: `generate_client.py` (+ `generate_operator.py` for the portfolio).

**This stage's owned steps**
- [ ] Assemble the **sidecar** for each home (see below) *before* composing.
- [ ] **Honesty gate:** confirm every figure on the rendered Statement is one the box
      actually measured (per `localDNS`'s "Data sourcing" table) — scope out per-category
      GB volume and peer benchmarks until those datasets are real.
- [ ] **Payment gate:** skip any household not `active` in billing (07). The gate is an
      automation (11), but verify it held this run.
- [ ] **Deliver:** email (link to the online statement) + print/mail where
      `delivery_channels` includes `mail` + confirm the inlined QR codes resolve.
- [ ] **Write back to the CRM (08):** set `statement.last_generated` and
      `statement.last_delivered` on each household record.

**After the run**
- [ ] Confirm the operator **portfolio** rolled up correctly (KPIs, attention queue, the
      work log) for each route.
- [ ] Spot-check one Statement end-to-end on a phone via its QR.

---

## Sidecar authoring guide (the human touch)

The sidecar is the only Statement input composed by a person each month. Its **shape** is
owned by `localDNS` (`localDNS/docs/statements/tools/collect/sample-sidecar.json`) — do
not redefine it here; fill that shape. It carries three things:

| Sidecar part | What goes in it | Voice |
| ------------ | --------------- | ----- |
| **Handled For You** log | The real work done this month, by name | Local patch notes: "*Cloudflare pushed a security update; your appliance was patched the same day — Jose.*" Always *your home / your appliance / your living-room TV* — never generic IT-speak. |
| **Alliance match** | The profile-matched member (face + blurb + connect QR) | Opt-in; a warm introduction, not an ad. |
| **Prior / YTD** | The period-over-period + year-to-date figures | Brokerage-statement plain; only figures the box measured. |

**Rules**
- Calm voice (00); pest control, not lawn care — sell the quiet.
- **Honesty of the kept document:** every line in the log is real work that happened;
  every figure is measured. If nothing changed, use the **affirmation** path
  ("nothing to change this month, beautifully boring"), never an invented upsell.
- Attribute by name — the named operator *is* the trust.

---

## What this stage never does

- Edit the Statement HTML or the generator (`localDNS` owns them).
- Print a figure the box didn't measure ([LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure)).
- Deliver to an unpaid account ([LAUNCH-NOTES #9](../LAUNCH-NOTES.md#9-statement-delivered-to-an-unpaid-account)).
- Fork the sidecar schema ([LAUNCH-NOTES #8](../LAUNCH-NOTES.md#8-statement-forkededited-in-this-repo-instead-of-generated-from-localdns)).
