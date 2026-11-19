# Proposal: add-slidecast-scenes

## Why

The four assignment videos render static text slides, and the review of the
assignment calls them dull and unclear. The tool already carries ffmpeg's
two drawing filters, and both take time expressions, so the slides can
build up like infographics: numbers that fade in, boxes and arrows that
draw a diagram, and bars that fill. No new dependency and no new filter
kind is needed.

## What Changes

- Add an optional `elements` list to every slide of a deck, with four
  element kinds: `stat` for a number tile, `box` for a labeled diagram box
  on a grid, `arrow` from one box to another, and `bar` for a filling bar.
- Animate the entrance of every element and every bullet with an alpha ramp
  and a slide, at a per-element time, so a slide builds up while the voice
  reads it.
- Keep the old decks working: a slide without elements staggers its
  bullets, exactly as before in content.
- Redraw the four assignment decks with elements, and re-render the four
  videos.

## Capabilities

### New Capabilities

- `slidecast-scenes`: The scene layer of slidecast: the element kinds, the
  grid, the entrance animation, and the backward-compatible bullet
  stagger.

### Modified Capabilities

## Impact

- `tools/slidecast/slidecast/`: a new scenes module that builds the
  filtergraph, small changes in the render and build modules, and deck
  validation for the new kinds.
- `tests/slidecast/`: exact filtergraph assertions per kind, the stagger
  math, and the old-deck behavior.
- `docs/videos/decks/`: the four decks carry elements. The videos are
  rebuilt artifacts.
