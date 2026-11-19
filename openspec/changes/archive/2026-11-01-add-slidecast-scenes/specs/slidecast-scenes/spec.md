## Purpose

The scene layer turns the static slides of slidecast into infographics that
build up: numbers fade in, diagram boxes and arrows draw a flow, and bars
fill, all while the narration reads. The layer uses the two drawing filters
the tool already carries, with the frame time in their expressions.

## ADDED Requirements

### Requirement: The element kinds
A slide of a deck SHALL carry an optional `elements` list. Each element
SHALL be one of four kinds: a `stat` with a value and a label, a `box` with
a label at a grid cell, an `arrow` with a from cell and a to cell, and a
`bar` with a label and a share. The loader SHALL refuse an unknown kind, a
cell outside the 12 by 6 grid, and a share outside 0 to 1, each with the
slide number in the message.

#### Scenario: A stat element loads
- **GIVEN** a slide with one stat element at column 1, row 1
- **WHEN** the deck loads
- **THEN** the element carries its value, its label, and its time

#### Scenario: An unknown kind is refused
- **GIVEN** a slide with an element of the kind `chart`
- **WHEN** the deck loads
- **THEN** the error names the slide number and the kind

#### Scenario: A cell outside the grid is refused
- **GIVEN** a box element at column 13
- **WHEN** the deck loads
- **THEN** the error names the slide number and the grid

### Requirement: The entrance animation
Every element and every bullet SHALL enter over 0.5 seconds at its `at`
time: the alpha ramps from 0 to 1, and the element slides 80 units from the
right. The filtergraph SHALL hold an element out of the frames before its
time. The bullets of a slide without elements SHALL stagger 0.7 seconds
apart from 0.5 seconds on.

#### Scenario: A box enters at its time
- **GIVEN** a box element at 2.0 seconds
- **WHEN** the builder draws the slide
- **THEN** the filter enables the box from 2.0 seconds, ramps the alpha
  over 0.5 seconds, and offsets the position by the remaining slide

#### Scenario: Bullets stagger without elements
- **GIVEN** a slide with three bullets and no elements
- **WHEN** the builder draws the slide
- **THEN** the bullets enter at 0.5, 1.2, and 1.9 seconds

### Requirement: The diagram joins boxes with arrows
An arrow element SHALL name a from cell and a to cell, and the builder
SHALL draw a straight connector between the cell centers with a head at
the target. The arrow SHALL enter at its own time, so a deck can draw the
boxes first and connect them after.

#### Scenario: An arrow joins two boxes
- **GIVEN** an arrow from cell 1,3 to cell 4,3, at 3.0 seconds
- **WHEN** the builder draws the slide
- **THEN** the filter draws the connector with a head, enabled from 3.0 seconds

### Requirement: The old decks still render
A deck without elements SHALL render exactly the slides it rendered before,
with the bullet content unchanged, plus the entrance stagger. The builder
SHALL change no CLI flag and no exit code.

#### Scenario: An old deck builds the same video
- **GIVEN** the previous business deck without elements
- **WHEN** the build runs
- **THEN** the exit code is 0, the clip count is the slide count, and each
  slide carries the same heading and narration
