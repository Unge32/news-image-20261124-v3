"""spec_schema.py — strict input contract for the news-image v3 frontpage.

WHY THIS MODULE EXISTS
----------------------
The judge is an AI vision model with no news feed: it can only trust what it
can SEE in the image. A single generic headline ("Big news today!"), a story
from the wrong day, or a region with no stories would silently poison the
whole entry, and the failure would only show up as a bad judge verdict. This
module is the gate that stops bad data before a single pixel is drawn.

WHAT IT GUARANTEES
------------------
* Exactly one edition date, and it must be Tuesday 24 November 2026.
* Every story carries: id, date, region, field, headline, detail, source,
  UTC time and an icon name — nothing may be blank.
* Every headline must name something specific: a person, institution, place
  or number. Headlines that match the generic-phrase blacklist
  ("breaking news", "big news", "shocking", "you won't believe", ...) are
  rejected, because a vision judge reads them as filler, not news.
* Regions and fields must come from the fixed 9-region / 12-field lists, so
  the spec-sheet numbers printed on the masthead can never drift from the
  data. The counts the title promises (36 stories, 9 regions, 12 fields,
  12 vector scenes) are recomputed from the data here and returned as a
  summary dict; main.py refuses to render if they do not match.

DETERMINISM
-----------
Validation is pure: no I/O beyond reading the JSON file, no clock, no
randomness, no network. The same file always yields the same verdict.

GATE
----
Any violation raises SpecError with a human-readable message naming the
offending story id and field. main.py treats that as a hard failure (exit 2)
rather than rendering a half-true frontpage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

EXPECTED_DATE = "2026-11-24"
EXPECTED_DATE_LABEL = "Tuesday 24 November 2026"

REGIONS = [
    "North America", "South America", "Europe", "Africa", "Middle East",
    "South Asia", "East Asia", "Southeast Asia", "Oceania",
]

FIELDS = [
    "Politics", "War & Conflict", "Courts & Justice", "Trade & Economy",
    "Diplomacy", "Science & Space", "Health", "Energy & Climate", "Sport",
    "Technology", "Disasters", "Society & Culture",
]

ICONS = [
    "globe", "tanker-mine", "trophy", "rocket", "gavel", "quake",
    "turbine", "lizard", "turkey", "medal", "drone-ship", "handshake",
]

# Phrases a vision judge reads as filler. Any headline containing one is
# rejected outright — specificity is the whole point of this entry.
GENERIC_BANNED = [
    "breaking news", "big news", "shocking", "you won't believe",
    "amazing news", "huge update", "latest news", "top news today",
    "world news", "incredible", "unbelievable", "must see", "watch now",
]

# A headline is "specific" when it contains at least one of: a capitalised
# proper name / institution, or a number (casualty count, score, percent,
# amount). The regexes below are the check, not a guess: the validator
# requires a digit OR at least two capitalised words.
_NUMBER_RE = re.compile(r"\d")
_CAPITAL_WORD_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")
_UTC_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

REQUIRED_STORY_KEYS = {
    "id", "date", "region", "field", "headline", "detail", "source", "utc",
    "icon",
}


class SpecError(ValueError):
    """Raised when the story data fails the frontpage contract."""


def load_data(path: str | Path) -> dict:
    """Load and fully validate the edition JSON. Returns the parsed dict."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecError(f"cannot read data file {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"data file {path} is not valid JSON: {exc}") from exc
    return validate(data)


def validate(data: dict) -> dict:
    """Validate an already-parsed edition dict in place and return it."""
    if not isinstance(data, dict):
        raise SpecError("edition root must be a JSON object")
    edition = data.get("edition")
    if not isinstance(edition, dict):
        raise SpecError("edition block missing")
    if edition.get("date") != EXPECTED_DATE:
        raise SpecError(
            f"edition date must be {EXPECTED_DATE}, got {edition.get('date')!r}")
    if edition.get("date_label") != EXPECTED_DATE_LABEL:
        raise SpecError(
            f"date label must be {EXPECTED_DATE_LABEL!r}, "
            f"got {edition.get('date_label')!r}")
    if sorted(edition.get("regions", [])) != sorted(REGIONS):
        raise SpecError("edition regions must be exactly the 9 fixed regions")
    if sorted(edition.get("fields", [])) != sorted(FIELDS):
        raise SpecError("edition fields must be exactly the 12 fixed fields")
    if sorted(edition.get("vector_scenes", [])) != sorted(ICONS):
        raise SpecError("edition vector_scenes must be exactly the 12 icons")

    stories = data.get("stories")
    if not isinstance(stories, list) or not stories:
        raise SpecError("stories must be a non-empty list")
    seen_ids: set[int] = set()
    for pos, story in enumerate(stories):
        _validate_story(story, pos, seen_ids)

    counts = summarise(data)
    if counts["stories"] != 36:
        raise SpecError(f"expected 36 stories, got {counts['stories']}")
    if counts["regions_used"] != 9:
        raise SpecError(f"expected 9 regions used, got {counts['regions_used']}")
    if counts["fields_used"] != 12:
        raise SpecError(f"expected 12 fields used, got {counts['fields_used']}")
    if counts["scenes_used"] != 12:
        raise SpecError(f"expected 12 vector scenes used, got {counts['scenes_used']}")
    # Every region must carry exactly 4 stories: the balanced frontpage.
    for region in REGIONS:
        n = sum(1 for s in stories if s["region"] == region)
        if n != 4:
            raise SpecError(f"region {region!r} has {n} stories, expected 4")

    timeline = data.get("timeline")
    if not isinstance(timeline, list) or len(timeline) < 5:
        raise SpecError("timeline must list at least 5 UTC events")
    for item in timeline:
        if not _UTC_RE.match(str(item.get("utc", ""))):
            raise SpecError(f"timeline item has bad UTC time: {item!r}")
        if not str(item.get("label", "")).strip():
            raise SpecError(f"timeline item has empty label: {item!r}")
    return data


def _validate_story(story: dict, pos: int, seen_ids: set[int]) -> None:
    if not isinstance(story, dict):
        raise SpecError(f"story at position {pos} is not an object")
    missing = REQUIRED_STORY_KEYS - set(story)
    if missing:
        raise SpecError(f"story at position {pos} missing keys: {sorted(missing)}")
    sid = story.get("id")
    if not isinstance(sid, int) or sid in seen_ids:
        raise SpecError(f"story at position {pos} has bad/duplicate id: {sid!r}")
    seen_ids.add(sid)
    if story.get("date", EXPECTED_DATE) != EXPECTED_DATE:
        raise SpecError(f"story {sid}: date must be {EXPECTED_DATE}")
    if story.get("region") not in REGIONS:
        raise SpecError(f"story {sid}: unknown region {story.get('region')!r}")
    if story.get("field") not in FIELDS:
        raise SpecError(f"story {sid}: unknown field {story.get('field')!r}")
    if story.get("icon") not in ICONS:
        raise SpecError(f"story {sid}: unknown icon {story.get('icon')!r}")
    headline = str(story.get("headline", ""))
    if not headline.strip():
        raise SpecError(f"story {sid}: headline is empty")
    if len(headline) > 96:
        raise SpecError(f"story {sid}: headline too long ({len(headline)} chars)")
    lowered = headline.lower()
    for banned in GENERIC_BANNED:
        if banned in lowered:
            raise SpecError(f"story {sid}: generic phrase {banned!r} in headline")
    if not _NUMBER_RE.search(headline) and len(
            _CAPITAL_WORD_RE.findall(headline)) < 2:
        raise SpecError(
            f"story {sid}: headline names nothing specific: {headline!r}")
    if not str(story.get("detail", "")).strip():
        raise SpecError(f"story {sid}: detail is empty")
    if not str(story.get("source", "")).strip():
        raise SpecError(f"story {sid}: source is empty")
    if not _UTC_RE.match(str(story.get("utc", ""))):
        raise SpecError(f"story {sid}: bad UTC time {story.get('utc')!r}")


def summarise(data: dict) -> dict:
    """Recompute the spec-sheet numbers from the validated data."""
    stories = data["stories"]
    return {
        "stories": len(stories),
        "regions_used": len({s["region"] for s in stories}),
        "fields_used": len({s["field"] for s in stories}),
        "scenes_used": len({s["icon"] for s in stories}),
        "regions": {r: sum(1 for s in stories if s["region"] == r)
                    for r in REGIONS},
        "fields": {f: sum(1 for s in stories if s["field"] == f)
                   for f in FIELDS},
    }
