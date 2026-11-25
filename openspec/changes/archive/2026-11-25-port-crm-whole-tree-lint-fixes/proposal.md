# Proposal: port-crm-whole-tree-lint-fixes

## Why

A whole-tree `npm run check:python` on `crm/` fails before pytest.
Ruff names 7 deferred imports in `crm/backend/tests/test_ported_refusals.py`.
Pyright names 9 errors in `crm/agent/api.py`, `crm/backend/main.py`,
`crm/backend/runs.py`, `crm/backend/tests/test_protocol.py`, and
`crm/backend/tests/test_scoreboard.py`. The upstream contribution branch
at `ArtemKoval/undercover` carries the fixes, green. The gate list of a
`crm` change never ran the whole-tree command, so the handover gates of
the last runs stayed blind to both debts. Issue 247 orders the port.
Confidence: observed.

## What Changes

- The apply phase ports 6 surgical fixes from the contribution branch:
  the top-level imports in `test_ported_refusals.py`, the `award` field
  removal in `agent/api.py`, the `dict | None` payload type on `gated`,
  the 500 guard in `run_effect`, the `or ""` fallback in `runs.py`, and
  the None guards and the `RowMapping` cast in the two test modules.
- The `quality-gates` capability gains one requirement: the gate list of
  a `crm` change runs the whole-tree `npm run check:python` before the
  merge, with no module scope.
- The crm-app skill Gates section gains the whole-tree command line, so
  the documented gate list carries the gate.
- The enforcing test lands in `tests/crm_infra/test_crm_infra.py`,
  beside the existing skill pins.
- The upstream copy of `backend/main.py` also removes the `create_case`
  endpoint and its imports. That edit serves a different upstream
  milestone. It is out of scope. No task ports it, and no delta names it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `quality-gates`: one new requirement puts the whole-tree
  `npm run check:python` command in the crm gate list. Three scenarios
  pin the merge bar, the out-of-scope finding, and the skill text.

## Impact

- `openspec/specs/quality-gates/spec.md` changes through the archive
  sync of this change.
- 7 files under `crm/` change in the apply phase: the 6 named fixes,
  plus the screening pin that task 2.8 added when the whole-tree run
  surfaced the pre-existing notebook failure. Every fix restores
  intended behavior, so no crm capability carries a delta.
- `.claude/skills/crm-app/SKILL.md` gains one gate-list line.
- `tests/crm_infra/test_crm_infra.py` gains one enforcing test.
- The diff touches no protected gate path, so the pull request needs no
  `gate-integrity: acknowledged` line.
