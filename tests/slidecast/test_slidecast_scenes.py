# The scene filters, regenerated from the live builders.

import json
from pathlib import Path

import pytest

from slidecast import build, deck, scenes

STAT_FILTER = "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='14':expansion=none:fontcolor=0x2BD9A4:fontsize=96:alpha='(t-1.0)/0.5':x='120+80*max(0\\,1-(t-1.0)/0.5)':y=200:enable='gte(t\\,1.0)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='days':expansion=none:fontcolor=0xE8EDF2:fontsize=34:alpha='(t-1.5)/0.5':x='120+80*max(0\\,1-(t-1.5)/0.5)':y=310:enable='gte(t\\,1.5)'"

BOX_FILTER = "drawbox=x=260:y=333:w=270:h=100:color=0x2BD9A4:t=6:enable='gte(t\\,1.5)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Queue':expansion=none:fontcolor=0xE8EDF2:fontsize=34:alpha='(t-1.65)/0.5':x='280+80*max(0\\,1-(t-1.65)/0.5)':y=363:enable='gte(t\\,1.65)'"

ARROW_FILTER = "drawbox=x=395:y=415:w=420:h=6:color=0xE8EDF2:t=fill:enable='gte(t\\,3.0)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='►':expansion=none:fontcolor=0xE8EDF2:fontsize=40:alpha='(t-3.1)/0.5':x='781+80*max(0\\,1-(t-3.1)/0.5)':y=398:enable='gte(t\\,3.1)'"

VARROW_FILTER = "drawbox=x=392:y=418:w=6:h=266:color=0xE8EDF2:t=fill:enable='gte(t\\,3.0)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='▼':expansion=none:fontcolor=0xE8EDF2:fontsize=40:alpha='(t-3.1)/0.5':x='373+80*max(0\\,1-(t-3.1)/0.5)':y=639:enable='gte(t\\,3.1)'"

BULLET_FILTER = "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='- one free copy':expansion=none:fontcolor=0xE8EDF2:fontsize=44:alpha='(t-0.5)/0.5':x='180+80*max(0\\,1-(t-0.5)/0.5)':y=330:enable='gte(t\\,0.5)'"


def test_cell_math_places_the_grid():
    assert scenes.cell_x(1) == 120
    assert scenes.cell_x(12) == 1660
    assert scenes.cell_y(1) == 200
    assert scenes.cell_y(6) == 865


def test_a_stat_carries_the_value_and_the_label():
    element = {"kind": "stat", "at": 1.0, "col": 1, "row": 1,
               "value": "14", "label": "days"}
    assert scenes.stat_filter(element) == STAT_FILTER


def test_a_box_carries_the_frame_and_the_label():
    element = {"kind": "box", "at": 1.5, "col": 2, "row": 2, "label": "Queue"}
    assert scenes.box_filter(element) == BOX_FILTER


def test_a_row_arrow_points_right():
    element = {"kind": "arrow", "at": 3.0, "from": [2, 2], "to": [5, 2]}
    assert scenes.arrow_filter(element) == ARROW_FILTER


def test_a_column_arrow_points_down():
    element = {"kind": "arrow", "at": 3.0, "from": [2, 2], "to": [2, 4]}
    assert scenes.arrow_filter(element) == VARROW_FILTER


def test_a_bullet_enters_with_the_slide_in():
    assert scenes.bullet_filter("one free copy", 330, 0.5) == BULLET_FILTER


def test_bullets_stagger_without_elements():
    filters = scenes.slide_filters("Heading", ["a", "b", "c"], [])
    joined = "\n".join(filters)
    assert "gte(t\\,0.5)" in joined
    assert "gte(t\\,1.2)" in joined
    assert "gte(t\\,1.9)" in joined


def test_elements_enter_at_their_times_and_bullets_follow():
    elements = [
        {"kind": "box", "at": 1.5, "col": 2, "row": 2, "label": "Queue"},
        {"kind": "box", "at": 2.5, "col": 5, "row": 2, "label": "Agent"},
    ]
    filters = scenes.slide_filters("Heading", ["one"], elements)
    joined = "\n".join(filters)
    assert "gte(t\\,1.5)" in joined
    assert "gte(t\\,2.5)" in joined
    assert "gte(t\\,3.7)" in joined  # the bullet follows the last entrance
    assert filters[0].startswith("drawtext=")  # the heading draws first


def test_bar_fills_ten_steps_for_a_full_share():
    element = {"kind": "bar", "at": 2.0, "col": 1, "row": 5,
               "label": "accuracy", "share": 1.0}
    joined = scenes.bar_filter(element)
    assert "gte(t\\,2.0 + 1.08)" in joined  # the tenth segment
    assert "gte(t\\,2.0 + 1.2)" not in joined


def a_deck_with_elements(tmp_path: Path) -> Path:
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {
                "heading": "H", "narration": "N.", "bullets": [],
                "elements": [
                    {"kind": "box", "at": 1.0, "col": 2, "row": 2, "label": "Q"},
                    {"kind": "bar", "at": 2.0, "col": 1, "row": 5,
                     "label": "accuracy", "share": 0.8},
                ],
            }
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_the_loader_carries_elements(tmp_path):
    loaded = deck.load(a_deck_with_elements(tmp_path))
    assert loaded.slides[0].elements[0]["label"] == "Q"
    assert loaded.slides[0].elements[1]["share"] == 0.8


@pytest.mark.parametrize(
    ("element", "message"),
    [
        ({"kind": "chart", "at": 1.0}, "carries the unknown element kind"),
        ({"kind": "box", "at": 1.0, "col": 2, "row": 2}, "without 'label'"),
        ({"kind": "stat", "at": 1.0, "col": 1, "row": 1, "value": "1"}, "without 'label'"),
        ({"kind": "bar", "at": 1.0, "col": 1, "row": 5, "label": "x"}, "outside 0 to 1"),
        ({"kind": "arrow", "at": 1.0, "from": [1, 1], "to": [13, 1]}, "outside the grid"),
        (5, "is not an object"),
        ({"kind": "box", "col": 2, "row": 2, "label": "Q"}, "without a time"),
        ({"kind": "box", "at": 1.0, "col": 13, "row": 2, "label": "Q"}, "outside the grid"),
        ({"kind": "box", "at": 1.0, "col": 2, "row": 7, "label": "Q"}, "outside the grid"),
        ({"kind": "arrow", "at": 1.0, "from": [1, 1], "to": [13, 1]}, "outside the grid"),
        ({"kind": "bar", "at": 1.0, "col": 1, "row": 5, "label": "x", "share": 1.5}, "outside 0 to 1"),
    ],
)
def test_the_loader_refuses_bad_elements(tmp_path, element, message):
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {"heading": "H", "narration": "N.", "bullets": [], "elements": [element]}
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(deck.DeckError, match=message):
        deck.load(path)


def test_clips_of_join_the_scenes_for_content_slides(tmp_path):
    slides = [
        deck.Slide("Title", [], "Hello."),
        deck.Slide("Queue", ["one"], "Words two.",
                   ({"kind": "box", "at": 1.0, "col": 2, "row": 2, "label": "Q"},)),
    ]
    the_deck = deck.Deck(title="T", subtitle="S", slides=slides)
    timings = build.clips_of(the_deck, Path("W"), [5.0, 6.0])
    assert timings[0].filters == ""
    assert "drawbox=x=260" in timings[1].filters


def test_clip_steps_carry_the_scene_filters():
    slides = [
        deck.Slide("Title", [], "Hello."),
        deck.Slide("Queue", ["one"], "Words two.",
                   ({"kind": "box", "at": 1.0, "col": 2, "row": 2, "label": "Q"},)),
    ]
    the_deck = deck.Deck(title="T", subtitle="S", slides=slides)
    timings = build.clips_of(the_deck, Path("W"), [5.0, 6.0])
    steps = build.clip_steps(timings, Path("out.mp4"))
    joined = " ".join(steps[1].command)
    assert "-vf" in joined
    assert "drawbox=x=260" in joined


def test_speak_and_draw_draws_bare_backgrounds_for_content_slides(tmp_path):
    elements = ({"kind": "box", "at": 1.0, "col": 2, "row": 2, "label": "Q"},)
    slides = [
        deck.Slide("Title", [], "Hello."),
        deck.Slide("Queue", ["one"], "Words two.", elements),
        deck.Slide("H3", ["b"], "Words three."),
        deck.Slide("H4", ["b"], "Words four."),
    ]
    the_deck = deck.Deck(title="T", subtitle="S", slides=slides)
    steps = build.speak_and_draw(the_deck, Path("/tmp/w9"), "V")
    draw_one = " ".join(steps[3].command)
    assert "color=c=0x10202B" in draw_one
    assert "drawtext" not in draw_one


def test_a_diagonal_arrow_draws_an_elbow():
    element = {"kind": "arrow", "at": 3.0, "from": [2, 2], "to": [5, 4]}
    joined = scenes.arrow_filter(element)
    assert joined.count("drawbox") == 2
    assert "text='►'" in joined


def test_the_loader_refuses_elements_that_are_not_a_list(tmp_path):
    data = {
        "title": "T", "subtitle": "S",
        "slides": [{"heading": "H", "narration": "N.", "elements": 5}
                   for _ in range(3)],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(deck.DeckError, match="not a list"):
        deck.load(path)


def test_the_loader_refuses_a_negative_time(tmp_path):
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {"heading": "H", "narration": "N.", "bullets": [],
             "elements": [{"kind": "box", "at": -1, "col": 2, "row": 2, "label": "Q"}]}
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(deck.DeckError, match="without a time"):
        deck.load(path)


def test_the_loader_refuses_a_text_cell(tmp_path):
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {"heading": "H", "narration": "N.", "bullets": [],
             "elements": [{"kind": "arrow", "at": 1.0, "from": ["a", 1], "to": [2, 1]}]}
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(deck.DeckError, match="outside the grid"):
        deck.load(path)


def test_the_loader_takes_empty_elements(tmp_path):
    data = {
        "title": "T", "subtitle": "S",
        "slides": [{"heading": "H", "narration": "N.", "elements": []}
                   for _ in range(3)],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded = deck.load(path)
    assert loaded.slides[0].elements == ()


def test_a_left_arrow_points_left():
    element = {"kind": "arrow", "at": 3.0, "from": [5, 2], "to": [2, 2]}
    joined = scenes.arrow_filter(element)
    assert "text='◄'" in joined
    assert "x=395:y=415:w=420:h=6" in joined  # the segment spans the same run
    assert "x='405+80" in joined  # the head sits at the target end


def test_the_loader_refuses_a_zero_column(tmp_path):
    import json
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {"heading": "H", "narration": "N.", "bullets": [],
             "elements": [{"kind": "stat", "at": 1.0, "col": 0, "row": 1,
                           "value": "1", "label": "x"}]}
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(deck.DeckError, match="outside the grid"):
        deck.load(path)


def test_an_arrow_without_a_from_cell_raises(tmp_path):
    import json
    data = {
        "title": "T", "subtitle": "S",
        "slides": [
            {"heading": "H", "narration": "N.", "bullets": [],
             "elements": [{"kind": "arrow", "at": 1.0, "to": [2, 1]}]}
            for _ in range(3)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        deck.load(path)


def test_an_apostrophe_becomes_the_typographic_mark():
    element = {"kind": "box", "at": 1.0, "col": 2, "row": 2, "label": "the lead's sign-off"}
    joined = scenes.box_filter(element)
    # The escaped apostrophe keeps the quoted run intact, so the filter
    # count survives: one drawbox and one drawtext.
    assert joined.count("drawtext=") == 1
    assert "the lead’s sign-off" in joined
