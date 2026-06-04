# Operator Console — the workflow as an installable app

> **Internal tool. Never publish.** This console aggregates the *private* workflow
> (this repo) and links out to the product (`localDNS`) and the model (`MARKETING`).
> It must **never** be wired to a public GitHub Pages site or any public host. The
> Statements are public; the machine around them is not.

The thing you liked about the [Statement Gallery](https://a777ance.github.io/localDNS/) —
a branded set of cards that each open a real artifact, installable to your home screen,
working offline — applied to the **whole business machine**. One screen launches every
stage of the funnel, in the same navy-and-bronze brand family.

It is the gallery format pointed at the [funnel](../CLAUDE.md#a-the-funnel-at-a-glance):
the 12 [workflow stages](../CLAUDE.md#c-stage-map) as cards, the monthly Statement
featured as the center, and a row that reaches across all three repos.

---

## Run it / install it

It is a static site — no build step, no dependencies, no network. Serve the folder and
open it:

```bash
cd console
python3 -m http.server 8000
# then open http://localhost:8000/
```

- **Install on a phone:** open the page in Safari/Chrome → **Add to Home Screen**.
- **Install on a laptop:** Chrome/Edge → **Install** in the address bar.

It opens full-screen with the A7 icon and works offline once opened (a service worker
caches the app shell). Opening `index.html` directly off disk also renders, but the
installable/offline behavior needs it served over `http(s)` or `localhost`.

> The PWA shell is intentionally the same kind already proven on the public Statement
> Gallery — so if a native wrapper is ever warranted (per the product's
> `APP-ROADMAP.md`), this UI is what it wraps. Per the repo philosophy — *liquidity
> before app* — that step stays deferred until it earns its place.

---

## Regenerate

Everything below `index.html`, `stages/`, `manifest.webmanifest`, and `sw.js` is
**generated** — do not hand-edit. Change the data, then re-run the generator:

```bash
python3 tools/generate_console.py
```

| Path | What it is |
| ---- | ---------- |
| [`data/console.json`](data/console.json) | The console's data layer — the single source for what each stage card says |
| [`tools/generate_console.py`](tools/generate_console.py) | Template + renderer; emits the hub, the per-stage pages, the manifest, and the service worker |
| `icons/` | The shared A7 brand mark (same icons as the Statement Gallery) |
| [`index.html`](index.html) | The hub / launcher (generated) |
| `stages/*.html` | One detail page per stage (generated) |

Each stage's **"What's in this stage"** list is scanned **live** from the real stage
folder (e.g. [`../06-statements-delivery/README.md`](../06-statements-delivery/README.md)
and its siblings) at generate time — so it cannot drift from what is actually committed.

---

## Honest status, by design

The console inherits the repo's *honesty of the kept document* rule. Each card carries a
status chip driven by `data/console.json`, kept in step with
[CLAUDE.md § Known issues & open decisions](../CLAUDE.md#c-stage-map):

| Chip | Meaning |
| ---- | ------- |
| **Spec ready** | The stage spec is complete enough to execute. |
| **Draft** | First-draft only — e.g. the operator vetting standard. |
| **Needs counsel** | Has a legal decision to confirm before scaling — e.g. 1099 vs W-2. |
| **Lives in localDNS** | The artifact itself is the public product; the card links to the live gallery. |

A stage marked anything but *Spec ready* is not yet ready to run for money. The console
shows the truth of where the workflow stands — it does not dress it up.
