# Council Notes: spec.md

## Author Summary

The author drafted nine requirements with 26 scenarios across the
surface selection, the sentence split, the marker detection, the pin
classification, the report, the outputs, the exit codes, and the
read-only guarantee. Every claim was verified against the tool
source and the existing suite.

## Reviewer Challenges

- Major: the five miss-class shapes lack named test evidence.
- Major: the `collapsed in pin` direction and the whitespace
  collapse never fire in tests.
- Major: the 110-character cut and the silent-file rule lack tests.
- Minor: the totals `sentences` count and the JSON `root` key lack
  assertions.
- Minor: the charter-last position is unasserted.
- Suggestion: drop the untestable network clause from the read-only
  requirement, and add the bullet-without-ender join scenario.

## Resolutions

- Accepted: the gap list carries every finding, and the tasks pin
  the README shapes for the miss-class test.
- Accepted: the tasks add both pin-direction and collapse tests.
- Accepted: the tasks add the cut and silent-file tests.
- Accepted: the tasks add the assertions.
- Accepted: the tasks add the charter-last assertion.
- Accepted: the read-only requirement carries only testable SHALL
  statements, and the delta carries the bullet-join scenario.

## Remaining Risks

- The miss-class scenario names the classes without examples. The
  README owns the examples, and the apply tests use the README
  shapes.
