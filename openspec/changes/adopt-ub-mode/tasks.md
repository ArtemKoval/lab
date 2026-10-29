# Tasks: adopt-ub-mode

## 1. Vendor the three gate tools

- [ ] 1.1 Copy the crapper working tree at `6fd92c4c9bcc56efb64a2f8743d5a2993bcfd42d` into `tools/crapper` without `.git`. Keep `LICENSE`, the `crapper` launcher, `src/`, `tests/`, `.gitignore`, and `uml`. Add the adoption note with the upstream URL and the pinned commit to its README.
- [ ] 1.2 Copy the dryer working tree at `66ff6d21a42c04afcad89c78a80066176d1294b0` into `tools/dryer` without `.git`. Keep `LICENSE`, the `dryer` launcher, `src/`, `tests/`, and `.gitignore`. Add the same adoption note shape to its README.
- [ ] 1.3 Copy the mutator working tree at `a5a0cb803b66e0cdb8bf471b3b08af701d424a41` into `tools/mutator` without `.git`. Keep `LICENSE`, the `mutator` launcher, `src/`, `tests/`, `.gitignore`, and `bugs/`. Add the same adoption note shape to its README.
- [ ] 1.4 Add `.metrics/` and `target/` to the root `.gitignore`.
- [ ] 1.5 Build the three unit venvs and install each tool editable with its dev extras plus `coverage`. Run the three vendored suites with the unit interpreters. Record the results, with the two zsh-dependent crapper failures as the known local failures.

## 2. Adopt the ub-mode skill

- [ ] 2.1 Write `.claude/skills/ub-mode/SKILL.md`. Keep the upstream body unchanged. The frontmatter carries `name: ub-mode`. The description uses the `Use when` form and names `/ub-mode` and the reduced principles. The `metadata.ported` block carries the upstream source, the pinned commit, and the unlicensed-upstream license note. Add one local gates section. It maps crapper, dryer, and mutator to the vendored commands and records the `uml-viewer` exclusion.
- [ ] 2.2 Commit `adr/0005-adopt-ub-mode-and-quality-tools.md` with this change. The record was authored during planning. Change it only when a decision moves during apply.

## 3. Fold the discipline into the pipeline

- [ ] 3.1 Verify the dryer boundary and exit codes against the vendored code (read `tools/dryer/src/dryer/cli.py`, run fixtures). Correct the `quality-gates` spec when the verified rule differs, before any other task in this section.
- [ ] 3.2 Add the subsection under the cross-cutting rules. It carries the three-phase frame and the five rules. The rules are: one decision in one place, data shape before logic, redesign from first principles, attack the premise, and subtract before you add.
- [ ] 3.3 Extend Step 3 with the discard rule: throw out a test that still passes when every function returns nothing.
- [ ] 3.4 Extend Step 10 with the commit message rule: why, what changed, and how you proved it.
- [ ] 3.5 Rewrite the Quality gates section to name the three vendored tools as the default gates with their commands and boundary semantics.

## 4. Register the setup units

- [ ] 4.1 Add one registry unit per tool in `tools/project_setup/registry.json` with `kind: dependency-file`. The install command builds the venv and installs the tool editable with dev extras plus `coverage`. The check command runs through the unit venv interpreter.

## 5. Wire CI

- [ ] 5.1 Extend `.github/workflows/tests.yml`: build the three unit venvs and run the three vendored suites from their vendored locations with the unit interpreters.
- [ ] 5.2 Add the gate derive step. Fetch the pull request base and list the changed gated paths. Exclude the vendored trees and the fixture path list. Pass the paths to the launchers as explicit arguments under the unit venv interpreters.
- [ ] 5.3 Convert the workflow coverage report to LCOV and pass it to the crapper and dryer gates with `--use-existing-coverage`.
- [ ] 5.4 Add the mutator gate step. Its arguments are the changed product paths only. Its test command is the root pytest suite through the shared venv. Cap the workers and set an explicit timeout.
- [ ] 5.5 Update `tests/claude_infra/test_ci_workflow.py`: flip the no-mutation pin and state the new mutation policy in the docstring.

## 6. Pin the adoption in tests

- [ ] 6.1 Add the contract tests in `tests/claude_infra/`. Pin the skill provenance with the exact `metadata.ported` field names. Pin the vendored layout with license files and README pins. Pin the registry units, the pipeline subsection and step edits, and the gates section wording. Pin the fixture exclusion list of the gate derive step.
- [ ] 6.2 Add `tests/quality_gates/test_ub_tools_e2e.py` behind `UB_TOOLS_E2E=1`. The fixture tree holds a conforming unit, a CRAP breach, a duplication breach, and a surviving mutant. Assert exits 0, 2, 2, and 3. Skip without the variable or a missing venv. Add `UB_TOOLS_E2E` to the `pytest.ini` marker docstring.

## 7. Update the docs

- [ ] 7.1 Update `CLAUDE.md`: Projects entries for the three tools and the skills note for `ub-mode`.
- [ ] 7.2 Update the root README: entries for the three tools and the skill.

## 8. Run the gates and verify

- [ ] 8.1 Run the full hermetic suite (`tools/zai_routing_audit/.venv/bin/python -m pytest`) and make it green.
- [ ] 8.2 Run the three gates with explicit paths on the repository-owned Python. Record the numbers. Fix violations in code this change touches. Record legacy violations with numbers in the handover issue.
- [ ] 8.3 Run `openspec validate adopt-ub-mode --type change --strict` and `tools/spec_ste_check` over `openspec/changes/adopt-ub-mode/` and `adr/0005`. Both pass before archive.

## 9. Close out

- [ ] 9.1 After the merge, open the handover issue. Put in the gate measurements, the mutation budget from the first CI run, and the known local failures.
