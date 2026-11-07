# sec-scan Specification

## Purpose
The sec-scan capability finds possibly exposed keys and secrets in this
repository before an outside reader does. The tool scans the working tree and,
on request, the git history. It names each finding with its file, line,
provider, and revoke path. Revocation is destructive, so it runs only behind an
explicit flag, and the OpenRouter revoke goes through the provisioning API. The
sec-scan skill owns the operator flow, and the fixture-secret rule keeps
synthesized same-shape fakes out of real secrets.

## Requirements

### Requirement: The scan
The `sec_scan` CLI SHALL scan the working tree for known secret shapes —
OpenRouter keys, AWS access keys, GitHub tokens, Slack tokens, private-key
blocks, and high-entropy assignments to credential-looking names — and SHALL
skip vendored, dependency, and ignored paths. Each finding SHALL name its
file, line, provider, and the revoke path. With `--history`, it SHALL scan
`git log -p` the same way.

#### Scenario: A planted key is found
- **GIVEN** a tree carrying a file with an OpenRouter-shaped key
- **WHEN** the scan runs
- **THEN** the finding names the file, the line, the provider, and the revoke path

#### Scenario: Vendored paths are skipped
- **GIVEN** a key under a node_modules directory
- **WHEN** the scan runs
- **THEN** no finding names that path

#### Scenario: History is scanned on request
- **GIVEN** a key that lived in a past commit and is gone from the tree
- **WHEN** the scan runs with `--history`
- **THEN** the finding names the commit and the path

### Requirement: The gated revocation
Revocation SHALL run only behind `--revoke`. An OpenRouter key SHALL be
disabled through the provisioning API when a provisioning key is in the
environment, and the disable SHALL be recoverable. Every other provider SHALL
print its exact manual revoke command and make no network call. Without
`--revoke`, the tool SHALL make no network call at all.

#### Scenario: A revoke without the flag touches nothing
- **GIVEN** a scan that found an OpenRouter key, and no `--revoke`
- **WHEN** the tool finishes
- **THEN** the report carries the revoke command and no network call was made

#### Scenario: A revoke with the flag disables through the provider
- **GIVEN** `--revoke` and an OpenRouter provisioning key in the environment
- **WHEN** the tool runs against the provider's API
- **THEN** the found key is disabled and the report says so

#### Scenario: A revoke without provider credentials names the manual path
- **GIVEN** `--revoke` and no provisioning key
- **WHEN** the tool finishes
- **THEN** the report prints the exact manual revoke command for each key
