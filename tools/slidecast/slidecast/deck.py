"""The deck model of slidecast: one JSON file per video.

A deck carries a title slide and three or more content slides. Each content
slide carries a heading, optional bullet lines, and the narration paragraph
the voice reads. The narration drives the slide duration, so one slide of
about 25 spoken words runs about ten seconds.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from . import scenes


class DeckError(Exception):
    """A deck is absent, malformed, or carries too little to narrate."""


@dataclass(frozen=True)
class Slide:
    """One content slide: its heading, its bullets, its narration, and its
    scene elements."""

    heading: str
    bullets: list[str]
    narration: str
    elements: tuple[dict, ...] = ()


@dataclass(frozen=True)
class Deck:
    """One deck: the video title, the subtitle, and its slides in order."""

    title: str
    subtitle: str
    slides: list[Slide]


def cells_of(kind: str, one: dict) -> list[tuple]:
    """Give the grid cells one element kind sits on. The caller checks the
    kind first, so the arrow cells are the fall-through."""
    if kind in ("stat", "box", "bar"):
        return [(one.get("col"), one.get("row"))]
    return [tuple(one.get("from", ())), tuple(one.get("to", ()))]


def element_from(one: object, number: int, path: Path) -> dict:
    """Examine one scene element, and give the dict the scenes read."""
    if not isinstance(one, dict):
        raise DeckError(f"element {number} is not an object")
    kind = one.get("kind")
    if kind not in scenes.KINDS:
        raise DeckError(
            f"slide {number} of {path} carries the unknown element kind {kind!r}"
        )
    at = one.get("at")
    if type(at) not in (int, float) or not math.isfinite(at) or at < 0:
        raise DeckError(f"slide {number} of {path} carries an element without a time")
    check_required(kind, one, number, path)
    for col, row in cells_of(kind, one):
        if type(col) is not int or not 1 <= col <= scenes.COLS:
            raise DeckError(
                f"slide {number} of {path} puts an element outside the grid"
            )
        if type(row) is not int or not 1 <= row <= scenes.ROWS:
            raise DeckError(
                f"slide {number} of {path} puts an element outside the grid"
            )
    check_share(kind, one, number, path)
    return dict(one)


def check_required(kind: str, one: dict, number: int, path: Path) -> None:
    """Refuse an element whose text keys the kind needs are missing."""
    for key in scenes.REQUIRED[kind]:
        value = one.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DeckError(
                f"slide {number} of {path} carries an element without '{key}'"
            )


def check_share(kind: str, one: dict, number: int, path: Path) -> None:
    """Refuse a bar whose share sits outside 0 to 1."""
    if kind != "bar":
        return
    share = one.get("share")
    in_range = type(share) in (int, float) and math.isfinite(share) and 0 <= share <= 1
    if not in_range:
        raise DeckError(f"slide {number} of {path} carries a share outside 0 to 1")


def slide_from(one: object, number: int, path: Path) -> Slide:
    """Examine one slide object, and give the Slide it carries."""
    if not isinstance(one, dict):
        raise DeckError(f"slide {number} of {path} is not an object")
    for key in ("heading", "narration"):
        if not isinstance(one.get(key), str) or not one[key].strip():
            raise DeckError(f"slide {number} of {path} lacks '{key}'")
    bullets = one.get("bullets", [])
    if not isinstance(bullets, list) or len(bullets) > 5:
        raise DeckError(f"slide {number} of {path} carries more than 5 bullets")
    raw_elements = one.get("elements", [])
    if not isinstance(raw_elements, list):
        raise DeckError(
            f"slide {number} of {path} carries elements that are not a list"
        )
    elements = tuple(
        element_from(one_element, number, path) for one_element in raw_elements
    )
    return Slide(
        heading=one["heading"],
        bullets=[str(line) for line in bullets],
        narration=one["narration"].strip(),
        elements=elements,
    )


def load(path: Path) -> Deck:
    """Read one deck JSON file, and refuse one the narrator cannot run."""
    if not path.is_file():
        raise DeckError(f"no deck at {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DeckError(f"the deck at {path} is not JSON: {error}") from error
    for key in ("title", "subtitle", "slides"):
        if key not in data:
            raise DeckError(f"the deck at {path} lacks the key '{key}'")
    slides = [
        slide_from(one, number, path)
        for number, one in enumerate(data["slides"], start=1)
    ]
    if len(slides) < 3:
        raise DeckError(f"the deck at {path} carries fewer than 3 slides")
    return Deck(title=data["title"], subtitle=data["subtitle"], slides=slides)
