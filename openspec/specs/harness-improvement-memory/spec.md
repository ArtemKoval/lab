# harness-improvement-memory Specification

## Purpose

The harness improvement loop keeps the memory of its own improvement
attempts. A harness lesson names its recurring problem, and an attempt
ledger records what each application of the rule predicted and observed,
in which setting, with a verdict. The plan review pulls the lessons whose
problems name the touched surfaces, the plan cites them, the review round
holds the teeth, and the run writes the observed outcome back to the
lesson it cited. The capability covers the feature-pipeline text, the
agent-memory kit, and the merge-time hook.

## Requirements

### Requirement: A lesson record names its problem and keeps its attempts
A lesson record SHALL carry a problem line that names the recurring problem
in one sentence. A lesson record SHALL carry an attempt ledger. Each
attempt SHALL record the date, the session, the trigger, the prediction,
the observation, the setting, and a verdict of holds, misled, or
superseded. The ledger SHALL keep an attempt whose verdict reads misled or
superseded. No text outside the ledger SHALL rewrite an attempt.

#### Scenario: A lesson records its first attempt
- **GIVEN** a lesson record with a problem line
- **WHEN** a recurrence confirms or refutes the rule of the lesson
- **THEN** the attempt ledger gains one attempt with the trigger, the
  prediction, the observation, the setting, and a verdict

#### Scenario: A misled verdict keeps its attempt
- **GIVEN** an attempt whose observation refutes the rule in its setting
- **WHEN** the session records the attempt
- **THEN** the verdict reads misled and the ledger keeps the attempt

#### Scenario: A replaced rule keeps its outcome
- **GIVEN** a lesson whose fix a later change replaced
- **WHEN** the session records the replacement
- **THEN** the ledger holds an attempt with the superseded verdict and the
  observation of the replacement

### Requirement: The plan cites the lessons of the surfaces it touches
The inner-loop step 2, the plan review, SHALL pull every lesson whose
problem line names a surface the change touches. The plan SHALL cite each
pulled lesson by name. The review round SHALL raise one review finding per
plan when the plan touches a surface whose converted index line names a
problem and the plan cites no lesson.

#### Scenario: A plan cites an owning lesson
- **GIVEN** a lesson whose index line names the problem of a surface the
  change touches
- **WHEN** the plan review runs
- **THEN** the plan cites the lesson by name

#### Scenario: An uncited plan is a review finding
- **GIVEN** a change that touches surfaces whose converted index lines
  name two problems
- **WHEN** the plan cites neither lesson
- **THEN** the review round raises one review finding that names both
  uncited lessons

#### Scenario: A surface with no lesson needs no citation
- **GIVEN** a change that touches only surfaces with no lessons
- **WHEN** the plan cites no lesson
- **THEN** the review round raises no finding

#### Scenario: An unconverted index line carries no teeth
- **GIVEN** a surface whose index line does not yet name a problem
- **WHEN** the plan touches that surface and cites no lesson
- **THEN** the review round raises no finding for that surface

### Requirement: The run writes the observed outcome back
The inner-loop result review SHALL append an attempt to the ledger of every
cited lesson whose rule the run exercised, when the run confirms or refutes
that rule, in the same session. A citation whose rule the run never
exercised SHALL gain no attempt. A miss SHALL open no new lesson file
unless the problem is new.

#### Scenario: A held lesson gains an attempt
- **GIVEN** a plan that cites a lesson
- **WHEN** the run exercises the rule of the lesson and the rule holds
- **THEN** the ledger of the lesson gains an attempt with the verdict holds

#### Scenario: A cited but unexercised lesson gains no attempt
- **GIVEN** a plan that cites a lesson
- **WHEN** the run never reaches the path the rule governs
- **THEN** the ledger of the lesson gains no attempt

#### Scenario: A misled lesson gains an attempt
- **GIVEN** a plan that cites a lesson
- **WHEN** the run exercises the rule of the lesson and the rule fails in
  this setting
- **THEN** the ledger of the lesson gains an attempt with the verdict
  misled and the setting field names the setting of the failure

### Requirement: The merge nudge names the write-back
The merge-time hook SHALL carry a fixed nudge that names the write-back of
cited-lesson outcomes beside the session close.

#### Scenario: The nudge reaches the session after a merge
- **GIVEN** a valid memory config and a merge command that the hook matches
- **WHEN** the hook injects its nudge
- **THEN** the nudge names the write-back of cited-lesson outcomes and the
  session close

### Requirement: Step 14 carries the write-back with no skip conflict
The Reflect sub-step of Step 14 SHALL hold the write-back discipline as a
shipped discipline. The Step 14 header SHALL name the write-back clause as
exempt from the skip rule. The reflection skill itself and the Analyse
sub-step stay skipped under the header rule.

#### Scenario: The skip text and the Reflect text agree
- **GIVEN** the Step 14 header skip rule
- **WHEN** a reader reads the Reflect sub-step
- **THEN** the Reflect sub-step presents the write-back as shipped and the
  header text names the write-back exemption alone

### Requirement: A store lesson gains its attempt on recurrence
The agent-memory kit SHALL append the attempt to the body of a lesson issue
on the first recurrence of its problem. The append SHALL keep the earlier
body text unchanged.

#### Scenario: A recurring store lesson gains its attempt
- **GIVEN** a lesson issue in the memory store
- **WHEN** its problem recurs in a later session
- **THEN** the session appends one attempt with the trigger, the prediction,
  the observation, the setting, and the verdict to the issue body

### Requirement: The index line names the problem and the setting
The memory index line of a converted lesson SHALL name the problem and the
setting beside the title and the link. The index lines of unconverted
lessons SHALL stay unchanged until their lessons convert.

#### Scenario: A converted lesson carries the full index line
- **GIVEN** a lesson that the conversion covered
- **WHEN** a reader scans the memory index
- **THEN** the line of the lesson names the problem and the setting beside
  the title and the link

#### Scenario: An unconverted lesson keeps its line
- **GIVEN** a lesson that the conversion did not cover
- **WHEN** a reader scans the memory index
- **THEN** the line of the lesson stays in its prior shape
