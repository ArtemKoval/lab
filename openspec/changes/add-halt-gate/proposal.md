# Proposal: add-halt-gate

## Why

esf gives the operator `factory cancel` and `factory halt` with a dry run by
default. An unattended loop in this lab stops only when the operator kills the
session, and a kill loses the handover. Proposal P2 of
`reports/2026-11-07-issue-100-esf-analysis.md` asks for a halt file that the
deny hook honors, so the next model-backed call stops and the run can end
cleanly with its handover.

## What changes

- A new pure-bash hook at `.claude/hooks/halt-gate.sh`. When the halt file
  exists at `.claude/halt`, the hook exits 2 and stderr carries the reason
  from the file's first line, the file path, and the resume instruction. The
  hook has no Python dependency, so the deny works even when the gate tools
  or the shared venv are broken.
- The wiring gains one PreToolUse group with the same matcher as the
  peak-hours gate. The update-config skill owns the settings edit.
- The contract test at `tests/claude_infra/test_halt_gate_hook.py` pins the
  executable bit, the wiring, and the deny and allow paths.
- The gitignore gains `.claude/halt`, because the halt file is runtime state.
- CLAUDE.md gains the hooks line for the halt gate.

## Out of scope

- No CLI. The operator creates or deletes one file.
- No change to the peak-hours gate script or its posture. The two gates stay
  separate: the peak gate is an availability control and fails open, the halt
  is a safety control and fails closed once the root resolves.
