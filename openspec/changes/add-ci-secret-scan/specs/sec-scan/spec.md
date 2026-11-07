## ADDED Requirements

### Requirement: The diff scan
The `sec_scan` CLI SHALL accept `--diff REF` and SHALL scan only the lines
the diff adds against `REF`. Each finding SHALL name the new file path and
the new-file line number.

#### Scenario: An added key is found with its new line number
- **GIVEN** a diff that adds a provider key shape at new-file line 12
- **WHEN** the tool runs with `--diff` from the worktree root
- **THEN** the finding names the file and the line 12

#### Scenario: A deleted line is skipped
- **GIVEN** the diff removes a provider key from the tree
- **WHEN** the tool runs in diff mode
- **THEN** no finding names that line

#### Scenario: Context is not scanned
- **GIVEN** a diff body that carries a key on a context line
- **WHEN** the tool runs in diff mode
- **THEN** only added lines carry findings

### Requirement: The literal scan
In diff mode the tool SHALL read operator literals from the
SECRET_SCAN_LITERALS environment variable when the variable is set. A
literal finding SHALL name the provider operator literal and SHALL show a
SHA-256 prefix of the literal. The output SHALL not carry the literal value.

#### Scenario: A literal finding shows a hash prefix only
- **GIVEN** the variable carries one literal, and the diff adds it
- **WHEN** the tool runs in diff mode
- **THEN** the finding shows a hash prefix, and the value is absent from the output

#### Scenario: No variable makes no literal scan
- **GIVEN** the variable is unset
- **WHEN** the tool runs in diff mode
- **THEN** the scan matches only the built-in shapes
