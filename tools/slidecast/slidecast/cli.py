"""The slidecast command line: examine a deck, plan a build, build a video.

slidecast validate --deck <json>
slidecast plan --deck <json>
slidecast build --deck <json> --out <mp4> [--voice en-US-AndrewNeural]

Exit 0 on success and 2 on operational failure. The build needs ffmpeg,
ffprobe, and edge-tts on the PATH.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import build, deck, render

VOICE = "en-US-AndrewNeural"


def main(argv: list[str] | None = None) -> int:
    """Run one command, and give the process exit code."""
    parser = argparse.ArgumentParser(prog="slidecast")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "plan", "build"):
        one = sub.add_parser(name)
        one.add_argument("--deck", required=True, type=Path)
        if name == "build":
            one.add_argument("--out", required=True, type=Path)
            one.add_argument("--voice", default=VOICE)
            one.add_argument("--retries", default=2, type=int)
    args = parser.parse_args(argv)
    try:
        loaded = deck.load(args.deck)
    except deck.DeckError as error:
        print(f"slidecast: {error}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(f"deck ok: {len(loaded.slides)} slides, {args.deck}")
        return 0
    if args.command == "plan":
        work = args.deck.parent / ".slidecast-work"
        for index, slide in enumerate(loaded.slides):
            words = len(slide.narration.split())
            print(f"slide {index}: {slide.heading} ({words} narration words)")
        return 0
    try:
        render.check_tools()
        work = Path(tempfile.mkdtemp(prefix="slidecast-"))
        timings = build.orchestrate(
            loaded, work, args.out, args.voice, retries=args.retries
        )
    except (render.RenderError, deck.DeckError) as error:
        print(f"slidecast: {error}", file=sys.stderr)
        return 2
    total = render.probe_seconds(args.out)
    print(f"built {args.out}: {len(timings)} clips, {total:.1f} seconds")
    return 0
