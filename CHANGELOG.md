# CHANGELOG — A777ance (cross-repo)

Plain-language activity log across all five repos, for collaborators catching up. Newest-first
(house style). This lives in `DESIGN` (private/internal) because it references private-repo
status — do **not** mirror it into the public `localDNS` repo.

**Read the status label, not just the headline.** Being committed to a repo is *not* the same as
being built and running. These repos are config/spec snapshots; the live t630 is the source of
truth for `localDNS`, and tooling that needs credentials stays guarded off until they exist.

| Label | Means |
| ----- | ----- |
| ✅ built & verified | Code/config committed **and** checked here (e.g. selftest passes). Still repo-side, not necessarily deployed. |
| 🧪 reference / scaffold | Committed, but not a wired end-to-end system (placeholders, Phase-2 stubs, demo only). |
| 🚧 not deployed | Needs the t630, a credential, or a `CHANGE_ME` filled in before it does anything live. |
| ⚠️ correction / gap | A claim corrected, or a known open gap to close. |

---

## 2026-06-07 · localDNS — LLM-router orchestration (reference + config; **not deployed**)

- ✅ **Deterministic dispatcher** — `10-llm-router/dispatcher.py`. Pure `classify()` rule table
  (no AI in the routing decision; same input → same route, zero token cost). Inline selftest
  passes: routing, the privacy redaction, and the readable `--reflect` log are all covered.
- ✅ **Reflection log made reviewable** — routes log to JSONL and read back via `--reflect`;
  redaction keeps a one-line takeaway on sensitive tasks while dropping the actual content.
- ✅ Engineer-facing design committed — `10-llm-router/ORCHESTRATION-BLUEPRINT.md`.
- 🧪 **It is a reference, not a wired router.** `dispatcher.py` routes to `cloud-explore` /
  `cloud-code` / `cloud-vision` tiers that **do not exist in `config.yaml` yet** (Phase-2). Only
  `local-fast`, `local-smart`, `local-reason`, `cloud-gpu-reason`, `cloud-overflow` are defined.
- 🚧 **Rented-GPU heat-offload is config, not capability.** The reasoning ladder is defined, but
  `cloud-gpu-reason`'s `api_base` is a `CHANGE_ME_GPU_HOST` placeholder and nothing is deployed
  to the t630. The "heavy R1 cooks the CPU" issue has a *designed* fix, not a *running* one.
- ⚠️ **Open privacy gap — does not yet match the claim.** An earlier draft of this log said
  sensitive tasks "can never be sent to a cloud provider." Not true today: in `config.yaml` the
  `local-reason` tier (where sensitive tasks route) falls back to `cloud-overflow`
  (`anthropic/claude-opus-4-8`, **cloud**). The dispatcher's `allow_cloud=False` is not enforced
  at the LiteLLM failover layer, and the dispatcher's own docstring *requires* a local-only
  fallback chain here. **A sensitive prompt could leak to the cloud if the local model is down.**
  → tracked in `docs/ai-cto/tech-debt.md`; fix = give `local-reason` a local-only fallback (fail
  closed) before any privacy guarantee is claimed.
- Housekeeping: consolidated to `main`; this session's feature branch retired locally.

## 2026-06-05 · House style adopted across all five repos

- ✅ `localDNS`, `MARKETING`, `DESIGN`, `claude-code-homelab`, `azure-lab` all adopt the shared
  conventions: **Gill Sans MT** everywhere, **newest-first** time-based content, **Z→A**
  alphabetical lists, reversed walkthrough blocks.

## 2026-06-05 · localDNS — Stage 10 LLM router (config committed; running state unverified)

- 🧪 LiteLLM + Ollama `config.yaml` and an Open WebUI `docker-compose.yml` committed; the
  "push-to-main, no branches" standing rule recorded. Whether it is actually running on the
  t630 is unverified from here (config snapshot; no box access).

## 2026-06-05 · MARKETING — "Rainbow Bridge" sync (scaffolded, **guarded OFF**)

- 🧪🚧 A Google Drive → NotebookLM pipeline (Apps Script manifest + GitHub Actions workflow +
  sync scripts) is committed, but `notebooklm-bridge.yml` **skips the sync until Google
  credentials are configured** — it is not live. The A777ance master spreadsheet and content
  folders were added alongside.

## 2026-06-05 · DESIGN — governance refresh

- ✅ Portfolio hub reconciled to live state; NARF (AI CTO) and ZORT (AI CFO) session updates
  filed; the Codex cross-repo review recorded under `docs/ai-cto/reviews/`.

---

*For the **decisions** behind these changes (not just the activity), see
`docs/ai-cto/decisions.md` and `docs/ai-cfo/decisions.md`.*
