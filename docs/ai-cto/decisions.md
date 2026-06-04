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
