# Council Notes: proposal.md

## Author Summary

The author drafted the four template sections. Why: two issue asks,
with the docs mapping quote and the observed `effort xhigh` fault.
What Changes: the separator, the seven row table, the map-always
decision, raw pass-through, n/a on absent effort, the mapped
`--json` value, the no-marker judgment, and the 100 character pin.
Capabilities: modified `session-statusline` only. Impact: four files
plus the negative space.

## Reviewer Challenges

- Blocker: the delta spec must restate all three scenarios of the
  render requirement, because a MODIFIED requirement replaces the
  whole block at archive.
- Blocker: the mapping rows need the verbatim docs sentence with
  source and date.
- Blocker: the map-always decision contradicts the literal
  detection ask of the issue, so the proposal must state the
  decision in so many words.
- Should-fix: the suite pins the line under 100 characters, and the
  separator can break that pin on an allowed payload.
- Should-fix: pin the `--json` mapped value, state the degraded
  line choice, exercise the mapping with `xhigh` in the delta,
  complete the Impact negative space, name the CLAUDE.md edit, put
  the gateway drift caveat on the mapping.
- Taste: keep the separator format out of the proposal.

## Resolutions

- Accepted: all blockers. The verbatim sentence lives in a fenced
  block with source and date. The map-always decision carries its
  own sentence. The 100 character pin gets an explicit
  re-examination bullet. The Modified Capabilities bullet states
  the restated scenarios. The Impact section names the CLAUDE.md
  edit, the three non-changes with reasons, and the README limits
  row.
- Accepted: `--json` carries the mapped value with no new field,
  and the degraded line gains the separator, both stated.
- Rejected: the taste challenge on the separator format. The issue
  names the pipe character, so the proposal quotes the requirement
  instead of a vague "visible separator".
- Deferred: the delta scenario set and the exact requirement
  heading belong to the specs artifact.

## Remaining Risks

- Always-map shows the z.ai label on a foreign ontology payload.
  The operator accepted this, and the proposal records it.
- The mapping is a point-in-time claim about a remote gateway. The
  README limits row carries the doc date.
