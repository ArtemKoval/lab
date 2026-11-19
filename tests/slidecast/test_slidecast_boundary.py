"""The boundary and pass-through assertions that close the mutation gate."""

import json
import subprocess
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


def test_five_bullets_is_allowed_and_six_is_not(tmp_path):
    five = write_deck(tmp_path, [{**a_slide(0), "bullets": list("abcde")}] * 3)
    assert len(deck.load(five).slides[0].bullets) == 5
    other = tmp_path / "s"
    other.mkdir()
    six = write_deck(other, [{**a_slide(0), "bullets": list("abcdef")}] * 3)
    with pytest.raises(deck.DeckError):
        deck.load(six)


def test_exactly_three_slides_is_allowed(tmp_path):
    path = write_deck(tmp_path, [a_slide(0), a_slide(1), a_slide(2)])
    loaded = deck.load(path)
    assert len(loaded.slides) == 3
    assert loaded.subtitle == "S"


def test_orchestrate_passes_the_deck_the_voice_and_the_out(monkeypatch):
    slides = [deck.Slide(f"H{n}", ["b"], f"L{n}.") for n in range(3)]
    the_deck = deck.Deck(title="T", subtitle="S", slides=slides)
    seen = {}
    ran = []
    real_clips_of = build.clips_of
    real_clip_steps = build.clip_steps

    def fake_clips_of(a_deck, work, lengths):
        seen["clips_deck"] = a_deck
        return real_clips_of(a_deck, work, lengths)

    def fake_clip_steps(timings, out):
        seen["out"] = out
        return real_clip_steps(timings, out)

    def fake_run(step):
        ran.append(step)
        if step.name.startswith("speak"):
            Path(step.command[-1]).write_bytes(b"audio")

    monkeypatch.setattr(build, "clips_of", fake_clips_of)
    monkeypatch.setattr(build, "clip_steps", fake_clip_steps)
    out = Path("out.mp4")
    build.orchestrate(
        the_deck, Path("W"), out, "V", run=fake_run, probe=lambda p: 1.0
    )
    assert seen["clips_deck"] is the_deck
    assert seen["out"] == out
    speak_steps = [s for s in ran if s.name.startswith("speak")]
    assert all(s.command[2] == "V" for s in speak_steps)


def test_the_parser_demands_a_command_and_the_flags(tmp_path, capsys):
    good = write_deck(tmp_path, [a_slide(0)] * 3)
    with pytest.raises(SystemExit) as exited:
        cli.main([])
    assert exited.value.code == 2
    assert "usage: slidecast" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cli.main(["validate"])
    err = capsys.readouterr().err
    assert "--deck" in err
    with pytest.raises(SystemExit):
        cli.main(["build", "--deck", str(good)])
    assert "--out" in capsys.readouterr().err


def test_the_build_work_folder_carries_the_prefix(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_orchestrate(a_deck, work, out, voice, run=None, probe=None, retries=0):
        seen["work"] = work
        return []

    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    good = write_deck(tmp_path, [a_slide(0)] * 3)
    code = cli.main(
        ["build", "--deck", str(good), "--out", str(tmp_path / "v.mp4")]
    )
    assert code == 0
    work = seen["work"]
    assert work.is_dir()
    assert work.name.startswith("slidecast-")
    capsys.readouterr()


def test_the_probe_reads_text(monkeypatch):
    seen = {}

    class Done:
        stdout = "3.0\n"
        returncode = 0

    def spy(command, capture_output, text, check):
        seen["text"] = text
        return Done()

    monkeypatch.setattr(render.subprocess, "run", spy)
    render.probe_seconds(Path("v.mp3"))
    assert seen["text"] is True


def test_the_failure_tail_carries_the_decoded_stderr():
    def boom(command, capture_output, check):
        raise subprocess.CalledProcessError(1, command, stderr=b"boom")

    original = render.subprocess.run
    render.subprocess.run = boom
    try:
        with pytest.raises(render.RenderError) as raised:
            render.run(render.Step("x", ["nope"]))
    finally:
        render.subprocess.run = original
    assert str(raised.value) == "the step x failed: boom"


def test_the_failure_tail_carries_at_most_400_characters():
    stderr = ("x" * 500).encode()

    def boom(command, capture_output, check):
        raise subprocess.CalledProcessError(1, command, stderr=stderr)

    original = render.subprocess.run
    render.subprocess.run = boom
    try:
        with pytest.raises(render.RenderError) as raised:
            render.run(render.Step("x", ["nope"]))
    finally:
        render.subprocess.run = original
    assert str(raised.value) == "the step x failed: " + "x" * 400


def test_the_failure_tail_replaces_bad_bytes():
    stderr = b"a\xffb"

    def boom(command, capture_output, check):
        raise subprocess.CalledProcessError(1, command, stderr=stderr)

    original = render.subprocess.run
    render.subprocess.run = boom
    try:
        with pytest.raises(render.RenderError) as raised:
            render.run(render.Step("x", ["nope"]))
    finally:
        render.subprocess.run = original
    assert str(raised.value) == "the step x failed: a�b"


def test_the_build_hands_the_loaded_deck_to_orchestrate(
    tmp_path, monkeypatch, capsys
):
    seen = {}

    def fake_orchestrate(a_deck, work, out, voice, run=None, probe=None, retries=0):
        seen["deck"] = a_deck
        return []

    monkeypatch.setattr(cli.render, "check_tools", lambda: None)
    monkeypatch.setattr(cli.render, "probe_seconds", lambda p: 5.0)
    monkeypatch.setattr(cli.build, "orchestrate", fake_orchestrate)
    good = write_deck(tmp_path, [a_slide(0)] * 3)
    code = cli.main(
        ["build", "--deck", str(good), "--out", str(tmp_path / "v.mp4")]
    )
    assert code == 0
    assert seen["deck"].title == "T"
    capsys.readouterr()


def test_an_empty_stderr_leaves_an_empty_tail(monkeypatch):
    def boom(command, capture_output, check):
        raise subprocess.CalledProcessError(1, command, stderr=None)

    monkeypatch.setattr(render.subprocess, "run", boom)
    with pytest.raises(render.RenderError) as raised:
        render.run(render.Step("x", ["nope"]))
    assert str(raised.value) == "the step x failed: "


def test_exhausted_retries_name_the_slide(monkeypatch):
    slides = [deck.Slide("H", ["b"], "L.")]
    the_deck = deck.Deck(title="T", subtitle="S", slides=slides)
    monkeypatch.setattr(render.subprocess, "run", lambda *a, **k: None)
    with pytest.raises(render.RenderError, match="speak slide 0"):
        build.orchestrate(
            the_deck, Path("W9"), Path("o9.mp4"), "V", retries=1,
            probe=lambda p: 1.0,
        )
