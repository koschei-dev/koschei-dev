#!/usr/bin/env python3
"""Builds the profile images in assets/ (light and dark versions of each).

  python3 scripts/build.py            # uses live GitHub data when it can reach the API
  python3 scripts/build.py --offline  # uses the fallback values below

Same look as the Organizy website: Bodoni Moda for display, Jost for text. Every image is a
plain SVG with its fonts embedded (see svgkit.py). Run by .github/workflows/profile.yml daily.
"""
import datetime as dt, json, os, sys, urllib.request
from pathlib import Path

from svgkit import HERE, THEMES, arrow, fit_size, monument, png_data, svg, t, width, wrap

ROOT = HERE.parent
OUT = ROOT / "assets"
USER = "seiunhim"
SITE = "seiunhim.github.io/organizy-app"
W = 900  # every image shares this width so type renders at the same scale
ICON = png_data(HERE / "organizy-icon.png")

# ---------------------------------------------------------------- data
FALLBACK = {"public_repos": 3, "release": None, "updated": dt.date.today()}


def gh(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def load_data(offline):
    data = dict(FALLBACK)
    if offline:
        return data
    try:
        data["public_repos"] = gh(f"users/{USER}")["public_repos"]
    except Exception as e:
        print("profile lookup failed, using fallback:", e)
    try:
        data["release"] = gh(f"repos/{USER}/organizy-app/releases/latest").get("tag_name")
    except Exception:
        data["release"] = None  # no release yet
    return data


# ---------------------------------------------------------------- hero
def hero(c):
    b, css = [], []
    b.append(t(0, 20, "App builder, cybersecurity student", "text", 16, c["muted"]))
    b.append(t(W, 20, "Santiago, DR", "text", 16, c["muted"], "end"))
    size = fit_size(USER + ".", W + 4)
    base = 40 + size * 0.80
    m, mcss, mw = monument(USER, size, -2, base, c["ink"], cls="h")
    b.append(m); css.append(mcss)
    # the full stop in the accent colour, landing last
    b.append(f'<g class="h-dot">{t(-2 + mw - 0.05 * size, base, ".", "display", size, c["accent"])}</g>')
    css.append(f".h-dot{{animation:h-dot .6s cubic-bezier(.22,1,.36,1) .85s both}}@keyframes h-dot{{from{{opacity:0;transform:translateY(12px)}}}}")
    y = base + 58
    b.append(f'<g class="h-foot">{t(0, y, "I build small, careful tools for messy computers.", "text", 22, c["ink"])}'
             f'{t(W, y, "English · Español", "text", 16, c["muted"], "end")}</g>')
    css.append(".h-foot{animation:h-foot .7s cubic-bezier(.22,1,.36,1) .7s both}@keyframes h-foot{from{opacity:0;transform:translateY(10px)}}")
    return svg(W, int(y + 12), "".join(b), ["display", "text"], "".join(css),
               f"{USER}. App builder and cybersecurity student in Santiago, DR. I build small, careful tools for messy computers. English and Spanish.")


# ---------------------------------------------------------------- project card
def organizy_card(c, data):
    P = 40
    H = 300
    b, css = [f'<rect width="{W}" height="{H}" rx="20" fill="{c["surface"]}"/>'], []
    size = 78
    base = P + size * 0.78
    m, mcss, _ = monument("Organizy", size, P, base, c["ink"], icon=ICON, cls="o")
    b.append(m); css.append(mcss)
    status = f"Latest release {data['release']}" if data.get("release") else "In testing, first release soon"
    b.append(t(W - P, P + 14, status, "text", 15, c["muted"], "end"))
    desc = ("A free Mac app that reads a messy folder, suggests where every file belongs, "
            "and moves nothing until you confirm. Every move can be undone.")
    y = base + 50
    for i, line in enumerate(wrap(desc, "text", 20, 560)):
        b.append(t(P, y + i * 30, line, "text", 20, c["ink"]))
    fy = H - P + 2
    b.append(t(P, fy, "macOS 14 or later  ·  Swift and SwiftUI  ·  Optional local AI  ·  MIT", "text", 15, c["muted"]))
    label = "Try the live demo"
    lw = width(label, "text-m", 17)
    b.append(t(W - P - 22, fy, label, "text-m", 17, c["accent_ink"], "end"))
    b.append(arrow(W - P - 14, fy - 5.5, c["accent_ink"]))
    _ = lw
    return svg(W, H, "".join(b), ["display", "text", "text-m"], "".join(css),
               "Organizy: a free Mac app that reads a messy folder, suggests where every file belongs, and moves nothing until you confirm. Try the live demo.")


# ---------------------------------------------------------------- now / stack / principles
SECTIONS = [
    ("Now", [("Building", "Organizy, a file sorter for macOS"), ("Next", "its first public release"),
             ("Studying", "cybersecurity"), ("Labs", "networking, Linux, pentesting")]),
    ("Stack", [("Apps", "Swift, SwiftUI, AppKit"), ("Web", "React, TypeScript, Tailwind"),
               ("Scripts", "Python, zsh"), ("Security", "Linux, virtual labs")]),
    ("Principles", [("Review first", "show the plan, then act"), ("Undo always", "every change can be reversed"),
                    ("Local first", "your files stay on your computer"), ("Small", "do one thing well")]),
]


def panels(c, data):
    b = []
    ROW, KX, VX = 34, 330, 500
    y = 0
    for head, rows in SECTIONS:
        b.append(f'<rect x="0" y="{y}" width="{W}" height="1" fill="{c["line"]}"/>')
        b.append(t(0, y + 44, head, "display-m", 32, c["ink"], extra='letter-spacing="-0.5"'))
        for j, (k, v) in enumerate(rows):
            ry = y + 44 + j * ROW
            b.append(t(KX, ry, k, "text-m", 16.5, c["ink"]))
            b.append(t(VX, ry, v, "text", 16.5, c["muted"]))
        y += 44 + len(rows) * ROW + 10
    b.append(f'<rect x="0" y="{y}" width="{W}" height="1" fill="{c["line"]}"/>')
    d = data["updated"]
    release = f"Organizy {data['release']}" if data["release"] else "Organizy in testing"
    foot = f"Updated {d.strftime('%B')} {d.day}, {d.year}  ·  {data['public_repos']} public repositories  ·  {release}"
    b.append(f'<circle cx="5" cy="{y + 33}" r="4" fill="{c["ok"]}"/>')
    b.append(t(18, y + 38, foot, "text", 14.5, c["muted"]))
    return svg(W, y + 48, "".join(b), ["display-m", "text", "text-m"],
               title="Now: building Organizy, studying cybersecurity. Stack: Swift, SwiftUI, React, TypeScript, Python. "
                     "Principles: review first, undo always, local first, small.")


def main():
    data = load_data("--offline" in sys.argv)
    OUT.mkdir(exist_ok=True)
    for theme, c in THEMES.items():
        (OUT / f"hero-{theme}.svg").write_text(hero(c))
        (OUT / f"organizy-{theme}.svg").write_text(organizy_card(c, data))
        (OUT / f"panels-{theme}.svg").write_text(panels(c, data))
    print("built", sorted(p.name for p in OUT.glob("*.svg")), data)


if __name__ == "__main__":
    main()
