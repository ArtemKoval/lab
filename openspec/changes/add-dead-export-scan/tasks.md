# Tasks: add-dead-export-scan

## 1. The tool and the surfaces

- [ ] 1.1 Add `tools/dead_export_scan/dead_export_scan.py` with the
      scanner, the CLI, and `requirements.txt` with the pinned
      vulture, plus `ruff.toml` in the house pattern.
- [ ] 1.2 Add the skill at `.claude/skills/dead-export-scan/SKILL.md`.
- [ ] 1.3 Add the `dead-export-scan` unit to
      `tools/project_setup/registry.json`.
- [ ] 1.4 Add the new directory to the gate lists in the workflow and
      the pin test, behind the operator acknowledgment line on the
      implementation pull request.
- [ ] 1.5 Add the tool to the Projects section of `CLAUDE.md`.

## 2. Tests

- [ ] 2.1 Add `tests/dead_export_scan/test_dead_export_scan.py` with
      the fixture trees, the json shape, the dependency failure, and
      the CLI smoke test.

## 3. Spec and delivery

- [ ] 3.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [ ] 3.2 Run the root suite, ruff, and the quality gates on the
      changed paths.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
