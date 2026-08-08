# Architecture Decisions Log

ADR-style. Each decision records what was chosen, why, and what it explicitly rules out.
New decisions go at the top — newest first, reverse-chronological per house style. Do not edit past decisions — add a superseding ADR if anything changes.

---

## ADR-008 — Branching: one standing `Yggdrasil` branch, `main` as the gated Well of Mimir

**Date:** 2026-08-08
**Status:** Accepted (founder's standing instruction; supersedes "push to `main`, no branches",
2026-06-05)

**Decision:** Every A777ance repo carries one standing working branch, **`Yggdrasil`**. All
session work is pushed there and **never** to `main`. **`main` is the Well of Mimir** — the
vetted tier — and moves only through a pull request the founder approves: **no cadence, no
auto-merge.** Sessions pull `--ff-only` and nothing else. The policy is *generated* into all ten
briefings from `localDNS/04-user-services/ai-orchestration/branch-policy-block.md` by
`tools/sync-briefings.py`, and the commit gate blocks any briefing that still carries the retired
directive.

**Why:** The predecessor rule was stated in two briefings and **absent from the other eight**.
Absence is not neutral — a session reading a briefing that says nothing about branching invents
an answer, and the invented answer cut **337 stale `claude/*` branches, 226 of them carrying
commits that exist nowhere else**. Fixing that meant fixing the generator, not the branches:
the rule now has a site in every briefing rather than an author in two.

The model maps onto doctrine already in force. `main` becomes the Bifrost **one-way door** at
portfolio scale — the outermost `*`, which no inner gate may release past — and the merge is the
**Provenance** promotion point, the one place a claim gets fresh contact with the founder rather
than transmission from another transcript.

**What's still open:** No merge cadence is defined, deliberately — the Well fills when the
founder decides it does. The tracked risk is the inverse of the one this fixes: a long-lived
branch that never merges does not remove merge debt, it **concentrates** it, and "the Well of
true knowledge" becomes a fiction that is six months stale. Watch the gap; if `Yggdrasil` runs
far ahead of `main` for long, that is the signal to merge, not to re-plan.

**What this rules out:** Per-session `claude/*` branches. Pushing to `main` directly. Force-pushing
either branch. Merging/rebasing/resetting a seed file over founder-authored text (`--ff-only` only).
Auto-merge or a scheduled promotion — the gate is a human, by design.

**Downstream:** GitHub Pages publishes **both** tiers to the one site a repo gets — Mimir at the
root, Yggdrasil under `/yggdrasil/` — each page banner-stamped with its tier, so a working draft
cannot be read as vetted doctrine. Two stale `claude/*` branches that could publish to the public
site were removed from the workflow trigger.

---

## ADR-007 — Customer pricing: $175 setup + $35/mo (market-validated band)

**Date:** 2026-06-04
**Status:** Accepted (working numbers; *validation* = first cohort renews at price)

**Decision:** Standard customer price is **$175 one-time setup + $35/mo**, confirmed against
2026 comparables rather than guessed (the playbook's prior $32 nudged to $35 — cleaner, signals
"managed," still in-band). Defensible band: **$29–39/mo, $150–199 setup**, with headroom toward
$39 once the Statement demonstrates ROI (threats blocked, uptime). The **setup fee is never
discounted** — it filters for serious buyers and signals a real service. **Founding cohort
(first ~5 homes):** hold the $175 setup and concede on the recurring instead — **$29/mo locked
12 months + a referral credit** — in exchange for a testimonial/case study.

**Why:** Comparables (2026): DIY managed DNS $2–6/mo (NextDNS, Control D); router-security
bundle $10/mo (eero Plus); family digital-safety $30/mo (Aura); in-home setup visits $99–250
(Geek Squad / HelloTech). A777ance is a superset — on-prem appliance + encrypted DNS + VPN +
monitoring + QoS + a human who handles incidents + a monthly Statement that proves the work —
so it prices above the consumer-app tier and around the household "safety subscription" anchor.

**What's still open:** Validation (a cohort renewing at the posted price) is pending. The
two-sided split — customer *platform membership* vs. *operator fee*, and whether the $50
operator dues (ADR-005) hold against a $35 retainer — only needs resolving when a *separate*
operator runs homes; that math will push either the customer price up or dues down.

**What this rules out:** Discounting the setup fee (including for founders — the founding break
is on the monthly). Competing on price with DIY tools — the pitch is "we run it and prove it,"
not "cheapest DNS."


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

---

## ADR-005 — Member dues: $50/mo flat

**Date:** 2026-06-04
**Status:** Accepted (working number)

**Decision:** Operator/member dues to the platform are **$50/mo flat**, recorded in `MARKETING/README.md`. This sits in the middle of NARF's recommended $40–60/mo range.

**Why:** Stage 09 (recruiting) and the operator pitch were blocked on a concrete number — a `CHANGE_ME` can't be used in an onboarding flow or a sales conversation. $50 is a clean, defensible mid-point: high enough to fund tooling, matching, and the brand; low enough that an operator covers it with a single home's margin.

**What's still open:** Exactly what the dues *unlock* (tooling tier, match priority, bonding/background-check coverage). Revisit the amount once real operator supply and per-operator economics exist — this is a price test, not gospel.

**What this rules out:** Per-job platform rake (the model is subscriptions, not a cut of every job — see ADR/MARKETING). Treating $50 as locked: it's the working number for the pilot, explicitly revisitable.

---

## ADR-004 — Statements: static HTML in Phase 1, PWA in Phase 2

**Date:** (pre-existing; from `MARKETING` roadmap)
**Status:** Accepted for Phase 1; Phase 2 revisits

**Decision:** Monthly Statements in Phase 1 are static HTML files built by a generator script and served from `localDNS/docs/statements/`. No app, no login, no dynamic rendering.

**Why:** Liquidity before app. The Statement does three jobs today (value receipt, salesperson, referral engine) without requiring any infrastructure beyond GitHub Pages. Building an app before proving customers pay would burn time on surface instead of moat.

**What this rules out:** A customer/operator toggle app, in-app payments, and dynamic statement rendering until the Phase 2 gate conditions are met (see `portfolio.md`).

---

## ADR-003 — Pi-hole and Uptime Kuma: network_mode: host

**Date:** (pre-existing; documented in `localDNS/network-context.md`)
**Status:** Accepted

**Decision:** Both containers run `network_mode: host` with no `ports:` mapping.

**Why:** Pi-hole must answer DNS queries from WireGuard peers over `wg0` — Docker DNAT was intercepting those packets. Uptime Kuma must reach Unbound at `127.0.0.1:5335` directly. Host networking resolves both. A side effect is that Pi-hole also answers on `10.8.0.1:53`, making VPN peer DNS work without extra routing rules.

**What this rules out:** Bridge-mode networking for either container.

---

## ADR-002 — DNS split: streaming domains → Cloudflare DoT, everything else recursive

**Date:** (pre-existing; documented in `localDNS/network-context.md`)
**Status:** Accepted

**Decision:** `streaming-forward.conf` is the single decision point for resolver selection. High-volume, low-sensitivity domains (Netflix, YouTube, Spotify, Steam, etc.) are forwarded to Cloudflare over DNS-over-TLS (`1.1.1.1@853`, `forward-tls-upstream: yes`). Everything else resolves recursively with DNSSEC via Unbound.

**Why:** The ISP sees an encrypted channel instead of cleartext lookups for streaming traffic. Personal and sensitive domains never reach Cloudflare. Fails closed to recursion via `forward-first` if port 853 is blocked.

**What this rules out:** Adding sensitive domains to the forward-path. Running `cloudflared proxy-dns` locally (Cloudflare removed that feature in v2026.2.0).

---

## ADR-001 — AI CTO: hub-and-spoke, single agent

**Date:** 2026-06-04
**Status:** Accepted

**Decision:** Use a single AI CTO agent rather than one agent per repo. The `DESIGN` repo is the portfolio hub (`docs/ai-cto/portfolio.md`). Each spoke repo has `docs/ai-cto/context.md`. The agent reads hub + relevant spoke at session start and updates the hub at session end.

**Why:** The 5 repos are tightly coupled — decisions in `MARKETING` directly affect `localDNS` deliverables and `DESIGN` stage specs. For a solo operation, coordinating independent agents adds overhead without benefit. Context stays manageable with well-structured files.

**Threshold for revisiting:** Any repo needs more than one agent-day of independent work per week, or a repo diverges enough that shared context becomes noise.

**What this rules out:** Fully autonomous per-repo CTO agents with their own decision loops. A portfolio manager layer above repo agents (revisit if the portfolio grows beyond ~8 repos or gains a second human operator).