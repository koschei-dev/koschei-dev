#!/usr/bin/env python3
"""Builds the profile images in assets/ (light and dark versions of each).

  python3 scripts/build.py            # uses live GitHub data when it can reach the API
  python3 scripts/build.py --offline  # uses the fallback values below

Every image is a plain SVG with its fonts embedded, so it renders the same on github.com,
in the mobile app and in previews. Run by .github/workflows/profile.yml once a day.
"""
import base64, datetime as dt, json, os, sys, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
USER = "seiunhim"

THEMES = {
    "light": dict(fg="#1B1A26", muted="#6C6A80", line="#E3E2EE", surface="#FFFFFF", alt="#F6F6FA",
                  accent="#6A63E8", ink="#4D46D9", soft="#ECEBFD", on="#FFFFFF", ok="#1F8A5B"),
    "dark":  dict(fg="#ECECF5", muted="#9C9BB2", line="#2A2A3A", surface="#151520", alt="#1B1B28",
                  accent="#8B95FF", ink="#AEB4FF", soft="#21233D", on="#111118", ok="#5FD49A"),
}

# ---------------------------------------------------------------- fonts
FACES = {
    "mono": ("dmmono-400.woff2", 400), "mono-m": ("dmmono-500.woff2", 500),
    "display": ("bricolage-700.woff2", 700), "body": ("hanken-450.woff2", 450), "body-b": ("hanken-600.woff2", 600),
}
_metrics = {}

def width(text, face, size):
    """Advance width of `text` in px, read from the embedded font itself."""
    if face not in _metrics:
        f = TTFont(FONTS / FACES[face][0])
        _metrics[face] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[face]
    return sum(hmtx.get(cmap.get(ord(ch), ".notdef"), (upm // 2, 0))[0] for ch in text) * size / upm

def font_css(faces):
    out = []
    for key in faces:
        file, weight = FACES[key]
        data = base64.b64encode((FONTS / file).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{key}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(out)

STACKS = {
    "mono": "'mono',ui-monospace,SFMono-Regular,Menlo,monospace",
    "mono-m": "'mono-m',ui-monospace,SFMono-Regular,Menlo,monospace",
    "display": "'display',system-ui,-apple-system,sans-serif",
    "body": "'body',system-ui,-apple-system,sans-serif",
    "body-b": "'body-b',system-ui,-apple-system,sans-serif",
}

def t(x, y, text, face, size, fill, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{STACKS[face]}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(text)}</text>')

def svg(w, h, body, faces, css="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
            f'<title>{escape(title)}</title><style>{font_css(faces)}{css}'
            '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'
            f'{body}</svg>')

def pill(x, y, text, c, face="mono", size=12, fill=None, color=None, pad=9, h=22):
    w = width(text, face, size) + pad * 2
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{fill or c["soft"]}"/>'
            + t(x + pad, y + h / 2 + size * 0.35, text, face, size, color or c["ink"])), w

def folder_icon(x, y, color, s=1.0):
    return (f'<path transform="translate({x} {y}) scale({s})" fill="{color}" '
            'd="M0 2a2 2 0 0 1 2-2h4.2l1.8 2.2H16a2 2 0 0 1 2 2V12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2z"/>')

def file_icon(x, y, c):
    return (f'<path transform="translate({x} {y})" fill="none" stroke="{c["muted"]}" stroke-width="1.3" '
            'd="M1.5 0.7h7l4 4v9.6h-11z M8.5 0.7v4h4"/>')

# ---------------------------------------------------------------- data
FALLBACK = {"public_repos": 3, "release": None, "updated": dt.date.today().isoformat()}

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
        rel = gh(f"repos/{USER}/organizy-app/releases/latest")
        data["release"] = rel.get("tag_name")
    except Exception:
        data["release"] = None  # no release yet
    return data

# ---------------------------------------------------------------- hero
FILES = [  # name, size, folder
    ("scan_4412.pdf", "412 KB", "Invoices & Receipts"),
    ("IMG_2291.HEIC", "3.1 MB", "Images"),
    ("Screenshot 10.14.03.png", "1.2 MB", "Screenshots"),
    ("resume_final.pdf", "148 KB", "Resumes & CVs"),
    ("IMG_2291 (2).HEIC", "3.1 MB", "Images"),
    ("invoice-march.pdf", "86 KB", "Invoices & Receipts"),
]
MESSY_ORDER = [2, 0, 4, 3, 1, 5]            # which file sits in each messy slot
JITTER = [(12, -1.6), (-8, 1.2), (16, 0.9), (-12, -1.0), (4, 1.7), (-4, -1.3)]
W = 900  # every image shares this width so type renders at the same scale

def demo_window(b, css, c, wx, wy, ww, ROW=28):
    """An animated Organizy window: six messy files sort themselves into folders, then reset."""
    sorted_rows, folder_rows, slot = {}, [], 0
    for folder in sorted({f[2] for f in FILES}):
        folder_rows.append((folder, slot, sum(1 for f in FILES if f[2] == folder))); slot += 1
        for i, f in enumerate(FILES):
            if f[2] == folder: sorted_rows[i] = slot; slot += 1
    n = slot
    head = 80
    wh = head + n * ROW + 44
    b.append(f'<rect x="{wx+.5}" y="{wy+.5}" width="{ww-1}" height="{wh}" rx="14" fill="{c["surface"]}" stroke="{c["line"]}"/>')
    b.append(t(wx + 16, wy + 28, "~/Downloads", "mono-m", 14, c["fg"]))
    b.append(t(wx + ww - 16, wy + 28, "6 files, unsorted", "mono", 12, c["muted"], "end", 'class="msg-a"'))
    b.append(t(wx + ww - 16, wy + 28, "sorted into 4 folders", "mono", 12, c["ink"], "end", 'class="msg-b"'))
    b.append(f'<line x1="{wx}" x2="{wx+ww}" y1="{wy+44}" y2="{wy+44}" stroke="{c["line"]}"/>')
    b.append(t(wx + 16, wy + 64, "Name", "mono", 11.5, c["muted"]))
    b.append(t(wx + ww - 16, wy + 64, "Size", "mono", 11.5, c["muted"], "end"))
    b.append(f'<line x1="{wx}" x2="{wx+ww}" y1="{wy+74}" y2="{wy+74}" stroke="{c["line"]}"/>')
    y0 = wy + head + 18
    for folder, s, count in folder_rows:
        y = y0 + s * ROW
        b.append(f'<g class="fold">{folder_icon(wx + 16, y - 11, c["accent"])}'
                 + t(wx + 42, y + 1, folder + "/", "mono-m", 13.5, c["ink"])
                 + t(wx + ww - 16, y + 1, f"{count} item{'s' if count > 1 else ''}", "mono", 12, c["muted"], "end") + "</g>")
    for i, (name, size, folder) in enumerate(FILES):
        ys = y0 + sorted_rows[i] * ROW
        ms = MESSY_ORDER.index(i)
        ym = y0 + 4 + ms * ROW * 1.5
        dx, rot = JITTER[ms]
        dx -= 24
        dy = ym - ys
        d = i * 0.7
        css.append(f".f{i}{{animation:f{i} 10s cubic-bezier(.2,.8,.2,1) infinite;transform-box:fill-box;transform-origin:center}}"
                   f"@keyframes f{i}{{0%,{30+d:.1f}%{{transform:translate({dx}px,{dy:.1f}px) rotate({rot}deg)}}"
                   f"{44+d:.1f}%,86%{{transform:translate(0px,0px) rotate(0deg)}}"
                   f"{95+d*0.4:.1f}%,100%{{transform:translate({dx}px,{dy:.1f}px) rotate({rot}deg)}}}}")
        b.append(f'<g class="f{i}">{file_icon(wx + 42, ys - 11, c)}'
                 + t(wx + 62, ys + 1, name, "mono", 13.5, c["fg"])
                 + t(wx + ww - 16, ys + 1, size, "mono", 12, c["muted"], "end") + "</g>")
    scan_h = n * ROW + 4
    b.append(f'<rect class="scan" x="{wx+1}" y="{wy+head-2}" width="{ww-2}" height="2" fill="{c["accent"]}"/>')
    css.append(f".scan{{opacity:0;animation:scan 10s linear infinite}}"
               f"@keyframes scan{{0%,20%{{opacity:0;transform:translateY(0px)}}21%{{opacity:1}}29%{{opacity:1;transform:translateY({scan_h}px)}}30%,100%{{opacity:0;transform:translateY({scan_h}px)}}}}")
    css.append(".fold{animation:fold 10s ease infinite}@keyframes fold{0%,38%{opacity:0}48%,86%{opacity:1}94%,100%{opacity:0}}")
    css.append(".msg-a{animation:ma 10s infinite}.msg-b{animation:mb 10s infinite}"
               "@keyframes ma{0%,40%{opacity:1}46%,88%{opacity:0}94%,100%{opacity:1}}"
               "@keyframes mb{0%,40%{opacity:0}46%,88%{opacity:1}94%,100%{opacity:0}}")
    css.append(".cursor{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
    fy = wy + wh - 14
    b.append(f'<line x1="{wx}" x2="{wx+ww}" y1="{fy-18}" y2="{fy-18}" stroke="{c["line"]}"/>')
    b.append(t(wx + 16, fy, "organizy · nothing moves until you confirm", "mono", 11.5, c["muted"]))
    return wh

def hero(c):
    faces = ["mono", "mono-m", "display", "body"]
    b, css = [], []
    X = 4
    b.append(t(X, 34, "~ / ", "mono", 16, c["muted"]))
    bw = width("~ / ", "mono", 16)
    b.append(t(X + bw, 34, USER, "mono-m", 16, c["fg"]))
    cw = width(USER, "mono-m", 16)
    b.append(f'<rect class="cursor" x="{X + bw + cw + 5:.1f}" y="21" width="8" height="16" fill="{c["accent"]}"/>')
    p, w = pill(X, 62, "APP BUILDER", c, "mono-m", 12.5, h=24); b.append(p)
    b.append(t(X, 118, "CYBERSECURITY STUDENT", "mono-m", 12.5, c["ink"]))
    b.append(t(X, 138, "SANTIAGO, DR", "mono-m", 12.5, c["ink"]))
    b.append(t(X - 3, 222, USER, "display", 86, c["fg"], extra='letter-spacing="-3"'))
    nw = width(USER, "display", 86) - 3 * len(USER)
    b.append(t(X - 3 + nw, 222, ".", "display", 86, c["accent"]))
    b.append(t(X, 268, "I build small, careful tools", "body", 22, c["muted"]))
    b.append(t(X, 298, "for messy computers.", "body", 22, c["muted"]))
    b.append(t(X, 346, "english · español", "mono", 14, c["muted"]))

    wh = demo_window(b, css, c, 452, 6, 444)
    H = 6 + wh + 8
    return svg(W, H, "".join(b), faces, "".join(css),
               f"{USER}: app builder and cybersecurity student in Santiago, DR. I build small, careful tools for messy computers.")

# ---------------------------------------------------------------- project card
def organizy_card(c, data):
    H = 214
    faces = ["mono", "mono-m", "display", "body"]
    b = [f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{c["surface"]}" stroke="{c["line"]}"/>']
    b.append(f'<rect x="24" y="26" width="76" height="76" rx="18" fill="{c["soft"]}"/>')
    b.append(f'<path transform="translate(39 46)" fill="none" stroke="{c["accent"]}" stroke-width="5.5" stroke-linejoin="round" '
             'd="M3 8a5 5 0 0 1 5-5h11l5 6h13a5 5 0 0 1 5 5v17a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5z"/>')
    b.append(f'<path transform="translate(76 34)" fill="{c["accent"]}" d="M7 0c.6 4.5 2.5 6.4 7 7-4.5.6-6.4 2.5-7 7-.6-4.5-2.5-6.4-7-7 4.5-.6 6.4-2.5 7-7z"/>')
    b.append(t(122, 58, "Organizy", "display", 36, c["fg"], extra='letter-spacing="-1"'))
    nw = width("Organizy", "display", 36) - 8
    b.append(t(122 + nw, 58, ".", "display", 36, c["accent"]))
    status = f"latest {data['release']}" if data.get("release") else "in testing"
    sw = width(status, "mono-m", 12.5) + 18
    p, _ = pill(W - 24 - sw, 34, status, c, "mono-m", 12.5, h=24); b.append(p)
    b.append(t(122, 90, "Tidies any messy folder on your Mac. It reads each file,", "body", 17.5, c["muted"]))
    b.append(t(122, 114, "suggests where it belongs, and moves nothing until you", "body", 17.5, c["muted"]))
    b.append(t(122, 138, "confirm. Every move can be undone.", "body", 17.5, c["muted"]))
    x = 122
    for tag in ["macOS 14+", "SwiftUI", "local AI", "free", "offline"]:
        p, w = pill(x, 160, tag, c, h=24); b.append(p); x += w + 8
    b.append(t(W - 24, 177, "open →", "mono-m", 14, c["ink"], "end"))
    return svg(W, H, "".join(b), faces, title="Organizy: tidies any messy folder on your Mac. Review every move, undo anything.")

# ---------------------------------------------------------------- now / stack / principles
COLUMNS = [
    ("now/", [("building", "Organizy 0.1"), ("next", "first public release"), ("studying", "cybersecurity"),
              ("labs", "networking · Linux · pentesting")]),
    ("stack/", [("apps", "Swift · SwiftUI · AppKit"), ("web", "HTML · CSS · JavaScript"), ("scripts", "Python · zsh"),
                ("security", "Linux · virtual labs")]),
    ("principles/", [("review-first", "show the plan, then act"), ("undo-always", "every change reversible"),
                     ("local-first", "your files stay yours"), ("small", "do one thing well")]),
]

def panels(c, data):
    faces = ["mono", "mono-m", "body"]
    gap = 14
    cw = (W - 2 * gap) / 3
    ROWH = 52
    ph = 52 + len(COLUMNS[0][1]) * ROWH + 6
    H = ph + 40
    b = []
    for i, (head, rows) in enumerate(COLUMNS):
        x = i * (cw + gap)
        b.append(f'<rect x="{x+.5:.1f}" y="0.5" width="{cw-1:.1f}" height="{ph-1}" rx="14" fill="{c["surface"]}" stroke="{c["line"]}"/>')
        b.append(folder_icon(x + 16, 17, c["accent"]))
        b.append(t(x + 42, 29, head, "mono-m", 15, c["ink"]))
        b.append(t(x + cw - 16, 29, f"{len(rows)}", "mono", 12, c["muted"], "end"))
        b.append(f'<line x1="{x:.1f}" x2="{x+cw:.1f}" y1="46" y2="46" stroke="{c["line"]}"/>')
        for j, (k, v) in enumerate(rows):
            y = 52 + j * ROWH
            if j % 2 == 0: b.append(f'<rect x="{x+1:.1f}" y="{y}" width="{cw-2:.1f}" height="{ROWH}" fill="{c["alt"]}"/>')
            b.append(t(x + 16, y + 20, k, "mono-m", 12.5, c["fg"]))
            b.append(t(x + 16, y + 41, v, "body", 15.5, c["muted"]))
    release = data["release"] or "no release yet"
    foot = f"updated {data['updated']}  ·  {data['public_repos']} public repos  ·  organizy-app: {release}"
    b.append(f'<circle cx="6" cy="{H-14}" r="4" fill="{c["ok"]}"/>')
    b.append(t(18, H - 10, foot, "mono", 12, c["muted"]))
    return svg(W, H, "".join(b), faces, title="now: building Organizy. stack: Swift, SwiftUI, HTML, CSS, JavaScript, Python. principles: review first, undo always, local first, small.")

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
