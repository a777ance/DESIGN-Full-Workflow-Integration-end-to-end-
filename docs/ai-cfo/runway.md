# Cost Structure & Break-even — A777ance

Pre-revenue cost structure, revenue projections, and break-even analysis.
Update when real costs or revenue change.

---

## Monthly Costs (pre-revenue)

| Category | Item | Est. Monthly | Notes |
| -------- | ---- | ------------ | ----- |
| AI tooling | Anthropic API (NARF + ZORT daily runs) | $5–15 | ~$0.01/run Haiku; $0.10–0.50/run Opus |
| Dev tooling | GitHub (private repos) | $0–4 | Free tier covers 5 private repos |
| Infrastructure | Domain + email forwarding | ~$2 | |
| Hardware | t630 power (~65 W × 24 h) | ~$4–6 | At $0.12–0.15/kWh |
| **Total pre-revenue** | | **~$15–27/mo** | |

**No VC, no loans. Break-even at customer #1.**

---

## Revenue Scenarios (all hypothetical until validated)

| Scenario | Gross MRR | Net MRR (after Stripe) | Notes |
| -------- | --------- | ---------------------- | ----- |
| 1 customer | $32 | ~$31 | Covers tooling; net positive day 1 |
| 3 customers (Phase 1 gate) | $96 | ~$92 | + $525 setup fees YTD |
| 10 customers | $320 | ~$307 | Real side income; 1 operator covers dues |
| 20 customers + 2 operators | $640 + $100 dues = $740 | ~$718 | Comfortable; operator model proving out |

---

## Stripe Fee Impact

At $32/mo per customer: fee = $0.30 + 2.9% × $32 = **$1.23/transaction**

At scale (10 customers): $12.30/mo in fees on $320 gross → ~3.8% drag. Negligible.

For setup fees ($175 one-time): fee = $0.30 + 2.9% × $175 = **$5.38/transaction**. Still small.

No action needed until significant scale. Re-evaluate if Stripe fees exceed 5% of gross.

---

## 1099 Compliance Cost

When operators earn >$600/calendar year from any single source, a 1099-NEC is required (US).
Cost: Gusto or Track1099 — estimate **$5–10/form**. Minimal. Track start dates and cumulative payments per operator in Stage 10.

**Risk:** Misclassifying employees as contractors. Requires legal review before scaling beyond 2–3 operators. Cost of misclassification: back taxes + penalties. This is the largest compliance risk in the model.

---

## Break-even Summary

| Milestone | Revenue | Cost | Net |
| --------- | ------- | ---- | --- |
| Pre-launch | $0 | ~$20/mo | –$20 |
| 1 customer | $32/mo | ~$20/mo | **+$12/mo** |
| Phase 1 gate (3 customers) | $96/mo | ~$20/mo | **+$76/mo** |
| 10 customers | $320/mo | ~$25/mo | **+$295/mo** |

The constraint is founder time, not money. No runway problem at any realistic scenario.
