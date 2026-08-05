# The design system — where the look actually lives

**Lives in:** `localDNS/design-system/` (public) → mirrored to a **Claude Design** project
(claude.ai/design).
**Go-live:** `python3 design-system/build.py` in `localDNS`, then `/design-sync` from a
terminal session. The Design project is a mirror; the repo is the source.

This page is the internal half of a public thing. The system itself is public because it is
extracted from the Statements, which are public. What is internal is **which surfaces have
to inherit it, and what may never travel with it.**

---

## The split

| | Public — `localDNS/design-system/` | Internal — here |
| --- | --- | --- |
| Tokens (`tokens.css`, `tokens.json`) | ✅ the source of truth for the look | pointer only, below |
| Components (Statement + Portfolio previews) | ✅ with `Sample …` / `A77-000` placeholders | — |
| Working rules (`CONVENTIONS.md`) | ✅ | — |
| Which stages inherit the look | — | ✅ this file + [`README.md`](README.md) |
| Logo binaries, Figma master | — | ✅ asset folder, linked from [`brand-kit.md`](brand-kit.md) |
| Pricing on any surface | ❌ never | `MARKETING` |
| Real households, operators, QR codes | ❌ never | `customers` (private) |

**Why the system is public and the brand kit is internal.** The tokens describe documents a
customer already holds in their hands — there is nothing to protect in a hex value that is
printed on every Statement. The *asset* files, the Figma master, and the list of surfaces we
are about to launch on are business facts. Keep the two apart and the question "can this go
in the Design project?" has an easy answer.

---

## What's in it

| Group | Cards |
| ----- | ----- |
| **Foundations** | Color · Type · Layout & rhythm |
| **Statement** (client) | Statement header · Account summary · Handled For You · Traffic allocation · Household profile · How You Compare · Our read this month · Connect in the Alliance · See for yourself · Service status & privacy · Statement footer |
| **Portfolio** (operator) | KPI band · Needs your attention · Work log · Homes roster |

Two carry a warning **inside the card** and must not appear on a Statement sold for money:
**How You Compare** (no real cohort dataset — see [CLAUDE.md § 1](../CLAUDE.md#1-known-issues--open-decisions))
and **Traffic allocation** (the by-category gigabyte breakdown; the measuring layer is
scaffolded in `localDNS`, not stood up). They exist so the *form* is settled and reviewable.

---

## Which stages inherit it

The look is settled once and every surface points back at it — that rule from
[`README.md`](README.md) now has a concrete target:

| Stage | Inherits |
| ----- | -------- |
| `06-statements-delivery/` | Everything. The Statement **is** the design system's home document. |
| `03-funnels-and-capture/` | Type, color, section rhythm on the landing page and booking form |
| `02-demand-generation/` | Type and color in ads, postcards, and email |
| `01-web-presence/` | Type, color, and the statement gallery embed |
| `00-brand-identity/` | The color table in [`brand-kit.md`](brand-kit.md) is *derived from* the tokens, not decided separately |

A postcard that picks its own blue is the failure this prevents. If a surface needs a value,
it takes it from `tokens.css` — it does not invent one and it does not eyeball one off a
screenshot.

---

## Working on it

Read `localDNS/design-system/CONVENTIONS.md` first — that is the briefing for design work,
and it carries the same rules this repo runs on (house style, honesty on the kept document,
plain-English naming, the public/private invariant, Bifrost, git). The procedure is
`/design-sync`, which runs a compliance gate **before** anything uploads.

**One limitation worth knowing before you plan around it:** `DesignSync` needs an
authorization that `/design-login` can only grant from an interactive terminal, so a Claude
Code *web* session cannot push to the Design project. Build and review from anywhere; push
from a terminal.

**And one honest gap:** the generated Statements inline their own CSS per household, so they
do **not** yet consume `tokens.css`. Today the tokens are a faithful copy, not a shared
dependency — changing a token does not change a customer's document until the generator is
taught to read from `design-system/tokens/`. Until then, a change to the look is two edits,
and the Statement is the one that counts.
