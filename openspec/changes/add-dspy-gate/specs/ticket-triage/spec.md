## ADDED Requirements

### Requirement: Ticket triage assigns a severity and a routing team
The triage module SHALL assign a severity from P0 to P3 and a routing team to every ticket from the ticket text alone. The module SHALL be a hand implementation with no model call at eval time.

#### Scenario: Outage keywords route to on-call [surface: dspy-eval]
- **WHEN** the ticket text contains the phrase production down or the phrase data loss
- **THEN** severity = P0
- **AND** team = on-call

#### Scenario: Billing disputes route to billing [surface: dspy-eval]
- **WHEN** the ticket mentions a charge, a refund, or an invoice dispute
- **THEN** severity is one of P1, P2, P3
- **AND** team = billing

#### Scenario: General tickets route to general [surface: dspy-eval]
- **WHEN** the ticket text holds no outage keyword and no billing term
- **THEN** team = general
- **AND** severity is one of P1, P2, P3

#### Scenario: Escalation happens before reply [surface: dspy-eval, judge]
- **WHEN** a P0 ticket goes through the triage flow
- **THEN** the escalate tool runs before the reply step [judge: rubric = rubrics/escalation.md]
- **AND** no customer-facing text exists before the escalation record
