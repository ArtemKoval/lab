## Purpose

The library pack speaks the loan desk's words everywhere the product shows
them. The labels cover the queue, the case page, the decisions, the history,
the evaluation and scoreboard tables, the settings, and the copilot cards.
The membership card renders from the pack's rows. The loan term shows in
days at every award display. The refusals name days, not dollars.

## ADDED Requirements

### Requirement: The loan-desk vocabulary of the library pack
The library manifest SHALL carry a vocabulary section with the `days` award
format, the loan-desk labels for the keys the dashboard renders, the
membership card rows, and the two refusal messages. The vocabulary SHALL
carry no trip, traveler, or insurance word.

#### Scenario: The queue speaks the loan desk
- **GIVEN** `CRM_DOMAIN` set to `library`
- **WHEN** a librarian opens the queue
- **THEN** the columns read the loan desk's words, and the borrower and
  replacement price columns carry no insurance word

#### Scenario: The membership card renders
- **GIVEN** a case of a borrower with a membership
- **WHEN** a librarian opens the case
- **THEN** the membership section shows the card number, the tier, the
  members on the card, the valid-from and valid-to dates, the home branch,
  the issued-at desk, the member-since date, and the loans held, and names
  none of plan, add-ons, trip, or travelers

#### Scenario: The over-limit refusal names days
- **GIVEN** the library pack's over-limit message
- **WHEN** the desk librarian approves a term over the limit
- **THEN** the refusal names the term in days
