# Proposal: add-ci-secret-scan

## Why

esf scans the patch as a distinct input beside the agent output. GitHub push
protection covers known provider shapes on push. It cannot know the literals
that live only in the operator configuration, and it does not examine pull
request diffs. Proposal P5 of
`reports/2026-11-07-issue-100-esf-analysis.md` asks for a CI gate that closes
that gap.

## What changes

- `tools/sec_scan/sec_scan.py` gains a `--diff REF` mode. The mode scans only
  the lines the diff adds against the reference, with the new-file line
  numbers. The tool reads operator literal secrets from the
  `SECRET_SCAN_LITERALS` environment variable, splits it on newlines, and
  reports a literal finding with a hash prefix, never the value.
- A new workflow file `.github/workflows/secret-scan.yml` runs the tool in
  diff mode on every pull request and on workflow dispatch. It carries no
  paths filter, so a pull request under `fde/` still gets the scan. A finding
  fails the job.
- `tests/sec_scan/` gains the diff-mode tests with a fake runner.
  `tests/claude_infra/test_secret_scan_workflow.py` pins the workflow file.

## Out of scope

- No history scan in CI. The tree and history scans stay manual through the
  sec-scan skill.
- No revocation in CI. `--revoke` stays a local, flagged action.
- The CI gate whitelist keeps `sec_scan` out for now. The whitelist ratchet
  for this tool is a follow-up, because a first mutation run may surface
  pre-existing survivors outside this diff.
