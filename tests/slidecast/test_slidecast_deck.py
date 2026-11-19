"""The deck loader's tests: the shapes it accepts, and the ones it refuses."""

import json
from pathlib import Path

import pytest

from slidecast import deck


def a_deck(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def good_data():
    return {
        "title": "Northgate Library",
        "subtitle": "business setup",
        "slides": [
            {"heading": f"Slide {n}", "bullets": ["one"], "narration": f"Words {n}."}
            for n in range(4)
        ],
    }


def test_load_reads_a_good_deck(tmp_path):
    loaded = deck.load(a_deck(tmp_path, good_data()))
    assert loaded.title == "Northgate Library"
    assert [s.heading for s in loaded.slides] == ["Slide 0", "Slide 1", "Slide 2", "Slide 3"]
    assert loaded.slides[0].bullets == ["one"]


def test_load_names_a_missing_file(tmp_path):
    with pytest.raises(deck.DeckError, match="no deck"):
        deck.load(tmp_path / "absent.json")


def test_load_refuses_non_json(tmp_path):
    path = tmp_path / "deck.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(deck.DeckError, match="not JSON"):
        deck.load(path)


@pytest.mark.parametrize("key", ["title", "subtitle", "slides"])
def test_load_refuses_a_missing_top_key(tmp_path, key):
    data = good_data()
    del data[key]
    with pytest.raises(deck.DeckError, match=key):
        deck.load(a_deck(tmp_path, data))


def test_load_refuses_a_slide_without_narration(tmp_path):
    data = good_data()
    data["slides"][1]["narration"] = "  "
    with pytest.raises(deck.DeckError, match="narration"):
        deck.load(a_deck(tmp_path, data))


def test_load_refuses_more_than_five_bullets(tmp_path):
    data = good_data()
    data["slides"][0]["bullets"] = [str(n) for n in range(6)]
    with pytest.raises(deck.DeckError, match="bullets"):
        deck.load(a_deck(tmp_path, data))


def test_load_refuses_fewer_than_three_slides(tmp_path):
    data = good_data()
    data["slides"] = data["slides"][:2]
    with pytest.raises(deck.DeckError, match="fewer than 3"):
        deck.load(a_deck(tmp_path, data))


def test_load_refuses_a_slide_that_is_not_an_object(tmp_path):
    data = good_data()
    data["slides"][1] = 5
    with pytest.raises(deck.DeckError, match="not an object"):
        deck.load(a_deck(tmp_path, data))
