# Tasks: port-crm-whole-tree-lint-fixes

Every command in this file runs from the worktree `crm/` directory.
`WTV` names the main checkout venv at
`/Users/art/Documents/git/lab/crm/.venv/bin`, and `NM` names the main
checkout node modules at `/Users/art/Documents/git/lab/crm/node_modules`.
The worktree has no `.venv` and no `node_modules` of its own.

## 1. Port the ruff fix

- [ ] 1.1 Move the `dataclasses.replace`, `case_requests`, and
  `domains.loader` imports in `crm/backend/tests/test_ported_refusals.py`
  to the top level. Remove the 7 deferred imports.
- [ ] 1.2 Arbitrate: `$WTV/ruff format --check backend/tests/test_ported_refusals.py`,
  then `$WTV/ruff check backend/tests/test_ported_refusals.py`, then
  `$WTV/python -m pytest backend/tests/test_ported_refusals.py -q`.

## 2. Port the pyright fixes

- [ ] 2.0 Reproduce: `$NM/.bin/pyright --threads` from the worktree
  `crm/`. Record the 9 error rows in the run notes. Every row maps to
  one task below. A row with no task gets a new task before the port
  starts.
- [ ] 2.1 Remove the dead `award: float` field from `DecisionRequest`
  in `crm/agent/api.py`. Arbitrate:
  `$WTV/python -m pytest agent/tests -q`.
- [ ] 2.2 Type the `payload` parameter of `gated` in
  `crm/backend/main.py` as `dict | None`.
- [ ] 2.3 Make `run_effect` in `crm/backend/main.py` raise 500 with a
  message when the effect record is absent.
- [ ] 2.4 Feed `outcome_line(...) or ""` to `HeldAward.outcome` in
  `crm/backend/runs.py`.
- [ ] 2.5 Arbitrate the 2.2 to 2.4 fix group:
  `$WTV/python -m pytest backend/tests -q`.
- [ ] 2.6 Assert `spec` and `spec.loader` before `module_from_spec` in
  `crm/backend/tests/test_protocol.py`. Arbitrate:
  `$WTV/python -m pytest backend/tests/test_protocol.py -q`.
- [ ] 2.7 Type `a_row` in `crm/backend/tests/test_scoreboard.py` as
  `RowMapping` through `cast`. Arbitrate:
  `$WTV/python -m pytest backend/tests/test_scoreboard.py -q`.

## 3. Prove the whole-tree check

- [ ] 3.1 Link `$NM` to `crm/node_modules` in the worktree, then run
  the whole-tree chain from the worktree `crm/`: `$WTV/ruff format --check`,
  `$WTV/ruff check`, `$NM/.bin/pyright --threads`, and
  `$WTV/python -m pytest -q -n auto --dist worksteal`. All four exit 0.
  The chain mirrors `npm run check:python`. The script itself resolves
  through `uv run` and builds a fresh worktree venv, so the linked
  paths stand in for it on this host. The unlink of the link at clean-up
  is part of this task.

## 4. Carry the gate in the gate list

- [ ] 4.1 Add the whole-tree `npm run check:python` line to the Gates
  section of `.claude/skills/crm-app/SKILL.md`.
- [ ] 4.2 Add the enforcing test to `tests/crm_infra/test_crm_infra.py`.
  It reads the Gates section of the crm-app skill and asserts the
  whole-tree command name.

## 5. Gates and merge

- [ ] 5.1 `openspec validate port-crm-whole-tree-lint-fixes --type
  change --strict` passes.
- [ ] 5.2 `tools/spec_ste_check` passes on every artifact of this
  change.
- [ ] 5.3 The root suite passes. The 7 lock-affected scan failures in
  the primary checkout do not count against this change.
- [ ] 5.4 The crapper, dryer, and mutator gates pass on the changed
  product modules `backend/main.py` and `backend/runs.py`, in the
  documented per-module gate shape.
