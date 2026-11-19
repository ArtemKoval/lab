## Purpose

The loan desk's words for the desk's decision form: the three actions, the
term they carry, and the rule sections the desk relied on.

## ADDED Requirements

### Requirement: The desk's decision words
The library manifest's labels SHALL carry the three action words, Approve
and issue, Decline the request, and Refer to the lead librarian, and the
keys for the term in days, the reason, and the rule sections.

#### Scenario: The desk sees its words
- **GIVEN** a waiting request and Iris signed in
- **WHEN** the case page renders
- **THEN** the desk's form reads the loan desk's words, and the term
  carries the pack's days unit
