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

The full append-only log lives in [`metrics-history.md`](metrics-history.md) (split out
2026-07-01 to keep this briefing small — see [`../ai-cto/process-efficiency.md`](../ai-cto/process-efficiency.md) §①).
Read that file only when you need the history; the current reading is below.

**Latest reading — ZORT review #14, 2026-06-22 (Day 18 of the 90-day cash-flow window):**

| KPI | Value | Note |
| --- | ----- | ---- |
| paying_customers | **0** | Pre-revenue; Phase 1 gate 0/6, unchanged since review #1. |
| MRR | **$0** | No active subscriptions. |
| net_burn | **~$11–27/mo** | Within the <$30 pre-revenue target (the only green line, and only because nothing has shipped). |

**Two RED blockers, both open since review #1, on separate critical paths:**
1. **Stripe not connected** (Stage 07) — design is complete but there's no live account / Products / test txn. Only input needed is CEO time; $0 cost — the cheapest blocker in the business.
2. **No honest Statement #1 shippable** (NARF's domain) — localDNS flow-accounting layer is scaffolded-not-stood-up and "How You Compare" is a placeholder; the honesty rule forbids invented peer averages on a kept $175 document. This is a *revenue* delay, not just tech.

**Carry-forward:** the $45/mo heavy-home tier (Stage 07) is still not folded into `runway.md` scenarios.

**Logging discipline (set 2026-07-01):** log only the *delta* from the prior reading — don't
re-state an unchanged situation in full. Restating the same two paragraphs daily is what bloated
the old log to ~3,400 words.

---
