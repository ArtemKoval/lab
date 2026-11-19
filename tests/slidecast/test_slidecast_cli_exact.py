"""Exact output assertions for the command line."""

import json
from pathlib import Path

from slidecast import build, cli, deck


def a_deck(tmp_path: Path) -> Path:
    data = {
        "title": "T",
        "subtitle": "S",
        "slides": [
            {"heading": f"S{n}", "bullets": ["x"], "narration": f"Line {n}."}
            for n in range(4)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_validate_prints_the_exact_line(tmp_path, capsys):
    deck_path = a_deck(tmp_path)
    assert cli.main(["validate", "--deck", str(deck_path)]) == 0
    assert capsys.readouterr().out == f"deck ok: 4 slides, {deck_path}\n"


def test_plan_prints_the_exact_lines(tmp_path, capsys):
    deck_path = a_deck(tmp_path)
    assert cli.main(["plan", "--deck", str(deck_path)]) == 0
    assert capsys.readouterr().out == (
        "slide 0: S0 (2 narration words)\n"
        "slide 1: S1 (2 narration words)\n"
        "slide 2: S2 (2 narration words)\n"
        "slide 3: S3 (2 narration words)\n"
    )


def test_build_prints_the_exact_line_and_the_default_voice(
    tmp_path, capsys, monkeypatch
):
    seen = {}

    def fake_orchestrate(deck, work, out, voice, run=None, probe=None, retries=0):
        seen["voice"] = voice
        return [
            build.Timing(0, work / "a", work / "i", work / "c", 1.0),
            build.Timing(1, work / "a", work / "i", work / "c", 2.0),
        ]

    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    out = tmp_path / "v.mp4"
    code = cli.main(["build", "--deck", str(a_deck(tmp_path)), "--out", str(out)])
    assert code == 0
    assert seen["voice"] == "en-US-AndrewNeural"
    assert capsys.readouterr().out == f"built {out}: 2 clips, 5.0 seconds\n"


def test_build_failure_prints_the_exact_line(tmp_path, capsys, monkeypatch):
    def boom():
        raise cli.render.RenderError("the build needs edge-tts on the PATH")

    monkeypatch.setattr(cli.render, "check_tools", boom)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    code = cli.main(
        ["build", "--deck", str(a_deck(tmp_path)), "--out", str(tmp_path / "v.mp4")]
    )
    assert code == 2
    assert (
        capsys.readouterr().err == "slidecast: the build needs edge-tts on the PATH\n"
    )


def test_validate_failure_prints_the_exact_line(tmp_path, capsys):
    path = tmp_path / "deck.json"
    path.write_text("not json", encoding="utf-8")
    code = cli.main(["validate", "--deck", str(path)])
    assert code == 2
    assert capsys.readouterr().err.startswith("slidecast: the deck at")


def test_clips_of_rounds_to_three_decimals():
    slides = [deck.Slide(f"S{n}", ["x"], f"Line {n}.") for n in range(3)]
    deck_obj = deck.Deck(title="T", subtitle="S", slides=slides)
    timings = build.clips_of(deck_obj, Path("W"), [1.2345, 2.0, 3.0])
    assert timings[0].seconds == 2.034
    assert timings[0].seconds != 2.0345
