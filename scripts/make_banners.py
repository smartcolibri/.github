"""Generate the org profile banners (dark + light) and the avatar as self-contained SVGs.

Text is converted to outlines so the SVGs render identically through GitHub's image proxy,
which loads no web fonts. Fonts are the ones served by www.smartcolibri.fr:

    python3 scripts/make_banners.py <fonts_dir> <icons_dir>

where <fonts_dir> holds sourceserif-normal.woff2, sourceserif-italic.woff2 and inter.woff2,
and <icons_dir> holds the 112 px app icons as PNG (cockpit-for-claude.png, macinside.png, gym-matinale.png).
"""
import base64
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = Path(sys.argv[1])
ICONS = Path(sys.argv[2])
OUT = Path(__file__).resolve().parent.parent / "profile" / "assets"

COLIBRI = """
  <path d="M47 41 C38 42 33 50 35 59 C37 68 45 74 56 79 C52 70 50 62 52 55 C55 47 53 41 47 41 Z"/>
  <path d="M47 42 L15 30 L46 46 Z"/>
  <path d="M50 49 C61 31 81 24 95 28 C83 39 67 48 55 56 Z"/>
  <path d="M55 76 L77 88 L60 72 Z"/>
  <path d="M54 77 L62 93 L57 74 Z"/>"""

# Tokens from www.smartcolibri.fr (navy, white, mist; brass is reserved for the EU AI Act frame).
NAVY, NAVY_DEEP, WHITE = "#0f2340", "#0a1830", "#ffffff"
THEMES = {
    "light": dict(bg=WHITE, panel="#f4f6f9", text="#16223a", muted="#5a6374",
                  rule="#69717f", border="#dde2ea", mark=NAVY, eye=WHITE),
    "dark": dict(bg=NAVY_DEEP, panel=NAVY, text=WHITE, muted="#b6bcc7",
                 rule="#8a93a2", border="#2a3a55", mark=WHITE, eye=NAVY),
}


def load(name, **axes):
    font = TTFont(FONTS / name)
    if axes and "fvar" in font:
        font = instancer.instantiateVariableFont(font, axes)
    return font


def outline(font, text, size, x, y, tracking=0.0):
    """Return (svg path data, end x) for `text` set at baseline (x, y)."""
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    hmtx, scale = font["hmtx"], size / font["head"].unitsPerEm
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            sys.exit(f"glyph missing for {ch!r} in {font['name'].getDebugName(4)}")
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[name][0] * scale + tracking * size
    return pen.getCommands(), x


def width(font, text, size, tracking=0.0):
    cmap, hmtx, scale = font.getBestCmap(), font["hmtx"], size / font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(ch)]][0] * scale + tracking * size for ch in text)


def wrap(font, text, size, max_width):
    lines, line = [], ""
    for word in text.split(" "):
        trial = f"{line} {word}".strip()
        if line and width(font, trial, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


# Apps, with the short descriptions used on www.smartcolibri.fr. `shape` follows the site's icon rules:
# the macOS icons carry Apple's transparent margin (scaled 1.22), the iOS icon is a full square (13/56 radius).
APPS = [
    dict(slug="cockpit-for-claude", name="Cockpit for Claude", plat="macOS · Gratuit", shape="mac",
         desc="Quotas Anthropic, coût et sessions Claude Code réunis dans une app native, 100 % locale."),
    dict(slug="macinside", name="MacInside", plat="macOS · Gratuit · Open source", shape="mac",
         desc="CPU, mémoire, réseau, capteurs, GPU et batterie en temps réel, dans une fenêtre et la barre des menus."),
    dict(slug="gym-matinale", name="Gym Matinale", plat="iPhone · Apple Watch · Mac · Apple TV", shape="square",
         desc="La routine de mobilité du matin, guidée par un coach vocal."),
]


def app_row(app, fonts):
    """One white slip per app. GitHub leaves a few pixels between stacked images and strips styles,
    so the rows are separate 2px-cornered slips rather than one ruled list; sizes stay legible on phones."""
    t = THEMES["light"]
    serif, _, sans, name_font = fonts
    W, X, ICON = 1280, 48, 104
    TX = X + ICON + 36
    desc = wrap(serif, app["desc"], 28, W - TX - 130)
    H = 46 + 40 + 34 + len(desc) * 38 + 34
    name, _ = outline(name_font, app["name"], 40, TX, 46 + 34)
    plat, _ = outline(sans, app["plat"], 21, TX, 46 + 40 + 26)
    body = "".join(
        f'<path d="{outline(serif, line, 28, TX, 46 + 40 + 34 + 34 + i * 38)[0]}" fill="#5a6374"/>'
        for i, line in enumerate(desc))
    png = base64.b64encode((ICONS / f"{app['slug']}.png").read_bytes()).decode()
    iy = (H - ICON) / 2
    if app["shape"] == "mac":
        s = ICON * 1.22
        icon = f'<image href="data:image/png;base64,{png}" x="{X + (ICON - s) / 2}" y="{iy + (ICON - s) / 2}" width="{s}" height="{s}"/>'
    else:
        r = ICON * 13 / 56
        icon = (f'<clipPath id="ic"><rect x="{X}" y="{iy}" width="{ICON}" height="{ICON}" rx="{r}"/></clipPath>'
                f'<image href="data:image/png;base64,{png}" x="{X}" y="{iy}" width="{ICON}" height="{ICON}" clip-path="url(#ic)"/>')
    ax, ay = W - 70, H / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">{app["name"]} — {app["plat"]}</title>
<rect width="{W}" height="{H}" rx="2" fill="{t["bg"]}"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="2" fill="none" stroke="{t["border"]}"/>
{icon}
<path d="{name}" fill="{t["text"]}"/>
<path d="{plat}" fill="#69717f"/>
{body}
<path d="M{ax - 12} {ay + 12} L{ax + 12} {ay - 12} M{ax - 9} {ay - 12} H{ax + 12} V{ay + 9}" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def banner(theme, fonts):
    t = THEMES[theme]
    W, H, X, P = 1280, 400, 88, 880
    serif, italic, sans, wordmark_font = fonts

    # DESIGN.md: no text above a headline, no uppercase runs; the wordmark sits apart, the short rule opens.
    wordmark, _ = outline(wordmark_font, "Smart Colibri", 22, X, 78)
    l1, _ = outline(serif, "Des apps natives,", 62, X - 2, 200, tracking=-.012)
    em, ex = outline(italic, "précises", 62, X - 2, 270, tracking=-.012)
    l2, _ = outline(serif, " comme un colibri", 62, ex, 270, tracking=-.012)
    lead1, _ = outline(sans, "Applications natives pour l'écosystème Apple, par un cabinet de", 18, X, 322)
    lead2, _ = outline(sans, "conseil indépendant en intelligence artificielle et stratégie.", 18, X, 349)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Smart Colibri — Des apps natives, précises comme un colibri</title>
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="2"/></clipPath></defs>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="{t["bg"]}"/>
  <rect x="{P}" width="{W - P}" height="{H}" fill="{t["panel"]}"/>
  <rect x="{P}" width="1" height="{H}" fill="{t["border"]}"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="2" fill="none" stroke="{t["border"]}"/>
<g transform="translate(1080 200) scale(2.7) translate(-55 -61)" fill="{t["mark"]}">{COLIBRI}
  <circle cx="42" cy="45" r="1.5" fill="{t["panel"]}"/>
</g>
<path d="{wordmark}" fill="{t["text"]}"/>
<rect x="{X}" y="118" width="40" height="1" fill="{t["rule"]}"/>
<path d="{l1}" fill="{t["text"]}"/>
<path d="{em}" fill="{t["text"]}"/>
<path d="{l2}" fill="{t["text"]}"/>
<path d="{lead1}" fill="{t["muted"]}"/>
<path d="{lead2}" fill="{t["muted"]}"/>
</svg>
"""


def avatar():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<rect width="512" height="512" fill="{NAVY}"/>
<g transform="translate(256 261) scale(4.6) translate(-55 -61)" fill="{WHITE}">{COLIBRI}
  <circle cx="42" cy="45" r="1.5" fill="{NAVY}"/>
</g>
</svg>
"""


def main():
    fonts = (
        load("sourceserif-normal.woff2", wght=400, opsz=60),
        load("sourceserif-italic.woff2", wght=400),
        load("inter.woff2", wght=400),
        load("sourceserif-normal.woff2", wght=500, opsz=20),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"banner-{theme}.svg").write_text(banner(theme, fonts))
    (OUT / "avatar.svg").write_text(avatar())
    for app in APPS:
        (OUT / f"app-{app['slug']}.svg").write_text(app_row(app, fonts))
    for f in sorted(OUT.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    main()
