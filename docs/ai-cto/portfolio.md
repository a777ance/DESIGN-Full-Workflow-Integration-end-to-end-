# NARF — AI CTO Portfolio — A777ance

NARF's working memory for the full portfolio. Read at session start; update at session end with new decisions, status changes, or priority shifts.

**Last updated:** 2026-06-04 (first customer onboarded — `customers` repo + ADR-006; customer pricing set — ADR-007)

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
| `customers` | Real customer data: live roster, per-home statement data + rendered statements, founder personal workspace | **Private** |

All repos develop on branch `claude/ai-cto-architecture-MZ2NF`.

---

## Current Focus — 2026-06-04 (revised this review)

**Phase:** 1 — Prove liquidity (now → 90 days)

**Top 3 actionable now (in order):**
1. **Deploy the nftables accounting layer to the t630** (`localDNS`). The code ships
   (ruleset + populator + runbook). This is execution, not engineering — load the
   ruleset, schedule `populate_sets.py`, verify counters. Unblocks TD-08, TD-13, and
   the first real Statement. Runbook: `docs/statements/tools/collect/README.md`.
2. **Generate the first real end-to-end Statement for one real household** (`localDNS` + `customers`).
   The household is **Dave = HH-0001**. The private home + pipeline exist (`customers` repo), the
   generator renders off the public repo (`--data-dir/--out-dir`), and it now **self-scopes** —
   omitting any section without honest data (commit `8dcb7fe`: no cohort → no "How You Compare";
   no volume → no donut/profile; no match → no Alliance card), so month one is honest by
   construction. **Only remaining:** run `collect_stats.py` on the t630 for real figures (needs
   box access); deploying nftables additionally lights up the volume + profile sections.
3. **Lock the member dues amount** (`MARKETING`). Decision, not work. Recommend
   $40–60/mo per operator; write it into `MARKETING/README.md` and remove the
   `CHANGE_ME`. Unblocks Stage 09 onboarding + the operator pitch.

---

## Cross-Repo Status

| Repo | Status | Last notable activity | Blocked on |
| ---- | ------ | --------------------- | ---------- |
| `localDNS` | Active | Statements PWA (#9); nftables layer shipped; generator renders to a **private** dir (`--data-dir/--out-dir`) and **self-scopes to honest sections** (omit-empty, `8dcb7fe`) | **Deploy nftables to t630** (SSH 192.168.1.118); first real `stats.json` not yet collected |
| `MARKETING` | Stable | Business model + roadmap drafted | Open decisions: dues, pricing validation, vetting standard |
| `DESIGN` | Active (path integrity issue) | Workflow overhauled, doc checker added | Stage 11 automations not wired; **hub files not at documented paths — see blocker** |
| `claude-code-homelab` | Stable | Chronikomicon lessons added | — |
| `azure-lab` | Stub | Initial commit only | Scope not defined |
| `customers` | New (local only) | Repo built + committed locally: roster, HH-0001 (Dave) statement pipeline, personal OS | **Not yet on GitHub** — integration can't create repos (403); founder must create the private remote, then push |

---

## Active Blockers (surfaced 2026-06-04)

1. **t630 access is the Phase-1 critical path.** Both top items (#1, #2) and the P2
   security items (TD-01, TD-02) require SSH/physical access to `192.168.1.118`.
   If founder access is intermittent, that is the true bottleneck — everything real
   in Phase 1 is downstream of it. Bundle the security cleanup into the same visit.
2. **DESIGN hub files not found at documented paths.** This review could not read
   `DESIGN-Full-Workflow-Integration-end-to-end-/README.md` or `.../docs/ai-cto/portfolio.md`
   at the paths the spoke context files reference. This breaks the one-source-of-truth
   premise (Stage 08 master list = business facts). **Next action:** verify the DESIGN
   repo's actual layout and correct the path references in all spoke `context.md` files.
3. **Client data file source is ambiguous.** Context says it comes from "Stage 05/08
   in DESIGN," but the hub can't currently be located (see #2). Resolve #2 to unblock #2-priority.

---

## Open Decisions (blocking progress)

Resolve these before starting Phase 2. Each one has a downstream blocker listed.

| Decision | Blocks | Where to resolve |
| -------- | ------ | ---------------- |
| ~~Member dues amount~~ — **set to $50/mo (2026-06-04, ADR-005)** | ~~Stage 09 onboarding~~ unblocked | What dues *unlock* still open |
| Pricing **set** — $175 + $35/mo, band $29–39, founding $29/mo locked (ADR-007); *validation* (cohort renews at price) still pending | Stage 05 ROI calc | first paying cohort |
| "Guild-certified" vetting standard | Stage 09 recruiting | Requires legal review |
| Contractor vs. employee classification | Stage 10 compliance | Requires lawyer |
| First channel partner to pilot | Phase 2 trigger | `MARKETING` |
| Cohort data for "How You Compare" | Statement section (NOT the whole statement) | Blocked on nftables data layer + real cohort dataset |

---

## Recent Decisions

| Date | Decision | See |
| ---- | -------- | --- |
| 2026-06-04 | Customer pricing set vs. 2026 comparables: **$175 + $35/mo** standard (band $29–39, headroom to $39 on proven ROI); setup never discounted; founding cohort **$29/mo locked 12mo** (monthly concession, not a setup cut) | `decisions.md` ADR-007 |
| 2026-06-04 | Real customer data → new private `customers` repo (one repo, per-household folders); `localDNS` generator renders privately via `--data-dir/--out-dir`; founder personal workspace under HH-0001 | `decisions.md` ADR-006 |
| 2026-06-04 | Hub-and-spoke AI CTO: single agent, DESIGN as hub, per-repo context files in spoke repos | `decisions.md` ADR-001 |
| 2026-06-04 | nftables accounting reclassified: code is shipped; remaining work is **deployment to t630**, not engineering. TD-03/TD-08 are now "ready to deploy," not "open dev." | this review |
| 2026-06-04 | Cohort data does NOT block the first real Statement — it blocks one section. Ship statements scoped to Pi-hole + Uptime Kuma + nftables; omit "How You Compare" until real cohort data exists. | this review |
| 2026-06-04 | Member dues set to **$50/mo flat** (mid-point of NARF's $40–60 range). Unblocks Stage 09 + operator pitch. | `decisions.md` ADR-005 |

---

## Phase Gate Checklist — Phase 1 → Phase 2

Do not start Phase 2 work until all of these are true:

- [ ] At least 3 paying customers (real money, 3+ months)
- [ ] At least 1 real operator running homes (not founders wearing the hat)
- [ ] Pricing validated (customers renewed at posted price)
- [ ] nftables volume populator deployed and generating real per-category data
- [ ] Statement generation pipeline tested on a real household end-to-end
