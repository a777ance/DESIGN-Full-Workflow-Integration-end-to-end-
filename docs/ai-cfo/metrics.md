# Financial KPIs — A777ance

Definitions and Phase 1 targets. ZORT appends actuals to the metrics log after each review.

---

## KPI Definitions

| KPI | Definition | Phase 1 Target |
| --- | ---------- | -------------- |
| **Paying customers** | Households with an active Stripe subscription (not free trials) | 3 |
| **MRR** | Monthly recurring revenue from customer subscriptions only | $105/mo (3 × $35 std) |
| **ARR** | MRR × 12 | $1,152 |
| **Setup fees YTD** | Cumulative one-time setup fees collected this calendar year | $525 |
| **Customer churn rate** | % of active customers who cancel in a given month | <5% |
| **Active operators** | Non-founder operators currently paying dues | 1+ |
| **Operator dues MRR** | Monthly dues revenue from active operators | $50+/mo |
| **Net burn** | Monthly costs minus all revenue (negative = cash negative) | Break-even at customer #1 |
| **Statement cost/home** | Actual API + mailing cost per Statement produced | <$1 |
| **LTV (12-month)** | Setup fee + (MRR × 12) at zero churn | $595 std ($175 + $420) / $523 founding ($175 + $348) |

---

## Unit Economics Checks

Run these whenever real transaction data exists:

1. **Does $29/mo (founding) cover tooling?** Tooling burn ~$15–27/mo → YES at customer #1 even at founding rate.
2. **Does operator margin work?** 2 homes × $35 = $70 > $50 dues → YES at 2 homes.
3. **Is statement cost honest?** Actual API cost + optional mail. Never estimate.
4. **Is pricing holding?** Count renewals at posted price. Any discounts signal pricing pressure.

---

## Metrics Log

Appended by ZORT's `log_metric` tool — newest first (reverse-chronological). Each entry: `DATE | KPI | VALUE | NOTES`

`2026-06-04` | net_burn | ~$11-27/mo | Within <$30 pre-revenue target. Recommend staying on free tiers (Wave/GitHub Pages/Google Voice) to customer #3; defer QuickBooks.
`2026-06-04` | MRR | $0 | No active subscriptions. $0 is $0. All revenue figures in files are labeled hypotheses until first transaction clears.
`2026-06-04` | paying_customers | 0 | 2026-06-04 first ZORT review. Pre-revenue. Phase 1 gate not met. Blocker: Stripe not connected (Stage 07) — no way to collect a dollar today.
`2026-06-10` | paying_customers | 0 | ZORT review #2 (2026-06-10). Still pre-revenue, no change since #1. Phase 1 gate not met (0/6). Two RED blockers: Stripe not connected (Stage 07, CEO sign-up) AND honest Statement #1 not deployable (localDNS flow-accounting not stood up + placeholder peer data violates house honesty rule). Both gate revenue.
`2026-06-10` | net_burn | ~$11-27/mo | Within <$30 target. WATCH: localDNS Step 12 LLM router has an Anthropic cloud-overflow tier that could push the AI line above its $15/mo budget. Recommend local-models-only default until customer #1.
