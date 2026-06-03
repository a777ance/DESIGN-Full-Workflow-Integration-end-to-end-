# 11 — Automations

**Lives in:** Zapier / Make + the `localDNS` Statement pipeline.
**Go-live / sync:** enable the zaps that carry a record stage→stage; never hand-copy.

The glue. In `localDNS`, the components are useless until DNS *flows* between them; here,
the stages are useless until a *record* flows between them. Making automation its own
stage forces a single map of every hand-off and a single owner for the seams.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`automation-map.md`](automation-map.md) | Every stage→stage hand-off and the automation that carries it |

## The one rule

If moving a record from tool A to tool B requires a human to **retype** it, that's a
dropped packet — a bug in this stage, not an acceptable manual step
([LAUNCH-NOTES #15](../LAUNCH-NOTES.md#15-a-stage-hand-off-requires-a-human-to-retype-data)).
Every arrow in the [funnel topology](../README.md#the-funnel-topology) is an automation
or a logged TODO to build one.

## The largest automation is localDNS's pipeline

The Statement run itself — roster record → `collect_stats.py` → `compose.py` →
`generate_client.py`/`generate_operator.py` → rendered Statement → delivery — is the
biggest automation in the map. This stage **schedules and connects** it (and gates it on
billing); it does not modify the generator.

## Build order (stand up as each tool goes live)

1. **Intake → CRM** (03→08): the first and most important seam — a form submit creates a
   lead record. Until this works, nothing else matters.
2. **Booking + call logging → CRM** (03/04→08).
3. **Close → billing + provisioning trigger** (05→07 + the `localDNS` handoff).
4. **Billing status → delivery gate** (07→06): the paid/unpaid gate.
5. **Monthly Statement run** (06, the `localDNS` pipeline) + "Statement ready" email (02).
6. **Hand-raise → operator-interest** (06→09) and **operator active → W-9 request** (09→10).

## Hand-offs

This stage touches **all** of them — it *is* the connective tissue. See the full table in
[`automation-map.md`](automation-map.md).
