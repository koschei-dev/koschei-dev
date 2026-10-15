"""Shared drawing kit for the profile and README images.

Same type as the Organizy website: Bodoni Moda for display, Jost for text, DM Mono only for
file names inside the app window. Fonts are embedded as base64 subsets and text is laid out
from the fonts' own advance widths, so images render the same everywhere GitHub shows them.
"""
import base64
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"

# Brand tokens, matching web/src/styles.css on the site.
THEMES = {
    "light": dict(bg="#F6F6FA", surface="#EBEAF3", ink="#16151F", muted="#4E4C62", line="#DCDAE8",
                  accent="#5B54E0", accent_ink="#4D46D9", soft="#ECEBFD", ok="#1F8A5B",
                  # the app window (the site's --mac-* tokens)
                  win="#FFFFFF", side="#EEEDF3", bar="#F7F7F9", wline="#E2E2E8", wtext="#1D1D1F",
                  wtext2="#6E6E78", tint="#6A63E8", tint_ink="#4D46D9", tint_soft="#ECEBFD",
                  select="#E4E2FB", control_line="#D2D2DA", on_tint="#FFFFFF", folder="#5AB0F7",
                  shadow="rgba(40,30,120,.30)"),
    "dark": dict(bg="#111118", surface="#1B1A26", ink="#ECECF5", muted="#A3A2BA", line="#2C2B3C",
                 accent="#8B95FF", accent_ink="#AEB4FF", soft="#21233D", ok="#5FD49A",
                 win="#1E1E23", side="#2A2A31", bar="#25252B", wline="#36363E", wtext="#F2F2F7",
                 wtext2="#A1A1AA", tint="#8B95FF", tint_ink="#AEB4FF", tint_soft="#2A2C4E",
                 select="#33355E", control_line="#4A4A53", on_tint="#111118", folder="#5AB0F7",
                 shadow="rgba(0,0,0,.65)"),
}

FACES = {
    "display": ("bodoni-700.woff2", 700), "display-m": ("bodoni-500.woff2", 500),
    "text": ("jost-400.woff2", 400), "text-m": ("jost-500.woff2", 500),
    "mono": ("dmmono-400.woff2", 400), "mono-m": ("dmmono-500.woff2", 500),
}
FALLBACK = {
    "display": "'Bodoni Moda',Didot,'Bodoni 72',Georgia,serif", "display-m": "'Bodoni Moda',Didot,'Bodoni 72',Georgia,serif",
    "text": "Jost,'Futura',system-ui,sans-serif", "text-m": "Jost,'Futura',system-ui,sans-serif",
    "mono": "ui-monospace,SFMono-Regular,Menlo,monospace", "mono-m": "ui-monospace,SFMono-Regular,Menlo,monospace",
}
_metrics = {}


def _font(face):
    if face not in _metrics:
        f = TTFont(FONTS / FACES[face][0])
        _metrics[face] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    return _metrics[face]


def adv(ch, face):
    """Advance width of one character, in em."""
    cmap, hmtx, upm = _font(face)
    return hmtx.get(cmap.get(ord(ch), ".notdef"), (upm // 2, 0))[0] / upm


def width(text, face, size, track=0.0):
    """Width of `text` in px; `track` is letter-spacing in em."""
    return sum(adv(ch, face) + track for ch in text) * size


def wrap(text, face, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        nxt = f"{cur} {word}".strip()
        if cur and width(nxt, face, size) > maxw:
            lines.append(cur); cur = word
        else:
            cur = nxt
    return lines + ([cur] if cur else [])


def font_css(faces):
    out = []
    for key in faces:
        file, weight = FACES[key]
        data = base64.b64encode((FONTS / file).read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{key}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(out)


def t(x, y, text, face, size, fill, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="\'{face}\',{FALLBACK[face]}" font-size="{size}" '
            f'font-weight="{FACES[face][1]}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(text)}</text>')


def svg(w, h, body, faces, css="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
            f'<title>{escape(title)}</title><style>{font_css(faces)}{css}'
            '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'
            f'{body}</svg>')


def png_data(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def arrow(x, y, color, s=1.0):
    """A thin right arrow whose left end sits at (x, y) on the text's x-height middle."""
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({s})" fill="none" stroke="{color}" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" d="M0 0h13M8 -5l5 5-5 5"/>')


EASE = "cubic-bezier(.7,0,.2,1)"
EASE_OUT = "cubic-bezier(.22,1,.36,1)"


def monument(text, size, x, base, fill, *, icon=None, track=-0.04, cls="m", delay=0.0):
    """The site's display wordmark: Bodoni bold, tight tracking, letters rising into place once.

    With `icon` (a PNG data URI) the app icon stands in for the first letter, as on the site.
    Returns (svg, css, width).
    """
    parts, css = [], []
    cx = x
    clip_id = f"{cls}-clip"
    if icon:
        s = 0.72 * size
        iy = base + 0.02 * size - s
        parts.append(f'<image class="{cls}-icon" href="{icon}" x="{cx:.1f}" y="{iy:.1f}" width="{s:.1f}" height="{s:.1f}"/>')
        css.append(f".{cls}-icon{{transform-box:fill-box;transform-origin:center;"
                   f"animation:{cls}-shut 1.1s {EASE} {delay:.2f}s both}}"
                   f"@keyframes {cls}-shut{{from{{clip-path:inset(0 0 100% 0);transform:scale(1.12)}}"
                   f"to{{clip-path:inset(0 0 0 0);transform:scale(1)}}}}")
        cx += s + 0.02 * size
        text = text[1:]
    letters = []
    for i, ch in enumerate(text):
        letters.append(f'<g class="{cls}-l" style="animation-delay:{delay + 0.25 + i * 0.045:.3f}s">'
                       + t(cx, base, ch, "display", size, fill) + "</g>")
        cx += (adv(ch, "display") + track) * size
    css.append(f".{cls}-l{{animation:{cls}-rise .9s {EASE_OUT} both}}"
               f"@keyframes {cls}-rise{{from{{transform:translateY({size * 0.9:.0f}px);opacity:0}}to{{transform:none;opacity:1}}}}")
    desc = any(ch in "gjpqyQ," for ch in text)
    top, bottom = base - size * 1.05, base + size * (0.3 if desc else 0.03)
    parts.append(f'<clipPath id="{clip_id}"><rect x="{x - 10}" y="{top:.1f}" width="{cx - x + size:.1f}" height="{bottom - top:.1f}"/></clipPath>'
                 f'<g clip-path="url(#{clip_id})">{"".join(letters)}</g>')
    return "".join(parts), "".join(css), cx - x - track * size


def fit_size(text, target, *, icon=False, track=-0.04):
    """Font size at which the monument spans `target` px."""
    em = sum(adv(ch, "display") + track for ch in (text[1:] if icon else text)) - track
    if icon:
        em += 0.74
    return target / em
