# Design: add-ci-secret-scan

## Plan review

The inner-loop review consulted the esf analysis report, the memory lessons,
and the two target specs. The review settled these decisions:

- Added lines only. A pre-existing secret in an untouched file must not block
  an unrelated pull request. The tree scan stays the manual authority through
  the sec-scan skill.
- Literals travel through the `SECRET_SCAN_LITERALS` repository secret into
  the job environment. They never sit on a command line and never enter the
  repository. The report shows a SHA-256 prefix of the literal, never the
  value.
- The scan lives in its own workflow file, because `paths-ignore` on the test
  workflow applies to every job in it. A separate file carries no paths
  filter, so an `fde/`-only pull request still gets the scan.
- The job runs the tool with the system Python, because the tool uses only the
  standard library. No venv build.
- Pushes to `main` stay with push protection. The workflow runs on pull
  requests and workflow dispatch only.
- Fork pull requests see no repository secrets, so the literal scan degrades
  to the built-in shapes there. The provider-shape scan always runs.

## ASIT pass

- Unification: the diff mode reuses the provider patterns, the entropy
  examination, the private-key rule, and the report of the existing tool. No
  second scanner.
- Division: the diff parser (file headers, hunk ranges, added lines) is
  separate from the rule application, so each half stays simple and testable.
- Breaking symmetry: the diff mode and the tree mode serve different trust
  boundaries (new content versus whole state), so they stay separate
  subcommands of one tool rather than one mode with flags.
- No new dependency, no new package, no new component kind.

## Spec deltas

- `sec-scan`: one added requirement, the diff scan, with the literal rule.
- `quality-gates`: one added requirement, the CI secret-scan workflow.

## Risks

- False positives from the entropy rule on synthesized fixtures. The fixtures
  in this repository are same-shape fakes, so the CI run may flag a fixture
  added in a future change. The failure message names the file and line, and
  the operator marks the fixture or tunes the value.
- The mutation gate does not cover `tools/sec_scan` today, because the CI
  whitelist omits the tool. This change keeps that gap and records it as a
  follow-up, so the diff-mode code still gets the full local gate run.
- The scan sees the net diff. A secret added and deleted inside one pull
  request never reaches the diff, and a direct push to `main` skips the
  workflow. Push protection backstops provider shapes. Operator literals
  carry no such backstop on those paths. The history scan through the
  sec-scan skill is the manual backstop.
