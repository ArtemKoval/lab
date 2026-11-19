"""The boundary and pass-through assertions that close the mutation gate."""

import json
import subprocess
from pathlib import Path

import pytest

from slidecast import build, cli, deck, render, scenes


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


def one_slide():
    return deck.Deck(title="T", subtitle="S",
                     slides=[deck.Slide("H", ["b"], "L.")])


def an_element_deck(tmp_path: Path, element: dict) -> Path:
    slide = {**a_slide(0), "elements": [element]}
    return write_deck(tmp_path, [slide, a_slide(1), a_slide(2)])


def a_box(col: int, row: int) -> dict:
    return {"kind": "box", "at": 1.0, "col": col, "row": row, "label": "B"}


@pytest.mark.parametrize("share", [0, 1, 0.5])
def test_a_bar_share_at_the_boundaries_loads(tmp_path, share):
    element = {"kind": "bar", "at": 1.0, "col": 1, "row": 1,
               "label": "L", "share": share}
    loaded = deck.load(an_element_deck(tmp_path, element))
    assert loaded.slides[0].elements[0]["share"] == share


@pytest.mark.parametrize("share", [-0.1, 1.1, "x"])
def test_a_bar_share_outside_the_range_is_refused(tmp_path, share):
    element = {"kind": "bar", "at": 1.0, "col": 1, "row": 1,
               "label": "L", "share": share}
    with pytest.raises(deck.DeckError, match="share outside 0 to 1"):
        deck.load(an_element_deck(tmp_path, element))


def test_an_element_at_zero_loads_and_a_negative_time_is_refused(tmp_path):
    loaded = deck.load(an_element_deck(
        tmp_path, {"kind": "box", "at": 0, "col": 1, "row": 1, "label": "B"}))
    assert loaded.slides[0].elements[0]["at"] == 0
    other = tmp_path / "s"
    other.mkdir()
    with pytest.raises(deck.DeckError, match="without a time"):
        deck.load(an_element_deck(
            other, {"kind": "box", "at": -0.5, "col": 1, "row": 1,
                    "label": "B"}))


@pytest.mark.parametrize("col", [1, scenes.COLS])
def test_a_box_on_the_first_and_last_column_loads(tmp_path, col):
    loaded = deck.load(an_element_deck(tmp_path, a_box(col, 1)))
    assert loaded.slides[0].elements[0]["col"] == col


@pytest.mark.parametrize("row", [1, scenes.ROWS])
def test_a_box_on_the_first_and_last_row_loads(tmp_path, row):
    loaded = deck.load(an_element_deck(tmp_path, a_box(1, row)))
    assert loaded.slides[0].elements[0]["row"] == row


@pytest.mark.parametrize("cell", [(0, 1), (13, 1)])
def test_a_box_column_outside_the_grid_is_refused(tmp_path, cell):
    with pytest.raises(deck.DeckError, match="outside the grid"):
        deck.load(an_element_deck(tmp_path, a_box(*cell)))


@pytest.mark.parametrize("cell", [(1, 0), (1, 7)])
def test_a_box_row_outside_the_grid_is_refused(tmp_path, cell):
    with pytest.raises(deck.DeckError, match="outside the grid"):
        deck.load(an_element_deck(tmp_path, a_box(*cell)))


def test_a_same_cell_row_arrow_points_left(tmp_path):
    element = {"kind": "arrow", "at": 3.0, "from": [2, 2], "to": [2, 2]}
    loaded = deck.load(an_element_deck(tmp_path, element))
    filter_text = scenes.arrow_filter(dict(loaded.slides[0].elements[0]))
    assert "◄" in filter_text
    assert "►" not in filter_text
    # The head of a same-cell arrow sits past the shared column, not behind
    # it: x2 + 10, never x2 - 34.
    head_x = scenes.cell_x(2) + 135
    assert str(head_x + 10) in filter_text
    assert str(head_x - 34) not in filter_text


def test_the_slide_bullets_space_down_the_slide():
    filters = scenes.slide_filters("H", ["first", "second"], [])
    # The second bullet sits at 330 + 90; the minus mutant would put it at
    # 240 and drop it above the heading's baseline.
    assert "420" in filters[2]
    assert "240" not in filters[2]


def test_an_empty_audio_file_is_refused_and_a_one_byte_audio_passes(
    tmp_path,
):
    def empty_run(step):
        if step.name.startswith("speak"):
            Path(step.command[-1]).write_bytes(b"")

    with pytest.raises(render.RenderError, match="wrote no audio"):
        build.orchestrate(
            one_slide(), tmp_path / "We", tmp_path / "oe.mp4", "V",
            run=empty_run, probe=lambda p: 1.0, retries=1,
        )

    seen = []

    def tiny_run(step):
        seen.append(step)
        if step.name.startswith("speak"):
            Path(step.command[-1]).write_bytes(b"a")

    timings = build.orchestrate(
        one_slide(), tmp_path / "Wt", tmp_path / "ot.mp4", "V",
        run=tiny_run, probe=lambda p: 1.0, retries=1,
    )
    speak_steps = [s for s in seen if s.name.startswith("speak")]
    assert len(speak_steps) == 1
    assert timings[0].seconds == 1.8


def test_the_retry_exhaustion_names_the_exact_run_count(tmp_path):
    def silent_run(step):
        pass

    with pytest.raises(render.RenderError, match="after 3 runs"):
        build.orchestrate(
            one_slide(), tmp_path / "Wx", tmp_path / "ox.mp4", "V",
            run=silent_run, probe=lambda p: 1.0, retries=2,
        )


def test_the_build_creates_missing_output_parents_and_reruns_in_place(
    tmp_path,
):
    def fake_run(step):
        if step.name.startswith("speak"):
            Path(step.command[-1]).write_bytes(b"audio")

    # The work tree sits deeper than the output's parent, so both mkdir
    # calls meet a missing parent on the first run.
    out = tmp_path / "shallow" / "out.mp4"
    work = tmp_path / "deep" / "nested" / "work"
    for _ in range(2):
        build.orchestrate(
            one_slide(), work, out, "V",
            run=fake_run, probe=lambda p: 1.0, retries=0,
        )
    assert out.parent.is_dir()
    assert work.is_dir()
