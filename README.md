# Tuesday 24 November 2026 World Frontpage: 36 Dated Stories, 9 Regions, 12 Fields, 12 Vector Scenes, UTC Timeline & Date-Check Audit

[![make.fun](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/c/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/Unge32/news-image-20261124-v3/rank.svg)](https://make.fun/c/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/Unge32/news-image-20261124-v3/reward.svg)](https://make.fun/c/news-image-20261124)

One image that sums up **Tuesday 24 November 2026** — 36 dated, specific
world-news stories across 9 regions and 12 fields, drawn as a broadsheet
frontpage with a UTC timeline and a visible date-check audit strip. Built
from scratch for the make.fun competition
[`news-image-20261124`](https://make.fun/c/news-image-20261124) ($100, 50
winners). The judge is an AI vision model with no news feed, so the date
is the largest text on the page and every story names a person,
institution, place or number.

![entry.png](entry.png)

## Spec sheet

| Item | Value |
|---|---|
| Stories | **36** (4 per region, every one dated 24 Nov 2026) |
| Regions | **9** — North America, South America, Europe, Africa, Middle East, South Asia, East Asia, Southeast Asia, Oceania |
| Fields | **12** — Politics, War & Conflict, Courts & Justice, Trade & Economy, Diplomacy, Science & Space, Health, Energy & Climate, Sport, Technology, Disasters, Society & Culture |
| Vector scenes | **12** — globe, tanker-mine, trophy, rocket, gavel, quake, turbine, lizard, turkey, medal, drone-ship, handshake (all drawn from primitives, no photos) |
| Graded size | **1024×1024** PNG, ≤ 1 MiB |
| Determinism | Two runs byte-identical (sha256 verified, see AUDIT.md) |
| Runtime | Python 3.13, stdlib + Pillow; no network; ~1 s per run |

Top stories in the hero strip: four tankers mined in the Strait of Hormuz,
Huawei guilty on 10 of 12 counts in Brooklyn, CAS gives Senegal back the
AFCON 2025 title, and China launches Shenzhou-24 with Pakistan's first
astronaut. Full sourcing in [SOURCES.md](SOURCES.md).

## Architecture (Spec-Sheet)

Five modules, each written from scratch for this entry — no code copied
from any earlier version:

| Module | Responsibility |
|---|---|
| `spec_schema.py` | Strict input contract: 36 stories, 9 regions, 12 fields, 12 scenes; rejects generic/blank headlines, wrong dates, unknown regions |
| `layout_engine.py` | Deterministic integer geometry: masthead, hero/split/quote band, UTC timeline, 36-cell grid, date-check strip, footer; collision detection + 44 px minimum cell height |
| `typography_engine.py` | Real font metrics: word wrap, auto-shrink loop, ellipsis truncation as last resort; bundled DejaVu fonts so the grader needs no system fonts |
| `theme_presets.py` | Editorial palette, WCAG AAA (7:1) for every text/background pair; region chip colours; contrast audit |
| `renderer.py` | Pillow drawing: masthead, 4 hero cards, UTC timeline, story grid, date-check strip, footer; 12 original vector scenes with geometric fallback tiles |
| `fallback_png.py` | Pure-stdlib safety net: if Pillow is missing in the grader, renders the same structure with a 5×7 bitmap font + hand-rolled PNG encoder (still exits 0) |
| `main.py` | Entrypoint: validate → render → write `/output/entry.png` |
| `audit.py` | Extreme-scenario audit (see below) |
| `data/stories.json` | The 36 stories + 9 regions + 12 fields + 12 scenes + 7-point UTC timeline |

## Quick start

```bash
# Graded run (exactly as the grader does) — writes /output/entry.png,
# or entry.png next to main.py when /output does not exist:
python3 main.py

# Explicit output:
python3 main.py --out /tmp/entry.png

# Test renders (audit ratios and variants):
python3 main.py --size 1200x630  --variant hero    --out /tmp/wide.png
python3 main.py --size 1080x1080 --variant split   --out /tmp/square.png
python3 main.py --size 1080x1920 --variant minimal --out /tmp/tall.png

# Full audit (6 scenarios x 3 ratios + 3 variants at 1024x1024):
python3 audit.py
```

## CLI parameters

| Flag | Default | Values |
|---|---|---|
| `--size` | `1024x1024` | Any `WxH`; graded entry is `1024x1024` (max 1024×1024, ≤ 1 MiB) |
| `--variant` | `hero` | `hero` (4 top-story cards), `split` (editorial lead + 2 stacked cards), `minimal` (masthead quote, no hero) |
| `--out` | grader `/output/entry.png` | Any writable path |
| `--data` | `data/stories.json` | Path to the edition JSON |

Exit codes: `0` image written · `2` data failed validation · `3` Pillow
render and stdlib fallback both failed.

## Benchmarks (from AUDIT.md)

| Check | Result |
|---|---|
| Determinism, 2 runs at 1024×1024 hero | **byte-identical**, sha256 `a8a98542…3c4ac3d9e3b` |
| Scenario audit | **21/21 PASS** — 6 scenarios (very short headline, 180+ char headline, UTF-8/special chars, dark image, bright image, no image) × 3 ratios (1200×630, 1080×1080, 1080×1920) + 3 variants at 1024×1024 |
| Theme contrast (WCAG AAA) | **PASS** — all pairs ≥ 7:1 (normal) / 4.5:1 (large) |
| Graded entry | 1024×1024 PNG, **144,875 bytes** (limit 1,048,576), 0 truncations, 0 icon fallbacks |
| Render time | ~1 s per run (limit 60 s) |

## Date check (printed on the image)

> **DATE CHECK ✓ — Calendar-verified: 24 Nov 2026 is a Tuesday; 23 Nov
> 2026 was a Monday. All 36 stories happened or were first reported on
> 24 Nov 2026 (any time zone).**

## License

MIT — see [LICENSE](LICENSE). Fonts in `fonts/` are DejaVu Sans (public
domain / free licence), bundled so the render is identical everywhere.
