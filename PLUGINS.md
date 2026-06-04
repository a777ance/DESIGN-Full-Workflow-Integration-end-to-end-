# PLUGINS.md

Which Claude Code **Directory** plugins (Anthropic & Partners) to turn on for this repo
— and, just as important, which to leave off. A companion to `SKILLS.md`: that file maps
the skills this workflow *exercises*; this one maps the off-the-shelf plugins that
*accelerate* them.

**The governing rule is this repo's own:** *"if it does none of those, it does not
belong"* (`CLAUDE.md` §3). A plugin is not free — enabling one loads its skills and
instructions into context and adds its tools to every turn, so a plugin that doesn't move
a Statement closer to earned, produced, delivered, or paid-for is pure noise against the
context budget. **Scope per repo, not globally:** this repo (the machine) wants the most;
`localDNS` (the stack) wants almost none; `MARKETING` (the why) wants a strategy subset.
The fact that the right set differs by repo *is* the recommendation.

---

## For this repo (DESIGN — the machine)

This is where the plugins earn their keep: most of the funnel stages map onto a Directory
plugin almost one-to-one.

**Enable (core) — these land straight on a stage:**

- **Marketing** — stage `02-demand-generation/`: own "pest control for your network,"
  local SEO, geo-targeted audiences, Mailchimp lifecycle. Also drafts the
  category-education content the funnel runs on.
  → `02-demand-generation/README.md`, `02-demand-generation/category-education.md`
- **Sales** — stage `05-sales-and-onboarding/` (discovery → scoped quote → setup fee →
  close) *and* stage `09-recruiting-and-guild/`: the operator funnel is a sales funnel
  pointed at supply.
  → `05-sales-and-onboarding/README.md`, `09-recruiting-and-guild/operator-funnel.md`
- **Finance** — stage `07-payments-receivables/` (setup fee + retainer plans, dunning,
  reconciliation) and the contractor payouts in stage `10-gig-workers-compliance/`.
  → `07-payments-receivables/receivables.md`, `10-gig-workers-compliance/1099-checklist.md`
- **Data** — stage `08-client-list-and-crm/`, the system of record: schema design,
  segmentation queries, and the roster the Statement generator reads. Touches stage
  `06`'s "How You Compare" cohort problem too.
  → `08-client-list-and-crm/schema.md`, `06-statements-delivery/monthly-run.md`

**Enable when that stage goes live:**

- **Legal** — stage `10-gig-workers-compliance/` (W-9, 1099-NEC, the contractor
  agreement) and the "guild-certified" vetting standard. Use it to *draft and triage*,
  not to rule: the repo already flags worker classification as the real risk to confirm
  **with counsel** — the plugin does not change that.
  → `10-gig-workers-compliance/contractor-agreement-outline.md`, `09-recruiting-and-guild/vetting-checklist.md`
- **Product Management** — specs, the integration map, and roadmap work. A meta-tool
  across the repo rather than a single stage; turn it on when you are planning, not
  executing.
  → `11-automations/automation-map.md`, `CLAUDE.md`

**Hold:**

- **Customer Support** — maps to stage `04-phone-and-comms/`, but a ticketing plugin
  earns its place at *volume*. By design every incident is a **cost** (the flat-retainer
  incentive invariant), so volume stays low early. Revisit once there is a real queue and
  a knowledge base to build.

**Skip:**

- **Productivity** — generic task/day planning + personal memory. Helps you; maps to no
  artifact in this repo.
- **Postiz** — social-media scheduling. The go-to-market is local density, the referral
  loop, and zip-at-a-time clustering (`MARKETING`) — *not* broadcast social. Wrong tool
  for this funnel.

---

## The three-repo picture

Same plugins, three different answers — scope them per repo:

| Plugin (Directory) | `localDNS` (stack) | `MARKETING` (why) | DESIGN (machine) |
| --- | --- | --- | --- |
| **Marketing** | — | Enable | Enable — `02` |
| **Sales** | — | — | Enable — `05`, `09` |
| **Finance** | — | Enable | Enable — `07`, `10` |
| **Data** | Tangential | When active | Enable — `08`, `06` |
| **Legal** | — | — | When active — `10` |
| **Product Management** | — | Enable | When active |
| **Customer Support** | — | — | Hold — `04` |
| **Productivity** | — | Skip | Skip |
| **Postiz** | — | Skip | Skip |

**Enable** = turn on now · **When active** = on while that stage/work is live ·
**Hold** = wait for volume · **Skip** = costs context, returns nothing here ·
**Tangential** = touches it, but the work lives elsewhere · **—** = no fit.

`localDNS` is a DNS/VPN/monitoring config repo; none of these business plugins help it —
it wants engineering tooling, not this Directory (see its own `PLUGINS.md`).

---

## Further reading

- **`CLAUDE.md`** §3 — the "if it does none of those, it does not belong" rule this note applies.
- **`SKILLS.md`** — the skills this workflow exercises, each mapped to its proving artifact.
- **`MARKETING` and `localDNS`** — each carries its own `PLUGINS.md` with the same decision for that repo.
