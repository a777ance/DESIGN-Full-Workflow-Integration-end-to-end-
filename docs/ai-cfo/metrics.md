# Financial KPIs — A777ance

Definitions and Phase 1 targets. ZORT appends actuals to the metrics log after each review.

---

## KPI Definitions

| KPI | Definition | Phase 1 Target |
| --- | ---------- | -------------- |
| **Paying customers** | Households with an active Stripe subscription (not free trials) | 3 |
| **MRR** | Monthly recurring revenue from customer subscriptions only | $96/mo |
| **ARR** | MRR × 12 | $1,152 |
| **Setup fees YTD** | Cumulative one-time setup fees collected this calendar year | $525 |
| **Customer churn rate** | % of active customers who cancel in a given month | <5% |
| **Active operators** | Non-founder operators currently paying dues | 1+ |
| **Operator dues MRR** | Monthly dues revenue from active operators | $50+/mo |
| **Net burn** | Monthly costs minus all revenue (negative = cash negative) | Break-even at customer #1 |
| **Statement cost/home** | Actual API + mailing cost per Statement produced | <$1 |
| **LTV (12-month)** | Setup fee + (MRR × 12) at zero churn | $559 ($175 + $384) |

---

## Unit Economics Checks

Run these whenever real transaction data exists:

1. **Does $32/mo cover tooling?** Tooling burn ~$15–27/mo → YES at customer #1.
2. **Does operator margin work?** 2 homes × $32 = $64 > $50 dues → YES at 2 homes.
3. **Is statement cost honest?** Actual API cost + optional mail. Never estimate.
4. **Is pricing holding?** Count renewals at posted price. Any discounts signal pricing pressure.

---

## Metrics Log

Appended by ZORT's `log_metric` tool. Each entry: `DATE | KPI | VALUE | NOTES`

_(no entries yet — first real data appears after the first customer payment clears)_
