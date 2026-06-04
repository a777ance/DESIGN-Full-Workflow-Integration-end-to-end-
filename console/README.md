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

## Run & install it — step by step

Two ways to use it. Pick one.

### A) Just look at it — no tools, 5 seconds

Find `console/index.html` in the files and **double-click it**. It opens in your browser
and every card works. That's it.

> Looking is enough to explore it. *Installing* it as an app (home-screen icon, works
> offline) needs path B below — browsers only allow that over a real web address, not a
> double-clicked file.

### B) Install it as a real app — offline, on your home screen

You need **Python 3** — already on every Mac and Linux machine; on Windows, get it from
[python.org](https://www.python.org/downloads/) and tick *“Add Python to PATH”* during
setup. Then, from the repo folder, run **one command**:

```bash
python3 console/serve.py
```

Your browser opens to `http://localhost:8000/` on its own. Keep that terminal window open
while you use the app; press **Ctrl+C** to stop. (If port 8000 is busy, the launcher hops
to the next free port and prints the new address.)

<details><summary>Prefer to do it by hand, without the launcher?</summary>

```bash
cd console
python3 -m http.server 8000
```

…then open `http://localhost:8000/` in your browser yourself.
</details>

**Then install it from that open page:**

| Device | How to install |
| ------ | -------------- |
| iPhone / iPad (Safari) | **Share** button → **Add to Home Screen** |
| Android (Chrome) | **⋮** menu → **Add to Home screen** / **Install app** |
| Mac / Windows (Chrome or Edge) | the **Install** icon in the address bar (a small screen with a ▾), or **⋮** menu → **Install A7 Console…** |

Once installed it opens full-screen with the A7 icon and keeps working with no internet —
a service worker caches the app shell.

### First time — getting the files onto your computer

This is a private repo, so first either:

- **Clone it:** `git clone <repo-url>`, then `cd` into the folder; or
- **Download it:** on GitHub, **Code ▾ → Download ZIP**, then unzip.

Then follow A or B above.

### If something’s off

- **`command not found: python3`** — install Python 3 (link above). On Windows, try
  `python console\serve.py` if `python3` isn’t recognized.
- **`Address already in use`** — `serve.py` auto-hops to the next free port and prints the
  new URL; with the by-hand command, just change `8000` to `8001`.
- **No Install button on a laptop** — use **Chrome** or **Edge** (desktop Safari doesn’t
  show one). Make sure the address bar reads `http://localhost…`, not a `file://` path.

> The PWA shell is intentionally the same kind already proven on the public Statement
> Gallery — so if a native wrapper is ever warranted (per the product’s `APP-ROADMAP.md`),
> this UI is what it wraps. Per the repo philosophy — *liquidity before app* — that step
> stays deferred until it earns its place.

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
| [`serve.py`](serve.py) | One-command launcher — serves the folder and opens your browser (path B above) |
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
