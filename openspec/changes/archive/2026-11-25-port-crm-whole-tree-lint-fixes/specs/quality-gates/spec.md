## ADDED Requirements

### Requirement: The crm gate list runs the whole-tree python check
The gate list of a `crm` change SHALL run the whole-tree command
`npm run check:python` from the `crm/` directory before the merge.
The command SHALL pass on the whole `crm/` tree, with no module
scope. A finding outside the changed modules SHALL block the merge
until the change carries the fix. The Gates section of the crm-app
skill SHALL name the command.

#### Scenario: The whole-tree command gates a crm change
- **WHEN** a `crm` change reaches its gate list
- **THEN** the whole-tree `npm run check:python` command runs from
  `crm/`, and its exit 0 is the merge bar

#### Scenario: A finding outside the changed modules blocks the merge
- **GIVEN** a whole-tree run that names a finding in a module the
  change did not touch
- **WHEN** the gate list runs
- **THEN** the change carries the fix before the merge, and no scoped
  run replaces it

#### Scenario: The skill text carries the command
- **WHEN** a reader opens the Gates section of the crm-app skill
- **THEN** the section names the whole-tree `npm run check:python`
  command in the gate list
