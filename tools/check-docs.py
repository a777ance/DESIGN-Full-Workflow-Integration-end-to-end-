#!/usr/bin/env python3
"""Validate Markdown cross-links across the whole repo.

The business-workflow analog of localDNS's tools/check-docs.py — extended for
this repo's structure. localDNS keeps its cross-references in root files, so its
checker scans only the repo root and resolves anchors within a single file. This
repo's stages live in numbered subfolders that link *across* files and folders
(e.g. a stage README linking to `../LAUNCH-NOTES.md#some-break-point`), so this
checker:

  - recurses into every `*.md` in the repo (not just the root),
  - for every relative file link `](path)`, confirms the file exists,
  - for every in-page anchor `](#slug)`, confirms the heading exists *here*,
  - for every cross-file anchor `](path#slug)`, confirms the heading exists in
    *that* file — the class of breakage a single-file checker cannot see.

Heading anchors use GitHub's slug algorithm (lowercase, drop characters that are
not word/space/hyphen, spaces -> hyphens, de-duplicate with -1/-2), identical to
the localDNS checker so anchors here match what GitHub will generate. Headings
and links inside fenced code blocks are ignored. External (`http(s)://`,
`mailto:`) links and links into the sibling `localDNS/` repo are skipped.

Exits non-zero if any link is broken, so it can gate a commit or CI run.

Usage:
    python3 tools/check-docs.py
"""
import glob
import os
import re
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def slugify(text, seen):
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s", "-", s)
    if s in seen:
        seen[s] += 1
        s = f"{s}-{seen[s]}"
    else:
        seen[s] = 0
    return s


def heading_anchors(lines):
    seen, anchors, in_fence = {}, set(), False
    for ln in lines:
        if re.match(r"^\s*```", ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", ln)
        if m:
            anchors.add(slugify(m.group(2), seen))
    return anchors


def strip_fenced(lines):
    out, in_fence = [], False
    for ln in lines:
        if re.match(r"^\s*```", ln):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else ln)
    return out


def anchors_for(path, cache):
    """Memoized heading-anchor set for a file (or None if it can't be read)."""
    if path not in cache:
        try:
            cache[path] = heading_anchors(
                open(path, encoding="utf-8").read().split("\n")
            )
        except OSError:
            cache[path] = None
    return cache[path]


def check(path, anchor_cache):
    lines = open(path, encoding="utf-8").read().split("\n")
    here = anchors_for(path, anchor_cache)
    base = os.path.dirname(path)
    problems = []
    for raw in LINK.findall("\n".join(strip_fenced(lines))):
        target = raw.strip().split(None, 1)[0]  # drop any optional "title"
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        # Pure in-page anchor.
        if target.startswith("#"):
            if target[1:] not in here:
                problems.append(f"broken anchor link: {raw.strip()}")
            continue
        filepart, _, anchor = target.partition("#")
        if not filepart:
            continue
        # Links into the sibling localDNS repo are out of this tree — skip.
        if filepart.startswith("localDNS/"):
            continue
        dest = os.path.normpath(os.path.join(base, filepart))
        if not os.path.exists(dest):
            problems.append(f"missing file link: {raw.strip()}")
            continue
        # Cross-file anchor: the file exists, now confirm the heading does too.
        if anchor and dest.endswith(".md"):
            dest_anchors = anchors_for(dest, anchor_cache)
            if dest_anchors is not None and anchor not in dest_anchors:
                problems.append(f"broken cross-file anchor: {raw.strip()}")
    return problems


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    anchor_cache = {}
    failed = False
    for f in sorted(glob.glob("**/*.md", recursive=True)):
        problems = check(f, anchor_cache)
        if problems:
            failed = True
            print(f"FAIL {f}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {f}")
    if failed:
        print("\nDoc check FAILED")
        sys.exit(1)
    print("\nAll doc links resolve.")


if __name__ == "__main__":
    main()
