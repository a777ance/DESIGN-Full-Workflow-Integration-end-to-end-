# NARF — AI CTO Portfolio — A777ance

NARF's working memory for the full portfolio. Read at session start; update at session end with new decisions, status changes, or priority shifts.

**Last updated:** 2026-06-17 (review: nothing material shipped since 2026-06-07 — root cause is t630-access cadence + pending human decisions, NOT backlog; TD-14 confirmed real against live config and elevated to "fix today"; GitHub issue creation BLOCKED — integration lacks `issues:write`)

---

## Session Protocol

1. Read this file first — it is the cross-repo status snapshot.
2. Read the spoke context for the repo you're working on (`docs/ai-cto/context.md` in that repo).
3. Work on the highest-priority item in "Current Focus" unless the user directs otherwise.
4. Before ending a session: record any decisions, status changes, or priority shifts here.

**Working efficiently:** how we spend tokens on the Claude loop itself (context, hybrid
routing, model tiering, prompting) is audited in
[`ai-process-efficiency.md`](ai-process-efficiency.md) — read it before a long or repeated
session. Move #2 there (route bulk work to the local ladder) is gated on **TD-14**.

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

All repos push to `main`, no branching (founder's standing instruction, 2026-06-05).

---

## Shipped — rolling digest

The plain-language cross-repo activity log lives at the repo root:
[`../../CHANGELOG.md`](../../CHANGELOG.md) — newest-first, with an honest **built / scaffold /
not-deployed** status on every item. Single source of truth; don't duplicate the log here.

**Status discipline (learned 2026-06-07):** "committed to a repo" is NOT "built and running."
These repos are config/spec snapshots — the t630 is the source of truth for localDNS, and tooling
that needs credentials is guarded off until they exist.

Latest entry: **2026-06-07** — localDNS LLM-router orchestration landed as *reference code +
config* (deterministic dispatcher + readable reflection log; **not yet deployed**, one open
privacy-fallback gap = TD-14, now elevated).

**2026-06-17 note:** No new CHANGELOG entry since 2026-06-07. Three review cycles, no real
Statement. This is not a backlog problem — it is an access-cadence + decision-cadence problem
(see Active Blockers #1).

---

## Current Focus — 2026-06-17 (revised this review)

**Phase:** 1 — Prove liquidity. Gate: **0/5 cleared.**

**Top 3 actionable now (in order):**

1. **Close TD-14 — fail closed on the LLM-router privacy fallback** (`localDNS`,
   `10-ai-orchestration/config.yaml`). Confirmed real against the live config:
   `local-reason: ["cloud-gpu-reason", "cloud-overflow"]` lets a `sensitive` task fail
   OPEN to Claude cloud if the local model is down. The config asserts the opposite in
   three comments (the guarantee lives in the un-deployed LangGraph gate). **This is the
   only P1 fixable without box access — a 3-line edit, do it today.** Fix: chain
   `local-reason` to local-only (`["local-smart","local-fast"]`); remove `cloud-overflow`
   from any chain a sensitive task can reach. A false privacy claim is worse than none.

2. **Schedule ONE t630 session and bundle every box-dependent item into it**
   (`localDNS` + `customers`). Not five tasks — one operator visit:
   load nftables ruleset (`sudo nft -f nftables-accounting.nft`), schedule
   `populate_sets.py --apply` (6h cron) + `collect_stats.py` (nightly cron), produce the
   first real `stats.json` for HH-0001, AND clean up WG peers 10.8.0.4–6 (TD-01) + rotate
   the laptop key (TD-02). Runbook: `docs/statements/tools/collect/README.md`. Unblocks
   TD-03, TD-08, TD-05, and the first real Statement in one trip.

3. **Decide what the $50 dues *unlock*** (`MARKETING`, decision not work). Amount is set
   (ADR-005); inclusions are still `CHANGE_ME`-shaped and block an honest operator pitch.
   NARF recommends dues buy: (a) Alliance listing + match priority, (b) shared tooling tier,
   and (c) explicitly **NOT** bonding/background-check coverage yet — that's tied to the
   unresolved contractor-vs-employee classification. **Budget + compliance impact — ZORT
   should weigh in** before we imply any coverage we don't carry.

---

## Cross-Repo Status

| Repo | Status | Last notable activity | Blocked on |
| ---- | ------ | --------------------- | ---------- |
| `localDNS` | Active | LLM-router reference landed (2026-06-07); generator self-scopes to honest sections (`8dcb7fe`) | **TD-14 config fix (no box needed)**; **t630 deploy session** (SSH 192.168.1.118) for nftables + first real `stats.json` |
| `MARKETING` | Stable | Business model + pricing set | Open decisions: dues *inclusions*, pricing validation, vetting standard, contractor/employee |
| `DESIGN` | Active | Workflow overhauled; doc checker in CI | Stage 11 automations not wired (TD-06) |
| `claude-code-homelab` | Stable | Chronikomicon lessons added | — |
| `azure-lab` | Stub | Initial commit only | Scope not defined |
| `customers` | Active (private) | Repo built: roster, HH-0001 (Dave) pipeline, personal OS | First real `stats.json` not yet collected (t630 access — Blocker #1) |

---

## Active Blockers

1. **t630 access is THE Phase-1 critical path — and the true reason Phase 1 isn't closing.**
   Three review cycles with no real Statement because everything real is downstream of one
   SSH session to `192.168.1.118`. Top item #2 and security items TD-01/TD-02 all live here.
   **If founder access is intermittent, that is the #1 business risk to Phase 1 — name it to
   the CEO as such.** Bundle nftables + stats + security cleanup into a single visit.

2. **Two decisions need humans, not NARF, and both have budget/compliance impact:**
   contractor-vs-employee classification (lawyer) and "guild-certified" vetting standard
   (legal). Both gate Stage 09/10. ZORT + CEO. The dues-inclusions decision (Focus #3)
   partly depends on the classification answer.

3. **NEW — GitHub issue creation is blocked.** The integration returns `403 Resource not
   accessible by integration` on `localDNS` — it lacks `issues:write`. Two ready-to-file
   issues (TD-14 fix; t630 deploy session) could not be created this session. **Action for
   CEO:** grant the integration issue-write scope, or copy the two issues (drafted in this
   review's transcript) in manually. Until fixed, the `issues` session mode cannot function.

---

## Open Decisions (blocking progress)

| Decision | Blocks | Where to resolve |
| -------- | ------ | ---------------- |
| **Dues *inclusions*** (amount set $50, ADR-005) — what they unlock; NARF rec: listing+match+tooling, NOT bonding yet | Honest operator pitch; Stage 09 | `MARKETING` + ZORT (compliance) |
| Pricing **validation** ($175 + $35/mo, ADR-007) — cohort renews at price | Stage 05 ROI calc | first paying cohort |
| "Guild-certified" vetting standard | Stage 09 recruiting | Requires legal review (budget impact) |
| Contractor vs. employee classification | Stage 10 compliance; gates dues-inclusions | Requires lawyer (budget impact) |
| First channel partner to pilot | Phase 2 trigger | `MARKETING` |
| Cohort data for "How You Compare" | One Statement section (not the whole statement) | Blocked on nftables data layer + real cohort dataset |

---

## Recent Decisions

| Date | Decision | See |
| ---- | -------- | --- |
| 2026-06-17 | TD-14 verified against live `config.yaml` and elevated to top actionable: it is the only P1 fixable without t630 access. Fix = fail closed (local-only fallback for `local-reason`). | this review |
| 2026-06-05 | Hub reconciled to live state; `customers` is private-on-GitHub; DESIGN path-integrity blocker resolved; TD-11 closed (check-docs in CI). | reconcile |
| 2026-06-04 | Customer pricing set: **$175 + $35/mo** (band $29–39); founding $29/mo locked 12mo. | ADR-007 |
| 2026-06-04 | Real customer data → private `customers` repo; localDNS generator renders via `--data-dir/--out-dir`. | ADR-006 |
| 2026-06-04 | Hub-and-spoke AI CTO: single agent, DESIGN as hub. | ADR-001 |
| 2026-06-04 | nftables accounting reclassified: code shipped; remaining work is deployment, not engineering. | review |
| 2026-06-04 | Cohort data blocks one Statement section, not the whole Statement. | review |
| 2026-06-04 | Member dues set to **$50/mo flat**. | ADR-005 |

---

## Phase Gate Checklist — Phase 1 → Phase 2

Do not start Phase 2 work until all of these are true (current: **0/5**):

- [ ] At least 3 paying customers (real money, 3+ months)
- [ ] At least 1 real operator running homes (not founders wearing the hat)
- [ ] Pricing validated (customers renewed at posted price)
- [ ] nftables volume populator deployed and generating real per-category data
- [ ] Statement generation pipeline tested on a real household end-to-end
