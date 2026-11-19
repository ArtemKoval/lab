## Purpose

A referral hands the decision to the lead librarian. The lead resolves a
referred request on its case page: the loan is issued through the pack's
effect, or the request is declined in the lead's words. Nobody else can
resolve a referral, and nothing but a referred request can be resolved
this way.

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
