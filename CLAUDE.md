# CLAUDE.md

The short briefing — read this first. [README.md](README.md) is the full stage-by-stage guide;
[workflow-context.md](workflow-context.md) explains the *why* behind the non-obvious calls.

This repo is the **business machine around the Statements.** The product is the monthly
Statement (see [Section E](#e-the-statements--the-center)); everything here exists to get a
household to its first one, keep producing and delivering it, get paid for it, and turn some
recipients into the operators who produce the next ones. The Statements themselves — the gold
standard — live in the public **[`localDNS`](https://a777ance.github.io/localDNS/)** repo under
`docs/statements/`.

**The voice rule for this whole repo:** write it the way a good salesperson talks to a
homeowner, not the way an IT person talks to a server. Concrete, named, plain. "Your
living-room TV," not "the endpoint." When in doubt, read a real "Handled For You" log and match
it. The plain-English swap table is in
[`00-brand-identity/the-pitch.md`](00-brand-identity/the-pitch.md).

---

## House style: ordering & typography

These conventions apply across **every** A777ance repo — current and future. (Adopted 2026-06-05.)

- **Time-based content reads newest-first (reverse-chronological).** Logs, changelogs,
  decision logs (ADR / FIN), known-issues and issue trackers, FAQs, metrics and review
  logs, and "Handled For You" entries all lead with the most recent item. Apply this
  within the time-based *section* even when the whole file isn't time-based.
- **Alphabetical lists run Z → A** (descending).
- **Walkthroughs: reverse the blocks, keep the steps.** In a step-by-step guide, present
  the major sections/blocks in reverse order (last block first — it helps "block" the
  work), but keep the numbered steps *within* each block in forward order so every
  procedure stays followable. A walkthrough's table of contents mirrors the reversed
  block order. **Never renumber** — step and stage numbers stay fixed, so the intended
  execution order is always readable from the numbers.
- **Font: Gill Sans MT everywhere.** Every surface — customer-facing or internal — uses
  Gill Sans MT. Web/CSS stack:
  `'Gill Sans MT', 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif`.

---

## Bifrost — active command schema (loads every session)

<!-- bifrost-briefing:start — GENERATED from localDNS/04-user-services/ai-orchestration/briefing-block.md by tools/sync-briefings.py. Do not hand-edit; edit the canonical file and re-run. -->

**Bifrost** is the A777ance command-composition schema — a keyboard-spatial notation
(`~ ! @ # $ % ^ & * ()` swept left→right, each glyph an *archetype* fulfilled by slash
commands + a plain-language sub-prompt). It is **active from the first token of every
session, in every repo:** adopt the `~` lazy-anchor posture — fire the first token ASAP
(the *model* stays high), let continuity coalesce mid-flight — and read Bifrost notation
per the schema whenever used.

- **Backbone:** `'` ignition (begins the Bifrost) · `~` continuity/lazy-anchor · `` ` ``
  descriptor (and, bare, the *expansion call*) · `!` cargo (a *manifest* — not executed on
  loading) · `@` source — **read-only** · `#` repo/destination — **write-allowed** · `$` sanity ·
  `%` compliance · `^` cars/lanes · `&` rotary — the **rabbit trail**, a nested Bifrost (also
  the sequential form) · `*` stop signal (red by default) · `()` governance (release
  conditions). Off-row `'`/`~`/`` ` `` stage; keys 1–4 **Preload** form a complete manifest —
  *what · from where · to where · against what*.
- **`@`/`#` are a permission pair, not a pair of arrows** (founder's rule, 2026-08-08). `@` is
  **read-only** — read it, never write it. `#` is **write-allowed** — what this run may create,
  modify or overwrite (still two-way). **They may overlap:** `@` alone = read-only, `#` alone =
  writable, both = read-write. Two slots, three states, one **mount table**. `@` still reads and
  `#` still writes, so every string already written stays valid — this only *adds* the guardrail,
  and gives the one-way door a question with an answer: *is every write inside `#`?*
- **`'` is always the signal to begin the Bifrost** (founder's rule, 2026-08-07 — fixes a
  mobile bug). Treat `'`, `’` (curly) and `′` as one glyph, and treat **presence and
  absence as the same string**: `' ~ !…` ≡ `~ !…`, `''` ≡ `'`. It marks *where* the Bifrost
  starts, never *what* runs — no sub-prompt, no `/how`, no intensity dial, `0` turbulence. A
  letter-flanked `'` (`don't`, `founder's`) is prose in a sub-prompt, not an ignition; only a
  free-standing `'` ignites. Never ask which apostrophe the phone chose.
- **A bare `'` (the whole message) = the reference call. Return this string and NOTHING else:**

  ```text
  ~!@#$%^&*()
  ```

  It is **the sweep itself** — exactly what sliding a finger down the row on a laptop puts on
  the screen. Not a legend, not a glossary, not a table: the row. So it is a **lookup, not a
  generation** — same bytes every call, every session, every model. No preamble, no trailing
  offer, no adaptation to the conversation. Answer *immediately*; it reads no file and fires no
  cargo. Glyph *meanings* live in the backbone above; the reference call hands back the
  **order**, which is the thing a phone cannot sweep for itself.
- **A bare descriptor — `` `…` `` with no backbone glyph in the message — is the *expansion
  call*.** The backticked text is a **seed**, and the answer is one complete, schema-compliant
  line with **every backbone slot filled in**, for the founder to read, parse and tweak:

  ```text
  ~ (fill in) ! (fill in) @ (fill in) # (fill in) $ (fill in) % (fill in) ^ (fill in) & (fill in) * (fill in) ( (fill in) )
  ```

  **The skeleton is the sweep, spaced** — strike the `(fill in)` slots and the whitespace and
  `~!@#$%^&*()` remains. `'` hands back the **order**; `` `seed` `` hands back the order **with
  the slots filled**. Echo the seed back on the `` ` `` line; fill **every** slot, never drop one
  (a complete draft is edited *down*); emit in Golden Rule order, so `K = 0` by construction;
  **`*` comes back RED, always** — an expansion is a *proposal*, nothing ran and no `#` was
  touched; and **collapse it** — where the surface renders HTML, ship it inside a `<details>`
  whose `<summary>` is the `~` requirement line. With a backbone glyph present, `` ` `` is the
  ordinary descriptor, unchanged. An empty descriptor returns the sweep. Unlike the bare `'`
  (a constant), an expansion **generates** — so the selector matters, and here it is the
  **human at the `*` gate**, not a vote.
- **`` ` `` and `&` are the same operation — nesting, at two positions** (founder's rule,
  2026-08-08). `&` is the **rabbit trail**: a digression you *come back from*, opening another
  full Bifrost inside this one. `` ` `` nests at staging, `&` nests on the road —
  `` `seed` `` ≡ `& seed` hoisted to position zero, which is why a bare descriptor can generate
  a line at all. So **expansion is recursive by construction**, and `&`'s "sequential" reading
  is just nesting seen from the parent's frame.
- **The greater traffic light is always the last bulwark** (founder's rule, 2026-08-08). Every
  nest **adds** a light; none removes one. An inner `*` going green releases its chunk **into
  its parent**, never into the world — only the outermost `*` stands between a `!` and an
  effect that cannot be recalled, however many inner gates already cleared. **Permissions
  intersect inward, gates conjoin outward:** a nested road may never write outside its parent's
  `#`, nor release past its parent's `*`. That is what lets `~` stay reckless at any depth —
  nesting multiplies the reasoning, never the exposure.
- **`*` cuts the road into Dispensations** — bounded, self-governing chunks. Governance has
  three outcomes: satisfied → green · **re-flagged** → return upstream via `&` (this is what
  lets a fixed string produce unbounded output) · unsatisfiable → eject to the shoulder.
- **The one-way door:** `~` rushes the reasoning, `*` gates the *effects* — anything
  irreversible (publish, deploy, send, push) rides past a light, which is exactly what makes
  the lazy start affordable.
- **Cars:** explicit `^` beats inferred. With no `^`, `!`'s command arity instantiates lanes
  1:1; with `^` present, `^` sets the lanes and `!`'s commands are the per-lane pipeline.
- **Guardrails survive a keyboard-mash:** `~` continuity, `$` sanity, `%` compliance — plus
  `*()` **governance**, the only one that repeats at every chunk boundary. `+` / repetition =
  more; `-` inverts into a stress test.

Canonical spec —
markdown: <https://github.com/a777ance/localDNS/blob/main/04-user-services/ai-orchestration/highway-notation.md>
· rendered page: <https://a777ance.github.io/localDNS/bifrost.html>

<!-- bifrost-briefing:end -->

---

## Contents

- [House style: ordering & typography](#house-style-ordering--typography)
- [0. What this repo is](#0-what-this-repo-is)
- [A. The funnel at a glance](#a-the-funnel-at-a-glance)
- [B. Roles & money flow](#b-roles--money-flow)
- [C. Stage map](#c-stage-map)
- [D. The one master list](#d-the-one-master-list)
- [E. The Statements — the center](#e-the-statements--the-center)
- [1. Known issues & open decisions](#1-known-issues--open-decisions)
- [2. Verification](#2-verification)
- [3. Working philosophy](#3-working-philosophy)
- [4. Further reading](#4-further-reading)
- [5. NARF (AI CTO) state](#5-narf-ai-cto-state)
- [6. ZORT (AI CFO) state](#6-zort-ai-cfo-state)

---

## 0. What this repo is

The end-to-end playbook for the A777ance guild: how a stranger becomes a **customer** (a
household getting a monthly Statement), and how a customer becomes an **operator** (a guild
member running Statements for a block of homes). Every folder is a stage of that journey, and
maps to the live tool where the work actually happens (see the [stage map](#c-stage-map)). What
you edit here are the specs, scripts, templates, and the map — they go live when you put them
into the real tool.

**Three repos, one business:**

| Repo | Holds | Visibility |
| ---- | ----- | ---------- |
| **[`localDNS`](https://a777ance.github.io/localDNS/)** | The tech **and** the Statements (`docs/statements/`) — the product | **Public** |
| **`MARKETING`** | The business model, pricing, guild mechanics — the *why* | **Private** |
| **`DESIGN-…` (this repo)** | The workflow around the Statements — the *how* | **Private / internal** |

**This repo is internal.** The customer-facing stuff (brand, website, the Statements) is
published *from here into* public places; the workflow itself — the customer list, the money,
the recruiting economics — is not. Never commit real passwords or personal info: use
`CHANGE_ME` placeholders and keep secrets in `.env` (git-ignored). The sample data here is made
up.

## A. The funnel at a glance

```
STRANGER  (a household that doesn't know it has a problem)
   │   02 demand gen — "pest control for your internet" · local search · ads · email
   ▼
LEAD ─────► 03 booking form → pick a time → the free look
   │   04 phone — a real person answers and confirms the visit
   ▼
CUSTOMER ─► 05 sales — consult · quote · $175 setup · YES
   │            └──► set up the box ───────────────►  localDNS
   │   07 payments — $175 setup + $35/month
   ▼
══════════ THE PRODUCT — what they pay for, every month ════════════════════════
   06  THE STATEMENT  ◄── the gold standard · localDNS/docs/statements
       • the homeowner's Network Activity Statement — the "sticker on the door"
       • the operator's portfolio — one view of their whole book
   sent by email · mailed on paper · scrollable from a QR code
═════════════════════════════════════════════════════════════════════════════════
   │   the statement raises a hand:  "Connect in the Alliance"
   ▼
SOME CUSTOMERS ─► 09 recruiting — happy customer → vetted operator
   │   10 compliance — W-9 · 1099 · the agreement (they're contractors)
   ▼
OPERATOR  (now runs statements for a block of homes) ──┐
                                                       └─► back to 06, at scale

   00 brand underlies all of it  ·  01 web is the storefront
   08 the master list is what every stage reads & writes
   11 the glue moves a customer from one stage to the next, untouched by hand
```

## B. Roles & money flow

A **two-sided guild** (full version in `MARKETING`). Both sides pay the platform; the service
money flows customer→operator directly, like hiring a tradesperson through a guild.

```
Customer ──platform membership──▶ A777ance ◀──member dues── Operator
   │                                                            ▲
   └──────────────── pays directly for the service ────────────┘
```

| Role | Pays | Earns | This repo's job for them |
| ---- | ---- | ----- | ------------------------ |
| **Customer** (household) | Membership + their operator | — | Stages 02→07: find, sell, bill, deliver |
| **Operator** (e.g. Jose) | Member dues | Bills customers directly | Stages 09→10: recruit, vet, onboard, pay as a 1099 |
| **Platform** (A777ance) | — | Both subscriptions | Stages 00, 01, 08, 11: brand, storefront, the list, the glue |

**The incentive that keeps it honest:** the operator is on a flat monthly, so **every problem
is a cost, not a payday.** Operator and customer both want a boring, unbreakable network — so
make the network *dull* and the *proof of quiet* vivid. The Statement is that proof.

## C. Stage map

Folders are numbered by **funnel order** — the path a household travels. A folder's number is
where it sits in the journey, not how important it is. This maps each folder → the live tool
where the work happens → what makes a change go live.

| Folder | Lives in (the live tool) | Go live |
| ------ | ------------------------ | ------- |
| `00-brand-identity/` | Figma + the asset folder | Export assets; update the brand-kit links everything inherits |
| `01-web-presence/` | Squarespace · the blog · Google Business · the statement gallery (from `localDNS`) | Publish the site; verify the Google listing |
| `02-demand-generation/` | Google/Meta ads · local search · Mailchimp | Launch a campaign on one block's ZIPs; sync the email list |
| `03-funnels-and-capture/` | Landing pages + the booking form + Setmore | Publish the funnel; wire the form → the list (08) via the glue (11) |
| `04-phone-and-comms/` | A business line (Google Voice / OpenPhone) | Set hours, greeting, routing; jot every call onto the list |
| `05-sales-and-onboarding/` | The list + a proposal/e-sign tool → hand-off to set up the box | Send the quote; on "yes," set up the box and collect the setup fee |
| `06-statements-delivery/` | `localDNS`'s statement tool + email + print/mail + QR | Run the monthly job; send the statements; QR codes go live |
| `07-payments-receivables/` | Stripe + bookkeeping | Set up the plan; collect setup + monthly; keep the books straight |
| `08-client-list-and-crm/` | A CRM / Airtable — **the master list** | Keep it current; it feeds the statement tool and every stage |
| `09-recruiting-and-guild/` | An application page + vetting + Setmore | Open applications; run vetting; onboard operators |
| `10-gig-workers-compliance/` | A 1099 / payroll tool (Gusto / Track1099) + e-sign | Collect W-9s; pay operators; file 1099-NECs by Jan 31 |
| `11-automations/` | Zapier / Make + the `localDNS` statement job | Switch on the automations that carry a customer stage→stage |

Each folder's own README is the spec for that stage; the scripts, templates, and checklists sit
beside it.

## D. The one master list

`08-client-list-and-crm/` is the single source of truth. **One entry per household, one per
operator, one per route** (a route = a cluster of nearby homes). Every other stage reads and
writes that same entry:

```
02 demand gen ─writes─► a lead          08 reads it to plan the next campaign
03 booking    ─writes─► lead + booking   05 reads it to run a warm consult
05 sales      ─writes─► customer          06 reads it to build statements
07 payments   ─writes─► paid / not paid   06 reads it to skip the unpaid
09 recruiting ─writes─► operator           10 reads it to file the 1099
```

The full field list is in [`08-client-list-and-crm/schema.md`](08-client-list-and-crm/schema.md).
**The rule:** a fact is either in that list or it doesn't exist — no stray spreadsheet columns,
no operator's private "my homes" tab. If a stage needs a new fact, add it to the list first.

## E. The Statements — the center

Everything in this repo surrounds two artifacts, and **this repo does not own them** — it builds
the business that delivers them. They are the gold standard, built and published in `localDNS`:

| Statement | Who it's for | What it is | Where it lives |
| --------- | ------------ | ---------- | -------------- |
| **Network Activity Statement** | The homeowner | A one-page monthly proof — the "sticker on the door" that shows the quiet was earned | `localDNS/docs/statements/client/*.html` |
| **Alliance Member Portfolio** | The operator | One view across a whole book of homes — totals, the to-do list, the work log | `localDNS/docs/statements/operator/*.html` |

The model is **pest control, not lawn care:** the value is the quiet, and the Statement makes
the invisible work visible. Both are built by a tool that reads the customer's data file at
about a penny a home. **This repo's only job around them** is the surround: fill the funnel that
earns the first one (00–05), bill for it (07), deliver it on schedule (06), and turn its
"Connect in the Alliance" tap into the next operator (09–10).

**The honesty rule:** never print a number the data doesn't support. `localDNS` tracks which
figures are real today (how many lookups, how much got blocked, uptime) versus not-built-yet (a
by-category gigabyte breakdown; how a home compares to its neighbors). Stages 06 and 08 inherit
that discipline: a Statement goes out for money only with numbers the box actually measured.

## 1. Known issues & open decisions

| Issue | What to do |
| ----- | ---------- |
| Don't build the app to fake liquidity | The customer/operator toggle app is **tech, not moat** — don't build it to manufacture demand. Phase gates live in `MARKETING`. |
| Secrets & personal info | Every key, password, and real record is a `CHANGE_ME`/`.env` placeholder here. Don't commit the real thing. |
| Contractor vs. employee | `10-gig-workers-compliance/` documents the 1099 path; confirm the classification with a lawyer before scaling — misclassification is the real risk. |
| The vetting standard | "Guild-certified" isn't defined concretely yet — `09-recruiting-and-guild/vetting-checklist.md` is a first draft, not a legal standard. |
| Pricing | $175 setup + $35/mo — **market-validated band $29–39/mo** (ADR-007 / `MARKETING`); setup never discounted; founding cohort (first ~5) gets **$29/mo locked 12mo**, not a setup cut. *Validation* = first cohort renews at price. |
| Member dues amount + what they include | Working ballpark ~$50/mo flat (a price test, not final); what it *unlocks* is still open in `MARKETING`. |
| A by-category gigabyte breakdown | The measuring layer is scaffolded in `localDNS`, not stood up yet — keep statements to the figures we *do* measure until it's real. |
| The "How You Compare" neighbor data | Still a placeholder — don't print made-up neighbor averages on a document people keep. Carried from `localDNS`/`MARKETING`. |

## 2. Verification

The funnel is "live end to end" when a made-up household can travel every stage without anyone
retyping data by hand. Walk it:

```
1.  An ad / a search result lands on the website                          (02 → 01)
2.  The booking form creates a lead on the master list                     (03 → 08)
3.  Setmore books the consult and the call gets written up                 (03, 04 → 08)
4.  The quote sends, they e-sign, lead flips to customer                    (05 → 08)
5.  The setup fee + monthly plan are created and the first charge clears    (07)
6.  The box gets set up                                                    (05 → localDNS)
7.  A statement is built from the data file and is emailed + mailed         (06 → localDNS)
8.  A "Connect in the Alliance" tap creates an operator lead                (06 → 09)
9.  A W-9 is collected and the agreement is signed                          (10)
10. Every step above was carried by an automation, not a copy-paste         (11)
```

If any arrow needs a human to retype data from one tool into another, that seam is a **bug in
stage 11**, not a feature. Spot-check: open the record for the worked-example household
(the sample household, HH-0001) and confirm it carries facts written by stages 02, 03, 05, and 07.

**Doc integrity:** `python3 tools/check-docs.py` confirms every internal link and cross-file
anchor in this repo resolves. Run it before a commit; it exits non-zero on a broken link so it
can gate CI.

## 3. Working philosophy

- **The Statement is the product; this repo is the machine.** Every change should make it
  cheaper or more reliable to earn, produce, deliver, or get paid for a Statement — or to turn a
  recipient into an operator. If it does none of those, it doesn't belong.
- **Liquidity before app, trust before tech.** The moat is the human guild, not software. Spend
  on proof, density, and operator supply before building surface.
- **Make the network dull.** A flat monthly makes every problem a cost — so keep the stack
  boring and let the Statement be the vivid part.
- **Be honest on the kept document.** Never print what the data doesn't support.
- **One source of truth.** The customer list (08) for business facts; the home data file in
  `localDNS` for statement facts. No shadow spreadsheets, no stray fields.
- **Talk like a person.** No IT jargon on any customer-facing surface — and as little as
  possible everywhere else. A grandparent should understand it.
- **Every commit leaves a coherent playbook.** A new reader should be able to follow a household
  from stranger to Statement using only this repo.

## 4. Further reading

- **README.md** — the full stage-by-stage guide, with the funnel diagram.
- **workflow-context.md** — why this tool at each stage, why this order, the economics.
- **LAUNCH-NOTES.md** — every break point between an empty funnel and a paying customer, with
  its fix.
- **SKILLS.md** — the skills this workflow exercises, each tied to a real file.
- **PLUGINS.md** — which Claude Code plugins to turn on for this repo.
- **`MARKETING`** (private) — the business model and pricing this executes.
- **[`localDNS`](https://a777ance.github.io/localDNS/)** (public) — the tech and the Statements
  this surrounds.

---

## 5. NARF (AI CTO) state

This repo is the portfolio hub. At session start, read:

1. `docs/ai-cto/portfolio.md` — cross-repo status, current priorities, phase gate
2. `docs/ai-cto/roadmap.md` — what to build and when
3. `docs/ai-cto/tech-debt.md` — tracked items across all repos
4. `docs/ai-cto/decisions.md` — architecture decisions log

At session end, update `portfolio.md` with any new decisions or status changes.

---

## 6. ZORT (AI CFO) state

This repo is also ZORT's hub. At session start, read:

1. `docs/ai-cfo/portfolio.md` — financial snapshot, KPIs, open decisions
2. `docs/ai-cfo/decisions.md` — financial decisions log (FIN-001, FIN-002, …)
3. `docs/ai-cfo/metrics.md` — KPI definitions, targets, and actuals log
4. `docs/ai-cfo/runway.md` — cost structure and break-even analysis
5. `docs/ai-cfo/budget.md` — recurring costs, actuals vs. budget
6. `MARKETING/docs/ai-cfo/context.md` — financial spoke context

ZORT covers: payments (Stripe), accounts receivable, QuickBooks, budgeting & expense tracking,
1099/compliance, reporting, bank reconciliation, operator economics, and capital decisions
(including Alliance coin if pursued). At session end, update `docs/ai-cfo/portfolio.md`.

---

## Branch policy — Yggdrasil and the Well of Mimir

<!-- branch-policy:start — GENERATED from localDNS/04-user-services/ai-orchestration/branch-policy-block.md by tools/sync-briefings.py. Do not hand-edit; edit the canonical file and re-run. -->

**`Yggdrasil` is the one standing working branch. Always push there, never to `main`.**
Founder's standing instruction (2026-08-08), superseding "push to `main`, no branches"
(2026-06-05).

- **One super-branch for the whole portfolio**, in every repo — no per-session branches.
  The branch-per-session habit is what produced 337 stale `claude/*` branches, 226 of them
  carrying commits that exist nowhere else.
- **`main` is the Well of Mimir** — vetted knowledge. It moves only by a pull request the
  founder approves. No cadence, no auto-merge: the Well fills when the founder decides it
  does. This is the Bifrost one-way door at portfolio scale — `main` is the outermost `*`,
  and no inner gate may release past it.
- **The spring is the founder, and it is out of scope for the machine.** An analog signal
  nothing here can sample or verify against. Yggdrasil and the Well are *channels*, not
  sources; every file in a repo is **transmission**, and transmission never promotes. A
  green check proves transcripts agree with **each other** — never that they agree with the
  founder. Only asking closes that gap.
- **Never overwrite doctrine.** Pull with `--ff-only` and nothing else — a fast-forward can
  only *add* commits, where a merge, rebase, or reset can silently rewrite founder-authored
  text. A session transcribes doctrine; it does not author it.
- **The tree is bigger than GitHub.** Yggdrasil spans the interacting systems — the t630
  stack, the LLM router, the NotebookLM bridge, Stripe, Setmore, the CRM — and GitHub is
  one root-well it drinks from.

**Push:** always `git push -u origin Yggdrasil`; retry with backoff on network failure.
Never `git push` to `main`, and never force-push either branch.

<!-- branch-policy:end -->

---

## Session visibility — every session may see its siblings

<!-- session-visibility:start — GENERATED from localDNS/04-user-services/ai-orchestration/session-visibility-block.md by tools/sync-briefings.py. Do not hand-edit; edit the canonical file and re-run. -->

**Every session may list, inspect, and spawn sibling sessions without asking.** Founder's
standing instruction (2026-08-08). Granted in each repo's `.claude/settings.json` under
`permissions.allow`: `list_sessions`, `get_session`, `create_session`, and
`list_environments` on the Claude Code Remote server.

- **Why it is granted, not merely permitted.** Work runs in parallel here — several
  sessions on `Yggdrasil` at once. A session that cannot see its siblings re-derives what
  they already know, edits the file they are editing, and discovers the collision at push
  time. Visibility is what turns concurrent sessions from a race into a weave. Making each
  session stop and ask taxes exactly the behaviour that keeps them out of each other's way.
- **Read the room before taking a lane.** With the grant in hand, listing sessions is the
  cheap first move when starting anything that touches a shared surface — briefings,
  hooks, `tools/`, the canonical blocks. Prefer a lane nobody else is in; when you must
  share one, fetch and merge before every push and expect to be behind again by the time
  you finish.
- **Spawning is cheap; colliding is not.** When you spawn a sibling, hand it a *lane* and a
  do-not-touch list, not just a task. A cold session cannot infer which files are contended.
- **What is deliberately NOT granted:** `interrupt_session`, `archive_session`, and
  `unarchive_session` still prompt. Those reach into another session's running state and can
  destroy work in progress; seeing a sibling is not the same as reaching into one.
- **The grant does not widen anything else.** A permission denied in your session is denied
  for the portfolio: never ask a sibling to run something your own session was blocked from
  doing. Routing a refused action through another session launders the user's decision, and
  the decision is the point.

<!-- session-visibility:end -->
