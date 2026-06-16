# Tech Debt

Tracked items across all repos. P1 = blocks Phase 1 shipping. P2 = important but not blocking. P3 = nice-to-fix.

Update this file when items are resolved or new ones are found. New items go at the top
(newest first, per house style); IDs stay fixed.

| ID | Item | Severity | Repo | Status |
| -- | ---- | -------- | ---- | ------ |
| TD-18 | Prompt caching not wired into the cloud path — app-level calls via LiteLLM→Anthropic re-pay full input price for the static system prompt/tool defs/templates every call. Add `cache_control` breakpoint after the static prefix (LiteLLM passes it through). Documented 60–90% input-cost cut; highest-ROI item. F-01. | P2 | localDNS | Open (found 2026-06-16) |
| TD-17 | Statement generation is a batch workload paying interactive prices — any cloud-model call in stage 06 / `customers` `make statement` should use the Message Batches API (50% off). See `docs/ai-cto/ai-process-efficiency.md` F-06. | P3 | DESIGN / customers | Open (found 2026-06-16) |
| TD-16 | Cloud tiers default to `claude-opus-4-8` almost everywhere in `10-ai-orchestration/config.yaml` (`cloud-overflow`, `cloud-explore`, `cloud-vision`). Demote to Haiku 4.5 / Sonnet 4.6 per task; reserve Opus for hardest reasoning. F-03. | P2 | localDNS | Open (found 2026-06-16) |
| TD-15 | Always-loaded context bloat: the house-style block is duplicated verbatim across all 6 CLAUDE.md files and re-paid every session; the two big briefings are large. Factor shared style to one referenced file; slim CLAUDE.md to essentials. F-02. | P2 | all repos | Open (found 2026-06-16) |
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
