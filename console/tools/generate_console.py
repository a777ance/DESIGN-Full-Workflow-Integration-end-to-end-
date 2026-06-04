#!/usr/bin/env python3
"""Render the A777ance Operator Console — an installable PWA hub over the whole
workflow — from data/console.json.

The business analog of localDNS's docs/statements generator: data in, self-
contained HTML out. The template never holds content; console.json is the single
source for the console's presentation, and each stage's file list is scanned live
from its real folder so "what's in this stage" can never drift from the repo.

Outputs (all generated — do not hand-edit):
    index.html              the hub / launcher (the gallery home screen)
    stages/<slug>.html      one detail page per workflow stage
    manifest.webmanifest    PWA manifest
    sw.js                   service worker (offline app shell)

No third-party dependencies — pure standard library, so it runs anywhere and is
easy to debug at 11pm. Icons live in icons/ (the shared A7 brand mark).

INTERNAL ONLY. This console aggregates the private workflow; it must never be
wired to a public GitHub Pages site. See console/README.md.

Usage:
    python3 tools/generate_console.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONSOLE = os.path.dirname(HERE)              # .../console
ROOT = os.path.dirname(CONSOLE)              # repo root
DATA = os.path.join(CONSOLE, "data", "console.json")

CACHE_VERSION = "v1"

# status key -> (chip label, css class)
STATUS = {
    "spec":     ("Spec ready", "ok"),
    "draft":    ("Draft", "watch"),
    "counsel":  ("Needs counsel", "warn"),
    "external": ("Lives in localDNS", "ext"),
}

ICONS = [
    "icons/icon.svg",
    "icons/icon-192.png",
    "icons/icon-512.png",
    "icons/icon-512-maskable.png",
    "icons/apple-touch-icon.png",
]

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0;}
:root{--navy:#13314f;--navy-2:#0e2640;--ink:#1f2733;--bronze:#a9803f;--bronze-soft:#c6a463;
--paper:#fbfaf7;--rule:#e6e2d6;--muted:#8a93a0;--good:#3f7d52;--good-soft:#e6efe8;
--watch:#8a5e16;--watch-soft:#f5ecd9;--warn:#9c4221;--warn-soft:#f6e7df;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
background:#e9ecf0;color:var(--ink);padding:0 0 64px;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1020px;margin:0 auto;padding:0 24px;}
a{color:var(--bronze);}
/* header */
.header{background:var(--navy);color:#fff;border-bottom:3px solid var(--bronze);}
.header .wrap{padding:28px 24px 24px;display:flex;align-items:center;gap:15px;}
.monogram{width:46px;height:46px;border-radius:10px;background:linear-gradient(150deg,#1c4a73,var(--navy-2));
border:1px solid var(--bronze);display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.monogram span{font-family:Georgia,serif;font-size:20px;font-weight:700;color:var(--bronze-soft);}
.brand{font-size:21px;font-weight:700;letter-spacing:0.16em;}
.brand-sub{font-size:9px;color:#8fb0cc;letter-spacing:0.2em;text-transform:uppercase;margin-top:5px;}
.badge{margin-left:auto;font-size:9.5px;letter-spacing:0.16em;text-transform:uppercase;color:var(--bronze-soft);
border:1px solid rgba(201,164,99,0.5);border-radius:999px;padding:5px 11px;white-space:nowrap;}
/* lead */
.lead{max-width:780px;margin:34px auto 0;padding:0 24px;}
.lead h1{font-family:Georgia,serif;font-size:27px;color:var(--navy);font-weight:700;}
.lead p{font-size:14px;color:#3a4553;line-height:1.65;margin-top:11px;}
.lead .note{margin-top:15px;font-size:12px;color:#5a5446;background:#f2efe7;border-left:3px solid var(--bronze);
padding:11px 14px;border-radius:0 6px 6px 0;}
.lead .install{margin-top:12px;font-size:12px;color:#3a4553;line-height:1.55;}
.lead .install b{color:var(--navy);}
/* featured product banner */
.feature{display:block;max-width:972px;margin:30px auto 0;border-radius:14px;overflow:hidden;
background:linear-gradient(135deg,#1b456b,var(--navy-2));border:1px solid var(--bronze);
box-shadow:0 10px 30px rgba(14,38,64,0.28);text-decoration:none;color:#fff;}
.feature .inner{padding:24px 26px;display:flex;gap:20px;align-items:center;}
.feature .mark{font-family:Georgia,serif;font-size:23px;font-weight:700;color:var(--navy-2);
background:var(--bronze-soft);width:54px;height:54px;border-radius:12px;display:flex;align-items:center;
justify-content:center;flex-shrink:0;}
.feature .kicker{font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:var(--bronze-soft);}
.feature h2{font-family:Georgia,serif;font-size:21px;margin-top:5px;}
.feature p{font-size:12.5px;color:#cfe0ef;line-height:1.55;margin-top:7px;max-width:600px;}
.feature .go{margin-left:auto;font-size:13px;color:var(--bronze-soft);font-weight:700;white-space:nowrap;align-self:center;}
/* sections */
.sect{margin-top:40px;}
.sect-h{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid var(--rule);
padding-bottom:10px;margin-bottom:20px;flex-wrap:wrap;}
.sect-h h2{font-size:13px;text-transform:uppercase;letter-spacing:0.16em;color:var(--navy);}
.sect-h span{font-size:11.5px;color:var(--muted);font-style:italic;}
/* grid + stage cards */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:12px;
box-shadow:0 4px 16px rgba(0,0,0,0.06);transition:transform .12s,box-shadow .12s;
text-decoration:none;color:inherit;display:flex;flex-direction:column;overflow:hidden;}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,0.12);}
.card .top{display:flex;align-items:center;gap:11px;padding:15px 16px 0;}
.num{font-family:Georgia,serif;font-size:14px;font-weight:700;color:#fff;background:var(--navy);
width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.card .t{font-size:14.5px;font-weight:700;color:var(--navy);line-height:1.25;}
.card .body{padding:10px 16px 15px;display:flex;flex-direction:column;flex:1;}
.card .tool{font-size:10.5px;color:var(--bronze);font-weight:600;letter-spacing:0.02em;line-height:1.4;}
.card .d{font-size:12.5px;color:#5a6573;line-height:1.5;margin-top:7px;flex:1;}
.card .cfoot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:13px;}
.open{font-size:12px;color:var(--bronze);font-weight:600;white-space:nowrap;}
/* chips */
.chip{font-size:9px;letter-spacing:0.07em;text-transform:uppercase;font-weight:700;border-radius:999px;
padding:3px 8px;white-space:nowrap;}
.chip.ok{color:var(--good);background:var(--good-soft);}
.chip.watch{color:var(--watch);background:var(--watch-soft);}
.chip.warn{color:var(--warn);background:var(--warn-soft);}
.chip.ext{color:var(--navy);background:#e7eef5;}
/* cross-repo cards */
.repo-card{background:#fff;border:1px solid var(--rule);border-radius:12px;padding:17px 18px 15px;
text-decoration:none;color:inherit;display:flex;flex-direction:column;
transition:transform .12s,box-shadow .12s;box-shadow:0 4px 16px rgba(0,0,0,0.05);}
.repo-card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,0.12);}
.repo-card .rh{display:flex;align-items:center;gap:9px;}
.repo-card .rt{font-size:15px;font-weight:700;color:var(--navy);}
.vis{font-size:8.5px;letter-spacing:0.1em;text-transform:uppercase;font-weight:700;padding:3px 8px;border-radius:999px;margin-left:auto;}
.vis.public{color:var(--good);background:var(--good-soft);}
.vis.private{color:var(--warn);background:var(--warn-soft);}
.repo-card .src{font-size:11px;color:var(--muted);margin-top:4px;font-family:ui-monospace,Menlo,monospace;}
.repo-card .d{font-size:12.5px;color:#5a6573;line-height:1.55;margin-top:9px;flex:1;}
.repo-card .cta{margin-top:12px;font-size:12px;color:var(--bronze);font-weight:700;}
/* footer */
.foot{margin-top:48px;padding-top:20px;border-top:1px solid var(--rule);font-size:11.5px;color:var(--muted);line-height:1.65;}
.foot a{color:var(--bronze);text-decoration:none;}
/* ===== stage detail page ===== */
.crumb{max-width:840px;margin:20px auto 0;padding:0 24px;font-size:12px;color:var(--muted);}
.crumb a{text-decoration:none;}
.stage{max-width:840px;margin:0 auto;padding:0 24px;}
.stage-head{display:flex;align-items:flex-start;gap:16px;margin-top:14px;}
.num-lg{font-family:Georgia,serif;font-size:22px;font-weight:700;color:#fff;background:var(--navy);
width:52px;height:52px;border-radius:11px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.stage-head .kicker{font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--bronze);font-weight:700;}
.stage-head h1{font-family:Georgia,serif;font-size:26px;color:var(--navy);margin-top:4px;}
.stage-head .tagline{font-size:13.5px;color:#5a6573;margin-top:6px;line-height:1.5;}
.stage-head .chip{margin-left:auto;margin-top:4px;align-self:flex-start;}
.meta{margin-top:22px;border:1px solid var(--rule);border-radius:10px;background:#fff;overflow:hidden;}
.meta-row{display:flex;gap:14px;padding:11px 15px;border-bottom:1px solid var(--rule);font-size:13px;}
.meta-row:last-child{border-bottom:0;}
.meta-row .k{flex:0 0 84px;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;font-size:10px;padding-top:2px;}
.meta-row .v{color:var(--ink);line-height:1.45;}
.summary{font-size:14.5px;color:#33404e;line-height:1.7;margin-top:22px;}
.callout{margin-top:16px;font-size:12.5px;color:#5a5446;background:#f2efe7;border-left:3px solid var(--bronze);
padding:11px 14px;border-radius:0 6px 6px 0;line-height:1.55;}
.gallery-btn{display:flex;align-items:center;gap:14px;margin-top:20px;background:linear-gradient(135deg,#1b456b,var(--navy-2));
border:1px solid var(--bronze);border-radius:12px;padding:18px 20px;text-decoration:none;color:#fff;}
.gallery-btn .gt{font-family:Georgia,serif;font-size:16px;}
.gallery-btn .gd{font-size:12px;color:#cfe0ef;margin-top:3px;}
.gallery-btn .ga{margin-left:auto;color:var(--bronze-soft);font-weight:700;white-space:nowrap;}
.files{margin-top:30px;}
.files h3{font-size:12px;text-transform:uppercase;letter-spacing:0.14em;color:var(--navy);
border-bottom:1px solid var(--rule);padding-bottom:9px;}
.files ul{list-style:none;margin-top:6px;}
.files li{display:flex;align-items:center;gap:12px;padding:10px 2px;border-bottom:1px solid #efece3;}
.files li a{font-size:13.5px;font-weight:600;text-decoration:none;color:var(--navy);font-family:ui-monospace,Menlo,monospace;}
.files li .kind{margin-left:auto;font-size:9.5px;letter-spacing:0.06em;text-transform:uppercase;
color:var(--muted);background:#eef0f3;border-radius:999px;padding:3px 9px;}
.spec-link{display:inline-block;margin-top:14px;font-size:13px;font-weight:700;color:var(--bronze);text-decoration:none;}
.prevnext{display:flex;justify-content:space-between;gap:12px;margin-top:34px;}
.prevnext a{flex:1;border:1px solid var(--rule);border-radius:10px;padding:12px 15px;text-decoration:none;
background:#fff;color:var(--navy);font-size:13px;font-weight:600;}
.prevnext a.next{text-align:right;}
.prevnext a .pn{display:block;font-size:9.5px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-bottom:3px;}
.prevnext .spacer{flex:1;}
@media (max-width:760px){.grid{grid-template-columns:1fr;}.feature .inner{flex-direction:column;align-items:flex-start;}
.feature .go{margin-left:0;margin-top:6px;}.stage-head .chip{margin-left:0;}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def file_kind(name):
    n = name.lower()
    if n == "readme.md":
        return "Spec"
    if "schema" in n:
        return "Schema"
    if "checklist" in n:
        return "Checklist"
    if "template" in n:
        return "Template"
    if "agreement" in n:
        return "Agreement"
    if n.startswith("data/") or n.endswith((".json", ".csv")):
        return "Sample data"
    if n.endswith(".md"):
        return "Doc"
    return "File"


def scan_stage(folder):
    """List the real files in a stage folder (one level into data/), so the
    'what's in this stage' section reflects the repo, not a hand-kept list."""
    base = os.path.join(ROOT, folder)
    items = []
    if not os.path.isdir(base):
        return items
    for entry in sorted(os.listdir(base)):
        full = os.path.join(base, entry)
        if os.path.isdir(full):
            if entry == "data":
                for sub in sorted(os.listdir(full)):
                    if os.path.isfile(os.path.join(full, sub)):
                        rel = "data/" + sub
                        items.append({"href": "../../%s/%s" % (folder, rel),
                                      "name": rel, "kind": file_kind(rel)})
            continue
        items.append({"href": "../../%s/%s" % (folder, entry),
                      "name": entry, "kind": file_kind(entry)})
    items.sort(key=lambda x: (x["name"].lower() != "readme.md", x["name"].lower()))
    return items


def head(title, up):
    """<head> + brand metas + manifest + inline CSS. `up` is "" for the hub at
    console root, "../" for pages under stages/."""
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "<title>%s</title>\n"
        "<link rel=\"manifest\" href=\"%smanifest.webmanifest\">\n"
        "<meta name=\"theme-color\" content=\"#13314f\">\n"
        "<meta name=\"apple-mobile-web-app-capable\" content=\"yes\">\n"
        "<meta name=\"mobile-web-app-capable\" content=\"yes\">\n"
        "<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"black-translucent\">\n"
        "<meta name=\"apple-mobile-web-app-title\" content=\"A7 Console\">\n"
        "<link rel=\"apple-touch-icon\" href=\"%sicons/apple-touch-icon.png\">\n"
        "<link rel=\"icon\" type=\"image/svg+xml\" href=\"%sicons/icon.svg\">\n"
        "<style>%s</style>\n</head>\n<body>\n"
        % (esc(title), up, up, up, CSS)
    )


def header_bar():
    return (
        "  <div class=\"header\"><div class=\"wrap\">\n"
        "    <div class=\"monogram\"><span>A7</span></div>\n"
        "    <div><div class=\"brand\">A777ANCE</div>"
        "<div class=\"brand-sub\">Residential Network Services</div></div>\n"
        "    <div class=\"badge\">Internal · Operator Console</div>\n"
        "  </div></div>\n"
    )


def sw_script(up):
    return (
        "  <script>\n"
        "    if ('serviceWorker' in navigator) {\n"
        "      window.addEventListener('load', function () {\n"
        "        navigator.serviceWorker.register('%ssw.js').catch(function () {});\n"
        "      });\n"
        "    }\n"
        "  </script>\n" % up
    )


def chip_html(stage):
    label, cls = STATUS.get(stage.get("status", "spec"), STATUS["spec"])
    return "<span class=\"chip %s\">%s</span>" % (cls, esc(label))


def stage_card(stage):
    return (
        "        <a class=\"card\" href=\"stages/%s.html\">\n"
        "          <div class=\"top\"><div class=\"num\">%s</div><div class=\"t\">%s</div></div>\n"
        "          <div class=\"body\">\n"
        "            <div class=\"tool\">%s</div>\n"
        "            <div class=\"d\">%s</div>\n"
        "            <div class=\"cfoot\">%s<span class=\"open\">Open &rarr;</span></div>\n"
        "          </div>\n"
        "        </a>\n"
        % (esc(stage["slug"]), esc(stage["num"]), esc(stage["title"]),
           esc(stage["tool"]), esc(stage["tagline"]), chip_html(stage))
    )


def render_index(d):
    stages = d["stages"]
    by_phase = {}
    for s in stages:
        by_phase.setdefault(s["phase"], []).append(s)
    featured = next((s for s in stages if s.get("featured")), None)

    out = [head("A777ance — Operator Console", "")]
    out.append(header_bar())

    # lead
    out.append("  <div class=\"lead\">\n")
    out.append("    <h1>Operator Console</h1>\n")
    out.append("    <p>%s</p>\n" % esc(d["lead"]))
    out.append("    <div class=\"note\"><strong>Internal tool.</strong> This console aggregates the "
               "private workflow — it is never wired to a public site. The product it surrounds (the "
               "Statements) is public; the model behind it (pricing, guild mechanics) is private. "
               "Status chips stay honest: a stage marked <em>Draft</em> or <em>Needs counsel</em> is "
               "not yet ready to run for money.</div>\n")
    out.append("    <p class=\"install\"><b>Tip —</b> install this like an app: on a phone, open this "
               "page and choose <b>Add to Home Screen</b>; on a laptop (Chrome/Edge), click "
               "<b>Install</b> in the address bar. It opens full-screen and works offline.</p>\n")
    out.append("  </div>\n")

    # featured product banner
    if featured:
        out.append(
            "  <a class=\"feature\" href=\"stages/%s.html\">\n"
            "    <div class=\"inner\">\n"
            "      <div class=\"mark\">%s</div>\n"
            "      <div>\n"
            "        <div class=\"kicker\">The product · every month</div>\n"
            "        <h2>%s</h2>\n"
            "        <p>%s</p>\n"
            "      </div>\n"
            "      <span class=\"go\">Open stage &rarr;</span>\n"
            "    </div>\n"
            "  </a>\n"
            % (esc(featured["slug"]), esc(featured["num"]), esc(featured["title"]),
               esc(featured["tagline"]))
        )

    out.append("  <div class=\"wrap\">\n")

    # one section per non-product phase, in declared order
    for phase in d["phases"]:
        if phase["id"] == "product":
            continue
        members = by_phase.get(phase["id"], [])
        if not members:
            continue
        out.append("    <div class=\"sect\">\n")
        out.append("      <div class=\"sect-h\"><h2>%s</h2><span>%s</span></div>\n"
                   % (esc(phase["label"]), esc(phase["blurb"])))
        out.append("      <div class=\"grid\">\n")
        for s in members:
            out.append(stage_card(s))
        out.append("      </div>\n    </div>\n")

    # cross-repo galleries / shortcuts
    out.append("    <div class=\"sect\">\n")
    out.append("      <div class=\"sect-h\"><h2>Across the three repos</h2>"
               "<span>one business — the product, the model, and the stack</span></div>\n")
    out.append("      <div class=\"grid\">\n")
    for r in d["crossrepo"]:
        vis = r.get("visibility", "private")
        out.append(
            "        <a class=\"repo-card\" href=\"%s\"%s>\n"
            "          <div class=\"rh\"><span class=\"rt\">%s</span>"
            "<span class=\"vis %s\">%s</span></div>\n"
            "          <div class=\"src\">%s</div>\n"
            "          <div class=\"d\">%s</div>\n"
            "          <div class=\"cta\">%s &rarr;</div>\n"
            "        </a>\n"
            % (esc(r["href"]),
               " target=\"_blank\" rel=\"noopener\"" if r["href"].startswith("http") else "",
               esc(r["title"]), esc(vis), esc(vis), esc(r["repo"]),
               esc(r["desc"]), esc(r.get("cta", "Open")))
        )
    out.append("      </div>\n    </div>\n")

    # footer
    out.append(
        "    <div class=\"foot\">\n"
        "      Generated by <a href=\"tools/generate_console.py\">tools/generate_console.py</a> "
        "from <a href=\"data/console.json\">data/console.json</a> — the console's data layer. "
        "Each stage's file list is scanned live from its folder. Installable PWA; works offline. "
        "&nbsp;·&nbsp; <strong>Internal — do not publish.</strong> &nbsp;·&nbsp; A777ANCE\n"
        "    </div>\n"
        "  </div>\n"
    )
    out.append(sw_script(""))
    out.append("</body>\n</html>\n")
    return "".join(out)


def render_stage(d, stage, prev_s, next_s):
    phase = next((p for p in d["phases"] if p["id"] == stage["phase"]), {"label": ""})
    out = [head("%s · %s — A7 Console" % (stage["num"], stage["title"]), "../")]
    out.append(header_bar())

    out.append("  <div class=\"crumb\"><a href=\"../index.html\">&larr; Operator Console</a> "
               "&nbsp;·&nbsp; %s</div>\n" % esc(phase["label"]))

    out.append("  <div class=\"stage\">\n")
    out.append(
        "    <div class=\"stage-head\">\n"
        "      <div class=\"num-lg\">%s</div>\n"
        "      <div>\n"
        "        <div class=\"kicker\">%s</div>\n"
        "        <h1>%s</h1>\n"
        "        <div class=\"tagline\">%s</div>\n"
        "      </div>\n"
        "      %s\n"
        "    </div>\n"
        % (esc(stage["num"]), esc(phase["label"]), esc(stage["title"]),
           esc(stage["tagline"]), chip_html(stage))
    )

    out.append(
        "    <div class=\"meta\">\n"
        "      <div class=\"meta-row\"><span class=\"k\">Lives in</span><span class=\"v\">%s</span></div>\n"
        "      <div class=\"meta-row\"><span class=\"k\">Go live</span><span class=\"v\">%s</span></div>\n"
        "    </div>\n"
        % (esc(stage["tool"]), esc(stage["golive"]))
    )

    out.append("    <p class=\"summary\">%s</p>\n" % esc(stage["summary"]))

    if stage.get("status_note"):
        out.append("    <div class=\"callout\">%s</div>\n" % esc(stage["status_note"]))

    # featured / external stage gets a prominent link to the live gallery
    if stage.get("status") == "external":
        gallery = next((r for r in d["crossrepo"] if r["title"] == "Statement Gallery"), None)
        if gallery:
            out.append(
                "    <a class=\"gallery-btn\" href=\"%s\" target=\"_blank\" rel=\"noopener\">\n"
                "      <div><div class=\"gt\">Open the Statement Gallery</div>"
                "<div class=\"gd\">The live client statements + operator portfolio — the product itself, in localDNS.</div></div>\n"
                "      <span class=\"ga\">localDNS &rarr;</span>\n"
                "    </a>\n" % esc(gallery["href"])
            )

    # what's in this stage (scanned live)
    files = scan_stage(stage["folder"])
    if files:
        out.append("    <div class=\"files\">\n      <h3>What's in this stage</h3>\n      <ul>\n")
        for f in files:
            out.append("        <li><a href=\"%s\">%s</a><span class=\"kind\">%s</span></li>\n"
                       % (esc(f["href"]), esc(f["name"]), esc(f["kind"])))
        out.append("      </ul>\n")
        out.append("      <a class=\"spec-link\" href=\"../../%s/README.md\">Open the full spec &rarr;</a>\n"
                   % esc(stage["folder"]))
        out.append("    </div>\n")

    # prev / next
    out.append("    <div class=\"prevnext\">\n")
    if prev_s:
        out.append("      <a class=\"prev\" href=\"%s.html\"><span class=\"pn\">&larr; Previous</span>%s %s</a>\n"
                   % (esc(prev_s["slug"]), esc(prev_s["num"]), esc(prev_s["title"])))
    else:
        out.append("      <span class=\"spacer\"></span>\n")
    if next_s:
        out.append("      <a class=\"next\" href=\"%s.html\"><span class=\"pn\">Next &rarr;</span>%s %s</a>\n"
                   % (esc(next_s["slug"]), esc(next_s["num"]), esc(next_s["title"])))
    else:
        out.append("      <span class=\"spacer\"></span>\n")
    out.append("    </div>\n")

    out.append(
        "    <div class=\"foot\">\n"
        "      Stage spec lives in <code>%s/</code> · generated by the Operator Console. "
        "&nbsp;·&nbsp; <strong>Internal — do not publish.</strong>\n"
        "    </div>\n"
        "  </div>\n" % esc(stage["folder"])
    )
    out.append(sw_script("../"))
    out.append("</body>\n</html>\n")
    return "".join(out)


def write_manifest(d):
    b = d["brand"]
    manifest = {
        "name": b["app_name"],
        "short_name": b["app_short"],
        "description": b["app_desc"],
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#13314f",
        "theme_color": "#13314f",
        "icons": [
            {"src": "icons/icon.svg", "type": "image/svg+xml", "sizes": "any", "purpose": "any"},
            {"src": "icons/icon-192.png", "type": "image/png", "sizes": "192x192", "purpose": "any"},
            {"src": "icons/icon-512.png", "type": "image/png", "sizes": "512x512", "purpose": "any"},
            {"src": "icons/icon-512-maskable.png", "type": "image/png", "sizes": "512x512", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(CONSOLE, "manifest.webmanifest"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")


def write_sw(stages):
    assets = ["./", "./index.html", "./manifest.webmanifest"]
    assets += ["./" + i for i in ICONS]
    assets += ["./stages/%s.html" % s["slug"] for s in stages]
    asset_lines = ",\n  ".join("'%s'" % a for a in assets)
    sw = (
        "/* A777ance Operator Console — service worker.\n"
        " * Makes the console installable (PWA) and openable offline on phone and laptop.\n"
        " * Cache-first for the known app shell; network with a cache fallback for the rest.\n"
        " * GENERATED by tools/generate_console.py — bump by regenerating, not by hand. */\n"
        "const CACHE = 'a777ance-console-%s';\n\n"
        "const ASSETS = [\n  %s\n];\n\n"
        "self.addEventListener('install', (event) => {\n"
        "  event.waitUntil(\n"
        "    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())\n"
        "  );\n});\n\n"
        "self.addEventListener('activate', (event) => {\n"
        "  event.waitUntil(\n"
        "    caches.keys()\n"
        "      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))\n"
        "      .then(() => self.clients.claim())\n"
        "  );\n});\n\n"
        "self.addEventListener('fetch', (event) => {\n"
        "  if (event.request.method !== 'GET') return;\n"
        "  event.respondWith(\n"
        "    caches.match(event.request).then((hit) => {\n"
        "      if (hit) return hit;\n"
        "      return fetch(event.request)\n"
        "        .then((resp) => {\n"
        "          const copy = resp.clone();\n"
        "          caches.open(CACHE).then((cache) => cache.put(event.request, copy));\n"
        "          return resp;\n"
        "        })\n"
        "        .catch(() => caches.match('./index.html'));\n"
        "    })\n"
        "  );\n});\n" % (CACHE_VERSION, asset_lines)
    )
    with open(os.path.join(CONSOLE, "sw.js"), "w", encoding="utf-8") as fh:
        fh.write(sw)


def main():
    with open(DATA, encoding="utf-8") as fh:
        d = json.load(fh)
    stages = d["stages"]

    os.makedirs(os.path.join(CONSOLE, "stages"), exist_ok=True)

    with open(os.path.join(CONSOLE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(render_index(d))
    print("wrote index.html")

    for i, s in enumerate(stages):
        prev_s = stages[i - 1] if i > 0 else None
        next_s = stages[i + 1] if i < len(stages) - 1 else None
        path = os.path.join(CONSOLE, "stages", "%s.html" % s["slug"])
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_stage(d, s, prev_s, next_s))
        print("wrote stages/%s.html" % s["slug"])

    write_manifest(d)
    print("wrote manifest.webmanifest")
    write_sw(stages)
    print("wrote sw.js")
    print("\nConsole generated: %d stages + hub. Open console/index.html." % len(stages))


if __name__ == "__main__":
    main()
