# Tech Debt

Tracked items across all repos. P1 = blocks Phase 1 shipping. P2 = important but not blocking. P3 = nice-to-fix.

Update this file when items are resolved or new ones are found. New items go at the top
(newest first, per house style); IDs stay fixed.

| ID | Item | Severity | Repo | Status |
| -- | ---- | -------- | ---- | ------ |
| TD-18 | Prompt-cache TTL: Claude Code default dropped 60m→5m (Mar 2026), raising cost for spaced sessions. Set 1h cache (`ENABLE_PROMPT_CACHING` + 1h TTL) for routines/returning sessions; verify cache-read vs write in `/cost`. See `docs/ai-cto/process-efficiency.md` §4. | P3 | DESIGN | Open (found 2026-06-14) |
| TD-17 | `CLAUDE.md` bloat + 6× duplication: ~58 KB / ≈14.6k tokens across repos loads every session; House-style block copy-pasted verbatim into all 6. Trim each to a <120-line briefing, link reference tables, dedupe House style into one `STYLE.md`. Biggest recurring token cost. See `docs/ai-cto/process-efficiency.md` §1. | P2 | DESIGN | Open (found 2026-06-14) |
| TD-16 | Model right-sizing: scheduled routines + mechanical tasks run on Opus `[1m]`. Default routines to Sonnet 4.6 (Haiku 4.5 for triage), reserve Opus for architecture/debugging — 3–10× cost lever. See `docs/ai-cto/process-efficiency.md` §2. | P2 | DESIGN | Open (found 2026-06-14) |
| TD-15 | Hybrid offload: the Odin/LiteLLM local-first router (`localDNS/10-ai-orchestration`) isn't used for our own dev busywork (link-checks, commit drafts, summaries, webhook triage). Add an "ask-local-first" path, Claude API on escalation — 60–90% cost cut on the easy 80%. BLOCKED on TD-14 (fail-closed first). See `docs/ai-cto/process-efficiency.md` §3. | P2 | localDNS | Open (found 2026-06-14) |
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
