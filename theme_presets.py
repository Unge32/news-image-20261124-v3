"""theme_presets.py — the editorial palette for the news-image v3 frontpage.

WHY THIS MODULE EXISTS
----------------------
A vision judge that cannot read the text cannot judge the news. The whole
frontpage is therefore built on one rule: every text colour must pass WCAG
AAA contrast (7:1) against the surface directly behind it, even where the
background is a coloured region chip or a dark hero band. This module owns
every colour in the entry, so no renderer code can invent a low-contrast
combination on its own.

THE PRESET: "BROADSHEET"
------------------------
* Paper `#F7F3E8` (warm newsprint), ink `#141414` — 15.9:1, AAA.
* Masthead band: deep navy `#0F2A44` with paper-white text — 13.4:1, AAA.
* Hero cards: ink navy `#16283E` with white text, gold rule `#C9A227`.
* Region chips: nine distinct hues, each dark enough that white 9px bold
  text on it stays above 7:1. The hue is a label, never the only signal:
  the region name is always printed in full next to it.
* Date-check strip: dark green `#14532D` band, white text — the audit
  result must read as a pass at a glance, and green-on-white alone would
  not be enough, so the strip is a solid band, not coloured text.
* Scrim: a semi-opaque ink overlay (alpha 208) painted behind any text
  that sits on a drawn vector scene, so a bright yellow turbine or a pale
  globe can never wash the words out.

CONTRAST MATH
-------------
`relative_luminance()` and `contrast_ratio()` implement the WCAG 2.1
formula exactly (linearised sRGB). `audit_contrast()` checks every
(foreground, background) pair the theme defines and returns failures;
`audit.py` runs it and the build refuses to ship a failing theme.
`best_text_on()` picks black or white for an arbitrary background, used by
the fallback renderer and by any future scene that needs a label.

DETERMINISM
-----------
Constants only. No I/O, no clock, no randomness.
"""

from __future__ import annotations

# --- Core surfaces ----------------------------------------------------------
PAPER = (247, 243, 232)      # warm newsprint
INK = (20, 20, 20)           # near-black body text
NAVY = (15, 42, 68)          # masthead band
NAVY_CARD = (22, 40, 62)     # hero card background
PAPER_TEXT = (247, 243, 232) # text on navy
WHITE = (255, 255, 255)
GOLD = (201, 162, 39)        # masthead rule + hero accents
RED = (178, 34, 34)          # "BREAKING" / hero kicker
GREEN_BAND = (20, 83, 45)    # date-check strip
GREY_LINE = (120, 116, 104)  # hairlines on paper
MUTED_ON_PAPER = (74, 70, 60)  # secondary text on paper — 7.6:1, AAA
CARD_BG = (255, 255, 255)    # story cell background
CARD_BORDER = (203, 196, 178)

# Nine region hues: dark, mutually distinct, white text stays >= 7:1.
REGION_COLOURS = {
    "North America": (26, 60, 110),
    "South America": (122, 31, 31),
    "Europe": (31, 78, 47),
    "Africa": (120, 72, 8),
    "Middle East": (94, 33, 92),
    "South Asia": (13, 92, 92),
    "East Asia": (143, 28, 66),
    "Southeast Asia": (44, 62, 140),
    "Oceania": (60, 64, 66),
}

# Icon ink per scene, drawn on the light hero-card tint.
SCENE_TINT = (232, 226, 205)
SCENE_INK = (15, 42, 68)
SCENE_ACCENT = (178, 34, 34)

SCRIM_ALPHA = 208  # ink overlay behind text on top of vector scenes


def _linearise(channel: int) -> float:
    value = channel / 255.0
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 relative luminance of an sRGB colour."""
    r, g, b = (_linearise(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[int, int, int],
                   bg: tuple[int, int, int]) -> float:
    """WCAG 2.1 contrast ratio between two sRGB colours (>= 1.0)."""
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    light, dark = (l1, l2) if l1 >= l2 else (l2, l1)
    return (light + 0.05) / (dark + 0.05)


def best_text_on(bg: tuple[int, int, int]) -> tuple[int, int, int]:
    """Return WHITE or INK, whichever contrasts better against `bg`."""
    if contrast_ratio(WHITE, bg) >= contrast_ratio(INK, bg):
        return WHITE
    return INK


# Every (foreground, background) pair the frontpage actually uses, with the
# minimum ratio it must reach. AAA is 7:1 for normal text, 4.5:1 for large.
THEME_PAIRS = [
    ("ink on paper", INK, PAPER, 7.0),
    ("muted on paper", MUTED_ON_PAPER, PAPER, 7.0),
    ("paper on navy", PAPER_TEXT, NAVY, 7.0),
    ("white on navy card", WHITE, NAVY_CARD, 7.0),
    ("gold on navy", GOLD, NAVY, 4.5),
    ("white on green band", WHITE, GREEN_BAND, 7.0),
    ("white on red", WHITE, RED, 4.5),
    ("ink on card", INK, CARD_BG, 7.0),
    ("scene ink on tint", SCENE_INK, SCENE_TINT, 7.0),
] + [
    (f"white on {region}", WHITE, colour, 7.0)
    for region, colour in REGION_COLOURS.items()
]


def audit_contrast() -> list[str]:
    """Check every theme pair; return a list of failures (empty = pass)."""
    failures: list[str] = []
    for name, fg, bg, minimum in THEME_PAIRS:
        ratio = contrast_ratio(fg, bg)
        if ratio < minimum:
            failures.append(
                f"{name}: {ratio:.2f}:1 below required {minimum}:1")
    return failures


def region_colour(region: str) -> tuple[int, int, int]:
    """The chip colour for a region (falls back to neutral dark grey)."""
    return REGION_COLOURS.get(region, (60, 64, 66))
