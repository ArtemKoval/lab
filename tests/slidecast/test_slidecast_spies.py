"""Spy assertions: the exact external calls the render side makes."""

from pathlib import Path

from slidecast import render


def test_probe_seconds_calls_ffprobe_with_the_exact_command(monkeypatch):
    seen = {}

    class Done:
        stdout = "12.5\n"
        returncode = 0

    def spy(command, capture_output, text, check):
        seen["command"] = command
        seen["capture_output"] = capture_output
        seen["text"] = text
        seen["check"] = check
        return Done()

    monkeypatch.setattr(render.subprocess, "run", spy)
    assert render.probe_seconds(Path("v.mp3")) == 12.5
    assert seen["command"] == [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", "v.mp3",
    ]
    assert seen["capture_output"] is True
    assert seen["check"] is True


def test_run_passes_capture_output_and_check(monkeypatch):
    seen = {}

    def spy(command, capture_output, check):
        seen["command"] = command
        seen["capture_output"] = capture_output
        seen["check"] = check

        class Done:
            returncode = 0
            stderr = b""

        return Done()

    monkeypatch.setattr(render.subprocess, "run", spy)
    render.run(render.Step("ok", ["true"]))
    assert seen == {
        "command": ["true"],
        "capture_output": True,
        "check": True,
    }


def test_check_tools_examines_the_three_tools_in_order(monkeypatch):
    seen = []
    monkeypatch.setattr(
        render.shutil, "which", lambda name: seen.append(name) or "/usr/bin/x"
    )
    render.check_tools()
    assert seen == ["ffmpeg", "ffprobe", "edge-tts"]


def test_the_escapes_are_exact():
    assert render._esc("a'b") == "a’b"
    assert render._esc("co:lon") == "co\\:lon"
    assert render._esc("plain") == "plain"
    assert render._esc("back\\slash") == "back\\\\slash"

"""Spy assertions: the exact external calls the render side makes."""

from pathlib import Path

from slidecast import render


def test_probe_seconds_calls_ffprobe_with_the_exact_command(monkeypatch):
    seen = {}

    class Done:
        stdout = "12.5\n"
        returncode = 0

    def spy(command, capture_output, text, check):
        seen["command"] = command
        seen["capture_output"] = capture_output
        seen["text"] = text
        seen["check"] = check
        return Done()

    monkeypatch.setattr(render.subprocess, "run", spy)
    assert render.probe_seconds(Path("v.mp3")) == 12.5
    assert seen["command"] == [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", "v.mp3",
    ]
    assert seen["capture_output"] is True
    assert seen["check"] is True


def test_run_passes_capture_output_and_check(monkeypatch):
    seen = {}

    def spy(command, capture_output, check):
        seen["command"] = command
        seen["capture_output"] = capture_output
        seen["check"] = check

        class Done:
            returncode = 0
            stderr = b""

        return Done()

    monkeypatch.setattr(render.subprocess, "run", spy)
    render.run(render.Step("ok", ["true"]))
    assert seen == {
        "command": ["true"],
        "capture_output": True,
        "check": True,
    }


def test_check_tools_examines_the_three_tools_in_order(monkeypatch):
    seen = []
    monkeypatch.setattr(
        render.shutil, "which", lambda name: seen.append(name) or "/usr/bin/x"
    )
    render.check_tools()
    assert seen == ["ffmpeg", "ffprobe", "edge-tts"]


def test_the_escapes_are_exact():
    assert render._esc("back\\slash") == "back\\\\slash"
    assert render._esc("quote'inside") == "quote’inside"
    assert render._esc("co:lon") == "co\\:lon"
    assert render._esc("plain") == "plain"
