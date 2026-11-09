# Tasks: add-retroactive-spec-mining

## 1. Package scaffold

- [x] 1.1 Create the `tools/spec_mining/` package with `__init__.py`, `__main__.py`, `cli.py`, `core.py`, and the house packaging files.
- [x] 1.2 Add `tests/spec_mining/` with a hermetic conftest and the injected runner fixture.
- [x] 1.3 Add `units.json` with the alias, project, and coverage maps built from the current tree, and pin it with a structure test.

## 2. Tree scan

- [x] 2.1 Write the tests first for the tree scan. The cases cover the uncovered unit and the alias keep-off rule.
- [x] 2.2 Implement the tree scan in `core.py` over the injected tree facts.
- [x] 2.3 Implement the tree walk and the units read in `cli.py` behind the runner seam.

## 3. Archive drift scan

- [x] 3.1 Write the tests first for the drift scan. The cases cover the drift entry, the synced clean case, and the no-delta skip.
- [x] 3.2 Implement the drift scan with the local scenario-name regex in `core.py`.

## 4. History ranking

- [x] 4.1 Write the tests first for the ranking over canned git facts.
- [x] 4.2 Implement the ranking in `core.py` and the one bounded `git log` call in `cli.py`.

## 5. Run output

- [x] 5.1 Write the tests first for the run layout. The cases cover the report set, the seeds outside `openspec/changes/`, and the same-day replace rule.
- [x] 5.2 Implement the `coverage.json` and `report.md` builders and the seed scaffold in `core.py`.

## 6. CLI contract

- [x] 6.1 Write the tests first for the exit 0 and 2 codes and the `--json` payload.
- [x] 6.2 Implement the `run` dispatch in `cli.py` and the `__main__.py` entry.

## 7. Skill and docs

- [x] 7.1 Write `.claude/skills/spec-mining/SKILL.md` with the commands, the exit codes, the report reading, and the seed to propose flow. The section warns that a rerun replaces the files the run owns and leaves the other files in place.
- [x] 7.2 Make the seed to propose section mandate the STE gate run when a seed enters `openspec/changes/`.
- [x] 7.3 Write `tools/spec_mining/README.md` with the purpose and the commands.
- [x] 7.4 Add the CLAUDE.md Projects line for the tool and the skill.
- [x] 7.5 Join the package to the CI coverage wiring. The files are `.coveragerc` (omit entry), the `--cov` line in `.github/workflows/tests.yml`, and the pin in `tests/claude_infra/test_ci_workflow.py`.

## 8. Gates and verification

- [x] 8.1 Run the full hermetic suite from the worktree and make it green.
- [x] 8.2 Hold 100 percent line and branch coverage on the new code and ratchet the floor.
- [x] 8.3 Hold cyclomatic complexity at 10 or less on every new function.
- [x] 8.4 Run the mutator on an out-of-tree copy and reach no survivors.
- [x] 8.5 Run the tool once against this repository and commit the run under `reports/spec_mining/`. The run names `spec_mining` itself as uncovered, because its spec lands at archive. The pull request review examines `units.json` and the run.
- [ ] 8.6 Run `openspec validate add-retroactive-spec-mining --type change --strict` before archive.
