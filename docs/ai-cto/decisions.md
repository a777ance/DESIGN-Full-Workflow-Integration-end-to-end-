# Architecture Decisions Log

ADR-style. Each decision records what was chosen, why, and what it explicitly rules out.
New decisions go at the top — newest first, reverse-chronological per house style. Do not edit past decisions — add a superseding ADR if anything changes.

---

## ADR-008 — Founder workstation: clean Ubuntu 24.04 LTS host + KVM VMs (inherited XPS 13 9340)

**Date:** 2026-06-06
**Status:** Accepted

**Decision:** The inherited **Dell XPS 13 9340** (Core Ultra / Meteor Lake, integrated Intel
Arc iGPU, 1 TB Micron NVMe, no discrete GPU) becomes **"the Controller"** — the A777ance
**control node / founder workstation**: the single machine from which the t630, the repos, and
the live tooling are administered. It is provisioned as a **clean, single-OS Ubuntu
24.04 LTS** workstation — matching the t630 production target (same OS, kernel 6.17 series, and
therefore identical `systemd` / Docker / `nftables` / WireGuard behavior). Because the machine
was **inherited**, the install is treated as a security reset: wipe the drive, set a
**BIOS/firmware admin password**, and **update the BIOS** (from 1.23.0) before installing.
**The founder declined full-disk encryption (LUKS)** — see *As-built* below for the
mitigation. **KVM/QEMU** provides the VM layer: (a) a **Windows VM** for the
occasional Windows-only need — chiefly **Gill Sans MT** proofing in Office (the house-style font
ships with MS Office, not Linux); (b) **ephemeral, blank clean-Ubuntu VMs** as the localDNS
install-**rehearsal** rig — spun up empty, run the README from zero, then discarded. **Local
LLM** inference (DeepSeek-R1 *distills*, ~7B/8B via Ollama/llama.cpp with Intel Arc acceleration)
runs on the host and registers into the existing **Open WebUI / LiteLLM** stack (localDNS stage 10).

**Why:** Parity with production means what runs on the laptop runs on the t630 — no translation
layer. The blank-Ubuntu rehearsal VM directly serves the standing rule *"every commit to main
must leave README able to reproduce a working system on clean Ubuntu 24.04"* and de-risks the
**#1 Phase-1 blocker (t630 access)** by letting the install be proven off-box. The business
tooling (Stripe, QuickBooks, Setmore, Squarespace, Mailchimp, e-sign) is web-based and
OS-agnostic. Local DeepSeek is better supported on Linux (IPEX-LLM / SYCL) and reuses
infrastructure already running. Gaming was **deprioritized by the founder (2026-06-06)**, so it
exerts no pull toward Windows.

**As-built (2026-06-06):** Installed clean **Ubuntu 24.04 LTS** to `nvme0n1` — AHCI/NVMe mode
confirmed (the installer saw the disk; the old RAID/RST mode would have hidden it), standard
**EFI (fat32) + ext4 root** layout, **no disk encryption** (founder's call), codecs +
third-party drivers enabled, **VT-x + VT-d ON** for KVM. Hostname `a777ance-XPS-13-9340`, user
`a777ance`. **Mitigation for the unencrypted disk:** the Controller relies on a strong login
password + physical custody; keep the t630 **SSH key passphrase-protected**, and keep real
customer PII **off the disk at rest** (it lives in the private `customers` repo / on the box,
per ADR-006). Revisit encryption if the Controller starts traveling or holding sensitive data
locally — it can be re-enabled later only by reinstalling.

**Threshold to revisit:** A serious local-LLM need (models beyond ~14B) or serious gaming →
stand up a **separate GPU machine** rather than re-OS this laptop; this chassis (iGPU only) can't
do either well regardless of OS.

**What this rules out:**
- **macOS on this hardware** — Apple's EULA restricts macOS to Apple-branded machines and a
  hackintosh VM is fragile; use real Apple hardware or a cloud Mac if macOS is ever needed.
- **Windows as the host / WSL2 as the primary dev environment** — inverts the priority (daily
  Linux infra work in the weaker environment) and can't faithfully rehearse
  `systemd-resolved` / `nftables` / `wg-quick`.
- **Dual-boot Windows** — gaming deprioritized; a Windows VM can't game on a single-iGPU laptop
  (no GPU passthrough; anti-cheat blocks VMs) and Proton wasn't needed. Revisit only if a
  kernel-anti-cheat title becomes a real need.
- **A standing clone/mirror of the t630** — it remains the single source of truth; rehearsal VMs
  are blank and disposable, holding no t630 state or secrets.

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