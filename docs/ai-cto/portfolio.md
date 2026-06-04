# NARF — AI CTO Portfolio — A777ance

NARF's working memory for the full portfolio. Read at session start; update at session end with new decisions, status changes, or priority shifts.

**Last updated:** 2026-06-04

---

## Session Protocol

1. Read this file first — it is the cross-repo status snapshot.
2. Read the spoke context for the repo you're working on (`docs/ai-cto/context.md` in that repo).
3. Work on the highest-priority item in "Current Focus" unless the user directs otherwise.
4. Before ending a session: record any decisions, status changes, or priority shifts here.

---

## Repo Map

| Repo | Role | Visibility |
| ---- | ---- | ---------- |
| `localDNS` | Tech stack + Statement artifacts — the product | Public |
| `MARKETING` | Business model, pricing, guild mechanics — the why | Private |
| `DESIGN-Full-Workflow-Integration-end-to-end-` | End-to-end workflow — the how (this repo, the hub) | Private/internal |
| `claude-code-homelab` | Claude Code setup guide (meta) | Public |
| `azure-lab` | Azure infrastructure (stub, scope undefined) | Private |

All repos develop on branch `claude/ai-cto-architecture-MZ2NF`.

---

## Current Focus — 2026-06-04

**Phase:** 1 — Prove liquidity (now → 90 days)

**Top priorities:**
1. Generate a working Statement end-to-end for one real household (`localDNS`)
2. Deploy nftables volume populator to the t630 (`localDNS`)
3. Lock member dues amount and pricing — unblocks stages 05, 07, 09 (`MARKETING`)
4. Wire stage 11 automations so no stage transition requires manual data re-entry (`DESIGN`)

---

## Cross-Repo Status

| Repo | Status | Last notable activity | Blocked on |
| ---- | ------ | --------------------- | ---------- |
| `localDNS` | Active | Statements PWA merged (#9) | nftables populator not deployed; no real client data file yet |
| `MARKETING` | Stable | Business model + roadmap drafted | Open decisions: dues, pricing validation, vetting standard |
| `DESIGN` | Active | Workflow overhauled, doc checker added | Stage 11 automations not wired |
| `claude-code-homelab` | Stable | Chronikomicon lessons added | — |
| `azure-lab` | Stub | Initial commit only | Scope not defined |

---

## Open Decisions (blocking progress)

Resolve these before starting Phase 2. Each one has a downstream blocker listed.

| Decision | Blocks | Where to resolve |
| -------- | ------ | ---------------- |
| Member dues amount + what they include | Stage 09 onboarding, operator pitch | `MARKETING/README.md` |
| Pricing validation ($175 setup + $32/mo) | Stage 05 sales, Statement ROI calc | 3-client pilot |
| "Guild-certified" vetting standard | Stage 09 recruiting | Requires legal review |
| Contractor vs. employee classification | Stage 10 compliance | Requires lawyer |
| First channel partner to pilot | Phase 2 trigger | `MARKETING` |
| Cohort data for "How You Compare" | Statement section | Blocked on nftables data layer |

---

## Recent Decisions

| Date | Decision | See |
| ---- | -------- | --- |
| 2026-06-04 | Hub-and-spoke AI CTO: single agent, DESIGN as hub, per-repo context files in spoke repos | `decisions.md` ADR-001 |

---

## Phase Gate Checklist — Phase 1 → Phase 2

Do not start Phase 2 work until all of these are true:

- [ ] At least 3 paying customers (real money, 3+ months)
- [ ] At least 1 real operator running homes (not founders wearing the hat)
- [ ] Pricing validated (customers renewed at posted price)
- [ ] nftables volume populator deployed and generating real per-category data
- [ ] Statement generation pipeline tested on a real household end-to-end
