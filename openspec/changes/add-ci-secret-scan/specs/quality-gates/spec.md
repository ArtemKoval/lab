## ADDED Requirements

### Requirement: The CI secret-scan workflow
The repository SHALL carry a `secret-scan` workflow that runs on pull requests
and on workflow dispatch with no paths filter. The workflow SHALL run the
`sec_scan` tool in diff mode against the pull request base with the system
Python, SHALL pass the `SECRET_SCAN_LITERALS` environment through from the
repository secret of the same name, and SHALL fail on any finding. A workflow
contract test SHALL pin the file.

#### Scenario: A pull request with a planted key fails the workflow
- **GIVEN** a pull request whose diff adds an OpenRouter-shaped key
- **WHEN** the secret-scan workflow runs
- **THEN** the job exits non-zero and the output names the file and the line

#### Scenario: A clean pull request passes the workflow
- **GIVEN** a pull request whose diff adds no secret shape
- **WHEN** the secret-scan workflow runs
- **THEN** the job exits 0

#### Scenario: An fde-only pull request still gets the scan
- **GIVEN** a pull request that changes only files under `fde/`
- **WHEN** the repository events run
- **THEN** the secret-scan workflow still runs, because its trigger carries
  no paths filter
