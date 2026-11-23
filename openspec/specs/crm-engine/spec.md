# crm-engine Specification

## Purpose

The crm engine runs a backoffice queue. AI case workers take cases,
read the policy documents by section, decide each case, and pay the
awards that a human signs off. This spec pins the week one behavior:
the queue, the decisions, the award limit, payment, queue runs, and
the harness failure path.

## Requirements

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
An approval SHALL carry the outcome the pack resolved for the attempt, as an
opaque payload. A decline or a referral SHALL carry no outcome. The decision
SHALL keep the reason and the section reference. The API SHALL refuse an
approval whose outcome the pack has not resolved on the attempt in flight.

#### Scenario: Record a decline
- **GIVEN** a case in progress
- **WHEN** the agent records a decline with a reason and a section reference
- **THEN** the case is decided, the decision carries no outcome, and the
  decision keeps the reason and the reference

#### Scenario: An approval needs a positive award
- **GIVEN** a case in progress whose outcome the pack has not resolved
- **WHEN** the agent records an approval
- **THEN** the API refuses the record with a validation error that names
  resolve_outcome

### Requirement: The award limit and sign-off
The pack's gate SHALL decide whether an approval waits for a worker sign-off,
under the limit in force. The API SHALL refuse to run the effect while the
case waits. A sign-off SHALL record the worker and the time and SHALL run the
held effect once. The case graph SHALL run the effect after the sign-off
resumes the case.

#### Scenario: An approval over the limit waits
- **GIVEN** the approval limit in the settings
- **WHEN** the agent records an approval whose outcome the pack's gate holds
- **THEN** the case waits for sign off and a request to run the effect is
  refused

#### Scenario: A worker signs off
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off
- **THEN** the sign-off records the worker and the time, and the effect runs
  once

#### Scenario: A worker signs off and the agent pays
- **GIVEN** a case waiting for sign off
- **WHEN** a worker signs off and the agent runs
- **THEN** the case resumes, and the effect run is already on the case

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

### Requirement: The case agent graph
The case agent SHALL be a hand-written graph with its own state, nodes, and edges. The graph SHALL keep every step recorded on the case, refusals returned to the model, and at most 30 model calls. The graph SHALL pay as a step for every approval and SHALL wait with an interrupt when the backend says the case needs a sign-off. The case agent SHALL have no pay tool.

#### Scenario: The graph keeps the middleware duties
- **GIVEN** a case agent working a case on the stub model
- **WHEN** the graph runs
- **THEN** each step lands on the case, a refusal returns to the model as text, and a thirtieth model call stops the case

#### Scenario: The graph waits with an interrupt
- **GIVEN** an approval over the limit
- **WHEN** the graph reaches the payment step
- **THEN** the graph stops at an interrupt with its state saved

### Requirement: Send-back on the case page
The case page SHALL carry a send-back form for a held case. The page SHALL show the sent-back decisions with who sent them and why.

#### Scenario: The page shows the sent-back decisions
- **GIVEN** a case with a sent-back decision
- **WHEN** the user opens the case page
- **THEN** the page shows the decisions with the worker and the reason

### Requirement: Take a sent-back case
A worker SHALL take a sent-back case back into their own work, which stops the agent's work on it.

#### Scenario: A worker takes the case
- **GIVEN** a sent-back case in progress
- **WHEN** a worker takes it
- **THEN** the agent's work on the case stops and the case stays with the worker

### Requirement: The traced case work
The case agent and the improver SHALL export their model-call traces
to the Langfuse server. Each case thread SHALL trace in its own
session. The improver's round SHALL trace in the round's session. A
run SHALL tag the traces of the cases it works with the run id. A
trace that cannot reach the server SHALL leave the work unchanged.

#### Scenario: A case traces in its thread session
- **GIVEN** the variables name the compose server
- **WHEN** the agent works a case
- **THEN** the trace carries the case's `case_id:thread_id` session and
  the work's trace name

#### Scenario: The improver traces its round
- **GIVEN** the variables name the compose server
- **WHEN** the improver works a round
- **THEN** the improver's traces carry the round's session and the
  `Improver` trace name

#### Scenario: A run tags the cases it works
- **GIVEN** a run works the queue
- **WHEN** the run works a case
- **THEN** the case's trace carries the run id as a tag

#### Scenario: An unreachable server leaves the work whole
- **GIVEN** the variables name an address that answers no request
- **WHEN** the agent works a case
- **THEN** the case decides as it decides without tracing, and no model
  call fails

### Requirement: The lead resolves a referred request
`POST /api/cases/{case_id}/resolution` SHALL accept a signed-in worker who
can sign off over the limit, with a body that names a resolution of `loan`
or `decline`.

#### Scenario: The lead issues the loan
- **GIVEN** a decided case whose decision is a referral
- **WHEN** the lead posts a `loan` resolution of 14 days
- **THEN** the outcome is recorded through the pack's resolve verb, the
  case's effect runs once, and the case shows the outcome's own line

#### Scenario: The lead declines the request
- **GIVEN** a decided case whose decision is a referral
- **WHEN** the lead posts a `decline` resolution with a reason
- **THEN** the case's decision reads a decline, with the lead as who
  decided it and the lead's reason as the reason

### Requirement: The loan resolution issues through the pack
The `loan` resolution SHALL carry the term in days. The engine SHALL
resolve the case's declared outcome through the pack's resolve verb,
record the outcome, run the case's effect once, and return the case with
its outcome shown.

#### Scenario: The effect runs once
- **GIVEN** the lead posts a `loan` resolution twice
- **WHEN** the second post arrives
- **THEN** the route refuses it, because the effect has run

### Requirement: The decline becomes the case's decision
The `decline` resolution SHALL carry a reason. The engine SHALL record the
decline as the case's decision, with the worker as who decided it and the
worker's reason as the reason. A case whose effect has run SHALL refuse
every resolution.

#### Scenario: The posted decline becomes the decision
- **GIVEN** a decided case whose decision is a referral
- **WHEN** the lead posts a `decline` resolution with a reason
- **THEN** the case's decision reads a decline, with the lead as who
  decided it and the lead's reason as the reason

#### Scenario: An issued request refuses a second resolution
- **GIVEN** a referred request the lead already issued
- **WHEN** any resolution arrives for it
- **THEN** the route answers 409 and names the effect that has run

### Requirement: The resolution's refusals
The route SHALL refuse a worker who cannot sign off over the limit, a case
whose status is not decided, a case whose decision is not a referral, and
a resolution the body does not name.

#### Scenario: The desk librarian cannot resolve
- **GIVEN** a worker who cannot sign off over the limit
- **WHEN** the worker posts a resolution
- **THEN** the route answers 403 with the pack's senior words

#### Scenario: Only a referral resolves
- **GIVEN** a case whose decision is an approval or a decline
- **WHEN** a lead posts a resolution
- **THEN** the route answers 409 and names the referral it needs

### Requirement: The desk decides a waiting request
`POST /api/cases/{case_id}/worker-decision` SHALL accept a signed-in
worker on a case that waits or is left for a worker, with a body that
names a decision of `approve`, `decline`, or `refer`, with the reason and
the rule sections relied on.

#### Scenario: The desk approves at the base term
- **GIVEN** a waiting request and a desk librarian signed in
- **WHEN** the desk posts an approval of 14 days
- **THEN** the outcome is resolved through the pack, the decision carries
  the desk librarian as who decided it, the effect runs, and the case
  reads decided

#### Scenario: The desk declines or refers
- **GIVEN** a waiting request
- **WHEN** the desk posts a decline or a referral with a reason
- **THEN** the decision is recorded with the desk librarian as who
  decided it, and a referral leaves the lead's resolution form on the
  case

### Requirement: An over-limit approval holds for the lead
An approval whose term sits over the approval limit SHALL hold the case
for the lead librarian's sign-off, and the effect SHALL not run until the
lead signs.

#### Scenario: The desk proposes over the limit
- **GIVEN** a waiting request and a renewal to 21 days
- **WHEN** the desk posts an approval of 21 days
- **THEN** the case waits for sign-off, no effect has run, and the lead
  signs it off

### Requirement: The desk route's refusals
The route SHALL refuse a case that is in progress or already decided,
and SHALL refuse a body that leaves out the reason, the sections, or, on
an approval, the term and the benefit.

#### Scenario: A decided request refuses the desk
- **GIVEN** a case the agent already decided
- **WHEN** the desk posts a decision
- **THEN** the route answers 409

#### Scenario: A body without the sections
- **GIVEN** a body whose sections are blank
- **WHEN** the desk posts the decision
- **THEN** the route answers 422 and asks for the sections

### Requirement: The desk adds a case at run time
The API SHALL offer `POST /api/cases` behind the worker and agent guard.
The route SHALL write the new case straight to the database with status
`waiting`. The route SHALL refuse a customer or a contract the database
does not hold with a 404, and SHALL not touch the seed files. The route
SHALL set `submitted_on` to the current date when the request omits it,
and SHALL refuse a request whose summary, story, or items are missing or
empty.

#### Scenario: A created request lands in the queue as waiting
- **GIVEN** a seeded library database
- **WHEN** the desk posts a valid request for an existing customer and
  contract
- **THEN** the reply carries a generated case id with the pack prefix and
  a `waiting` status
- **AND** a following `GET /api/cases` lists the new case

#### Scenario: An unknown customer is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request naming a customer the database does
  not hold
- **THEN** the reply is 404 and no case row is written

#### Scenario: An unknown contract is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request naming a contract the database does
  not hold
- **THEN** the reply is 404 and no case row is written

#### Scenario: An empty summary is refused
- **GIVEN** a seeded library database
- **WHEN** the desk posts a request whose summary or story is empty, or
  whose item list carries no item
- **THEN** the reply is 422 and no case row is written

### Requirement: The case id comes from the pack's series
The route SHALL generate the case id from the pack's id series: the scan
runs over the cases that carry no evaluation copy marker, reads the
alphabetic prefix and the trailing number of the highest existing case
id, and takes the next number. A database with no cases at all SHALL
receive `C-1` as the first generated id.

#### Scenario: The id series skips past the seed
- **GIVEN** a library database whose highest case id is `LN-5003`
- **WHEN** the desk posts three valid requests in a row
- **THEN** the generated ids run `LN-5004`, `LN-5005`, `LN-5006` in order

#### Scenario: An evaluation copy does not move the series
- **GIVEN** a library database whose highest regular case id is `LN-5003`
  and whose highest evaluation copy id is `LN-5003-E7`
- **WHEN** the desk posts one valid request
- **THEN** the generated id is `LN-5004`, not a number read off the copy

#### Scenario: The first case in an empty database
- **GIVEN** a database whose case table holds no cases
- **WHEN** the desk posts one valid request
- **THEN** the generated id is `C-1`

### Requirement: The control's pickers read the desk's people and memberships
The existing customer search SHALL return every customer when the name
query is absent, and SHALL sit behind the same worker and agent guard as
the queue reads, returning the identifier and the name of every match.
The API SHALL offer `GET /api/customers/{customer_id}/contracts`,
returning only the contracts that belong to that customer.

#### Scenario: The customer list feeds the picker
- **GIVEN** a seeded library database
- **WHEN** the desk reads the customer search without a name query
- **THEN** every seed customer appears with the identifier and the name

#### Scenario: The contract picker filters by customer
- **GIVEN** two customers with separate contracts
- **WHEN** the desk reads the contracts of the first customer
- **THEN** only that customer's contracts come back
