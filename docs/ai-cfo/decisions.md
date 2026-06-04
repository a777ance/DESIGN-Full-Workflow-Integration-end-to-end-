# Financial Decisions Log

FIN-ADR style. Each decision records what was chosen, why, and what it explicitly rules out.
New decisions go at the bottom. Do not edit past decisions — add a superseding entry if anything changes.

---

## FIN-001 — Member dues: $50/mo flat

**Date:** 2026-06-04
**Status:** Accepted (working number — revisit once real operator economics exist)

**Decision:** Operator/member dues to the platform are **$50/mo flat**. Recorded in `MARKETING/README.md`. Cross-referenced as ADR-005 in the CTO decisions log.

**Why:** Stage 09 recruiting and the operator pitch were blocked on a concrete number. $50 sits in the middle of the $40–60/mo range that covers platform tooling, match priority, and brand while leaving operators a viable margin at even 2 homes ($35 × 2 = $70 > $50 dues).

**What's still open:** Exactly what the dues unlock — tooling tier access, match priority, bonding/background-check coverage. Revisit once real operator supply and per-operator unit economics exist.

**What this rules out:** Per-job platform rake (the model is subscriptions, not a cut of every job). Treating $50 as permanent before it is tested with a real operator.

---

## FIN-002 — Accounting system: QuickBooks (not yet connected)

**Date:** 2026-06-04
**Status:** Decided; not yet implemented

**Decision:** QuickBooks Online is the accounting system of record. Set it up before the first customer payment clears. Chart of accounts: Customer Subscriptions, Setup Fees, Operator Dues (revenue); Statement Production, Operator Payments (COGS); AI Tooling, Dev Tooling, Infrastructure, Compliance, Legal (OpEx).

**Why:** Need a real general ledger before revenue starts. QuickBooks has MCP integration available in Claude Code sessions for read/write access. Setting it up later (retrofitting) is always harder.

**What this rules out:** Spreadsheet-only accounting at any revenue level. Setting it up "after the first few customers" — that's how you lose track of deductible expenses.

**Next action:** Connect QuickBooks Online account; configure chart of accounts; wire Stripe → QuickBooks sync.

---

## FIN-003 — Alliance coin: open decision, legal review required first

**Date:** 2026-06-04
**Status:** Open — do not model revenue; do not proceed without securities lawyer

**Context:** Alliance coin is a potential token-based capital raise for the guild ecosystem — members holding coin, operators earning coin for service, customers paying/redeeming coin. The concept is tracked here as an open decision.

**What must happen before any action:**
1. Securities lawyer opinion on whether the token is a security (Howey test).
2. FinCEN/BSA analysis if the token is exchangeable for value.
3. State money-transmitter license review.
4. Tax treatment opinion (income? property? commodity?).

**Why it's promising (if legal):** Aligns operator and customer incentives with platform growth. A guild token earned through service is a compelling retention and recruiting mechanism.

**What this rules out:** Any public offering, whitepaper, or "Alliance coin" mention to customers or operators until legal review is complete. Modeling coin as revenue in financial projections.

---

## FIN-004 — Pricing: $175 setup + $35/mo standard (ADR-007)

**Date:** 2026-06-04
**Status:** Set (cross-ref: MARKETING ADR-007) — **not yet validated by renewals**

**Decision:** $175 one-time setup + $35/mo standard subscription. Price band $29–39/mo.
Founding cohort (first ~5 customers): $29/mo locked for 12 months.

**Why:** Anchored against ISP "advanced security" (~$10/mo, far less capability). $35/mo is defensible and covers tooling with margin. The setup fee covers real install labor and anchors the relationship — never discount it. Founding rate ($29/mo) creates urgency without cutting the setup fee.

**Validation required:** First cohort renews at $29/mo (founding) or $35/mo (standard) after 3+ months. Until then, all revenue projections are hypotheses.

**What this rules out:** Discounting the setup fee. Treating any projection as validated before the first cohort renews. Adjusting the standard rate without a new FIN decision.
