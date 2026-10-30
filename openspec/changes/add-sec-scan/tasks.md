# Tasks: add-sec-scan

## 1. The scanner

- [ ] 1.1 Write `tools/sec_scan/sec_scan.py`: the tree walk with the skipped-path set, the provider patterns, the entropy examination, the report, `--json`, `--history`, and `--revoke`.
- [ ] 1.2 Write the OpenRouter provisioning revoke behind `--revoke` and the manual revoke commands for AWS, GitHub, and Slack findings.

## 2. Tests

- [ ] 2.1 Write `tests/sec_scan/` with synthetic same-shape fixtures assembled at test time. They cover the tree findings, the skipped paths, the history scan, the entropy suspects, and the revoke gate.
- [ ] 2.2 Prove the no-network rule: without `--revoke`, the tool touches no network (the HTTP path is never imported into the call graph).

## 3. The skill and setup

- [ ] 3.1 Write `.claude/skills/sec-scan/SKILL.md`: the scan, the report, the revoke gate, and the fixture-secret lesson.
- [ ] 3.2 Register the tool in `tools/project_setup/registry.json` and the project-setup skill.

## 4. Delivery

- [ ] 4.1 Run the root suite, ruff on the new tool, and the gates on the changed paths.
- [ ] 4.2 Commit, push, open the pull request, and merge after review.
