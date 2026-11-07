"""The allowed-author list: path, load, and shape validation."""

import json
from pathlib import Path

# Module-relative, so a worktree cwd cannot break the resolution.
AUTHORS_PATH = Path(__file__).absolute().parent / "authors.json"

REQUIRED_KEY = "allowed_authors"


class AuthorsError(Exception):
    """The authors config is missing, unparsable, or the wrong shape."""


def load_authors(path=None):
    """Return the validated raw string list of allowed authors.

    The predicate lowercases both sides, so the loader keeps the raw
    strings. Extra top-level keys stay ignored, and an empty list is a
    valid shape that refuses everyone.
    """
    target = Path(path or AUTHORS_PATH)
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuthorsError(
            f"cannot read the authors config at {target}: {exc}"
        ) from exc
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise AuthorsError(
            f"the authors config at {target} does not parse"
        ) from exc
    if not isinstance(data, dict) or REQUIRED_KEY not in data:
        raise AuthorsError(
            f"the authors config at {target} needs the key {REQUIRED_KEY}"
        )
    names = data[REQUIRED_KEY]
    if not isinstance(names, list) or not all(
        isinstance(name, str) for name in names
    ):
        raise AuthorsError(
            f"the authors config at {target} needs a list of strings"
        )
    return names
