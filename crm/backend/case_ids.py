"""The case id series: the next id derives from the ids the database
holds. The scan reads only ids in the series shape, so an evaluation
copy's suffix sits out, and an empty database starts the engine's own
prefix."""

import re

_ID = re.compile(r"^(?P<prefix>[A-Za-z]+)-(?P<number>\d+)$")

FALLBACK = "C-1"


def next_case_id(case_ids: list[str]) -> str:
    """Return the next id in the series: the prefix of the highest existing
    id and the number after it. An id outside the series shape (an
    evaluation copy's `-E7` suffix, a hand-inserted row) sits out of the
    scan. An empty list starts the engine's own `C-1`."""
    best: tuple[str, int] | None = None
    for case_id in case_ids:
        match = _ID.match(case_id)
        if match:
            pair = (match["prefix"], int(match["number"]))
            if best is None or pair > best:
                best = pair
    if best is None:
        return FALLBACK
    return f"{best[0]}-{best[1] + 1}"
