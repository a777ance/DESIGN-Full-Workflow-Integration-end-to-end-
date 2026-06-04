# Architecture Decisions Log

ADR-style. Each decision records what was chosen, why, and what it explicitly rules out.
New decisions go at the bottom. Do not edit past decisions — add a superseding ADR if anything changes.

---

## ADR-001 — AI CTO: hub-and-spoke, single agent

**Date:** 2026-06-04
**Status:** Accepted

**Decision:** Use a single AI CTO agent rather than one agent per repo. The `DESIGN` repo is the portfolio hub (`docs/ai-cto/portfolio.md`). Each spoke repo has `docs/ai-cto/context.md`. The agent reads hub + relevant spoke at session start and updates the hub at session end.

**Why:** The 5 repos are tightly coupled — decisions in `MARKETING` directly affect `localDNS` deliverables and `DESIGN` stage specs. For a solo operation, coordinating independent agents adds overhead without benefit. Context stays manageable with well-structured files.

**Threshold for revisiting:** Any repo needs more than one agent-day of independent work per week, or a repo diverges enough that shared context becomes noise.

**What this rules out:** Fully autonomous per-repo CTO agents with their own decision loops. A portfolio manager layer above repo agents (revisit if the portfolio grows beyond ~8 repos or gains a second human operator).

---

## ADR-002 — DNS split: streaming domains → Cloudflare DoT, everything else recursive

**Date:** (pre-existing; documented in `localDNS/network-context.md`)
**Status:** Accepted

**Decision:** `streaming-forward.conf` is the single decision point for resolver selection. High-volume, low-sensitivity domains (Netflix, YouTube, Spotify, Steam, etc.) are forwarded to Cloudflare over DNS-over-TLS (`1.1.1.1@853`, `forward-tls-upstream: yes`). Everything else resolves recursively with DNSSEC via Unbound.

**Why:** The ISP sees an encrypted channel instead of cleartext lookups for streaming traffic. Personal and sensitive domains never reach Cloudflare. Fails closed to recursion via `forward-first` if port 853 is blocked.

**What this rules out:** Adding sensitive domains to the forward-path. Running `cloudflared proxy-dns` locally (Cloudflare removed that feature in v2026.2.0).

---

## ADR-003 — Pi-hole and Uptime Kuma: network_mode: host

**Date:** (pre-existing; documented in `localDNS/network-context.md`)
**Status:** Accepted

**Decision:** Both containers run `network_mode: host` with no `ports:` mapping.

**Why:** Pi-hole must answer DNS queries from WireGuard peers over `wg0` — Docker DNAT was intercepting those packets. Uptime Kuma must reach Unbound at `127.0.0.1:5335` directly. Host networking resolves both. A side effect is that Pi-hole also answers on `10.8.0.1:53`, making VPN peer DNS work without extra routing rules.

**What this rules out:** Bridge-mode networking for either container.

---

## ADR-004 — Statements: static HTML in Phase 1, PWA in Phase 2

**Date:** (pre-existing; from `MARKETING` roadmap)
**Status:** Accepted for Phase 1; Phase 2 revisits

**Decision:** Monthly Statements in Phase 1 are static HTML files built by a generator script and served from `localDNS/docs/statements/`. No app, no login, no dynamic rendering.

**Why:** Liquidity before app. The Statement does three jobs today (value receipt, salesperson, referral engine) without requiring any infrastructure beyond GitHub Pages. Building an app before proving customers pay would burn time on surface instead of moat.

**What this rules out:** A customer/operator toggle app, in-app payments, and dynamic statement rendering until the Phase 2 gate conditions are met (see `portfolio.md`).

---

## ADR-005 — Member dues: $50/mo flat

**Date:** 2026-06-04
**Status:** Accepted (working number)

**Decision:** Operator/member dues to the platform are **$50/mo flat**, recorded in `MARKETING/README.md`. This sits in the middle of NARF's recommended $40–60/mo range.

**Why:** Stage 09 (recruiting) and the operator pitch were blocked on a concrete number — a `CHANGE_ME` can't be used in an onboarding flow or a sales conversation. $50 is a clean, defensible mid-point: high enough to fund tooling, matching, and the brand; low enough that an operator covers it with a single home's margin.

**What's still open:** Exactly what the dues *unlock* (tooling tier, match priority, bonding/background-check coverage). Revisit the amount once real operator supply and per-operator economics exist — this is a price test, not gospel.

**What this rules out:** Per-job platform rake (the model is subscriptions, not a cut of every job — see ADR/MARKETING). Treating $50 as locked: it's the working number for the pilot, explicitly revisitable.

---

## ADR-006 — Real customer data: one private `customers` repo

**Date:** 2026-06-04
**Status:** Accepted (working structure for the pilot)

**Decision:** Real customer identities and statement data live in a new **private** repo,
`a777ance/customers`, one folder per household (`households/<id>/`). Each holds the home's
`sidecar.json`, collected `stats/`, composed `data/`, and rendered `statements/`; the live
roster is `roster.json` at the repo root. The public `localDNS` statement generator renders
*into* this repo via new `--data-dir`/`--out-dir` flags, so `localDNS` never holds real data.
The founder household (`HH-0001-dave`) also carries a `personal/` workspace (novel, job hunt,
ADHD organization) — scoped to that household, not a product feature.

**Why:** `localDNS` is public (GitHub Pages) and `MARKETING`/`DESIGN` keep only fictional
samples — so nothing had a home for a real household's name and figures. One private repo
(not repo-per-customer) fits Phase 1 (N=1–3): it mirrors the public `data/clients/` layout,
supports one monthly batch, and preserves one source of truth. Real PII stays out of `DESIGN`;
its `08-client-list-and-crm/sample-roster.json` remains the fictional schema reference.

**Threshold to revisit:** Split to a repo-per-operator-book when there are real operators
needing GitHub access scoped to their own homes (the Phase-2 gate: "≥1 real operator running
homes"). A real CRM, if stood up later, may supersede `roster.json` as the business-fact source.

**What this rules out:** Committing real customer PII to any public repo, or to `DESIGN`.
Repo-per-customer sprawl at pilot scale.
