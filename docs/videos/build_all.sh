#!/bin/bash
# The slidecast build for the four assignment videos. Run from the repository
# root: docs/videos/build_all.sh
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PATH="$ROOT/tools/slidecast/.venv/bin:$PATH"
export PYTHONPATH="$ROOT/tools/slidecast"
for name in business it factory self-improving; do
  python3 -m slidecast validate --deck "docs/videos/decks/$name.json"
  python3 -m slidecast build --deck "docs/videos/decks/$name.json" --out "docs/videos/$name.mp4"
done
ls -la docs/videos/*.mp4
