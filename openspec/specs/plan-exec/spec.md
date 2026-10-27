# plan-exec Specification

## Purpose
TBD - created by archiving change adopt-superpowers-harness-upgrades. Update Purpose after archive.

## Requirements

### Requirement: The tool extracts one task brief
The CLI at `tools/plan_exec` SHALL give a `brief` subcommand. The subcommand reads a plan file, extracts one task, and writes it to `task-<ID>-brief.md` under the given output directory. The task selector SHALL accept a plain number and a dotted `X.Y` number. The parser SHALL support section headings (`### Task N:`) and OpenSpec checkbox tasks (`- [ ] X.Y` with indented body lines).

#### Scenario: A dotted task extracts from a checkbox plan
- **WHEN** the command `brief --plan tasks.md --task 2.3 --out DIR` runs against a plan whose task `2.3` sits in a checkbox list with indented body lines
- **THEN** the file `DIR/task-2.3-brief.md` exists and carries the task title and its body lines
- **AND** the command exits 0

### Requirement: The brief subcommand fails cleanly and stays in bounds
The `brief` subcommand SHALL exit 2 with a message and no traceback for an unknown task, a non-numeric selector, or a missing plan file. It SHALL write only under the given output directory.

#### Scenario: An unknown task fails cleanly
- **WHEN** the command `brief --plan tasks.md --task 9.9 --out DIR` runs against a plan with no task `9.9`
- **THEN** the command exits 2 and names the missing task in its message
- **AND** no file appears under `DIR`

### Requirement: The tool packages a review diff
The CLI SHALL give a `package` subcommand. The subcommand runs `git log --oneline`, `git diff --stat`, and `git diff -U10` for a `BASE..HEAD` range in a repository. It writes them to one file named `review-package-<base7>-<head7>.md` under the given output directory. The placeholders `<base7>` and `<head7>` are the first seven characters of the resolved commit ids. The subcommand SHALL treat the repository as read-only, SHALL require `--base`, and SHALL create the output directory when missing.

#### Scenario: A commit range packages to one file
- **WHEN** the command `package --repo ROOT --base a1b2c3d --head e4f5a6b --out DIR` runs in a git repository that holds both commits
- **THEN** the file `DIR/review-package-a1b2c3d-e4f5a6b.md` exists and carries the commit list, the stat summary, and the diff
- **AND** the repository working tree is unchanged

### Requirement: The package subcommand refuses invalid ranges
The `package` subcommand SHALL exit 2 when the target is not a git repository, when base equals head, or when a named revision does not resolve.

#### Scenario: An invalid range fails cleanly
- **WHEN** the command `package --repo ROOT --base X --head X --out DIR` runs with equal base and head
- **THEN** the command exits 2 and names the problem

### Requirement: The tool keeps an append-only execution ledger
The CLI SHALL give a `ledger` subcommand with the actions `init`, `complete`, `task-rule`, and `show`. The ledger file sits at `<dir>/progress.md` and starts with the identity line `# plan_exec ledger - plan: <absolute plan path>`. The subcommand SHALL resolve the plan path to an absolute path before any comparison and SHALL never delete or rewrite ledger lines. `init` SHALL exit 0 without writing when the identity matches, and `show` SHALL print the ledger content.

#### Scenario: A completed task appends one line
- **WHEN** `ledger --plan plan.md --dir DIR complete --task 1.2 --tests "pytest -k task12" --result "3 passed"` runs against a ledger whose identity names `plan.md`
- **THEN** the ledger ends with the line `Task 1.2: complete (tests: pytest -k task12 -> 3 passed)`
- **AND** every earlier line is unchanged

#### Scenario: A ruling appends one line
- **WHEN** `ledger --plan plan.md --dir DIR task-rule --task 2.1 --what "split the parser" --why "complexity 14" --cost "a wrong split hides a bug"` runs against a ledger whose identity names `plan.md`
- **THEN** the ledger ends with a line of the form `Task 2.1: Ruling: <what> - <why> - <what it costs if wrong>`
- **AND** every earlier line is unchanged

### Requirement: The ledger refuses foreign or missing records
`ledger init` SHALL exit 2 when an existing ledger names another plan. The actions `complete`, `task-rule`, and `show` SHALL exit 2 when the ledger is missing or carries no identity line. The default ledger directory `<repo-root>/.plan_exec/<plan-basename>/` SHALL stay out of version control.

#### Scenario: A foreign identity refuses to append
- **WHEN** `ledger --plan other.md --dir DIR init` runs against a ledger whose identity line names `plan.md`
- **THEN** the command exits 2 and names both plan paths
- **AND** the ledger content is unchanged
