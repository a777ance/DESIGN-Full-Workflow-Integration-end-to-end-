# NARF — AI CTO Portfolio — A777ance

NARF's working memory for the full portfolio. Read at session start; update at session end with new decisions, status changes, or priority shifts.

**Last updated:** 2026-06-07 (added a 2-day *Shipped* digest below for collaborators catching up; localDNS LLM-router orchestration layer landed and consolidated to `main`)

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

All repos push to `main`, no branching (founder's standing instruction, 2026-06-05).

---

## Shipped — rolling digest (newest-first)

Plain-language log of what actually landed, for collaborators catching up. This is the
*activity* record; for the *decisions* behind it, see Recent Decisions further down.

### 2026-06-07 · localDNS — the local-first AI brain got an orchestration layer
- **Deterministic dispatcher** (`10-llm-router/dispatcher.py`): a plain rule table decides
  which model handles a task — *no AI in the routing decision*, so the same input always
  routes the same way, at zero token cost. Swapping a model is a config edit, not a code edit.
- **Privacy enforced in code, not by trust:** anything tagged sensitive (bank / tax / health /
  legal …) is pinned to a local-only model and can never be sent to a cloud provider.
- **Heat fix:** heavy reasoning (full DeepSeek-R1) offloads to a rented GPU on demand; light
  work stays on a cool local model — resolves the "heavy R1 cooks the CPU" known issue.
- **Reflection log made reviewable:** routes are logged and readable back (`--reflect`); the
  log keeps a one-line takeaway even on sensitive tasks while redacting the actual content.
- Engineer-facing design in `10-llm-router/ORCHESTRATION-BLUEPRINT.md`. Consolidated to `main`;
  feature branch retired.

### 2026-06-05 · House style adopted across ALL five repos
- Every repo (localDNS, MARKETING, DESIGN, claude-code-homelab, azure-lab) now follows the
  shared conventions: **Gill Sans MT** everywhere, **newest-first** time-based content,
  **Z→A** alphabetical lists, reversed walkthrough blocks. This is why every doc now leads
  with its most recent item.

### 2026-06-05 · localDNS — Stage 10 LLM router born
- Local-first LLM router stood up (LiteLLM + Ollama on the t630) with an Open WebUI chat
  front-end; "push-to-main, no branches" recorded as the standing rule.

### 2026-06-05 · MARKETING — "Rainbow Bridge" knowledge sync
- A Google Drive → NotebookLM sync pipeline built end-to-end (Apps Script + GitHub Actions +
  sync scripts, credential-guarded), plus the A777ance master spreadsheet and content folders.
  Finalized under the name **Rainbow Bridge**.

### 2026-06-05 · DESIGN — governance refresh
- Portfolio hub reconciled to live state; NARF (CTO) and ZORT (CFO) session updates filed;
  Codex cross-repo review recorded under `docs/ai-cto/reviews/`.

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
| `DESIGN` | Active | Workflow overhauled; doc checker added + wired into CI (`check-docs.yml`) | Stage 11 automations not wired (TD-06) |
| `claude-code-homelab` | Stable | Chronikomicon lessons added | — |
| `azure-lab` | Stub | Initial commit only | Scope not defined |
| `customers` | Active (private on GitHub) | Repo built + pushed: roster, HH-0001 (Dave) statement pipeline, personal OS | First real `stats.json` not yet collected (t630 access — see Blocker #1) |

---

## Active Blockers

1. **t630 access is the Phase-1 critical path.** Both top items (#1, #2) and the P2
   security items (TD-01, TD-02) require SSH/physical access to `192.168.1.118`.
   If founder access is intermittent, that is the true bottleneck — everything real
   in Phase 1 is downstream of it. Bundle the security cleanup into the same visit.

**Resolved in the 2026-06-05 reconcile** (numbers kept for reference):

2. ~~**DESIGN hub files not found at documented paths.**~~ Verified false in the
   co-located clone: the spoke `context.md` files reference `…/docs/ai-cto/portfolio.md`,
   which resolves. The 2026-06-04 miss was an artifact of the repos not being checked out
   side by side — no path edits were needed.
3. ~~**Client data file source is ambiguous.**~~ Was premised on #2. With the hub located,
   the data file flows as documented: business facts from Stage 05/08 (DESIGN), network
   facts from the t630. The remaining dependency is t630 access (Blocker #1), not paths.

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
| 2026-06-05 | Hub reconciled to live state (triggered by the 2026-06-05 Codex cross-repo review, item #3): `customers` is private-on-GitHub (was "local only"); DESIGN path-integrity blocker (#2) verified resolved; TD-11 closed — `check-docs.py` runs in CI. | this reconcile |
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
