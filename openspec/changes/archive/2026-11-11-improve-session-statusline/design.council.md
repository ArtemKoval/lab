# Council Notes: design.md

## Author Summary

The design carries the C4 component flow, five decisions (map
always, one table with raw pass-through, a block list join, the
mapped `--json` value, the line length pin), the risk list, and the
no-migration note.

## Reviewer Challenges

- Blocker: D5 stated a false pinned line length.
- Should-fix: the design and the adr manifest disagreed on where the
  decision lives.
- Risk: a falsy non-string level collapses to `n/a` in the live code,
  and D2 did not state that rule.
- Risk: the under-100 pin is payload-dependent, and the realistic
  worst case claim was unverified.
- Taste: one sentence ran past the descriptive word bound.

## Resolutions

- Accepted: D5 now states the verified numbers. The separator adds
  14 characters over seven junctions. The pinned payload keeps the
  `high` token, so its line grows from 77 to 91 characters. A 24
  character model name can reach 107, and the pin binds the pinned
  payload only.
- Accepted: the open questions section now defers to the adr
  manifest.
- Accepted: D2 states the falsy rule.
- Accepted: D5 records the payload-dependent bound.
- Accepted: the long sentence is split.

## Remaining Risks

- The display names the client-side mapped level of the request. The
  gateway applies it, and no probe runs in this change.
