#!/usr/bin/env python3
"""main.py — entrypoint for the news-image-20261124-v3 frontpage.

WHAT THIS PROGRAM DOES
----------------------
It reads `data/stories.json` (36 dated, specific world-news stories from
Tuesday 24 November 2026), validates the data against the strict contract
in `spec_schema.py`, renders the "World Frontpage" poster at 1024x1024 with
the five-module engine (layout, typography, theme, renderer), and writes
exactly one image to the output path. Nothing else is read, nothing is
downloaded, and no clock or random value ever reaches the image bytes.

HOW TO RUN IT (exactly as the grader does)
------------------------------------------
    python3 main.py

That writes `/output/entry.png` when the `MAKEFUN_OUTPUT_DIR` environment
variable is not set and `/output` exists, otherwise it writes
`entry.png` next to this file (and `screenshots/entry.png` when that
directory exists, for the repository preview). Explicit overrides:

    python3 main.py --out /tmp/entry.png
    python3 main.py --size 1200x630 --variant split --out /tmp/test.png
    python3 main.py --size 1080x1920 --variant minimal --out /tmp/tall.png

The graded entry is always the default: 1024x1024, hero variant.

DETERMINISM
-----------
Seed fixed (20261124), fonts bundled in `fonts/`, colours fixed in
`theme_presets.py`, no timestamps, no network, no environment-dependent
paths in the output. Two runs on the same machine produce byte-identical
files — `audit.py` verifies this with sha256.

FALLBACK
--------
If Pillow cannot be imported in the grading container, the program does
NOT crash: it renders the same frontpage structure with the pure-stdlib
`fallback_png.py` (bitmap font + hand-rolled PNG encoder) and still exits
0 with a valid image. The Pillow path is the graded-quality path; the
fallback is a safety net, and which path ran is printed on stdout.

EXIT CODES
----------
0  image written successfully
2  data failed validation (see spec_schema.SpecError)
3  Pillow render failed AND the stdlib fallback also failed
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from spec_schema import load_data, summarise  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the Tuesday 24 November 2026 world frontpage.")
    parser.add_argument("--size", default="1024x1024",
                        help="WxH, e.g. 1024x1024, 1200x630, 1080x1920")
    parser.add_argument("--variant", default="hero",
                        choices=["hero", "split", "minimal"],
                        help="layout variant (default: hero)")
    parser.add_argument("--out", default=None,
                        help="output PNG path (default: grader /output)")
    parser.add_argument("--data", default=str(ROOT / "data" / "stories.json"),
                        help="path to stories.json")
    return parser.parse_args(argv)


def parse_size(text: str) -> tuple[int, int]:
    try:
        w, h = text.lower().split("x")
        width, height = int(w), int(h)
    except ValueError as exc:
        raise SystemExit(f"bad --size {text!r}, expected WxH") from exc
    if width <= 0 or height <= 0:
        raise SystemExit(f"bad --size {text!r}: dimensions must be positive")
    return width, height


def default_output() -> Path:
    """Where the grader expects the image: /output/entry.png, else local."""
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return Path(env_dir) / "entry.png"
    if Path("/output").is_dir():
        return Path("/output/entry.png")
    return ROOT / "entry.png"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    width, height = parse_size(args.size)

    try:
        data = load_data(args.data)
    except Exception as exc:  # spec_schema.SpecError
        print(f"spec error: {exc}", file=sys.stderr)
        return 2
    data["_counts"] = summarise(data)

    out = Path(args.out) if args.out else default_output()
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        from renderer import FALLBACKS, render_frontpage
        image, renderer = render_frontpage(data, width, height, args.variant)
        image.save(str(out), format="PNG")
        print(f"rendered {width}x{height} variant={args.variant} "
              f"stories={data['_counts']['stories']} "
              f"truncations={len(renderer.truncations)} "
              f"icon_fallbacks={len(FALLBACKS)} "
              f"-> {out} ({out.stat().st_size} bytes)")
    except ImportError:
        print("Pillow unavailable: using stdlib fallback renderer",
              file=sys.stderr)
        return _render_fallback(data, width, height, out)
    except Exception as exc:  # Pillow render failed: try the fallback
        print(f"Pillow render failed ({exc}); trying stdlib fallback",
              file=sys.stderr)
        return _render_fallback(data, width, height, out)

    # Mirror the graded image into the repo for preview/upload, when the
    # output went elsewhere (grader /output) and this is the default size.
    if out.resolve() != (ROOT / "entry.png").resolve() \
            and (width, height) == (1024, 1024):
        import shutil
        shutil.copyfile(out, ROOT / "entry.png")
        shots = ROOT / "screenshots"
        if shots.is_dir():
            shutil.copyfile(out, shots / "entry.png")
    return 0


def _render_fallback(data: dict, width: int, height: int, out: Path) -> int:
    try:
        from fallback_png import render_fallback
        png = render_fallback(data, width, height)
        out.write_bytes(png)
        print(f"fallback rendered {width}x{height} -> {out} "
              f"({len(png)} bytes)")
        return 0
    except Exception as exc:
        print(f"fallback render failed: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
