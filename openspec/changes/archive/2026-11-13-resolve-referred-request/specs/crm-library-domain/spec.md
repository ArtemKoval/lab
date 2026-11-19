## Purpose

The loan desk's words for the lead's resolution: the two actions on a
referred request, the term they carry, and the line the case shows after.

## ADDED Requirements

### Requirement: The loan-desk words for the resolution
The library manifest's labels SHALL carry the two action words, Issue the
loan and Decline the request, and the term label in days.

#### Scenario: The lead sees the two actions
- **GIVEN** a referred request and Rosa signed in
- **WHEN** the case page renders
- **THEN** the actions read Issue the loan and Decline the request, with
  the term asked in days

#### Scenario: The issued request tells the desk
- **GIVEN** a referred request the lead issued for 14 days
- **WHEN** the case page renders
- **THEN** the case carries the loan record the pack's execute gives, with
  the title and the days
