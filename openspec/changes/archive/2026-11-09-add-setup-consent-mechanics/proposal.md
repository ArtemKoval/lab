# Proposal: add-setup-consent-mechanics

## Why

The project-setup skill examines the registry and asks for permission,
but no code owns the plan. Nothing validates the registry before the
interview runs, and the consent mechanics live only in prose. Proposal
P3 of `reports/2026-11-10-issue-175-rea-analysis.md` requests the
mechanics. rea plans every write in the open, keeps backups, and reads
the written file again before it claims success.

## What Changes

### The registry doctor

A new setup doctor in the house doctor contract examines the registry
and reports the plan. Read-only by default: it validates the registry
file and runs each unit's `check` command, and it names each absent
unit with its exact `install` command. `--install` refuses a blanket
run: it requires `--units` with an explicit unit list, runs the named
units' install commands, and re-runs each `check` command as the
readback. A readback mismatch is a failure. `--json` carries the plan
with an `ok` field. Exit 0 means a valid registry and verified
installs. Exit 2 names an invalid registry, an unknown unit, a failed
install, or a readback mismatch.

### The consent rules in the project-setup skill

The skill gains the mechanics as written rules. The doctor's read-only
run is the plan. Detection selects nothing, and only a unit with
explicit consent installs. The installer makes a backup copy of each
file it replaces. Any blanket consent flag covers only registry-owned
state.

### The registry unit

The registry gains one unit for the doctor, in the stdlib-only pattern
of sec-scan.

## Capabilities

### New Capabilities

None. The doctor follows the house doctor contract, and the registry
and the skill are harness surfaces with no capability spec.

### Modified Capabilities

None. The change declares `skip_specs` and carries no delta.

## Out of scope

- No backup mechanics inside the two wiring doctors
  (handover-telemetry-hook and dspy-gate). Their file writes keep
  their shape, and a later change can add backups there.
- No blanket install flag on the doctor. `--install` requires the
  unit list.
- No change to the interview protocol steps. The rules extend them.
- The CI gate lists name the owned tool directories in the workflow.
  Adding the new directory touches the workflow and its pin test, and
  both are protected gate paths. The operator acknowledges through the
  gate-integrity line on the implementation pull request.

## Impact

- `tools/project_setup_setup/project_setup_setup.py`: the doctor.
- `tests/project_setup_setup/test_project_setup_doctor.py`: the tests.
- `.claude/skills/project-setup/SKILL.md`: the consent rules.
- `tools/project_setup/registry.json`: one unit for the doctor.
- `CLAUDE.md`: one Setup section sentence for the doctor command.
- `.github/workflows` and `tests/claude_infra/test_ci_workflow.py`:
  the gate lists gain the new directory, behind the operator
  acknowledgment.
