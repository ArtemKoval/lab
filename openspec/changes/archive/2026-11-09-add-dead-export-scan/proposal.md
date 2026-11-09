# Proposal: add-dead-export-scan

## Why

The lab gates cover complexity, coverage, duplication, and mutation.
A trivial dead export passes every lab gate today, because no test
imports it and the mutator cannot see it. Proposal P6 of
`reports/2026-11-10-issue-175-rea-analysis.md` requests the scan. rea
runs knip with all rules at error level, and a dead export fails the
build.

## What Changes

### The scan tool

A new stdlib CLI at `tools/dead_export_scan/` runs the Python dead
code detector vulture over the owned tool directories and reports the
findings. The CLI follows the house contract: `--paths` scopes the
scan, `--min-confidence` filters vulture's confidence, `--json`
carries `ok` and the findings, and exit 0 means a clean scan while
exit 2 means findings or an operational failure. The scan is
non-destructive and reads the tree. Vulture is the one third-party
dependency, pinned in `requirements.txt`.

### The opt-in posture

The scan starts as an opt-in report, in the pattern of sec-scan: a
registry unit and a skill make it discoverable, and no pipeline step
runs it. A later change promotes it to a gate when the first run
names real residue.

### The registry unit and the skill

The registry gains one unit for the scan, whose `check` command runs
a scoped scan over `tools/project_setup_setup` and expects a clean
exit. A skill in `.claude/skills/dead-export-scan/` gives the
commands and the reading of results.

## Capabilities

### New Capabilities

None. The scan follows the sec-scan pattern, and the sec-scan
capability spec stays scoped to secrets. The change declares
`skip_specs` and carries no delta.

### Modified Capabilities

None.

## Out of scope

- No promotion to a CI gate in this change. The report scopes the
  scan as an opt-in report, and the promotion is a later change with
  the first run's evidence.
- No fix of the findings in this change. The first run names residue,
  and a later change removes it.
- No whitelist machinery. Vulture's confidence filter covers the
  first runs, and a whitelist arrives when a false positive names
  itself.
- No CI wiring beyond the gate lists. The operator acknowledged the
  workflow and pin-test edits that add the new directory.

## Impact

- `tools/dead_export_scan/dead_export_scan.py`, `requirements.txt`,
  `ruff.toml`: the tool.
- `tests/dead_export_scan/test_dead_export_scan.py`: the tests.
- `.claude/skills/dead-export-scan/SKILL.md`: the skill.
- `tools/project_setup/registry.json`: the unit.
- `.github/workflows/tests.yml` and
  `tests/claude_infra/test_ci_workflow.py`: the gate lists, behind
  the operator acknowledgment.
- `CLAUDE.md`: one Projects section line.
