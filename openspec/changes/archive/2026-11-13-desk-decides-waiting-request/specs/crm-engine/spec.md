## Purpose

A signed-in worker decides a waiting request at the desk, the way the
manual gives the desk its decisions: approve with a term, decline, or
refer to the lead. An approval over the limit holds for the lead's
sign-off, the same as the agent's.

## ADDED Requirements

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
