## MODIFIED Requirements

### Requirement: The CI gate derives its paths from the pull request diff
The gate step SHALL fetch the pull request base and SHALL derive the
changed gated paths from the diff. The whitelist SHALL be the owned
gated tools, `tools/saturation_pass`, and `tests/`. The crapper gate
SHALL cover changed product and test paths. The dryer and mutator
gates SHALL cover changed product paths only. The coverage run SHALL
include the test paths, so a changed test file scores its own
coverage.

#### Scenario: A clean CI checkout still gates the changed files
- **WHEN** the gate step runs in CI, where the working tree is clean
- **THEN** the tools receive the changed paths as explicit arguments
  and no step uses `--changed`

#### Scenario: The coverage input is the workflow coverage run
- **WHEN** the crapper gate step runs on a pull request
- **THEN** it reads the LCOV conversion of the coverage report the
  workflow coverage run produced, with the test paths among the
  measured sources

#### Scenario: A changed saturation pass file runs the gates
- **GIVEN** the installed gate units
- **WHEN** a pull request changes a file under `tools/saturation_pass`
- **THEN** the workflow runs the crapper, dryer, and mutator steps on
  that file