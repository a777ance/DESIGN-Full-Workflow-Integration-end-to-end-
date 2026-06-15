# Budget & Expense Tracker — A777ance

Single source of truth for costs. ZORT reviews this monthly and flags any line that exceeds
budget or any new expense before it's committed. Pre-revenue burn target: <$30/mo.

**Last updated:** 2026-06-04

---

## Recurring Costs

| Category | Item | Budget/mo | Actual/mo | Status |
| -------- | ---- | --------- | --------- | ------ |
| AI tooling | Anthropic API (NARF + ZORT) | $15 | ~$5–15 | Estimated; check console monthly. **2026-06-15: autonomous usage (routines, GitHub Actions, `claude -p`) now bills against a capped programmatic credit ($20 Pro / $100 Max-5x / $200 Max-20x), then API rates. Model plan tier vs. expected overage — see `docs/ai-cto/ai-process-efficiency.md` (TD-15).** |
| Dev tooling | GitHub Team (private repos) | $4 | $0–4 | Free tier current |
| Infrastructure | Domain (annual ÷ 12) | $2 | ~$2 | |
| Infrastructure | Email forwarding | $0 | $0 | Gmail alias currently free |
| Hardware | t630 power (~65 W × 730 h/mo) | $6 | ~$4–6 | At $0.12–0.15/kWh |
| Compliance | 1099 filing (annual, amortized) | $1 | $0 | Not yet triggered |
| **Total** | | **$28** | **~$11–27** | Within target |

**Pre-revenue burn target:** <$30/mo. Currently within range.

---

## One-Time / Capital Costs

| Item | Date | Amount | Notes |
| ---- | ---- | ------ | ----- |
| HP t630 hardware | (pre-repo) | ~$150 | Sunk cost; no ongoing depreciation tracked |

---

## Future Costs (not yet committed)

| Item | Trigger | Est. Monthly | Notes |
| ---- | ------- | ------------ | ----- |
| Stripe fees | First customer | ~$1.23/customer/mo | 2.9% + $0.30 per transaction |
| Statement mailing | If mailed | ~$1/customer/mo | Optional; email is $0 |
| Gusto / Track1099 | First operator payment | ~$5–10/form/yr | 1099-NEC filing |
| Legal (contractor classification) | Before operator #3 | $500–2,000 one-time | Do not skip |
| Legal (Alliance coin / token) | If capital raise considered | $5,000–20,000+ | Securities law; required before any public offering |
| CRM / Airtable (Stage 08) | First customer | $0–20/mo | Free tier may cover Phase 1 |
| Squarespace / website | Stage 01 launch | ~$16–23/mo | Annual plan cheaper |
| Google Voice / OpenPhone (Stage 04) | First customer | ~$10–15/mo | Business line |

---

## Budget vs. Actual — Monthly Log

Entries appended after each monthly close — newest first (reverse-chronological). Format: `YYYY-MM | Total actual | vs. budget | Notes`

_(no entries yet — first close after June 2026)_

---

## Accounting Notes

- **Chart of accounts** (to set up in QuickBooks when connected):
  - Revenue: Customer Subscriptions, Setup Fees, Operator Dues
  - COGS: Statement Production (API costs), Operator Payments (pass-through)
  - OpEx: AI Tooling, Dev Tooling, Infrastructure, Compliance, Legal, Marketing
- **Bank reconciliation:** Monthly, once any revenue exists. Target: <5 days after month-end.
- **QuickBooks:** Not yet connected. Set up before first customer payment clears.
