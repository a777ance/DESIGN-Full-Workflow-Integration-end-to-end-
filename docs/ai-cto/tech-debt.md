# Tech Debt

Tracked items across all repos. P1 = blocks Phase 1 shipping. P2 = important but not blocking. P3 = nice-to-fix.

Update this file when items are resolved or new ones are found. New items go at the top
(newest first, per house style); IDs stay fixed.

| ID | Item | Severity | Repo | Status |
| -- | ---- | -------- | ---- | ------ |
| TD-16 | `CLAUDE.md` token bloat: all 6 `CLAUDE.md` files are 5k–7k tokens and load every turn of every session — the largest recurring token cost we control. The ~250-word House-Style block is duplicated verbatim in all six. Fix: trim each to a lean index (<1,500 tokens) with detail in linked files read on demand; factor House-Style into one shared `HOUSE-STYLE.md` linked from each. Keep the cached prefix byte-stable (no dates inside) so prompt caching applies. Est. 50–70% off standing context. See `docs/ai-cto/reviews/2026-06-22-ai-process-efficiency.md`. | P2 | all | Open (found 2026-06-22) |
| TD-15 | Daily portfolio review burns a frontier-model run to re-derive deterministic state: ~2 weeks of near-identical "nothing shipped" reviews (≈5–6 KB each) on Opus. Fix: compute the state-check deterministically (git log since last review, grep TD-14 in live `config.yaml`, phase-gate counter) and only invoke the LLM when state actually changed — same pattern as `check-docs.py`. Default routines to Sonnet 4.6, Opus opt-in. Est. ~90% of review runs avoid the LLM. See the 2026-06-22 efficiency review. | P2 | DESIGN | Open (found 2026-06-22) |
| TD-14 | LLM-router privacy fallback gap: a `sensitive`-tagged task routes to `local-reason`, but `config.yaml` gives `local-reason` a `["cloud-gpu-reason", "cloud-overflow"]` fallback — so a sensitive prompt can fail over to `cloud-overflow` (Claude cloud) if the local model is down. The dispatcher's `allow_cloud=False` is not enforced at the LiteLLM failover layer, and its own docstring requires a local-only chain here. Fix: give `local-reason` a local-only fallback (fail closed). No privacy guarantee until then. | P1 | localDNS | Open (found 2026-06-07) |
| TD-13 | Statement PWA: merged but not deployed or tested on real mobile devices | P1 | localDNS | Open |
| TD-12 | WireGuard IPv6 black hole: peers routing ::/0 black-hole IPv6 traffic | P3 | localDNS | Documented; ULA+NAT66 fix in network-context.md |
| TD-11 | `tools/check-docs.py` is not wired into CI — manual only | P2 | DESIGN | Resolved (2026-06-05) — `.github/workflows/check-docs.yml` runs it on push/PR to `main` |
| TD-10 | azure-lab is an empty stub — no scope, no CLAUDE.md, no infrastructure | P3 | azure-lab | Deferred until scope defined |
| TD-09 | Member dues amount is CHANGE_ME — open business decision, not a code issue | P1 | MARKETING | Open decision |
| TD-08 | Per-category gigabyte breakdown: nftables measuring layer scaffolded but not running | P2 | localDNS | Blocked on TD-03 |
| TD-07 | "How You Compare" neighbor benchmark is placeholder — no real cohort data | P2 | localDNS | Blocked on cohort dataset |
| TD-06 | Stage 11 automations not wired — all cross-stage transitions require manual data re-entry | P1 | DESIGN | Open |
| TD-05 | Pi-hole live upstreams may differ from repo after volume migration — verify after next deploy | P2 | localDNS | Verify on deploy |
| TD-04 | `FTLCONF_webserver_api_password` is `CHANGE_ME` — deliberate placeholder, must stay out of git | P1 | localDNS | Intentional; use .env |
| TD-03 | nftables volume populator scaffolded in repo but not deployed to t630 | P1 | localDNS | Open |
| TD-02 | Windows laptop WireGuard key was exposed during setup — rotate before trusting this peer | P2 | localDNS | Open |
| TD-01 | WireGuard peers 10.8.0.4–6 have real public keys but no recent handshake — identify or remove | P2 | localDNS | Open |
