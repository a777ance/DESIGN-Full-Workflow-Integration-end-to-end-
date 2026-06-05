# ZORT — AI CFO Portfolio — A777ance

ZORT's working memory for financial health across the portfolio. Read at session start; update at session end with new metrics, decisions, or financial status changes.

**Last updated:** 2026-06-04 (ZORT review #1)

---

## Session Protocol

1. Read this file first — it is the financial snapshot.
2. Read `MARKETING/README.md` — all pricing, unit economics, and open decisions live there.
3. Read `MARKETING/docs/ai-cfo/context.md` — financial spoke context.
4. Work on the highest-priority item in "Current Focus" unless the user directs otherwise.
5. Before ending a session: record any metric updates, financial decisions, or status changes here.

---

## Founder mandate (recorded 2026-06-04)

- **Cash flow within 90 days** is the explicit goal. Everything routes back to: can a customer pay, and can they receive a Statement.
- **Healthy position to form an LLC in ~6 years (target ~2032).** Trigger is liability/revenue, not the calendar — see "LLC readiness" below.
- **Lean and mean.** Two cash-poor sole proprietors. Free tiers until customer #3. ZORT price-checks every new tool before commit.

---

## Current Financial State — 2026-06-04

**Phase:** 1 — Prove liquidity (now → 90 days)

| Metric | Phase 1 Target | Actual | Notes |
| ------ | -------------- | ------ | ----- |
| Paying customers | 3 | 0 | Pre-revenue — and no way to collect yet (Stripe not connected) |
| MRR | $105/mo (3 × $35 std) | $0 | Pricing untested; founding rate $29/mo |
| Setup fees collected | $525 (3 × $175) | $0 | |
| Active operators (non-founder) | 1+ | 0 | |
| Operator dues MRR | $50+/mo | $0 | Dues set (FIN-001); no operators yet |
| Monthly tooling burn | <$30 | ~$11–27 | Within target — protect it |
| Net burn | — | ~$11–27 | Break-even at customer #1 |

**Phase 1 financial gate:** 3 paying customers, 3+ months each, at posted price. **Not met.**

---

## Open Blockers (ZORT review #1 — 2026-06-04)

| # | Blocker | Severity | Owner / next step | Tracked |
| - | ------- | -------- | ----------------- | ------- |
| 1 | **Stripe not connected** — no way to take a dollar (Stage 07) | 🔴 Gates all revenue | ZORT drafts go-live checklist; CEO creates live account | Issue #1 |
| 2 | **No accounting system** — recommend defer QuickBooks, free ledger to ~10 cust (proposed FIN-005) | 🟡 | CEO decision | Issue #2 |
| 3 | **Pricing unvalidated** — $175 + $35/mo is a labeled hypothesis until 3 renewals | 🟡 | Unblocks only via real customers (needs #1) | FIN-004 |
| 4 | **Statement deploy gates first revenue** — localDNS must deliver Statement #1 (NARF's domain) | 🟡 | Confirm with NARF: can a customer receive Statement #1 this quarter? | — |

---

## Top Financial Priorities — 2026-06-04

1. **Connect Stripe before the first customer** (Stage 07). Setup-fee price + standard monthly + founding monthly + one real test txn. CEO creates the account; ZORT drafts the checklist. $0 to set up; pay-as-you-go only.
2. **Confirm the Statement is deliverable** (NARF / localDNS). I can't collect a setup fee for a product that can't ship Statement #1. This is the ZORT↔NARF revenue dependency.
3. **Sign + validate the first cohort.** One payment proves nothing; 3 customers × 3+ months at posted price = data. Until then all revenue figures are hypotheses.

---

## Open Financial Decisions

| Decision | Blocks | Where to resolve |
| -------- | ------ | ---------------- |
| Validate $175 setup + $35/mo pricing (band $29–39; founding $29/mo) | Statement ROI, operator pitch, Stage 05 | 3-customer pilot |
| **Proposed FIN-005:** defer QuickBooks, free ledger to ~10 customers | Pre-revenue burn | CEO decision (Issue #2) |
| Define what $50/mo dues unlocks | Operator onboarding pitch | MARKETING + legal |
| Operator unit economics: homes-per-operator to cover dues | Recruiting pitch | Real operator data |
| Contractor vs. employee classification | Stage 10 compliance | Requires lawyer before operator #3 |
| First channel partner pilot (real estate / HOA / elder-care) | Phase 2 revenue pipeline | MARKETING |
| Alliance coin (FIN-003) | Capital strategy | Securities lawyer before any public step — do NOT model as revenue |

---

## Lean-tooling stance (free-tier first, to customer #3)

| Stage suggests | Their $ | Lean alternative | Status |
| -------------- | ------- | ---------------- | ------ |
| QuickBooks (FIN-002) | ~$35/mo | Wave (free) / spreadsheet ledger | Recommend defer (FIN-005) |
| Squarespace (Stage 01) | $16–23/mo | GitHub Pages — $0 | Recommend free |
| CRM / Airtable (Stage 08) | $0–20/mo | Airtable/Notion free tier | Recommend free |
| Phone (Stage 04) | $10–15/mo | Google Voice — $0 | Recommend free until call volume |
| 1099 filing (Stage 10) | $5–10/form | IRS IRIS portal — free | Only triggers with paid operator |

**Only pay for Stripe fees** — and those exist only once money is coming IN. Keeps burn <$30/mo to break-even.

---

## LLC readiness (target ~2032 — watching, not acting)

Nothing now blocks a future LLC; a few $0 habits make the conversion painless:
- **Clean books from dollar one** (even a free ledger) → conversion is paperwork, not archaeology.
- **Separate customer-IN (Stage 07) and operator-OUT (Stage 10) ledgers** — already required by the stage READMEs.
- **Form earlier than 2032 if either trigger hits:** (a) a non-founder operator touches customer networks under the A777ance brand (liability), or (b) revenue ~$20–30k+. Then the ~$50–500 filing fee is cheap insurance. ZORT watches both.
- Until then, sole-prop income flows to personal returns; track every expense for deductibility.

---

## Cost Structure (pre-revenue)

| Line item | Est. monthly | Notes |
| --------- | ------------ | ----- |
| Anthropic API (NARF + ZORT) | $5–15 | Scales with daily run frequency |
| GitHub (private repos) | $0–4 | Free tier covers current 5-repo setup |
| Domain + email | ~$2 | |
| t630 power (~65 W × 24 h) | ~$4–6 | At $0.12–0.15/kWh |
| Statement mailing (optional) | ~$1/customer/mo | Email delivery is $0 |
| Stripe fees | 2.9% + $0.30/txn | On customer payments only — once revenue starts |
| **Total pre-revenue burn** | **~$11–27/mo** | Within <$30 target |

**Break-even:** 1 customer at $29/mo (founding rate) still covers the tooling burn.

---

## Unit Economics (hypotheses — unvalidated)

| Per customer | Amount | Notes |
| ------------ | ------ | ----- |
| Setup fee (one-time) | $175 | Covers install labor; never discounted |
| Monthly subscription | $35/mo standard; $29/mo founding | $29 locked 12mo for first ~5 customers |
| Statement production cost | ~$0.01–$1/mo | API (~$0.01 Haiku) + optional mail (~$1) |
| Stripe fee per month | ~$1.32 | 2.9% + $0.30 on $35 |
| **Net per customer/mo** | **~$33–34** (std) / **~$27** (founding) | After statement + Stripe; before operator share |

| Per operator | Amount | Notes |
| ------------ | ------ | ----- |
| Monthly dues | $50/mo | FIN-001; covers tooling + match + brand |
| Break-even homes for dues | ~2 homes at $35/mo ($70 > $50 dues) | Viable from first referral |

---

## Compliance calendar / risks

| Item | Trigger | Timing | Status |
| ---- | ------- | ------ | ------ |
| W-9 before first operator payment | Operator #1 | Hard stop before any payout | Not yet needed; rule is firm (Stage 10) |
| 1099-NEC filing | Operator paid ≥$600/yr | **Jan 31, 2027** | Track from operator day 1; ZORT flags every Q4 |
| Contractor vs. employee | Before operator #3 | Legal review | ⚠️ Largest $ risk; don't dictate routes/scripts/prices |
| Sales tax nexus | Before scaling past 1–2 states | State-by-state | Flag before geographic expansion |

---

## Phase Gate Checklist — Phase 1 → Phase 2

Do not start Phase 2 financial planning until all of these are true:

- [ ] Stripe billing live and tested (setup fee + recurring) — **BLOCKER, Issue #1**
- [ ] At least 3 paying customers (real money collected)
- [ ] Pricing validated (customers renewed at posted price for 3+ months)
- [ ] At least 1 non-founder operator paying dues
- [ ] Contractor classification confirmed with legal counsel
- [ ] 1099 compliance flow tested (W-9 collected, 1099 template ready)

---

## Recent Financial Decisions

| Date | Decision | See |
| ---- | -------- | --- |
| 2026-06-04 | **ZORT review #1:** logged $0 baseline; flagged Stripe blocker (#1) + QB defer (#2); recorded founder mandate (90-day cash flow, 6-yr LLC, lean tooling) | metrics.md, Issues #1–2 |
| 2026-06-04 | Pricing set (ADR-007): $175 setup + $35/mo std; founding $29/mo locked 12mo | MARKETING ADR-007 / FIN-004 |
| 2026-06-04 | Alliance coin: open, legal review required, do not model as revenue | decisions.md FIN-003 |
| 2026-06-04 | QuickBooks chosen as system of record (now proposed to defer — FIN-005) | decisions.md FIN-002 |
| 2026-06-04 | Member dues set to **$50/mo flat** | decisions.md FIN-001 |
