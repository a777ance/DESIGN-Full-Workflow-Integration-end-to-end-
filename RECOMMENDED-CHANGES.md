# Recommended changes — cross-repo distillation audit (2026-06-10)

Result of a five-repo consistency audit (`localDNS`, `MARKETING`, `DESIGN-…`,
`claude-code-homelab`, `Azure-lab`): contradictions, stale references, and duplications.
Newest-first per house style — what was **remediated in this pass** leads; what remains
**recommended** (judgment calls needing an owner decision) follows.

---

## Remediated in this pass (2026-06-10)

| Fix | Where | What changed |
| --- | ----- | ------------ |
| Deploy-automation framing | `claude-code-homelab/docs/04-deploys.md` | Noted the Actions+SSH workflow is the *automation upgrade*, not a prerequisite — localDNS deploys manually today (its only Action publishes the Statement gallery to Pages) |
| Branch-strategy contradiction | `claude-code-homelab/docs/05-best-practices.md` | The guide taught feature-branch/PR workflow while the case study (localDNS) mandates "push to `main`, no branches" (founder instruction, 2026-06-05). Now presents both models — solo/founder-direct (localDNS today) and branch-and-review (teams) — and says to write the choice into each repo's CLAUDE.md |
| Dead SETUP.md references | `claude-code-homelab/docs/02-repo-structure.md`, `docs/05-best-practices.md` | localDNS absorbed SETUP.md into README.md; the guide still told readers to maintain SETUP.md. Added a reconciliation note ("your reproduction guide, wherever it lives") at the point of introduction and at each load-bearing mention |
| ADR-005 numbering collision | `Azure-lab/CLAUDE.md`, `Azure-lab/docs/ai-cto/context.md` | Both told the reader to record the Azure scope decision as **ADR-005**, but ADR-005 is already "Member dues: $50/mo flat" in the DESIGN decisions log. Now point at the next free number (ADR-008 at time of writing, with a "check the log first" caveat) |
| Stale "No CLAUDE.md" status | `Azure-lab/docs/ai-cto/context.md` | The stub CLAUDE.md exists; status line now says so |
| Stale $32/mo pricing | `MARKETING/docs/ai-cfo/context.md` | Two pre-ADR-007 figures survived the 2026-06-04 pricing decision: "$175/$32" and "1 home at $32/mo … 10 homes = ~$3,600/yr". Corrected to the ADR-007 standard: $35/mo, ~$4,200/yr. (The LTV figures in the same file were already $35-based.) |
| Dues decision marked fully open | `MARKETING/CLAUDE.md` §2 | "Member dues amount + what they unlock" implied the amount was undecided; it was set 2026-06-04 (ADR-005/FIN-001, $50/mo). Now matches README: amount **set**, inclusions still open |
| Orphaned folders undocumented | `MARKETING/CLAUDE.md` §4 | `notebooklm-bridge/` (a working repo→Drive sync for NotebookLM sources) and `fun/` (empty creative-asset scaffolding) were invisible from the repo's own docs. Both now listed under Further reading |
| Three-repo table header drift | `DESIGN…/CLAUDE.md` | "Who sees it" → "Visibility", matching MARKETING/CLAUDE.md's identical table |
| ZORT hub staleness | `DESIGN…/docs/ai-cfo/portfolio.md` | Refreshed "Last updated" and logged the pricing-figure sync in Recent Financial Decisions (no financial state change since review #1) |

---

## Recommended — not applied (need an owner decision)

1. **Distill the house-style block (6 copies).** Byte-identical in five CLAUDE.md files +
   `claude-code-homelab/templates/CLAUDE.md.template` (Azure-lab adds one intentional
   sentence). In sync today; it will drift on the next edit. Options: declare the
   template canonical and stamp each copy with "copied verbatim from the template on
   YYYY-MM-DD", or add a one-line editor's note ("edited? update all six") to each copy.

2. **De-duplicate localDNS CLAUDE.md ↔ README.md tables.** Services/ports, WireGuard
   peers, hardware specs, and the DNS-split narrative each live in both files. Verified
   in sync today (every port and peer matches), but it's a two-place update burden.
   Nominate one file canonical per table and cross-reference from the other — suggested:
   CLAUDE.md keeps the authoritative tables (it calls itself "the authoritative
   summary"); README links to them where it currently repeats them.

3. **Schedule a real ZORT review #2.** The hub got a doc-sync touch in this pass, but the
   financial snapshot itself is still the 2026-06-04 baseline while the NARF hub has
   moved to 2026-06-07. The session-end update protocol exists; it missed a cycle.

4. **Give `MARKETING/fun/` a purpose or remove it.** Four empty directories
   (collections/galleries/images/songs). If assets are coming, add a one-line README; if
   not, delete the scaffolding.

5. **Exercise claude-code-homelab's own "verify against localDNS" rule periodically.**
   The SETUP.md and branch-strategy staleness fixed above are exactly the rot its
   Working philosophy warns about. Cheapest fix: a recurring check, or a link/claims
   checker in CI like DESIGN's `tools/check-docs.py` (which passes cleanly today).

6. **Accepted duplication (leave as is).** The roles/money-flow diagram and funnel appear
   in both DESIGN and MARKETING (CLAUDE.md + README each) — intentional, different
   audiences, currently identical in substance. The biggest drift risk here is numbers;
   pricing is governed by ADR-007, which is the right control.

---

## Verified healthy (no action)

- **localDNS** is the cleanest repo: all 40 deploy-path entries exist on disk; every port
  (53/8080/5335/51820/4000/3389/22/4040/3000/8088/7681/7682/3001) matches across
  CLAUDE.md, README.md, UFW script, and compose files; the WireGuard peer table matches
  `wg0.conf`; the DoT forward config matches its docs; the Pi-hole v6 env-var migration
  is complete. The "six drop-ins" claim in CLAUDE.md §D is **correct** (six `.conf` files
  ship in `01-unbound/`).
- **Pricing** ($175 + $35/mo, band $29–39, founding $29 locked 12mo) now consistent in
  every file checked. **Dues** ($50/mo, ADR-005/FIN-001) consistent everywhere.
- **ADR/FIN numbering** has no gaps or duplicates (ADR-001–007; FIN-001–004, FIN-005
  proposed) now that the Azure-lab pointer is fixed.
- **Cross-repo paths** DESIGN claims in localDNS (`docs/statements/client/*.html`,
  `operator/*.html`, `tools/collect/*`) all exist. `python3 tools/check-docs.py` passes.
- **House-style ordering** (newest-first logs, reversed walkthrough blocks) is correctly
  applied in the changelogs, decision logs, and the localDNS README contents.
