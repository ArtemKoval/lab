## ADDED Requirements

### Requirement: The pipeline governs the long-run state
The `feature-pipeline` skill SHALL carry a ledger rule: a run that
crosses several steps starts a `plan_exec` ledger and appends one
entry at each step boundary. The skill SHALL carry a selective-reading
rule: a task with a long input saves the input to a file and reads it
with targeted, bounded reads, and never pastes whole documents into
the conversation.

#### Scenario: A reader finds the long-run rules
- **WHEN** a reader scans the `feature-pipeline` skill
- **THEN** the ledger rule and the selective-reading rule are present

## MODIFIED Requirements

### Requirement: The pipeline governs review reception and model selection
The `feature-pipeline` skill SHALL carry rules for receiving review findings: verify before fix, reasoned pushback, no performative agreement, and clarify before fix. The skill SHALL carry a model-selection rule for agent dispatch and the final review. The skill SHALL carry a dispatch checklist. Every agent brief carries the task verbatim, the state, the rejected options, the file pointers, the expected output shape, and one narrow retrieval command.

#### Scenario: A reader finds the review and model rules
- **WHEN** a reader scans the `feature-pipeline` skill
- **THEN** the review-reception and model-selection rules are present
- **AND** the dispatch checklist is present
