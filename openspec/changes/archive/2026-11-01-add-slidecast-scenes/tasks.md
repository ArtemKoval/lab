# Tasks: add-slidecast-scenes

## 1. The scene layer

- [x] 1.1 Write `tools/slidecast/slidecast/scenes.py` test first. The module turns one slide into the filter list: the stat, the box, the arrow, the bar, and the staggered bullets. The entrance is the alpha ramp and the slide over 0.5 seconds, held out before the element time.
- [x] 1.2 Extend the deck loader for the elements: the four kinds, the 12 by 6 grid, the share range, and the named refusals. The tests pin every refusal message.
- [x] 1.3 Wire the scenes into the render path. `draw_slide` takes the filter list, and the build hands it the scenes for each slide.

## 2. The decks and the videos

- [ ] 2.1 Redraw the four decks with elements. Use the stat tiles, the flow diagrams, and the bars, with entrance times that follow the narration.
- [ ] 2.2 Re-render the four videos. Read one frame per act to see the infographics.

## 3. The gates

- [x] 3.1 Run the slidecast tests at 100 percent line and branch coverage. Run ruff at complexity 10. Run the mutation run on an out-of-tree copy at 95 percent or higher.
- [ ] 3.2 Commit the units as atomic commits. Push the branch. Open the pull request. Run the adversarial review. Merge.
