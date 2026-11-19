"""The render command builders' tests, with no media work at all."""

from pathlib import Path

import pytest

from slidecast import render


def test_draw_title_names_the_two_lines():
    command = render.draw_title("Northgate", "the loan desk")
    assert command[0] == "ffmpeg"
    assert "Northgate" in " ".join(command)
    assert "the loan desk" in " ".join(command)
    assert render.FONT_BOLD in " ".join(command)


def test_draw_background_draws_the_bare_paper():
    command = " ".join(render.draw_background())
    assert "color=c=0x10202B:s=1920x1080" in command
    assert " -vf " not in f" {command} "


def test_clip_carries_the_scene_filters():
    command = render.clip(Path("s.png"), Path("a.mp3"), 9.0, Path("c.mp4"),
                          filters="f1,f2")
    joined = " ".join(command)
    assert "-vf f1,f2" in joined
    assert "-loop 1" in joined


def test_speak_calls_edge_tts():
    command = render.speak("Hello there.", Path("/tmp/v.mp3"), "en-US-X")
    assert command[:2] == ["edge-tts", "--voice"]
    assert command[-1] == "/tmp/v.mp3"


def test_clip_loops_the_image_and_pads():
    command = render.clip(Path("s.png"), Path("v.mp3"), 11.5, Path("c.mp4"))
    joined = " ".join(command)
    assert "-loop 1" in joined
    assert "apad=whole_dur=11.5" in joined
    assert "libx264" in joined


def test_join_uses_the_concat_demuxer():
    command = render.join(Path("out.mp4"), Path("l.txt"))
    joined = " ".join(command)
    assert "-f concat" in joined
    assert "-safe 0" in joined
    assert "l.txt" in joined
    assert "concat:a.mp4" not in joined


def test_write_concat_list_writes_one_line_per_clip(tmp_path):
    list_file = tmp_path / "list.txt"
    render.write_concat_list([Path("/x/a.mp4"), Path("/x/b.mp4")], list_file)
    assert list_file.read_text() == "file '/x/a.mp4'\nfile '/x/b.mp4'\n"


def test_esc_neutralizes_filter_metacharacters():
    assert render._esc("a'b") == "a’b"
    assert render._esc("a:b") == "a\\:b"


def test_check_tools_names_the_missing_tool(monkeypatch):
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    with pytest.raises(render.RenderError, match="ffmpeg"):
        render.check_tools()


def test_probe_seconds_reads_ffprobe(monkeypatch):
    class Done:
        stdout = "12.5\n"
        returncode = 0

    monkeypatch.setattr(
        render.subprocess, "run", lambda *a, **k: Done()
    )
    assert render.probe_seconds(Path("v.mp3")) == 12.5


def test_probe_seconds_wraps_a_failure(monkeypatch):
    def boom(*a, **k):
        raise render.subprocess.CalledProcessError(1, "ffprobe")

    monkeypatch.setattr(render.subprocess, "run", boom)
    with pytest.raises(render.RenderError, match="ffprobe cannot read"):
        render.probe_seconds(Path("v.mp3"))


def test_run_names_the_step_that_failed():
    step = render.Step("explode", ["false"])
    with pytest.raises(render.RenderError, match="the step explode failed"):
        render.run(step)


def test_run_passes_a_working_step():
    render.run(render.Step("true step", ["true"]))


def test_probe_seconds_refuses_non_numeric_output(monkeypatch):
    class Bad:
        stdout = "abc\n"
        returncode = 0

    monkeypatch.setattr(render.subprocess, "run", lambda *a, **k: Bad())
    with pytest.raises(render.RenderError, match="ffprobe cannot read"):
        render.probe_seconds(Path("v.mp3"))


def test_check_tools_passes_when_all_tools_exist(monkeypatch):
    monkeypatch.setattr(render.shutil, "which", lambda name: f"/usr/bin/{name}")
    render.check_tools()


def test_run_reads_stderr_when_the_step_wrote_none(monkeypatch):
    class Fail:
        returncode = 1
        stderr = None

    def boom(command, capture_output, check):
        raise render.subprocess.CalledProcessError(1, command, stderr=None)

    monkeypatch.setattr(render.subprocess, "run", boom)
    with pytest.raises(render.RenderError, match="the step empty failed"):
        render.run(render.Step("empty", ["nope"]))
