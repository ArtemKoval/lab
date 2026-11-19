"""The retry behavior: the flaky voice, the default, and the flag."""

import json
from pathlib import Path

import pytest

from slidecast import build, cli, deck, render


def write_deck(tmp_path: Path, slides) -> Path:
    data = {"title": "T", "subtitle": "S", "slides": slides}
    path = tmp_path / "deck.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def a_slide(n):
    return {"heading": f"H{n}", "bullets": ["b"], "narration": f"Line {n}."}


def one_slide_deck():
    slides = [deck.Slide("H", ["b"], "L.")]
    return deck.Deck(title="T", subtitle="S", slides=slides)


def test_the_second_speak_attempt_writes_the_audio(tmp_path, monkeypatch):
    calls = {"n": 0}

    def flaky_run(step):
        if step.name.startswith("speak"):
            calls["n"] += 1
            if calls["n"] == 1:
                raise render.RenderError("the step speak slide 0 failed: net")
            Path(step.command[-1]).write_bytes(b"audio")

    timings = build.orchestrate(
        one_slide_deck(), tmp_path / "Wr", tmp_path / "or.mp4", "V",
        run=flaky_run, probe=lambda p: 1.0, retries=2,
    )
    assert calls["n"] == 2
    assert timings[0].seconds == 1.8


def test_the_default_retries_refuse_a_second_attempt(tmp_path, monkeypatch):
    calls = {"n": 0}

    def flaky_run(step):
        if step.name.startswith("speak"):
            calls["n"] += 1
            if calls["n"] == 1:
                raise render.RenderError("the step speak slide 0 failed: net")
            Path(step.command[-1]).write_bytes(b"audio")

    with pytest.raises(render.RenderError):
        build.orchestrate(
            one_slide_deck(), tmp_path / "Wd", tmp_path / "od.mp4", "V",
            run=flaky_run, probe=lambda p: 1.0,
        )
    assert calls["n"] == 1


def test_the_cli_hands_the_retries_flag_to_the_build(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_orchestrate(a_deck, work, out, voice, run=None, probe=None, retries=0):
        seen["retries"] = retries
        return []

    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    good = write_deck(tmp_path, [a_slide(0)] * 3)
    code = cli.main(
        ["build", "--deck", str(good), "--out", str(tmp_path / "v.mp4"), "--retries", "5"]
    )
    assert code == 0
    assert seen["retries"] == 5
    capsys.readouterr()


def test_the_cli_retries_default_is_two(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_orchestrate(a_deck, work, out, voice, run=None, probe=None, retries=0):
        seen["retries"] = retries
        return []

    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    good = write_deck(tmp_path, [a_slide(0)] * 3)
    code = cli.main(["build", "--deck", str(good), "--out", str(tmp_path / "v.mp4")])
    assert code == 0
    assert seen["retries"] == 2
    capsys.readouterr()
