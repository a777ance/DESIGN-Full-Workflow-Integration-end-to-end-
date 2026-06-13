# A777ance — Lean Business Plan

*A one-page strategy snapshot. It **summarizes** the authoritative sources — it does not
replace them. Figures cross-reference ADR-007 / FIN-001–005; any number that is a projection
is labelled as one. Snapshot date: 2026-06-13.*

*House style: sections run in forward framework order (§1 → §7), matching `CLAUDE.md` and the
stage map. Time-based lists read newest-first; alphabetical lists run Z→A.*

> **Why this is not an "open-source monetization" plan.** A common template models localDNS as
> an open-source DNS-*server* product to be monetized via open-core, a SaaS control plane, or
> dual-licensing. That mis-reads the company. localDNS is the public, MIT-licensed *configuration
> and Statement* repo of a managed home-network **service** — it ships no DNS server of its own
> (it configures Unbound + Pi-hole). What we sell is the **monthly Statement and the service
> around it**, not the code. The plan below reflects that.

## Contents

- [1. Executive summary](#1-executive-summary)
- [2. Company and product overview](#2-company-and-product-overview)
- [3. Market analysis](#3-market-analysis)
- [4. Monetization and value capture](#4-monetization-and-value-capture)
- [5. Marketing and go-to-market](#5-marketing-and-go-to-market)
- [6. Operational and technical roadmap](#6-operational-and-technical-roadmap)
- [7. Financial projections](#7-financial-projections)
- [Sources](#sources)

## 1. Executive summary

**Mission.** Keep ordinary households' home networks quiet, private, and unbroken — and prove
it every month — delivered by a local guild of trusted operators, not a product download.

**What we sell.** A managed home-network service whose product is a monthly **Network Activity
Statement** — "pest control for your internet." A real person sets up a small box in the home;
every month the household gets a one-page, plain-English proof that the quiet was earned. The
underlying tech (`localDNS`) is open-source and free; the business is the install, the service,
and the kept proof.

**How it makes money.** $175 one-time setup + $35/mo per household ($29/mo for the founding
cohort). Operators — the people who run homes — pay $50/mo in dues and bill their customers
directly; the platform earns from both subscriptions.

**Commercialization strategy — the "big question," answered.** A managed service on a two-sided
guild — deliberately **not** open-core, a SaaS control plane, or dual-licensing. The moat is
trust and local density, not software. *Liquidity before app; trust before tech.*

**Where we are (2026-06-13).** Pre-revenue. The one thing between us and the first dollar is
connecting Stripe. Phase 1 goal: 3 paying households in 90 days, at posted price, each receiving
a real Statement.

## 2. Company and product overview

**Company.** A777ance — a two-sided guild, run lean by two sole proprietors. Free tiers until
customer #3; an LLC is planned only when liability or revenue triggers it (watch-list, ~2032).

**The product is the Statement** — two artifacts, both built by a generator that reads one home's
data file at about a penny a home:

- **Network Activity Statement** (for the homeowner): a one-page monthly proof — the "sticker on
  the door" that shows the network stayed quiet, private, and up.
- **Alliance Member Portfolio** (for the operator): one view across a whole book of homes —
  totals, the to-do list, the work log.

**The tech underneath** (`localDNS`, public, MIT). On a small HP t630 box: Unbound (recursive DNS
with a DNS-over-TLS split for streaming), Pi-hole (blocking), WireGuard (private remote access),
Uptime Kuma (monitoring), CAKE (anti-bufferbloat). localDNS *configures* third-party resolvers —
it is not itself a DNS server. The only ownable software is the **Statement generator** (Python),
and that is a production tool, not a product for sale.

**What's unique (USP).** Not footprint or an API. It is *done-for-you quiet plus monthly proof,
from a local person you trust* — the invisible work made visible, on a document you keep.

**The honesty rule.** We print only numbers the box actually measured (lookups, blocked, uptime).
Not-yet-built figures — a by-category gigabyte breakdown, or "how you compare" to neighbors —
stay off the Statement until the data is real. The trustworthy document *is* the moat.

## 3. Market analysis

**Who we serve.** Local households — ordinary, non-technical. "A grandparent should understand
it." This is **pest control, not lawn care**: the value is the quiet, and we make the routine,
invisible work visible. The homelab / DIY crowd is not the customer — they are a *recruiting pool
for operators*.

**Who we actually compete with** (listed Z→A per house style — and note none of these is another
DNS server):

- **Status quo** — the household that does nothing. Inertia is the biggest competitor.
- **Router / ISP "advanced security" add-ons** — ~$10/mo, far less capability; our pricing
  anchors against these.
- **Managed-IT / "Geek Squad"-style** one-off services — no monthly proof, no relationship.
- **Consumer security suites** (antivirus / VPN bundles) — software you operate yourself; no
  install, no local trust.

**Not competitors — components.** Pi-hole, AdGuard, CoreDNS, and dnsmasq are tools a DIY user
self-hosts. We *run* Pi-hole and Unbound. The differentiator versus DIY is not the software; it
is that nobody in the home has to become an administrator — a person installs it, and a Statement
proves it every month.

**Market entry.** Win one ZIP cluster at a time. Density over reach.

## 4. Monetization and value capture

**The model.** A two-sided guild. The customer pays a platform membership *and* pays their
operator directly for the service. The operator pays $50/mo in dues (FIN-001). The platform earns
from both subscriptions; service money flows customer → operator, like hiring a tradesperson
through a guild.

**Pricing** (ADR-007 / FIN-004 — set, *not yet validated by renewals*):

| Line | Amount | Note |
| ---- | ------ | ---- |
| Setup (one-time) | **$175** | Covers install labor; never discounted |
| Monthly, standard | **$35/mo** | Market band $29–39 |
| Monthly, founding cohort (first ~5) | **$29/mo** | Locked 12 months — urgency, not a setup cut |
| Operator dues | **$50/mo** | Flat; subscriptions, never a per-job rake |

**Why the open code does not bleed value.** The tech is MIT and public *on purpose* — it is
credibility and the operator-recruiting asset. A fork gives you the config; it does not give you
the install in someone's living room, the local trust, or the monthly proof — which is what
people pay for. Dual-licensing is moot under MIT in any case. *Liquidity before app; trust before
tech.*

**Not modeled as revenue.** "Alliance coin" (FIN-003) is an open, legal-review-gated idea — never
counted as revenue, and never mentioned to customers or operators until a securities lawyer
clears it.

## 5. Marketing and go-to-market

**The funnel is local and human — not GitHub stars.** A household that does not know it has a
problem → reached by local search, ads, and email on one block's ZIPs ("pest control for your
internet") → books a free look → **a real person answers the phone** → consult and quote → $175
setup → yes. The README is not the landing page; the website and a person are.

**The repo is proof, not a download funnel.** The public Statement gallery and the open code build
credibility. The conversion that matters on the Statement itself is the **"Connect in the
Alliance"** tap — a happy customer raising a hand to become an operator. That is the recruiting
funnel.

**Two conversions to optimize:** stranger → paying household (stages 02–05), and happy customer →
vetted operator (stages 09–10). Reach is cheap; density and trust are the work.

## 6. Operational and technical roadmap

Forward by phase, matching `docs/ai-cto/roadmap.md`. **Principle: spend nothing on app surface
until liquidity is proven.**

**Phase 1 — Prove liquidity (now → 90 days).** Ship: a finalized client data schema; the
Statement pipeline working end-to-end for one real household; the nftables volume layer deployed
on the box; the Statement PWA installable on iOS and Android; a tracked QR → landing page; and
**Stripe live** (the revenue blocker). Do **not** build: the customer/operator app, in-app
payments, "How You Compare," the per-category gigabyte breakdown, or Azure.

**Phase 2 — Unified app (~10–20 homes + 1–2 real operators).** Only after the Phase-1 gate: a PWA
with a customer ↔ operator toggle, a single login, dynamically served Statements, an operator
dashboard, and Alliance match. The app is a Phase-2 deliverable *gated on* liquidity — never a
tool to manufacture it.

**Phase 3 — Scale (no timeline).** Native apps, in-app payments, route optimization, geographic
expansion, and channel partners (real estate, HOA, elder care).

## 7. Financial projections

**Current state (2026-06-13): pre-revenue.** $0 MRR, 0 paying customers, 0 non-founder operators.
Monthly burn ~$11–27 (target <$30); **break-even at customer #1** — one founding household at
$29/mo covers the tooling. The single revenue blocker is that **Stripe is not yet connected**.

**Cost structure (pre-revenue), largest first:**

| Line | Est. monthly |
| ---- | ------------ |
| AI tooling (Anthropic API — the two AI officers) | $5–15 |
| t630 power (~65 W, 24×7) | $4–6 |
| GitHub (private repos) | $0–4 |
| Domain + email | ~$2 |
| Statement mailing | ~$1/customer (email is $0) |
| Stripe fees | 2.9% + $0.30 — only once money comes in |

**Unit economics (hypotheses until the first cohort renews — FIN-004):**

| Per customer / mo | Standard | Founding |
| ----------------- | -------- | -------- |
| Subscription | $35 | $29 |
| − Statement production (~$0.01 AI + optional ~$1 mail) | ~$0.01–1 | ~$0.01–1 |
| − Stripe (~2.9% + $0.30) | ~$1.32 | ~$1.14 |
| **Net before operator share** | **~$33–34** | **~$27** |

Operator economics: $50/mo dues, break-even at ~2 homes ($35 × 2 = $70 > $50).

**90-day target (the Phase-1 gate):** 3 paying households at posted price → ~$105/mo MRR + $525 in
setup fees; ≥1 non-founder operator → +$50/mo dues. **Validation = the first cohort renews at
posted price**; until then, every projection above is a hypothesis.

**Metrics that matter** (not OSS monthly-active-users or a 1–3% upgrade rate): leads → consults →
closed homes; customer → operator conversion; MRR (subscriptions + dues); setup fees collected;
renewal / churn (the validation metric); and homes-per-operator.

**Capital posture.** Lean, free-tier-first to customer #3; defer paid accounting until ~10
customers (proposed FIN-005). LLC when liability or revenue triggers it (~2032 watch-list).
Alliance coin is *not* revenue (FIN-003).

## Sources

This snapshot summarizes; the following remain authoritative. Newest-first where the source is a
log.

- **Pricing & money:** `docs/ai-cfo/decisions.md` (FIN-004 → FIN-001), `docs/ai-cfo/portfolio.md`,
  `docs/ai-cfo/runway.md`
- **Roadmap & phase gates:** `docs/ai-cto/roadmap.md`, `docs/ai-cto/portfolio.md`
- **The workflow & funnel:** `README.md`, `workflow-context.md`
- **The business model (the "why"):** `MARKETING` (private)
- **The tech & the Statements (the product):** [`localDNS`](https://a777ance.github.io/localDNS/)
  (public)
