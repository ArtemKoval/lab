# crm-library-domain Specification

## Purpose


The library pack runs the loan desk of Northgate Public Library on the crm
engine. Librarians work loan requests against the membership rules, the loan
term in days is the pack's numeric outcome, and a term over 14 days needs the
lead librarian's sign-off. The pack carries the words, the rules, the seed
data, the instructions, and the evals of the domain, and the engine reads it
through the one loader with no engine edit.

## Requirements

### Requirement: The manifest of the pack
The pack at `crm/domains/library/` SHALL carry a manifest with all twelve
keys the validator requires. The name is `library`, and `engine_api` is 2.
The settings carry `award_approval_limit` at 14.0, and `config` describes
that setting. The documents are `wording` and `manual`, the two names the
engine serves. The
seed names the five files. The resolutions are `approve`, `decline`, and
`refer`. The outcome `loan` binds to `resolve`, and the effect on `loan` is
gated.

#### Scenario: The validator passes the pack
- **GIVEN** the pack folder with all of its files
- **WHEN** `uv run python validate.py library` runs from `crm/`
- **THEN** the exit code is 0, and no finding names a pack file

### Requirement: The pack is loadable
The loader SHALL load the pack when `CRM_DOMAIN` names `library`, with no
loader edit. The pack tests SHALL load the pack and SHALL pin the rules and
protocol contract signatures.

#### Scenario: The loader loads the pack
- **GIVEN** `CRM_DOMAIN` set to `library`
- **WHEN** the engine loads the pack
- **THEN** the manifest passes the declaration examinations, and the pack is the active pack

### Requirement: The loan term arithmetic
The rules module SHALL define `work_out_award(contract, plans, request,
approval_limit)`. The request line SHALL carry the kind `item`, the `nights`
field with the requested days, and zero hours. The arithmetic SHALL read the
requested days from the `nights` field, SHALL cap the term at the tier field
`max_loan_days`, SHALL record every step, and SHALL return the term in days.

#### Scenario: A standard checkout holds 14 days
- **GIVEN** a standard membership, and a request with one line of 14 nights
- **WHEN** `work_out_award` computes the term
- **THEN** the award is 14, and the steps name the base term of the plan

#### Scenario: A term over the tier cap is truncated
- **GIVEN** a research membership with `max_loan_days` at 28, and a request with one line of 35 nights
- **WHEN** `work_out_award` computes the term
- **THEN** the award is 28, and one step names the cap of the tier

### Requirement: The sign-off question
The rules module SHALL define `needs_sign_off(award, approval_limit)`. It
SHALL return true when the term exceeds the approval limit of 14 days.

#### Scenario: A research renewal over the limit needs sign-off
- **GIVEN** a research membership, and a request with one line of 21 nights
- **WHEN** `work_out_award` computes the term, and `needs_sign_off` reads it
- **THEN** the award is 21, and `needs_sign_off` returns true

### Requirement: The protocol verbs
The protocol module SHALL define `resolve`, `gate`, `execute`, `summarize`,
and `metric`. `resolve` SHALL return the award of the rules for the case and
the request. `gate` SHALL return the sign-off question of the rules.
`execute` SHALL return the loan record with the title from the case record's
items and the days from the outcome. `summarize` SHALL return the worker
line with the days. `metric` SHALL return the days in the payload as a
number.

#### Scenario: Resolve returns the rules award
- **GIVEN** an approved case with its membership, and a request with one line of 14 nights
- **WHEN** `resolve` runs with the pack config
- **THEN** the award equals the award of `work_out_award` for the same request

#### Scenario: Gate asks the sign-off question
- **GIVEN** an outcome with the award at 21, and the approval limit at 14
- **WHEN** `gate` runs
- **THEN** it returns true

#### Scenario: The worker line names the days
- **GIVEN** an outcome with the award at 14
- **WHEN** `summarize` runs
- **THEN** the line names 14 days and the loan

#### Scenario: The loan record names the copy and the days
- **GIVEN** an approved case whose record items name one title, and an outcome with the award at 14
- **WHEN** `execute` runs
- **THEN** the record carries the title and 14 days

#### Scenario: The metric reads the days
- **GIVEN** a payload with the days at 14
- **WHEN** `metric` runs
- **THEN** it returns 14

### Requirement: The seed data of the pack
The seed files SHALL describe Northgate Public Library, two librarians with
the lead allowed over the limit, at least six borrowers, memberships on the
`standard` and `research` tiers, and at least eight loan requests with a
waiting status. Every seed record SHALL satisfy the engine record models.
The pack tests SHALL load every record into the engine models before the
smoke gate.

#### Scenario: Every seed record fits the engine models
- **GIVEN** the seed files of the pack
- **WHEN** the pack test loads each record into the engine model of its kind
- **THEN** no record raises, and the pack test passes

### Requirement: The seed fills the queue
The seed command SHALL fill the database from the pack including the
security files, and the same seed SHALL rebuild the same queue.

#### Scenario: The seed fills the queue
- **GIVEN** a fresh database, and `CRM_DOMAIN` set to `library`
- **WHEN** the seed command runs
- **THEN** the database holds the loan requests, the borrowers, the
  memberships, and the librarians of the pack, and every request waits

#### Scenario: The smoke run works three cases
- **GIVEN** the pack with its seed and its instructions
- **WHEN** `uv run python smoke.py library` runs from `crm/`
- **THEN** the exit code is 0, and three decision lines print

### Requirement: The policy documents carry the assignment rules
The wording `wording` SHALL carry the copy availability rule, the 14-day
term rule, the cap of three concurrent loans per borrower on both tiers, the
tier term caps, and the roles of the desk librarian and the lead librarian.
The manual `manual` SHALL state when a request goes to the lead.

#### Scenario: The wording names the loan cap
- **GIVEN** the wording document
- **WHEN** the document search reads the concurrent loan section
- **THEN** the section states the cap of three concurrent loans per borrower on both tiers

#### Scenario: The manual names the sign-off threshold
- **GIVEN** the librarian manual
- **WHEN** the document search reads the escalation section
- **THEN** the section states that a term over 14 days needs the lead

### Requirement: The instructions name served tools only
The instruction files SHALL name only the tools the engine serves, and SHALL
teach the line shape of the arithmetic requirement. The validator SHALL find
no upstream tool word in the instruction text. A pack test SHALL pin the
served tool list over the instruction files.

#### Scenario: The validator finds no upstream tool word
- **GIVEN** the instruction files of the pack
- **WHEN** `uv run python validate.py library` runs from `crm/`
- **THEN** no finding names an upstream tool word in the instructions

#### Scenario: The pack test pins the served tools
- **GIVEN** the instruction files of the pack
- **WHEN** the pack test collects the tool names in the text
- **THEN** every named tool is in the served list of the engine

### Requirement: The eval records
The decision evals SHALL give one expected decision for every seed case.
Each record SHALL carry the keys the seed reads: `case_id`, `decision`,
`award`, `tiny`, `reason`, and `reference`, plus pack extras. A pack test
SHALL prove that every seed case has a decision, and that the held-out
cases name no queued case.

#### Scenario: Every seed case has a pinned decision
- **GIVEN** the decision evals and the seed cases
- **WHEN** the pack test compares the two sets
- **THEN** every seed case id names a decision, and no held-out case id names a queued case

### Requirement: The eval coverage
The eval set SHALL cover an approved checkout, a declined request with no
copy free, a declined request at the loan cap, a referred special
collection request, and an approved renewal over the sign-off limit.

#### Scenario: The eval set covers the assignment rules
- **GIVEN** the decision evals
- **WHEN** the decisions are read
- **THEN** the set holds one approve, one decline for no copy, one decline
  for the cap, one refer, and one approve over the limit

### Requirement: The e2e flow runs the library pack
The e2e suite SHALL accept `CRM_DOMAIN=library`. With it, the worker
selection and the storage state SHALL follow the pack, the insurance specs
SHALL stay out of the run, and the library flow spec SHALL sign in a
library librarian, open the queue, open one loan request, and see the pack
words. Without it, the default run SHALL stay on the insurance pack with no
change.

#### Scenario: The library flow signs in and reads the queue
- **GIVEN** `CRM_DOMAIN` set to `library`, and the e2e stack up
- **WHEN** the library flow spec signs in as the lead librarian and opens the queue
- **THEN** the queue shows the seed loan requests of the library pack

#### Scenario: The default run stays on insurance
- **GIVEN** `CRM_DOMAIN` not set, and the e2e stack up
- **WHEN** the default e2e run finishes
- **THEN** the suite passes on the insurance pack as before

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

### Requirement: The desk's decision words
The library manifest's labels SHALL carry the three action words, Approve
and issue, Decline the request, and Refer to the lead librarian, and the
keys for the term in days, the reason, and the rule sections.

#### Scenario: The desk sees its words
- **GIVEN** a waiting request and Iris signed in
- **WHEN** the case page renders
- **THEN** the desk's form reads the loan desk's words, and the term
  carries the pack's days unit

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
