# Codex Full-Tilt Cross-Repo Review - 2026-06-05

Prepared by: ChatGPT Codex

Install location: `DESIGN-Full-Workflow-Integration-end-to-end-/docs/ai-cto/reviews/`

## Why this belongs here

`DESIGN-Full-Workflow-Integration-end-to-end-` is the right repo for this review because it is already the portfolio hub: it tracks the operating workflow, CTO/CFO state, roadmap, decisions, and cross-repo tech debt. The findings below span `localDNS`, `customers`, `MARKETING`, `Chronikomicon`, `Azure-lab`, and `claude-code-homelab`, so installing the review in any spoke repo would hide the broader picture.

The implementation work should happen in the affected repos, but the ranked action list belongs here.

## Review scope

Reviewed repos:

- `localDNS`
- `customers`
- `DESIGN-Full-Workflow-Integration-end-to-end-`
- `MARKETING`
- `Chronikomicon`
- `Azure-lab`
- `claude-code-homelab`

Checks run:

- `localDNS/tools/check-docs.py` passed.
- `DESIGN-Full-Workflow-Integration-end-to-end-/tools/check-docs.py` passed.
- JSON parse pass found one expected JSON-with-comments issue in `Chronikomicon/access/Chronikon.code-workspace`; VS Code accepts this format, strict JSON parsers do not.
- Local statement rendering failed because `segno` is not installed locally and `localDNS` does not declare its Python dependencies.

## Ranked improvements

### 1. Fix the statement data contract

This is the highest-impact item. `localDNS/docs/statements/tools/collect/collect_stats.py` writes `null` when Pi-hole, Kuma, WireGuard, or nftables sources are unavailable, but `localDNS/docs/statements/tools/compose.py` assumes the account-summary fields exist. That means the advertised "best effort" pipeline can crash or print bad values when a source is missing.

Recommended work:

- Define a stats schema for `queries`, `uptime`, `latency_ms`, `vpn_sessions`, `devices`, and `volume`.
- Make `compose.py` null-safe per section.
- Add sample fixtures for full data, no volume, no Kuma, no wg, and no Pi-hole.
- Add tests proving each missing source omits or marks the right section without inventing numbers.
- Clarify which metrics are period-scoped and which are current snapshots.

Primary repo: `localDNS`

Related repo: `customers`

### 2. Automate the public/private data boundary

`customers` intentionally holds real household data. `localDNS` is public and publishes `docs/statements/` to GitHub Pages. The policy is documented, but it needs automated enforcement.

Recommended work:

- Add a CI check in `localDNS` that blocks public statement data containing real household IDs, private account IDs, or known customer names.
- Add a CI check in `customers` that asserts the repo remains private when GitHub metadata is available.
- Add a smoke test proving real statements render only through `--data-dir` and `--out-dir` into private paths.
- Add a pre-publish checklist for Pages artifacts.

Primary repo: `localDNS`

Related repos: `customers`, `DESIGN-Full-Workflow-Integration-end-to-end-`

### 3. Make DESIGN the authoritative control plane

The hub is useful but stale in places. For example, `docs/ai-cto/tech-debt.md` says `tools/check-docs.py` is not wired into CI, while `.github/workflows/check-docs.yml` exists. `docs/ai-cto/portfolio.md` says `customers` is local-only, while the repo is now on GitHub and cloned.

Recommended work:

- Add a machine-readable `portfolio.json` or `repos.yml`.
- Add a hub sync check that verifies repo names, visibility expectations, CI presence, and key tracker claims.
- Update `portfolio.md` and `tech-debt.md` from that source instead of hand-maintaining conflicting state.
- Reclassify stale items after the sync check passes.

Primary repo: `DESIGN-Full-Workflow-Integration-end-to-end-`

### 4. Declare dependencies and test the statement pipeline locally

`generate_client.py` imports `segno`; the Pages workflow installs it ad hoc, but `localDNS` has no dependency file. The `customers` Makefile shells out to `localDNS`, but its `check` target only verifies that one file exists.

Recommended work:

- Add `localDNS/requirements.txt` or `docs/statements/requirements.txt`.
- Add `make test-statement` or `python -m` test entry points.
- Run collect sample -> compose -> render in CI.
- Make the `customers` Makefile discover a sibling `../localDNS` checkout before falling back to `$(HOME)/localDNS`.

Primary repo: `localDNS`

Related repo: `customers`

### 5. Put scheduled AI workflows behind reports or PRs

`DESIGN` has daily AI CTO/CFO workflows with `contents: write` and automatic commits. That is powerful but gives scheduled text generation direct write authority over the hub.

Recommended work:

- Change scheduled runs to create issues, artifacts, or PR branches.
- Keep manual `workflow_dispatch` for deliberate write sessions.
- Add clear commit attribution and run metadata.
- Add a guard that prevents empty or repetitive auto-commits.

Primary repo: `DESIGN-Full-Workflow-Integration-end-to-end-`

### 6. Pin infrastructure versions and fail fast on placeholders

`localDNS/02-pihole/docker-compose.yml` uses `pihole/pihole:latest`, even though the repo documents prior version-scheme drift. Monitor scripts still carry push-token placeholders that can fail silently if deployed unchanged.

Recommended work:

- Pin Pi-hole to a tested version.
- Add `.env.example`.
- Add a `doctor` or `preflight` command that refuses deploys with `CHANGE_ME`, `<PUSH_TOKEN_*>`, or missing required env.
- Add shell checks for monitor scripts.

Primary repo: `localDNS`

### 7. Clear WireGuard trust debt

`localDNS/05-wireguard/wg0.conf` records one peer whose private key was exposed and three unidentified peers with no recent handshake.

Recommended work:

- Rotate the exposed Windows laptop key.
- Identify or remove stale peers.
- Add a peer inventory with owner, device, public key fingerprint, assigned IP, created date, and last verified date.
- Add a deploy check that flags unidentified peers.

Primary repo: `localDNS`

### 8. Fix Chronikomicon automation paths

`Chronikomicon` workflows watch root `manuscript/**`, but the repo structure keeps manuscript files under the shadow hierarchy. Build and word-count automation can miss the real draft. The PDF build also references `weasyprint` without installing it first.

Recommended work:

- Point workflows at the actual manuscript path or create a root manuscript symlink/path intentionally.
- Install the PDF engine used by the workflow or remove the explicit engine.
- Add a workflow test that fails when no chapter files are found.

Primary repo: `Chronikomicon`

### 9. Add AGENTS.md bridge files

Most repos have `CLAUDE.md`; none have `AGENTS.md`. Codex reads `AGENTS.md` naturally, so each repo should have a small bridge that points agents to the existing Claude brief and repo-specific rules.

Recommended work:

- Add `AGENTS.md` to each repo.
- Keep it short: purpose, primary source docs, safety rules, and "read `CLAUDE.md` when present."
- Do not duplicate the whole `CLAUDE.md`; use it as the source of truth.

Primary repo: all repos

Control repo: `DESIGN-Full-Workflow-Integration-end-to-end-`

### 10. Resolve or explicitly park Azure-lab

`Azure-lab` is an intentional stub. That is fine, but it should stop showing up as active work until a scope decision exists.

Recommended work:

- Record ADR-005 with the chosen scope, or mark the repo parked.
- If parked, update `DESIGN` so the repo is not treated as an active blocker.
- If scoped, add a real `CLAUDE.md`, `AGENTS.md`, and minimal CI.

Primary repo: `Azure-lab`

Related repo: `DESIGN-Full-Workflow-Integration-end-to-end-`

## Recommended first implementation batch

Do these first:

1. `localDNS`: add stats fixtures and null-safe `compose.py` behavior.
2. `localDNS`: add dependency file and a CI test for collect sample -> compose -> render.
3. `DESIGN`: add a repo manifest and sync check for stale portfolio claims.
4. `customers`: improve the Makefile path discovery and add a private-render smoke test.

That batch turns the portfolio from good documentation into a repeatable operating system.
