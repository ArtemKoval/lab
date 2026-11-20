## Purpose

The garage pack runs the repair desk of the AutoFix vehicle repair network
on the crm engine. Desk workers take customer calls as repair jobs, route
each job to a garage by the routing rules, and authorize the repair against
the vehicle's service agreement. The authorization amount is the pack's
numeric outcome, the pack prices it in pounds in its own records, and an
authorization over the 600 pound limit needs a service manager's
sign-off. The pack carries the words, the rules, the seed data,
the instructions, and the evals of the domain, and the engine reads it
through the one loader with no engine edit.

## ADDED Requirements

### Requirement: The manifest of the pack
The pack at `crm/domains/garage/` SHALL carry a manifest with all twelve
keys the validator requires. The name is `garage`, and `engine_api` is 2.
The settings carry `award_approval_limit` at 600.0, and `config` describes
that setting. The documents are `wording` and `manual`, the two names the
engine serves. The seed names the five files. The resolutions are
`approve`, `decline`, and `refer`. The outcome `authorization` binds to
`resolve`, and the effect on `authorization` is gated.

#### Scenario: The validator passes the pack
- **GIVEN** the pack folder with all of its files
- **WHEN** `uv run python validate.py garage` runs from `crm/`
- **THEN** the exit code is 0, and no finding names a pack file

### Requirement: The pack is loadable
The loader SHALL load the pack when `CRM_DOMAIN` names `garage`, with no
loader edit. The pack tests SHALL load the pack and SHALL pin the rules and
protocol contract signatures.

#### Scenario: The loader loads the pack
- **GIVEN** `CRM_DOMAIN` set to `garage`
- **WHEN** the engine loads the pack
- **THEN** the manifest passes the declaration examinations, and the pack is the active pack

### Requirement: The request line shape
The request line of an approved job SHALL carry the kind `item`, a
`description` with the fault text, a `quantity` at 1, the `amount` with the
estimated cost of the fault line, and zero nights and hours.

#### Scenario: The taught line builds
- **GIVEN** a request line with the kind `item`, the fault description, the quantity 1, and the amount 180
- **WHEN** the engine builds the line model
- **THEN** the model accepts the line

### Requirement: The authorization arithmetic
The rules module SHALL define `work_out_award(contract, plans, request,
approval_limit)`. The arithmetic SHALL sum the covered fault lines, SHALL
subtract the plan field `base_excess` once, SHALL floor the total at zero,
SHALL cap the total at the plan field `per_repair_cap`, SHALL record every
step, and SHALL return the authorization.

#### Scenario: A covered repair computes
- **GIVEN** a standard agreement with `base_excess` at 25 and `per_repair_cap` at 500, and a request with two covered lines of 180 and 120
- **WHEN** `work_out_award` computes the authorization
- **THEN** the award is 275, and the steps name the excess of 25

#### Scenario: A repair past the cap is truncated
- **GIVEN** a standard agreement with `base_excess` at 25 and `per_repair_cap` at 500, and a request with one line of 640
- **WHEN** `work_out_award` computes the authorization
- **THEN** the award is 500, and one step names the excess and one step names the cap of the plan

### Requirement: The sign-off question
The rules module SHALL define `needs_sign_off(award, approval_limit)`. It
SHALL return true when the authorization exceeds the approval limit of 600
pounds.

#### Scenario: A fleet repair over the limit needs sign-off
- **GIVEN** a fleet agreement with `base_excess` at 0 and `per_repair_cap` at 900, and a request with covered lines that total 720
- **WHEN** `work_out_award` computes the authorization, and `needs_sign_off` reads it
- **THEN** the award is 720, and `needs_sign_off` returns true

### Requirement: The protocol verbs
The protocol module SHALL define `resolve`, `gate`, `execute`, `summarize`,
and `metric`. `resolve` SHALL return the award of the rules for the case
and the request. `gate` SHALL return the sign-off question of the rules.
`execute` SHALL return the authorization record with the case reference and
the amount from the outcome. The decision reason names the chosen garage.
`summarize` SHALL return the worker line with the amount. `metric` SHALL
return the amount in the payload as a number.

#### Scenario: Resolve returns the rules award
- **GIVEN** an approved case with its agreement, and a request with two covered lines
- **WHEN** `resolve` runs with the pack config
- **THEN** the award equals the award of `work_out_award` for the same request

#### Scenario: Gate asks the sign-off question
- **GIVEN** an outcome with the award at 720, and the approval limit at 600
- **WHEN** `gate` runs
- **THEN** it returns true

#### Scenario: The worker line names the authorization
- **GIVEN** an outcome with the award at 275
- **WHEN** `summarize` runs
- **THEN** the line names 275 and the authorization

#### Scenario: The authorization record names the case and the amount
- **GIVEN** an approved case, and an outcome with the award at 275
- **WHEN** `execute` runs
- **THEN** the record carries the case reference and 275

#### Scenario: The metric reads the amount
- **GIVEN** a payload with the amount at 275
- **WHEN** `metric` runs
- **THEN** it returns 275

### Requirement: The seed data of the pack
The seed files SHALL describe the AutoFix network, at least two desk
workers with one service manager allowed over the limit, at least six
customers, agreements on the `standard`, `ev`, and `fleet` tiers, and at
least eight repair jobs with a waiting status. Every seed record SHALL
satisfy the engine record models. The pack tests SHALL load every record
into the engine models before the smoke gate.

#### Scenario: Every seed record fits the engine models
- **GIVEN** the seed files of the pack
- **WHEN** the pack test loads each record into the engine model of its kind
- **THEN** no record raises, and the pack test passes

### Requirement: The seed fills the queue
The seed command SHALL fill the database from the pack including the
security files, and the same seed SHALL rebuild the same queue.

#### Scenario: The seed fills the queue
- **GIVEN** a fresh database, and `CRM_DOMAIN` set to `garage`
- **WHEN** the seed command runs
- **THEN** the database holds the repair jobs, the customers, the
  agreements, and the desk workers of the pack, and every job waits

#### Scenario: The smoke run works three cases
- **GIVEN** the pack with its seed and its instructions
- **WHEN** `uv run python smoke.py garage` runs from `crm/`
- **THEN** the exit code is 0, and three decision lines print

### Requirement: The policy documents carry the routing rules
The wording `wording` SHALL carry the coverage rules of each plan tier,
with the covered fault classes, the base excess, the per-repair cap, and
the certified EV requirement of the EV tier. The manual `manual` SHALL
carry the routing order (brand first, then specialisms, then location, then
queue capacity), the certified EV gate, and the rule that sends an
authorization over 600 pounds to the service manager.

#### Scenario: The wording names the EV gate
- **GIVEN** the wording document
- **WHEN** the document search reads the EV tier section
- **THEN** the section states that an EV job goes to a garage with the certified EV mark

#### Scenario: The manual names the routing order
- **GIVEN** the service manager manual
- **WHEN** the document search reads the routing section
- **THEN** the section states the four routing steps in their order

#### Scenario: The manual names the sign-off threshold
- **GIVEN** the service manager manual
- **WHEN** the document search reads the escalation section
- **THEN** the section states that an authorization over 600 pounds needs the service manager

### Requirement: The instructions name served tools only
The pack SHALL carry the four instruction files `case`, `queue`, `recipe`,
and `improver`. They SHALL name only the tools the engine serves, and
SHALL teach the line shape of the arithmetic requirement. The validator
SHALL find no upstream tool word in the instruction text. A pack test SHALL
pin the served tool list over the four instruction files.

#### Scenario: The validator finds no upstream tool word
- **GIVEN** the instruction files of the pack
- **WHEN** `uv run python validate.py garage` runs from `crm/`
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
The eval set SHALL cover an approved standard repair, a declined job with a
fault the plan does not cover, a declined job on an expired agreement, a
referred EV job with no certified garage in the caller's city, and an
approved fleet repair over the sign-off limit.

#### Scenario: The eval set covers the routing and coverage rules
- **GIVEN** the decision evals
- **WHEN** the decisions are read
- **THEN** the set holds one approve, one decline for the fault class, one
  decline for the expired agreement, one refer for the EV gate, and one
  approve over the limit

### Requirement: The e2e flow runs the garage pack
The e2e suite SHALL accept `CRM_DOMAIN=garage`. With it, the worker
selection and the storage state SHALL follow the pack, the insurance specs
SHALL stay out of the run, and the garage flow spec SHALL sign in a desk
worker, open the queue, open one repair job, and see the pack words.
Without it, the default run SHALL stay on the insurance pack with no
change.

#### Scenario: The garage flow signs in and reads the queue
- **GIVEN** `CRM_DOMAIN` set to `garage`, and the e2e stack up
- **WHEN** the garage flow spec signs in as the service manager and opens the queue
- **THEN** the queue shows the seed repair jobs of the garage pack

#### Scenario: The default run stays on insurance
- **GIVEN** `CRM_DOMAIN` not set, and the e2e stack up
- **WHEN** the default e2e run finishes
- **THEN** the suite passes on the insurance pack as before

### Requirement: The garage-desk vocabulary of the pack
The garage manifest SHALL carry a vocabulary section with the `money` award
format, the repair-desk labels for the keys the dashboard renders, the
agreement card rows, and the refusal messages the pack authors in its own
words, with no amount placeholder that the engine fills. The vocabulary
SHALL carry no trip, traveler, or insurance word on a label.

#### Scenario: The queue speaks the repair desk
- **GIVEN** `CRM_DOMAIN` set to `garage`
- **WHEN** a desk worker opens the queue
- **THEN** the columns read the repair desk's words, and the estimate
  column carries no insurance word

#### Scenario: The agreement card renders
- **GIVEN** a case of a customer with an agreement
- **WHEN** a desk worker opens the case
- **THEN** the agreement section shows the agreement number, the tier, the
  covered vehicle, the vehicle make, the first-registered date, the
  service-due date, and the sold-through desk, and names none of plan,
  add-ons, trip, or travelers

#### Scenario: The over-limit refusal carries the pack's words
- **GIVEN** the garage pack's over-limit message
- **WHEN** the desk worker approves an authorization over the limit
- **THEN** the refusal states the sign-off rule in the pack's words, with
  no engine money prefix

### Requirement: The desk's decision words
The garage manifest's labels SHALL carry the three action words, Authorize
the repair, Decline the job, and Refer to the service manager, and the keys
for the amount label, the reason, and the rule sections.

#### Scenario: The desk sees its words
- **GIVEN** a waiting job and a desk worker signed in
- **WHEN** the case page renders
- **THEN** the desk's form reads the repair desk's words with the pack's
  amount label, and the award comes from the case items through the rules
