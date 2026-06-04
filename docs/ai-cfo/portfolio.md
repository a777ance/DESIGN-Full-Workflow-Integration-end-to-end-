# ZORT — AI CFO Portfolio — A777ance

ZORT's working memory for financial health across the portfolio. Read at session start; update at session end with new metrics, decisions, or financial status changes.

**Last updated:** 2026-06-04

---

## Session Protocol

1. Read this file first — it is the financial snapshot.
2. Read `MARKETING/README.md` — all pricing, unit economics, and open decisions live there.
3. Read `MARKETING/docs/ai-cfo/context.md` — financial spoke context.
4. Work on the highest-priority item in "Current Focus" unless the user directs otherwise.
5. Before ending a session: record any metric updates, financial decisions, or status changes here.

---

## Current Financial State — 2026-06-04

**Phase:** 1 — Prove liquidity (now → 90 days)

| Metric | Phase 1 Target | Actual | Notes |
| ------ | -------------- | ------ | ----- |
| Paying customers | 3 | 0 | Pre-revenue |
| MRR | $105/mo (3 × $35 std) | $0 | Pricing untested; founding rate $29/mo |
| Setup fees collected | $525 (3 × $175) | $0 | |
| Active operators (non-founder) | 1+ | 0 | |
| Operator dues MRR | $50+/mo | $0 | Dues set (FIN-001); no operators yet |
| Monthly tooling burn | — | ~$15–27 | API + infra + domain |
| Net burn | — | ~$15–27 | Break-even at customer #1 |

**Phase 1 financial gate:** 3 paying customers, 3+ months each, at posted price. **Not met.**

---

## Top Financial Priorities — 2026-06-04

1. **Set up Stripe billing before the first customer.** Stage 07 in DESIGN. The recurring plan and invoice must exist before the setup fee clears — not as a retroactive fix.
2. **Sign the first paying customer.** $175 setup + $35/mo standard ($29/mo founding rate for the first ~5). Every financial model here is hypothesis until there is one real transaction.
3. **Validate the price point with 3 renewals.** One payment proves nothing. Three customers × 3+ months = data. Founding cohort locked at $29/mo for 12 months — validate renewal at that rate first.

---

## Open Financial Decisions

| Decision | Blocks | Where to resolve |
| -------- | ------ | ---------------- |
| Validate $175 setup + $35/mo pricing (band $29–39; founding $29/mo) | Statement ROI, operator pitch, Stage 05 | 3-customer pilot |
| Define what $50/mo dues unlocks | Operator onboarding pitch | MARKETING + legal |
| Operator unit economics: homes-per-operator to cover dues | Recruiting pitch | Real operator data |
| Contractor vs. employee classification | Stage 10 compliance | Requires lawyer before scaling |
| First channel partner pilot (real estate / HOA / elder-care) | Phase 2 revenue pipeline | MARKETING |

---

## Cost Structure (pre-revenue)

| Line item | Est. monthly | Notes |
| --------- | ------------ | ----- |
| Anthropic API (NARF + ZORT) | $5–15 | Scales with daily run frequency |
| GitHub (private repos) | $0–4 | Free tier covers current 5-repo setup |
| Domain + email | ~$2 | |
| t630 power (~65 W × 24 h) | ~$4–6 | At $0.12–0.15/kWh |
| Statement mailing (optional) | ~$1/customer/mo | Email delivery is $0 |
| Stripe fees | 2.9% + $0.30/txn | On customer payments only |
| **Total pre-revenue burn** | **~$15–27/mo** | Essentially zero |

**Break-even:** 1 customer at $29/mo (founding rate) still covers the tooling burn ($15–27/mo).

---

## Unit Economics (hypotheses — unvalidated)

| Per customer | Amount | Notes |
| ------------ | ------ | ----- |
| Setup fee (one-time) | $175 | Covers install labor; sets expectations |
| Monthly subscription | $35/mo standard; $29/mo founding | $29 locked 12mo for first ~5 customers |
| Statement production cost | ~$0.01–$1/mo | API (~$0.01 Haiku) + optional mail (~$1) |
| Stripe fee per month | ~$1.32 | 2.9% + $0.30 on $35 |
| **Net per customer/mo** | **~$33–34** (std) / **~$27** (founding) | After statement + Stripe; before operator share |

| Per operator | Amount | Notes |
| ------------ | ------ | ----- |
| Monthly dues | $50/mo | FIN-001; covers tooling + match + brand |
| Break-even homes for dues | ~2 homes at $35/mo ($70 > $50 dues) | Viable from first referral |

---

## Phase Gate Checklist — Phase 1 → Phase 2

Do not start Phase 2 financial planning until all of these are true:

- [ ] Stripe billing live and tested (setup fee + recurring)
- [ ] At least 3 paying customers (real money collected)
- [ ] Pricing validated (customers renewed at posted price for 3+ months)
- [ ] At least 1 non-founder operator paying dues
- [ ] Contractor classification confirmed with legal counsel
- [ ] 1099 compliance flow tested (W-9 collected, 1099 template ready)

---

## Recent Financial Decisions

| Date | Decision | See |
| ---- | -------- | --- |
| 2026-06-04 | Member dues set to **$50/mo flat** (mid-point of $40–60 range) | decisions.md FIN-001 |
| 2026-06-04 | Pricing set (ADR-007): $175 setup + $35/mo standard; band $29–39; founding cohort $29/mo locked 12mo | MARKETING ADR-007 |
