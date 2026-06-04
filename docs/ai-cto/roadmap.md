# Technical Roadmap

The CTO's view of what to build and when. Source of truth for sequencing decisions.
Business rationale lives in `MARKETING`; operational stages live in `DESIGN/README.md`.

---

## Phase 1 — Prove Liquidity (now → 90 days)

**Goal:** 3 paying clients with real Statements, one real operator, referral loop working.
**Principle:** Spend nothing on app surface until liquidity is proven.

### Must ship

- [ ] Client data file format — finalized schema, documented in `localDNS`
- [ ] Statement generation pipeline — working end-to-end for 1 real household
- [ ] nftables volume populator — deployed on t630, generating per-category flow data
- [ ] Statement PWA — installable on iOS and Android (scaffold merged, needs deploy + test)
- [ ] QR code on statement → landing page — live and tracked

### Must not build in Phase 1

- Customer/operator toggle app (no users yet)
- In-app payments (Stripe manual links work fine at this scale)
- "How You Compare" neighbor benchmark (no cohort data)
- Per-category gigabyte breakdown (data layer not running yet)
- Azure infrastructure (scope undefined)

---

## Phase 2 — Unified App (~10–20 homes + 1–2 real operators)

**Trigger:** Phase 1 gate checklist complete (see `portfolio.md`).
**Goal:** Unify client statement + operator portfolio + Alliance match behind one login.
**Format:** PWA, not native app.

### Target deliverables

- [ ] PWA with customer ↔ operator toggle
- [ ] Auth layer (single login per household or operator)
- [ ] Statement served dynamically from app (not static HTML export)
- [ ] Operator dashboard: book-of-homes view with totals and to-do list
- [ ] Alliance match: "Connect in the Alliance" tap routes to available operators

### Prerequisites

- Phase 1 gate checklist complete
- At least 1 operator using the portfolio view manually (validates the UX need)

---

## Phase 3 — Scale (long term, no timeline)

- Native app (iOS + Android)
- In-app payments
- Route optimization for operators
- Geographic expansion beyond first ZIP cluster
- Channel partners: real estate, HOA, elder care

---

## Tech Debt

See `tech-debt.md` for the tracked list. Items tagged P1 block Phase 1 shipping.
