"""The rendering side of slidecast: the commands, and the build.

The module only assembles ffmpeg and edge-tts command lines and runs them
in order. It carries no media logic of its own, so the tests can examine
every command without a render. One build walks the deck once: it draws
each slide as a PNG, speaks its narration to MP3, turns the pair into one
clip, and concatenates the clips into the video.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOOK = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
WIDTH = 1920
HEIGHT = 1080
INK = "0xE8EDF2"
TRACK = "0x1B3242"
PAPER = "0x10202B"
ACCENT = "0x2BD9A4"
TAIL_SECONDS = 0.8


class RenderError(Exception):
    """A render step failed, with the step that failed."""


@dataclass(frozen=True)
class Step:
    """One external command of a build, with the step name for errors."""

    name: str
    command: list[str]


def draw_title(title: str, subtitle: str) -> list[str]:
    """Give the ffmpeg arguments that draw the title slide."""
    return [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={PAPER}:s={WIDTH}x{HEIGHT}",
        "-vframes", "1",
        "-vf", (
            f"drawtext=fontfile={FONT_BOLD}:text='{_esc(title)}':"
            f"fontcolor={ACCENT}:fontsize=88:x=(w-text_w)/2:y=(h-text_h)/2-70,"
            f"drawtext=fontfile={FONT_BOOK}:text='{_esc(subtitle)}':"
            f"fontcolor={INK}:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2+60"
        ),
    ]


def draw_background() -> list[str]:
    """Give the ffmpeg arguments that draw the bare slide background.

    The scene filters play on the clip, where the frame time advances, so
    the still carries nothing but the paper.
    """
    return [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={PAPER}:s={WIDTH}x{HEIGHT}",
        "-vframes", "1",
    ]


def speak(text: str, out: Path, voice: str) -> list[str]:
    """Give the command that speaks one narration paragraph."""
    return ["edge-tts", "--voice", voice, "--text", text,
            "--write-media", str(out)]


def clip(image: Path, audio: Path, seconds: float, out: Path,
         filters: str | None = None) -> list[str]:
    """Give the command that turns one slide and its narration into a clip.

    The scene filters ride the clip, where the looped still advances the
    frame time and the entrances play.
    """
    command = ["ffmpeg", "-y", "-loop", "1", "-i", str(image), "-i", str(audio)]
    if filters:
        command += ["-vf", filters]
    command += [
        "-af", f"apad=whole_dur={seconds}", "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-t", f"{seconds:.3f}", str(out),
    ]
    return command


def join(out: Path, list_file: Path) -> list[str]:
    """Give the command that concatenates the clips into the video.

    The clips join through the concat demuxer, which reads the list file
    and copies the streams. The raw concat protocol cannot join MP4 files.
    """
    return [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy", str(out),
    ]


def write_concat_list(clips: list[Path], list_file: Path) -> None:
    """Write the concat demuxer list for the clips, one line each."""
    lines = [f"file '{clip}'" for clip in clips]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def probe_seconds(path: Path) -> float:
    """Give the duration of one audio file in seconds, through ffprobe."""
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    try:
        text = subprocess.run(
            command, capture_output=True, text=True, check=True
        ).stdout.strip()
        return float(text)
    except (subprocess.CalledProcessError, ValueError) as error:
        raise RenderError(f"ffprobe cannot read {path}: {error}") from error


def _esc(text: str) -> str:
    """Escape one line of text for a drawtext filter.

    An apostrophe closes a quoted filtergraph run and no escape sequence
    survives every parser layer, so the text carries the typographic
    apostrophe instead, which needs no escape and reads better on a slide.
    """
    return (
        text.replace("'", "’")
        .replace("\\", "\\\\")
        .replace(":", "\\:")
    )


def check_tools() -> None:
    """Refuse a build whose external tools are missing."""
    for tool in ("ffmpeg", "ffprobe", "edge-tts"):
        if shutil.which(tool) is None:
            raise RenderError(f"the build needs {tool} on the PATH")


def run(step: Step) -> None:
    """Run one step, and name the step when it fails."""
    try:
        subprocess.run(step.command, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        tail = (error.stderr or b"")[-400:].decode(errors="replace")
        raise RenderError(f"the step {step.name} failed: {tail}") from error
