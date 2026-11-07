## ADDED Requirements

### Requirement: The scan
The `residue_scan` CLI SHALL carry a read-only `scan` subcommand that
examines the local typed branches against the merged and open pull request
lists and the commit count against the mainline. A typed branch whose pull
request is merged SHALL report as residue with its PR number, and a typed
branch with no commits ahead of the mainline SHALL report as residue. The
scan SHALL exit 0 on a clean repository and 2 when residue sits in the
repository.

#### Scenario: A merged branch reports with its PR number
- **GIVEN** a typed local branch whose pull request is merged
- **WHEN** the scan runs
- **THEN** the report names the branch as residue with the PR number

#### Scenario: A branch with no commits ahead reports as residue
- **GIVEN** a typed local branch whose commit count against the mainline is zero
- **WHEN** the scan runs
- **THEN** the report names the branch as residue

### Requirement: The exclusions and the failure
A typed branch with an open pull request SHALL stay off the report, and a
typed branch with unmerged commits and no pull request SHALL stay off the
report and the prune. A failed fact call SHALL exit 2, with the reason on
stderr.

#### Scenario: An open pull request keeps the branch off the report
- **GIVEN** a typed local branch with unmerged commits and an open pull request
- **WHEN** the scan runs
- **THEN** the report carries no entry for the branch

#### Scenario: Unclaimed work stays off the report and the prune
- **GIVEN** a typed local branch with unmerged commits and no pull request
- **WHEN** the scan runs
- **THEN** the report and the prune carry no entry for the branch

#### Scenario: A failed fact call fails the scan with the reason
- **GIVEN** a gh call that exits non-zero
- **WHEN** the scan runs
- **THEN** the scan exits 2 and stderr names the failed list

### Requirement: The prune
The CLI SHALL carry a `prune` subcommand that deletes the reported residue
behind an explicit subcommand name. The prune SHALL remove the registered
worktrees before it deletes the branches. A refused removal SHALL become one
note on stderr, the remaining entries SHALL still run, and the command SHALL
exit 2 when any note exists and 0 when every entry is gone.

#### Scenario: The worktree goes before its branch
- **GIVEN** a residue branch with a registered worktree
- **WHEN** the prune runs
- **THEN** the worktree removal happens before the branch deletion

#### Scenario: A refused removal notes and continues
- **GIVEN** one branch that refuses deletion
- **WHEN** the prune runs
- **THEN** stderr carries one note for that branch, the other entries run,
  and the exit code is 2

### Requirement: The sources stay behind the seam
The git and gh calls SHALL go through one injectable runner, and the
hermetic tests SHALL run with no network and no real git. The gitignore, the
worktree state, and the remote state SHALL stay untouched by a scan.

#### Scenario: The tests run hermetic
- **WHEN** the residue test suite runs on a clean clone
- **THEN** no test spawns a real git or gh call, and the suite passes with
  no network
