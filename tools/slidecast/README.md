# slidecast

One narrated video from one JSON deck, through `edge-tts` and `ffmpeg`. The
tool draws each slide as a PNG, speaks its narration to MP3, turns the pair
into one clip, and concatenates the clips into the video. The deck carries
the whole video: the title, the subtitle, and one heading, bullet list, and
narration paragraph per slide.

## Why

The lab's presentations are generated artifacts, not studio work. A deck in
version control and a build command keep every video reproducible, and a
content edit is a diff.

## Commands

The build needs `ffmpeg`, `ffprobe`, and `edge-tts` on the PATH. The video
venv carries edge-tts:

```bash
python3 -m venv tools/slidecast/.venv
tools/slidecast/.venv/bin/pip install edge-tts
```

From the repository root:

```bash
PATH="$PWD/tools/slidecast/.venv/bin:$PATH" PYTHONPATH=tools/slidecast \
python3 -m slidecast validate --deck docs/videos/decks/business.json
PATH="$PWD/tools/slidecast/.venv/bin:$PATH" PYTHONPATH=tools/slidecast \
python3 -m slidecast build --deck docs/videos/decks/business.json --out docs/videos/business.mp4
docs/videos/build_all.sh   # all four assignment videos
```

Exit 0 means success, and exit 2 names the operational failure: a deck that
does not parse, or an external tool that is missing or failed. `plan` prints
one line per slide with its narration word count, and builds nothing.

The voice is `en-US-AndrewNeural` by default, and `--voice` names another.

## Deck shape

```json
{
  "title": "The title on the title slide",
  "subtitle": "The line under it",
  "slides": [
    {"heading": "...", "bullets": ["..."], "narration": "..."},
    {"heading": "...", "bullets": [], "narration": "..."}
  ]
}
```

At least three slides, at most five bullets per slide, one narration
paragraph per slide. About 25 spoken words run about ten seconds, so a
one-minute video carries roughly 160 narration words over six slides. The
first slide renders as the title slide, so it usually carries no bullets.

## Tests and gates

The tool is standard library only, and its tests run in the root suite:

```bash
PYTHONPATH=tools/slidecast tools/zai_routing_audit/.venv/bin/python -m pytest tests/slidecast
```

Coverage sits at 100 percent line and branch, and the mutation run kills at
least 95 percent of the production mutants. Run mutmut on an out-of-tree
copy whose root carries the `slidecast/` package beside `tests/`, with the
mutants path first on the pytest pythonpath, exactly as the plan_exec README
describes for its own package.

## Status

The tool rendered the four assignment videos in `docs/videos/`, and its
decks sit beside them in `docs/videos/decks/`.
