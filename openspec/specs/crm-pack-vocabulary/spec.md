# crm-pack-vocabulary Specification

## Purpose

The pack owns every domain word the product shows. The manifest carries a
vocabulary section, the pack endpoint serves it, and the dashboard renders
domain words from it. The contract panel reads no domain-specific field of a record on its
own, and the labels carry the pack's domain words. An award renders in the
pack's unit: money or days.

## Requirements

### Requirement: The vocabulary section of the manifest
The manifest MAY carry a `vocabulary` object with four keys. The vocabulary
SHALL use these shapes: `labels` maps stable key ids to the pack's words.
`award_format` is `money` or `days`. `messages` carries four templates
with brace slots: `over_limit` and `contract_not_found` for the backend,
and `senior` and `cant_sign_off` for the senior-worker refusal and the
copilot's refusal.

#### Scenario: The loader passes the vocabulary through
- **GIVEN** a manifest with a vocabulary section
- **WHEN** the engine loads the pack
- **THEN** the loader exposes the section to the pack endpoint

### Requirement: The contract rows of the vocabulary
The vocabulary's `contract` SHALL carry a `title` and `rows`. A row SHALL
name a `label` and one `field` with a `format`, or a `template` with
`{field}` slots and a `formats` map that names each field's format. A row
MAY carry an `empty` word to show when its field or fields hold nothing.

#### Scenario: A row composes two dates
- **GIVEN** a row whose template reads `{a} to {b}` with two date fields
- **WHEN** the panel renders the row
- **THEN** the row shows both dates in the row's label

### Requirement: The loader validates the vocabulary
The loader SHALL refuse a pack whose vocabulary names an unknown award
format or an unknown row format, and SHALL name the offending key. A pack
with no vocabulary section SHALL load with the engine's default words and
the `money` award format.

#### Scenario: The loader refuses an unknown award format
- **GIVEN** a manifest whose `award_format` is `pages`
- **WHEN** the engine loads the pack
- **THEN** the loader refuses the pack and names `award_format`

#### Scenario: A pack with no vocabulary section
- **GIVEN** a manifest with no vocabulary section
- **WHEN** the engine loads the pack
- **THEN** the pack loads, and the pack endpoint serves no vocabulary

### Requirement: The pack endpoint serves the vocabulary
`GET /api/pack` SHALL carry the pack's vocabulary section beside its
declarations. A pack with no vocabulary section SHALL leave the field absent.

#### Scenario: The endpoint serves the library words
- **GIVEN** `CRM_DOMAIN` set to `library`
- **WHEN** a signed-in worker calls `GET /api/pack`
- **THEN** the answer carries the library labels, the library contract rows,
  the `days` award format, and the library messages

### Requirement: Labels in the dashboard
The dashboard SHALL render a domain word from the pack's labels by key, with
the engine's current English words as the fallback when the labels name no
key. The dashboard SHALL hold one label lookup for every page.

#### Scenario: A library label replaces an insurance word
- **GIVEN** the library pack's labels map `case.incident` to `Received at`
- **WHEN** a librarian opens a case page
- **THEN** the field reads `Received at`

#### Scenario: The fallback word
- **GIVEN** a pack whose labels name no key for a label the page shows
- **WHEN** the page renders
- **THEN** the page shows the engine's current English word for that key

### Requirement: The contract renders from the pack's rows
The dashboard SHALL render the contract section from the pack's contract
rows over the contract record's fields. Each row shows its label beside the
field's value in the row's format: `text` as text, `date` as a date,
`money` as money, `days` as a number of days, and `list` as a list joined
with a comma and a space. A row whose field or fields hold nothing SHALL show its `empty` word
when the row names one, and SHALL not show otherwise.

#### Scenario: The library membership renders
- **GIVEN** the library pack with a Membership title and its rows
- **WHEN** a librarian opens a case of a borrower
- **THEN** the section shows the card number, the tier, the members, the
  validity dates, the home branch, and the loans held, with no insurance
  word

#### Scenario: An empty row stays hidden
- **GIVEN** a contract record with no add-ons
- **WHEN** the pack's rows name an add-ons row
- **THEN** the section shows no add-ons row

### Requirement: A pack with no rows keeps today's panel
A pack whose vocabulary names no contract rows SHALL keep the contract
panel the core ships today, until that pack declares its rows.

#### Scenario: A pack with no rows keeps today's panel
- **GIVEN** a pack whose vocabulary names no contract rows
- **WHEN** a worker opens a case with a contract
- **THEN** the panel renders as it does today, with today's fields

### Requirement: The award renders in the pack's unit
The dashboard SHALL render an award value through the pack's award format at
every award display: `money` as money, `days` as a number with its unit. The
backend SHALL compose the approval-limit refusal from the pack's
`over_limit` message with the limit in the pack's unit, and the
contract-not-found refusal from the pack's `contract_not_found` message.

#### Scenario: The library term renders in days
- **GIVEN** the library pack with the `days` award format
- **WHEN** a decision with a 14-day award shows its award
- **THEN** the award reads `14 days`, not `$14.00`

#### Scenario: The insurance award renders in money
- **GIVEN** the insurance pack with the `money` award format
- **WHEN** a decision with an award of 1350 shows its award
- **THEN** the award reads `$1,350.00`

#### Scenario: The library over-limit refusal
- **GIVEN** the library pack's over-limit message
- **WHEN** a desk librarian approves a term over 14 days
- **THEN** the refusal names days, not dollars

### Requirement: The settings input's unit follows the award format
The settings page SHALL label the approval limit's input with the pack's
unit: the `money` format keeps the dollars prefix, and the `days` format
shows the number with a days suffix and no dollars sign.

#### Scenario: The library limit's input
- **GIVEN** the library pack with the `days` award format
- **WHEN** the lead librarian opens the settings page
- **THEN** the approval limit reads 14 with a days label, and no dollars
  sign
