# Spec Delta

## Purpose

Produces the installable artifacts for the three operating systems, with the Python runtime inside each one, and proves each artifact starts.

## ADDED Requirements

### Requirement: The build produces the per-OS targets
The build MUST produce: macOS dmg and zip for arm64 and x64, Windows NSIS installer for x64, and Linux AppImage for x64. The GitHub Actions workflow MUST produce all of these artifacts on one tag build.

#### Scenario: Tag build produces all artifacts
- **WHEN** the workflow runs on a tag
- **THEN** the artifacts of all targets appear as workflow outputs

### Requirement: Each artifact carries the embedded runtime
Each artifact MUST contain the CPython runtime tree and the dependency tree inside the app resources. The packaged backend MUST run from these trees with no system Python and no network.

#### Scenario: Clean machine runs the backend
- **WHEN** the app starts on a machine with no Python installed
- **THEN** the backend starts from the trees in the app resources

#### Scenario: Artifact holds the runtime
- **WHEN** the build finishes for one target
- **THEN** the artifact contains the interpreter and the dependency tree under the app resources

#### Scenario: Interpreter path sits in the resources
- **WHEN** the smoke test reads the interpreter path from the ready line
- **THEN** the path sits under the app resources and the backend started from it

### Requirement: The runtime is pinned and verified
A lock file MUST pin the runtime release tag and its sha256 for every target platform. The build MUST verify the checksum before it packs the runtime. A checksum mismatch MUST fail the build.

#### Scenario: Checksum passes
- **WHEN** the downloaded runtime matches the pinned sha256
- **THEN** the build packs the runtime into the app resources

#### Scenario: Checksum fails
- **WHEN** the downloaded runtime does not match the pinned sha256
- **THEN** the build stops with a checksum error

### Requirement: Each build runs a launch smoke test
After packaging, the build MUST start the packaged app and MUST confirm that the backend reports readiness within 60 seconds. The main process MUST write one readiness result line, with the outcome `ready` or the start failure, to its log file in the user data folder. The harness MUST read that line from the log file. A build whose smoke test fails MUST fail the job.

#### Scenario: Smoke test passes
- **WHEN** the packaged app starts and the log file holds the readiness line with the outcome `ready` within 60 seconds
- **THEN** the smoke test passes

#### Scenario: Smoke test fails
- **WHEN** the readiness line holds a start failure or does not appear within 60 seconds
- **THEN** the build job fails

#### Scenario: Linux start mechanics
- **WHEN** the Linux job runs the smoke test
- **THEN** the app starts under a virtual display and the AppImage starts with the extract-and-run option

#### Scenario: macOS start mechanics
- **WHEN** the macOS job runs the smoke test
- **THEN** the harness starts the binary inside the bundle directly

#### Scenario: Windows start mechanics
- **WHEN** the Windows job runs the smoke test
- **THEN** the harness starts the executable of the unpacked build

#### Scenario: Smoke test runs with a PATH without python
- **WHEN** the harness launches the packaged app with a PATH that holds no python entry
- **THEN** the backend still starts from the embedded tree

### Requirement: The v1 artifacts carry an ad-hoc signature only
The v1 build MUST use no Developer ID identity and no notarization. The macOS bundle MUST carry an ad-hoc signature, and the build MUST pin the macOS identity to the ad-hoc value. The packaging job MUST examine each macOS artifact and MUST confirm the ad-hoc signature state. The README MUST give the exact first-run steps per OS: the Gatekeeper `Open Anyway` path on macOS, the SmartScreen `More info` path on Windows, and the execute permission step on Linux.

#### Scenario: Ad-hoc signature state is checked
- **WHEN** the packaging job finishes a macOS build
- **THEN** the check confirms that the bundle carries the ad-hoc signature and no Developer ID identity

#### Scenario: README names the steps
- **WHEN** the user reads the README install section
- **THEN** it lists the first-run steps for macOS, Windows, and Linux
