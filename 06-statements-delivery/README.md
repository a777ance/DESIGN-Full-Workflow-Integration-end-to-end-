# 06 — Statements delivery

**Lives in:** the `localDNS` generator (`docs/statements/`) + email + print/mail + QR.
**Go-live / sync:** run the monthly generate-from-roster job; email + mail the Statement;
QR codes go live.

**The center.** This is what everything else surrounds — and **this stage does not own
or rebuild the Statement.** The artifact is the gold standard, built and published in
`localDNS`. Stage 06 is a *delivery runbook*: schedule the run, assemble the operator
sidecar, deliver on cadence, stop there.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`monthly-run.md`](monthly-run.md) | The monthly cadence checklist + the operator-sidecar authoring guide |

## The two Statements (built in localDNS)

| Statement | Audience | Source |
| --------- | -------- | ------ |
| **Network Activity Statement** | The homeowner — a 1–2 page monthly value receipt, the "sticker on the door" | `localDNS/docs/statements/client/*.html` |
| **Alliance Member Portfolio** | The operator — one fleet view over a book of homes | `localDNS/docs/statements/operator/*.html` |

What's on each (Account Summary, "Handled For You," Traffic Allocation, Household
Profile, "How You Compare," "Connect in the Alliance," the QR codes) is documented and
rendered in `localDNS/docs/statements/README.md` — read it; don't restate it here.

## Why we deliver, not rebuild

The Statement is the gold standard precisely because it has **one** source of truth
(`localDNS/docs/statements/`), is JSON-driven, self-contained, and honest about which
figures are real. Forking it here would create the exact drift stage 00 exists to
prevent, and could print stale or invented numbers
([LAUNCH-NOTES #8](../LAUNCH-NOTES.md#8-statement-forkededited-in-this-repo-instead-of-generated-from-localdns)).
So stage 06 touches the generator only through its intended inputs.

## The monthly run

```
1. collect/refresh stats on each box   localDNS: collect_stats.py  (Pi-hole/Kuma/wg/nft)
2. assemble the operator SIDECAR       this stage: "Handled For You" log + Alliance match + prior/YTD
3. compose → home-JSON                 localDNS: compose.py
4. render the Statements               localDNS: generate_client.py / generate_operator.py
5. GATE on a paid account (07)         this stage: skip unpaid — never give away the receipt
6. deliver                             this stage: email + print/mail + QR
```

Steps 1, 3, 4 are `localDNS`'s pipeline (run as-is). Steps 2, 5, 6 are this stage's job.
The per-run checklist and the sidecar authoring guide live in [`monthly-run.md`](monthly-run.md).

## The sidecar — the personal, named proof of work

The one input this stage genuinely *owns* is the **operator sidecar** (`localDNS`'s
`tools/collect/sample-sidecar.json` shape): the "Handled For You" log written like local
patch notes and **attributed by name** ("*Cloudflare pushed a security update; your
appliance was patched the same day — Jose*"), plus the Alliance match and the prior/YTD
figures. This is where the human touch enters the artifact. Keep it in the calm voice
(00) and *your home / your appliance*, never generic IT-speak.

## Delivery

| Channel | How | Note |
| ------- | --- | ---- |
| **Email** | "Your Statement is ready" → link to the online scrollable statement | The default |
| **Print / mail** | Print the self-contained HTML → mail (~$1) | The literal "sticker on the door" for homes that value paper |
| **QR** | Already inlined in the artifact (segno) | Status page + online statement; real, not mock |

## The honesty gate (inherited from localDNS)

Per `localDNS`'s "Data sourcing" table: queries/blocks/uptime/latency/VPN sessions are
**real today**; per-category GB volume is **buildable** (flow-accounting scaffolded, not
yet stood up); peer-average benchmarks **need a real cohort dataset**. **Do not print a
figure the box didn't measure** ([LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure)).
Scope each Statement to what's real until the rest is stood up.

## The richer-copy seam

`localDNS` flags `compose_prose()` as the single point to swap in a Claude (Haiku) call
for richer copy at ~$0.01/home, once wanted — the inputs are already assembled. That's
the only generator change this stage would ever request, and it lives in `localDNS`.

## Hand-offs

- **← 05/08:** the provisioned, paid customer + the roster record drive the run.
- **← 07 payments:** the paid/unpaid gate.
- **→ 09 recruiting:** a "Connect in the Alliance" tap becomes an operator-interest record.
- **→ 02 email:** the "Statement is ready" send + the in-Statement referral CTA.
