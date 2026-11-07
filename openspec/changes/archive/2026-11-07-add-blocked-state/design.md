# Design: add-blocked-state

## Plan review

The inner-loop review consulted the esf report, the process-issues spec, and
the scanner code. The review settled these decisions:

- Table-driven precedence. The three pure label states (`handover`,
  `blocked`, `answered`) move into one precedence table, so the new state is
  one row and the classify complexity falls instead of rising. The
  `human-approved` and `waiting-human-approval` branches keep their place
  after the table, so the existing precedence order survives exactly.
- The `blocked` slot sits between `handover` and `answered`. A handover issue
  stays terminal above it, and a blocked issue outranks a stale `answered`
  label, because the block is the newest fact.
- The action carries the same name as the state, so the JSON and the printed
  line read the same way, and no loop logic mistakes it for a retry action.
- The skill carries the behavioral rule, because the scanner is classification
  only and the loop lives in the skill.
- The stale spec path in the skill moves in the same edit, because the file
  is already open and the drift misleads a reader today.

## ASIT pass

- Unification: the table gives an existing structure one more row. The scan
  CLI, the JSON shape, and the README table keep their contracts.
- Division: the label precedence (table) and the artifact precedence
  (`human-approved` branches) separate, so each stays simple.
- No new component kind: one label, one state, one action.

## Spec delta

One added requirement on `process-issues`: the blocked state, with the
precedence scenarios and the never-retry rule.

## ADR review

No new ADR. The change adds one loop state, and no architecture record
changes meaning.
