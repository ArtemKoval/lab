# Design: add-slidecast-scenes

## The closed world

The tool renders through two ffmpeg filters already in the tree: drawtext
and drawbox. Both accept expressions with the frame time `t` in their
position, alpha, and enable options. The scene layer is a reorganization of
those two filters: each element becomes one or two filters whose alpha and
offset are functions of `t`, and `enable` holds the element out of the
frames before its time. No new dependency, no new filter, no frame
generator.

## The vocabulary

| Element | What it draws | The animation |
| --- | --- | --- |
| `stat` | One big value over one label, at a grid column | Fade and rise at its time |
| `box` | One labeled box at a grid cell | Fade and slide at its time |
| `arrow` | A straight connector between two grid cells | Appears at its time, after its boxes |
| `bar` | A track with a filling bar, one label | The fill grows over one second from its time |

The grid is 12 columns by 6 rows over the 1920 by 1080 canvas. A cell is
140 by 130 units with margins, so the decks speak in layout words, not in
pixels.

## The animation contract

Every element carries `at`, the second of the slide when it enters. The
entrance runs 0.5 seconds: the alpha ramps from 0 to 1, and the element
slides 80 units from the right into its place. `enable=between(t,at,end)`
keeps the element out of the early frames. The bullets of a slide without
elements stagger at 0.7 seconds apart, starting at 0.5, with the same
entrance.

## Alternatives

- A frame generator with an image library. A new dependency, and one
  process per frame, for animations the two filters already express.
  Rejected.
- A scene description language with its own parser. The deck is already
  JSON, and the four kinds cover the assignment's infographics. Rejected.

## Risks

- **The filter strings grow long.** One slide carries up to ten elements,
  so the `-vf` value carries tens of filters. ffmpeg parses it, and the
  tests assert the exact strings.
- **Expression escaping.** The filtergraph treats commas as separators, so
  the builder escapes them inside expression arguments, and the tests pin
  the escaped output.
