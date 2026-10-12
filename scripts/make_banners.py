"""Generate the org profile banners (dark + light) and the avatar as self-contained SVGs.

Text is converted to outlines so the SVGs render identically through GitHub's image proxy,
which loads no web fonts. Fonts are the ones served by smartcolibri.github.io:

    python3 scripts/make_banners.py <fonts_dir>

where <fonts_dir> holds fraunces.woff2, fraunces-italic.woff2, inter.woff2, plexmono500.woff2.
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "profile" / "assets"

COLIBRI = """
  <path d="M47 41 C38 42 33 50 35 59 C37 68 45 74 56 79 C52 70 50 62 52 55 C55 47 53 41 47 41 Z"/>
  <path d="M47 42 L15 30 L46 46 Z"/>
  <path d="M50 49 C61 31 81 24 95 28 C83 39 67 48 55 56 Z"/>
  <path d="M55 76 L77 88 L60 72 Z"/>
  <path d="M54 77 L62 93 L57 74 Z"/>"""

THEMES = {
    "dark": dict(bg="#0f0e0b", bg2="#16140f", text="#f3efe4", muted="#a39b8a", eyebrow="#c9a227",
                 rule="#7d6119", line="#e9cd82", line_op=".16", glow="#c9a227", glow_op=".14",
                 irid=("#3f7f70", "#e9cd82", "#c9a227", "#c58a72"), em=("#e9cd82", "#c9a227", "#c58a72"),
                 eye="#0f0e0b"),
    "light": dict(bg="#f4f1e9", bg2="#fbfaf5", text="#16140f", muted="#6b6355", eyebrow="#7d6119",
                  rule="#c9a227", line="#7d6119", line_op=".18", glow="#c9a227", glow_op=".16",
                  irid=("#2e5e42", "#c9a227", "#7d6119", "#8a3b2a"), em=("#7d6119", "#a8841c", "#8a3b2a"),
                  eye="#f4f1e9"),
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


def gradient(gid, stops, x2="1", y2="1"):
    n = len(stops) - 1
    offs = [0, .42, .7, 1] if n == 3 else [i / n for i in range(n + 1)]
    inner = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in zip(offs, stops))
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{inner}</linearGradient>'


def banner(theme, fonts):
    t = THEMES[theme]
    W, H, X = 1280, 400, 88
    serif, italic, sans, mono = fonts

    eyebrow, _ = outline(mono, "SMART COLIBRI · ÉDITION LOGICIELLE", 14, X + 44, 112, tracking=.24)
    l1, _ = outline(serif, "Des apps natives,", 64, X - 3, 192, tracking=-.018)
    em, ex = outline(italic, "précises", 64, X - 3, 266, tracking=-.018)
    l2, _ = outline(serif, " comme un colibri", 64, ex, 266, tracking=-.018)
    lead1, _ = outline(sans, "Applications natives pour Mac, iPhone, Apple Watch et Apple TV.", 19, X, 324)
    lead2, _ = outline(sans, "Par un cabinet de conseil en stratégie, digital et intelligence artificielle.", 19, X, 352)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Smart Colibri — Des apps natives, précises comme un colibri</title>
<defs>
  {gradient("irid", t["irid"])}
  {gradient("em", t["em"], x2="1", y2=".25")}
  <radialGradient id="glow" cx="78%" cy="42%" r="46%">
    <stop offset="0" stop-color="{t["glow"]}" stop-opacity="{t["glow_op"]}"/>
    <stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t["bg"]}"/><stop offset="1" stop-color="{t["bg2"]}"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
<rect width="{W}" height="{H}" rx="18" fill="url(#glow)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>
<g transform="translate(856 18) scale(4.6) translate(-10 -20)" fill="url(#irid)">{COLIBRI}
  <circle cx="42" cy="45" r="1.5" fill="{t["eye"]}"/>
</g>
<rect x="{X}" y="106" width="28" height="1" fill="{t["rule"]}"/>
<path d="{eyebrow}" fill="{t["eyebrow"]}"/>
<path d="{l1}" fill="{t["text"]}"/>
<path d="{em}" fill="url(#em)"/>
<path d="{l2}" fill="{t["text"]}"/>
<path d="{lead1}" fill="{t["muted"]}"/>
<path d="{lead2}" fill="{t["muted"]}"/>
</svg>
"""


def avatar():
    t = THEMES["dark"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>{gradient("irid", t["irid"])}
  <radialGradient id="glow" cx="55%" cy="45%" r="60%">
    <stop offset="0" stop-color="#c9a227" stop-opacity=".18"/><stop offset="1" stop-color="#c9a227" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="512" height="512" fill="{t["bg"]}"/>
<rect width="512" height="512" fill="url(#glow)"/>
<g transform="translate(256 262) scale(4.9) translate(-55 -60)" fill="url(#irid)">{COLIBRI}
  <circle cx="42" cy="45" r="1.5" fill="{t["eye"]}"/>
</g>
</svg>
"""


def main():
    fonts = (
        load("fraunces.woff2", wght=360, opsz=144),
        load("fraunces-italic.woff2", wght=340, opsz=144),
        load("inter.woff2", wght=350),
        load("plexmono500.woff2"),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"banner-{theme}.svg").write_text(banner(theme, fonts))
    (OUT / "avatar.svg").write_text(avatar())
    for f in sorted(OUT.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    main()
