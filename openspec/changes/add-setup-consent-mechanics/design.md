# Design: add-setup-consent-mechanics

## Plan review

The review kept the report proposal as the plan. ASIT: Multiplication,
with the justification that the consent rules need one code owner.
The house doctor contract is the existing pattern with two instances,
and the registry doctor is the third instance of that pattern,
parameterized by the registry file. The registry, the skill, and the
doctor contract all exist, and the change adds no new kind of
component.

Alternatives the review rejected:

- Rules in the skill only. The report asks for the mechanics as code,
  and prose cannot validate a registry or run a readback.
- A blanket install flag. rea's detect rule and the skill's CAUTION
  both refuse it, and one flag over 17 units hides what runs.
- Backup mechanics in the wiring doctors of this change. Their file
  writes belong to their own units, and the change keeps one subject.

## The doctor contract

The doctor follows the house contract: read-only by default, `--json`
with an `ok` field, `--repo-root`, exit 0 on success and 2 on
operational failure. The library part stays pure: the registry
validator and the plan builder take data and return data, and the CLI
part owns the process runs. The complexity of every function stays at
10 or less.

Semantics:

- Read-only run: validate the registry, run each unit's `check`
  command, and classify each unit as `present` or `absent`. Absent
  units are findings, not failures, because a clean clone starts with
  absent units. Exit 2 only for an invalid registry, an unknown unit
  in `--units`, a failed install, or a readback mismatch.
- `--install`: refuses a run without `--units`. Per named unit, the
  doctor runs the `check` and skips a present unit. For an absent
  unit, the doctor runs the `install` and re-runs the `check`. A unit
  whose `check` still fails is a readback mismatch and fails the run.
- `--json`: one object with `ok`, the per-unit plan, and the errors.
- The `check` field is a command list of words, and the `install`
  field is a list of words or a shell string. The doctor runs a list
  as argv and a string through the shell.

## Edge cases

- A registry that is not valid JSON, misses a required field, or
  repeats an id is invalid, and the doctor names the defect. The
  required fields are `id`, `kind`, `check`, and `install`. The `id`
  values are unique kebab-case names. `purpose` and `requires` are
  advisory and stay optional.
- A unit whose install is the stdlib note keeps the note as its
  install command, and the doctor reports it as a no-op line.
- `--units` with an id that the registry does not hold is an unknown
  unit, and the doctor exits 2 before any install runs.
- The doctor makes no file copies in this change, because no install
  it runs replaces a repository file. The backup rule binds the skill
  prose for the installers that do.

## Fixture registries

The tests build each fixture registry under a temporary directory, and
`--repo-root` names that directory. A fixture `check` and a fixture
`install` are argument lists of the test interpreter with `-c` one
liners, and the install one liners create or remove a marker file
inside the temporary directory. No fixture touches the machine
outside the temporary directory.

## The gate-list wiring

Task 1.4 edits `.github/workflows/tests.yml` in two places: the
whitelist alternation gains `project_setup_setup`, and the coverage
`--source` list gains the same directory. The pin tests
`test_workflow_whitelists_the_gated_roots` and
`test_workflow_measures_coverage_over_the_gated_roots` in
`tests/claude_infra/test_ci_workflow.py` gain the same directory, so
the pin matches the file. The operator acknowledged these protected
paths, and the merge of the implementation pull request carries the
acceptance.

## Verification

`tests/project_setup_setup/test_project_setup_doctor.py` covers the
validator, the plan, the install flow, the readback mismatch, the
blanket refusal, and the unknown unit, with fixture registries and
`check` commands built from the test interpreter. The guard for the
skill rules lives in the same test file. The suite pins the registry
unit through the existing registry examinations.
