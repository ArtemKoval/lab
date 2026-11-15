## MODIFIED Requirements

### Requirement: The CLI names the run sources
The CLI SHALL discover the newest session transcript of the current
project under the Claude Code projects root. The CLI SHALL accept
`--project-dir`, `--transcript`, and `--session` to name other
sources. The search SHALL look in the launch project directory
first, then in every project directory. The path order SHALL break
a tie. The named-session path SHALL NOT use the newest transcript.
The CLI SHALL exit 2 and name the session when a named session has
no match in the search scope.

#### Scenario: The default source is the newest transcript
- **WHEN** the build command runs with no session flags in a project
  whose directory holds transcripts
- **THEN** the command uses the newest transcript and exits 0

#### Scenario: A named session in another project directory is found
- **GIVEN** the project directory of the launch path does not hold
  the named session file
- **WHEN** the build command runs with `--session` and another
  project directory holds the session transcript at its top level
- **THEN** the command uses that transcript and exits 0

#### Scenario: The named project directory sets the search scope
- **GIVEN** the command carries `--project-dir` and `--session`
- **WHEN** the named session file is absent from that directory and
  present in another project directory
- **THEN** the command exits 2 and does not use the other directory

#### Scenario: The newest match wins the cross-project search
- **GIVEN** two project directories hold the named session file with
  different modification times
- **WHEN** the build command runs with `--session`
- **THEN** the command uses the newest match

#### Scenario: A named session with no match fails the build
- **GIVEN** no project directory holds the named session file
- **WHEN** the build command runs with `--session`
- **THEN** the command exits 2 and names the session
