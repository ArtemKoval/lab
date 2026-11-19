"""The command line's tests: the exit codes, and the messages."""

import json
from pathlib import Path

import pytest

from slidecast import cli


def a_deck(tmp_path: Path) -> Path:
    data = {
        "title": "Northgate",
        "subtitle": "one minute",
        "slides": [
            {"heading": f"S{n}", "bullets": ["x"], "narration": f"Line {n}."}
            for n in range(4)
        ],
    }
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_validate_accepts_a_good_deck(tmp_path, capsys):
    code = cli.main(["validate", "--deck", str(a_deck(tmp_path))])
    assert code == 0
    assert "deck ok: 4 slides" in capsys.readouterr().out


def test_validate_refuses_a_bad_deck(tmp_path, capsys):
    path = tmp_path / "deck.json"
    path.write_text("{}", encoding="utf-8")
    code = cli.main(["validate", "--deck", str(path)])
    assert code == 2
    assert "slidecast:" in capsys.readouterr().err


def test_plan_lists_the_slides(tmp_path, capsys):
    code = cli.main(["plan", "--deck", str(a_deck(tmp_path))])
    assert code == 0
    out = capsys.readouterr().out
    assert "slide 0: S0" in out


def test_build_reports_the_built_video(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)

    def fake_orchestrate(deck, work, out, voice, run=None, probe=None, retries=0):
        out.write_bytes(b"mp4")
        return []

    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    out = tmp_path / "video.mp4"
    code = cli.main(["build", "--deck", str(a_deck(tmp_path)), "--out", str(out)])
    assert code == 0
    assert "built" in capsys.readouterr().out


def test_build_reports_a_render_failure(tmp_path, monkeypatch, capsys):
    def boom():
        raise cli.render.RenderError("the build needs edge-tts on the PATH")

    monkeypatch.setattr(cli.render, "check_tools", boom)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    code = cli.main(
        ["build", "--deck", str(a_deck(tmp_path)), "--out", str(tmp_path / "v.mp4")]
    )
    assert code == 2
    assert "edge-tts" in capsys.readouterr().err
