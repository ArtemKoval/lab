# Council Notes: design.md

## Author Summary

The design settles the lock root resolution, the module split, the stale
rules and their order, the record write shape, the holder label form,
the CLI contract with exit 64, the skill-owned halt step, and the
no-MCP call. The container diagram shows the lock examination before the
gh fetches, and the component view shows the three modules.

## Reviewer Challenges

- BLOCKER: the lock root wording, the ADR 0012 acknowledgment, the
  foreign-host wedge, the corrupt-record wedge, and the shared holder
  label, all carried from the proposal round.
- SHOULD-FIX: the subcommand edges, the exit-64 statement, the core.py
  charter, the README and Commands impact lines, the Out of scope
  section, the halt location and order, and the boot id field.

## Resolutions

- Accepted: every blocker folds into the proposal, the delta, or this
  design, with the ADR restating the authority grant.
- Accepted: the stale-rule order puts the cheap field comparisons first,
  and the age rule sits last.
- Rejected: surface tags on the delta scenarios, because the house spec
  files carry none for non-governed capabilities.
- Rejected: dsh 30 second staleness, because the run spans hours.

## Remaining Risks

- A wedged live holder, the stale-clear race, and an old git without the
  path-format flag, all documented in the design failure modes.
