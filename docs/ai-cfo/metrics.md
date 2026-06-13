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
`2026-06-11` | paying_customers | 0 | ZORT review #3 (2026-06-11). Still pre-revenue; no change since #2 (7 days). Phase 1 gate 0/6. Two RED blockers persist: (1) Stripe not connected (Stage 07 — CEO signup, $0 cost, only blocker input is CEO time); (2) no honest Statement #1 shippable — localDNS flow-accounting layer still scaffolded-not-stood-up, house honesty rule forbids invented peer data. Blocker 2 is NARF's domain and is a REVENUE delay, not just tech.
`2026-06-11` | net_burn | ~$11-27/mo | Within <$30 target. WATCH (confirmed from localDNS source): Step 12 LiteLLM router defaults local-Ollama-first (good) but ships an Anthropic cloud-overflow tier that could silently push the AI line above its $15/mo budget. Cheapest control: leave the Anthropic key unpopulated in ~/llm-router/.env until customer #1 so overflow cannot fire. NARF/CEO config call; no spend committed.
`2026-06-12` | paying_customers | 0 | ZORT review #4 (2026-06-12). Still pre-revenue; no change since #3 (1 day). Phase 1 gate 0/6. Both RED blockers persist verbatim: (1) Stripe not connected — Stage 07 confirms two-charge model ($175 setup never discounted + $35/mo) but the README is design-only; no live account, no test txn. Only input needed is CEO time. (2) No honest Statement #1 shippable — localDNS README confirms the flow-accounting layer is still scaffolded-not-stood-up (MARKETING open decision lists it explicitly), and the "How You Compare" benchmark is a placeholder; house honesty rule forbids shipping invented peer averages on a kept document. Blocker 2 is NARF's domain and is a REVENUE delay.
`2026-06-12` | net_burn | ~$11-27/mo | Within <$30 target. WATCH unchanged: localDNS Step 12 LiteLLM router ships an Anthropic cloud-overflow tier; .env.example carries an Anthropic key as CHANGE_ME. Step 13 adds Open WebUI + ttyd web terminals — no new $ line (all open-source, LAN/WG-only) but more services on the t630 = marginally higher idle power, immaterial at ~10W. Cheapest control on the AI line stands: leave the Anthropic key unpopulated in ~/llm-router/.env until customer #1 so overflow cannot fire. NARF/CEO config call; no spend committed.
`2026-06-13` | paying_customers | 0 | ZORT review #5 (2026-06-13). Still pre-revenue; no change since #4 (1 day). Phase 1 gate 0/6. Both RED blockers persist verbatim: (1) Stripe not connected — Stage 07 README confirmed this session as clean design (two-charge $175-never-discounted setup + $35/mo std + $45 heavy home, paid-only statement gate, account-state machine) but NO live account, no products/prices, no test txn; only input needed is CEO time, $0 cost. (2) No honest Statement #1 shippable — localDNS README confirms flow-accounting layer is scaffolded-not-stood-up (not a setup step; MARKETING open decision) and "How You Compare" benchmark is a placeholder; house honesty rule forbids shipping invented peer averages on a kept $175 document. Blocker 2 is NARF's domain and is a REVENUE delay. Day 9 of the 90-day cash-flow window.
`2026-06-13` | net_burn | ~$11-27/mo | Within <$30 target — only green Phase 1 line, and only because nothing has shipped. WATCH unchanged (confirmed from localDNS source #5): Step 12 LiteLLM router ships an Anthropic cloud-overflow tier; .env.example carries Anthropic key as CHANGE_ME; local Ollama is the default (good). Step 13 adds Open WebUI + ttyd web terminals — no new $ line (open-source, LAN/WG-only), marginal idle power immaterial at ~10W. Cheapest control stands: leave the Anthropic key unpopulated in ~/llm-router/.env until customer #1 so overflow cannot fire. NARF/CEO config call; no spend committed.
