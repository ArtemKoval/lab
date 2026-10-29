## ADDED Requirements

### Requirement: The case queue
The API SHALL list every case with its status. A status is one of waiting, in progress, waiting for sign off, or decided. The queue page SHALL show each case and its standing.

#### Scenario: Queue lists cases with statuses
- **GIVEN** a seeded queue with one waiting case and one decided case
- **WHEN** the user opens the queue page
- **THEN** the page shows both cases with their statuses

### Requirement: The case detail
The case page SHALL show the story, the documents, the steps, the decision, its reason, and its section reference.

#### Scenario: Case page shows the full case
- **GIVEN** a case with a story, documents, and a decision
- **WHEN** the user opens the case page
- **THEN** the page shows the story, the documents, the steps, the decision, its reason, and its reference

#### Scenario: The page shows the agent steps
- **GIVEN** an agent that read two sections and recorded a decision on a case
- **WHEN** the user opens the case page
- **THEN** the page shows each step in order with its kind and content

### Requirement: The case start
The API SHALL move a waiting case to in progress once per attempt. The API SHALL refuse a second start with a conflict.

#### Scenario: Start moves a waiting case to in progress
- **GIVEN** a waiting case
- **WHEN** a client posts a start for the case
- **THEN** the case is in progress and the attempt count is one

#### Scenario: A second start is refused
- **GIVEN** a case in progress
- **WHEN** a client posts a start for the same case again
- **THEN** the API refuses the request with a conflict

### Requirement: Decisions
An approval SHALL carry a positive award. A decline or a referral SHALL carry an award of zero. The decision SHALL keep the reason and the section reference.

#### Scenario: Record a decline
- **GIVEN** a case in progress
- **WHEN** the agent records a decline with a reason and a section reference
- **THEN** the case is decided, the award is zero, and the decision keeps the reason and the reference

#### Scenario: An approval needs a positive award
- **GIVEN** a case in progress
- **WHEN** the agent records an approval with an award of zero
- **THEN** the API refuses the record with a validation error

### Requirement: The award limit and sign-off
An approval over the limit SHALL wait for a worker sign-off. The API SHALL refuse payment while the case waits. A sign-off SHALL pay the award once and record the worker.

#### Scenario: An approval over the limit waits
- **GIVEN** the approval limit in the settings
- **WHEN** the agent records an approval with an award over the limit
- **THEN** the case waits for sign off and a payment request is refused

#### Scenario: A worker signs off
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off
- **THEN** the case pays the award and the payment records the worker

### Requirement: Payment
The API SHALL pay an approved case under the limit once. The API SHALL refuse a second payment.

#### Scenario: Payment happens once
- **GIVEN** an approved case under the limit
- **WHEN** the agent pays the award and then pays again
- **THEN** the first payment succeeds and the second payment is refused

### Requirement: Queue runs
A run SHALL work the whole waiting queue and finish with a short summary. A run with a cap SHALL work cases up to the cap and leave the rest waiting. The run SHALL keep a to-do list with a state for each case. A to-do item is to do, in progress, done, or left for a worker. A case that is not started maps to to do. A case in progress maps to in progress. A decided or paid case maps to done. A case left for a worker maps to left for a worker.

#### Scenario: A run works the queue
- **GIVEN** a seeded queue with waiting cases
- **WHEN** the user starts a run without a cap
- **THEN** the run works every waiting case and finishes with a short summary

#### Scenario: A capped run leaves the rest waiting
- **GIVEN** more waiting cases than the cap
- **WHEN** the user starts a run with a cap
- **THEN** the run works cases up to the cap and the rest stay waiting

#### Scenario: The run keeps a to-do list
- **GIVEN** a run in progress
- **WHEN** the user opens the queue page
- **THEN** the page shows the to-do list with each item to do, in progress, done, or left for a worker

### Requirement: The failure path
A case that fails before a decision SHALL return to waiting. The run SHALL retry it within its cap. A case that fails twice SHALL stay left for a worker. A missed case is a waiting case within the cap that the run did not work. The run SHALL examine the queue at the end, work a missed case within the cap, and report one in its summary.

#### Scenario: A failed case returns to the queue
- **GIVEN** a case whose work fails before a decision
- **WHEN** the run moves on with cap room left
- **THEN** the case waits again and the run retries it

#### Scenario: A second failure leaves the case for a worker
- **GIVEN** a case that failed once
- **WHEN** its retry fails before a decision
- **THEN** the run leaves the case for a worker and never retries it

#### Scenario: The run works a missed case
- **GIVEN** a run with cap room left and a waiting case it did not plan
- **WHEN** the run reaches its end sweep
- **THEN** the run works that case before it finishes

#### Scenario: The run leaves a case past the cap
- **GIVEN** a run whose cap is spent
- **WHEN** the run reaches its end sweep
- **THEN** the run reports the waiting case as past the cap and does not work it

### Requirement: The fresh subagent
The harness SHALL hand each case to a subagent that starts clean. The subagent SHALL report one line with the decision and the award, or the failure. Each step SHALL land on its case.

#### Scenario: The subagent reports one line
- **GIVEN** a run working a case
- **WHEN** the subagent finishes the case
- **THEN** the run records one line with the decision and the award, or the failure

#### Scenario: Steps land on the case
- **GIVEN** a subagent working a case
- **WHEN** the subagent reads or decides
- **THEN** each step is recorded on that case

### Requirement: Document lookup
The agent SHALL search the documents by phrase and receive the sections that match. The agent SHALL read one section, and the case SHALL record the title, the number, and the content.

#### Scenario: Search finds sections
- **GIVEN** the seeded documents
- **WHEN** the agent searches one phrase
- **THEN** the search returns the sections that contain the phrase

#### Scenario: Read one section
- **GIVEN** a section found by search
- **WHEN** the agent reads it
- **THEN** the case records the document title, the section number, and the content

### Requirement: The model call limit
The harness SHALL stop a case agent at its model call limit. The stopped case SHALL take the failure path.

#### Scenario: The cap stops a case
- **GIVEN** a case agent at its model call limit
- **WHEN** the harness asks it to continue
- **THEN** the harness records a failure on the case and the case takes the failure path

### Requirement: The instructions page
The instructions page SHALL show the queue instructions and the case instructions.

#### Scenario: The page shows both instructions
- **WHEN** the user opens the instructions page
- **THEN** the page shows the queue instructions and the case instructions
