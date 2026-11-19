## ADDED Requirements

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

#### Scenario: The lead declines the request
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
