"""The scene layer of slidecast: one slide's filters, with the entrances.

Every element and bullet enters over 0.5 seconds at its own time: the
alpha ramps from 0 to 1, and the element slides 80 units from the right.
The layout speaks in grid cells, 12 columns by 6 rows over the canvas.
The filters are strings for the render module, so the tests can examine
a whole slide without a render.
"""

from __future__ import annotations

from .render import FONT_BOLD, FONT_BOOK, INK, ACCENT, TRACK, _esc

COLS = 12
ROWS = 6
MARGIN_X = 120
MARGIN_Y = 200
CELL_W = 140
CELL_H = 133
ENTER = 0.5
SLIDE_IN = 80
BULLET_START = 0.5
BULLET_STAGGER = 0.7


class SceneError(Exception):
    """One element cannot sit on the grid."""


def cell_x(col: int) -> int:
    """Give the left edge of one grid column."""
    return MARGIN_X + (col - 1) * CELL_W


def cell_y(row: int) -> int:
    """Give the top edge of one grid row."""
    return MARGIN_Y + (row - 1) * CELL_H


def _n(text) -> str:
    """Quote one drawtext argument for the filtergraph."""
    return f"'{_esc(str(text))}'"


def _expr(text) -> str:
    """Quote one expression argument, with the commas escaped."""
    return "'" + _esc(str(text)).replace(",", "\\,") + "'"


def entrance(x: int, at: float) -> str:
    """Give the entrance options of one drawtext element at its place."""
    return (
        f"alpha={_expr(f'(t-{at})/{ENTER}')}"
        f":x={_expr(f'{x}+{SLIDE_IN}*max(0,1-(t-{at})/{ENTER})')}"
    )


def _text_filter(text: str, x: int, y: int, size: int, at: float,
                 color: str = INK, font: str = None) -> str:
    """Give one animated drawtext filter."""
    fontfile = font or FONT_BOOK
    return (
        f"drawtext=fontfile={fontfile}:text={_n(text)}"
        f":expansion=none:fontcolor={color}:fontsize={size}"
        f":{entrance(x, at)}"
        f":y={y}"
        f":enable={_expr(f'gte(t,{at})')}"
    )


def stat_filter(element) -> str:
    """Give the filters of one stat: the big value over its label."""
    x = cell_x(element["col"])
    y = cell_y(element["row"])
    at = element["at"]
    value = _text_filter(
        element["value"], x, y, 96, at, color=ACCENT, font=FONT_BOLD
    )
    label = _text_filter(element["label"], x, y + 110, 34, at + ENTER)
    return f"{value},{label}"


def box_filter(element) -> str:
    """Give the filters of one diagram box: the frame and its label."""
    x = cell_x(element["col"])
    y = cell_y(element["row"])
    at = element["at"]
    frame = (
        f"drawbox=x={x}:y={y}:w=270:h=100:color={ACCENT}:t=6"
        f":enable={_expr(f'gte(t,{at})')}"
    )
    label = _text_filter(element["label"], x + 20, y + 30, 34, at + 0.15)
    return f"{frame},{label}"


def arrow_filter(element) -> str:
    """Give the filters of one connector between two cell centers."""
    c1, r1 = element["from"]
    c2, r2 = element["to"]
    at = element["at"]
    x1, y1 = cell_x(c1) + 135, cell_y(r1) + 85
    x2, y2 = cell_x(c2) + 135, cell_y(r2) + 85
    hold = f"enable={_expr(f'gte(t,{at})')}"
    head_x, head_y, glyph = x2, y2, "►"
    if r1 == r2:
        seg = (
            f"drawbox=x={min(x1, x2)}:y={y1 - 3}:w={abs(x2 - x1)}:h=6"
            f":color={INK}:t=fill:{hold}"
        )
        head_x = x2 - 34 if x2 > x1 else x2 + 10
        head_y = y2 - 20
        glyph = "►" if x2 > x1 else "◄"
    elif c1 == c2:
        seg = (
            f"drawbox=x={x1 - 3}:y={min(y1, y2)}:w=6:h={abs(y2 - y1)}"
            f":color={INK}:t=fill:{hold}"
        )
        head_x, head_y, glyph = x1 - 22, y2 - 45, "▼"
    else:
        mid_y = y1
        seg = (
            f"drawbox=x={min(x1, x2)}:y={mid_y - 3}:w={abs(x2 - x1)}:h=6"
            f":color={INK}:t=fill:{hold},"
            f"drawbox=x={x2 - 3}:y={min(y1, y2)}:w=6:h={abs(y2 - y1)}"
            f":color={INK}:t=fill:{hold}"
        )
    head = _text_filter(glyph, head_x, head_y, 40, at + 0.1, color=INK)
    return f"{seg},{head}"


def bar_filter(element) -> str:
    """Give the filters of one bar: the track, the stepped fill, the label."""
    x = cell_x(element["col"])
    y = cell_y(element["row"])
    at = element["at"]
    share = element["share"]
    track = (
        f"drawbox=x={x}:y={y}:w=520:h=46:color={TRACK}:t=8"
        f":enable={_expr(f'gte(t,{at})')}"
    )
    filled = int(share * 10 + 0.5)
    segments = [
        f"drawbox=x={x + 4 + i * 52}:y={y + 4}:w=48:h=38:color={ACCENT}"
        f":t=fill:enable={_expr(f'gte(t,{at} + {i * 0.12})')}"
        for i in range(filled)
    ]
    label = _text_filter(element["label"], x, y - 50, 34, at)
    parts = [track, *segments, label]
    return ",".join(parts)


def bullet_filter(text: str, y: int, at: float) -> str:
    """Give one animated bullet line."""
    return _text_filter(f"- {text}", 180, y, 44, at)


REQUIRED = {
    "stat": ("value", "label"),
    "box": ("label",),
    "arrow": (),
    "bar": ("label",),
}

KINDS = {
    "stat": stat_filter,
    "box": box_filter,
    "arrow": arrow_filter,
    "bar": bar_filter,
}


def slide_filters(heading: str, bullets: list[str], elements: list[dict]) -> list[str]:
    """Give every filter of one slide, in draw order.

    The heading enters first. With elements, each element enters at its own
    time and the bullets follow the last element. Without elements, the
    bullets stagger from 0.5 seconds on.
    """
    filters = [_text_filter(heading, 140, 170, 64, 0.0, color=ACCENT, font=FONT_BOLD)]
    if elements:
        last = 0.0
        for element in elements:
            filters.append(KINDS[element["kind"]](element))
            end = element["at"] + (1.1 if element["kind"] == "bar" else ENTER)
            last = max(last, end)
        start = last + 0.7
    else:
        start = BULLET_START
    for number, line in enumerate(bullets):
        filters.append(
            bullet_filter(line, 330 + number * 90, start + number * BULLET_STAGGER)
        )
    return filters
