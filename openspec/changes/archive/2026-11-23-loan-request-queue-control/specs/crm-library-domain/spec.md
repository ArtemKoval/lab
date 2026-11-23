## ADDED Requirements

### Requirement: The queue page carries the loan-request control
The library pack's queue page SHALL carry an "Add a loan request" control
that opens a form with the member picker, the membership picker, the
title of the loan, the story, and the replacement price. Submitting the
form SHALL post the request through the API and refresh the queue. The
form SHALL surface a server refusal instead of a silent failure.

#### Scenario: The control adds a request that lands in the queue
- **GIVEN** the signed-in desk on the queue page
- **WHEN** the desk fills the form with an existing member, one of that
  member's memberships, a title, a story, and a replacement price, and
  submits
- **THEN** the queue refreshes and shows the new request with status
  waiting

#### Scenario: A server refusal surfaces in the form
- **GIVEN** the open form
- **WHEN** the desk submits a request naming a member the pack does not
  hold
- **THEN** the form shows the refusal message and the queue stays
  unchanged

### Requirement: The control renders from the pack vocabulary
The library pack's vocabulary SHALL carry the control's words under a
loan-request key, and the queue page SHALL render the control only when
that key is present. A non-library pack's vocabulary names no such key,
so its queue page carries no control. The words cover the control's
label, the member picker, the membership picker, the title, the story,
the replacement price, and the submit button.

#### Scenario: The pack words drive the control's labels
- **GIVEN** the library pack's vocabulary carrying the loan-request key
- **WHEN** the desk opens the control
- **THEN** the form reads in the pack's words: the control's label, the
  member picker, the membership picker, the title, the story, the
  replacement price, and the submit button

#### Scenario: A pack without the key shows no control
- **GIVEN** a pack whose vocabulary carries no loan-request key
- **WHEN** the desk reads the queue page
- **THEN** no loan-request control renders
