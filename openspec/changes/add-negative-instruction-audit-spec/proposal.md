# Proposal: add-negative-instruction-audit-spec

## Why

Issue 201 tracks the prototype tools that carry no OpenSpec capability
spec. The CLI at `tools/negative_instruction_audit/` shipped through PR
207 and carries no spec under `openspec/specs/`. The strict validate
expects one capability spec per shipped capability, and the
per-capability layout expects the file at
`openspec/specs/<name>/spec.md`. Debt item 1 of issue 201 orders this
spec change before any wide harness-text conversion. The operator
approved the change with the `human-approved` label.

## What Changes

### The spec delta

One delta at `specs/negative-instruction-audit/spec.md` under this
change. The delta records the observed behavior of the shipped CLI.
The requirements cover the harness surface selection, the sentence
extraction, the marker detection, and the pin classification. Further
requirements cover the report records, the two output formats, the
root selection, the exit codes, and the read-only guarantee.

### The ownership split

The tool owns the sentence detection and the pin classification. The
operator owns the contract judgment on the unpinned candidates. The
spec records the split in its Purpose section. The five documented
miss classes stay outside the recall by design.

### No code changes

This change writes no production code. The delta formalizes the
shipped behavior only. The apply phase maps every delta scenario to a
test and adds the missing tests, so the suite pins every scenario.

### Out of scope

- No behavioral eval. The dspy-gate `gates.yaml` and `rubrics/` sit
  outside this change, and the harness registry declares no such
  capability.
- No wide harness-text conversion and no marker-set expansion. Both
  wait until the operator orders a wide conversion.

## Capabilities

### New Capabilities

- `negative-instruction-audit`: The retroactive behavior spec of the
  shipped CLI at
  `tools/negative_instruction_audit/negative_instruction_audit.py`.
  The requirements cover the scan inputs, the sentence extraction, the
  marker detection, the pin classification, the report, the outputs,
  the root selection, the exit codes, and the read-only guarantee.

### Modified Capabilities

None.

## Impact

- `openspec/specs/negative-instruction-audit/spec.md`: the archive
  step creates this file from the delta. No file exists today.
- `tools/negative_instruction_audit/`: no code change. The README
  keeps the commands, the exit codes, and the limits.
- `tests/negative_instruction_audit/`: the apply phase adds the tests
  for the scenarios that no existing test covers. The review round
  counted 13 such scenarios at proposal time.
- `CLAUDE.md`: no change. The Projects entry for the tool exists.
- Gates: `openspec validate add-negative-instruction-audit-spec
  --type change --strict` and `tools/spec_ste_check` pass on the
  change text before archive.
- No dspy-gate `gates.yaml`, no `rubrics/`, and no registry unit. The
  harness registry declares no such capability.
- No `.claude/settings.json` change and no CI change. The suite path
  and the coverage entry are already in `.github/workflows/tests.yml`.
- No dependency change. The tool and the tests use the standard
  library and the shared zai venv interpreter.
