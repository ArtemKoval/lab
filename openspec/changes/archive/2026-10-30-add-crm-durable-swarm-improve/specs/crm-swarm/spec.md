## ADDED Requirements

### Requirement: The dispatcher
A dispatch SHALL work every case left in progress and every waiting case, oldest first, with at most N case agents at once. Code SHALL choose the cases and keep the run, with no model.

#### Scenario: A dispatch works the queue in parallel
- **GIVEN** a seeded queue and N case agents
- **WHEN** the user starts a dispatch
- **THEN** the dispatch works every waiting case with at most N at once and finishes with a summary built from the records

#### Scenario: One bad case never stops the dispatch
- **GIVEN** a dispatch in progress
- **WHEN** one case fails with an error
- **THEN** the dispatch retries it once and the other cases carry on

#### Scenario: A second start is refused
- **GIVEN** a dispatch or evaluation running
- **WHEN** the user starts another
- **THEN** the API refuses the start

### Requirement: Cost and time per case
The engine SHALL record the tokens, the cost, and the work time of each case. The record SHALL name the run it happened in, or no run when there is none. The work time SHALL leave out any wait for a sign-off.

#### Scenario: A run's totals are its own
- **GIVEN** a dispatch that worked cases
- **WHEN** the user reads the run
- **THEN** the run shows its own model cost and work time, failed attempts included

### Requirement: Evaluations
An evaluation SHALL work its own copies of a labelled set through the same dispatcher and case agent. The copies SHALL never show in the queue, a dispatch SHALL never carry them on, and nobody SHALL sign them off.

#### Scenario: An evaluation scores the labelled set
- **GIVEN** the queue set with the workers' decisions
- **WHEN** the user starts an evaluation
- **THEN** the evaluation works copies of the set and scores each decision against the workers'

#### Scenario: Evaluation copies stay out of the queue
- **GIVEN** an evaluation in progress
- **WHEN** the user reads the queue
- **THEN** the queue shows no evaluation copy

### Requirement: The scoreboard
The dashboard SHALL offer a scoreboard page. A worker starts a dispatch or an evaluation there and chooses N from 1 to 25. The page SHALL show the measures: decision accuracy, cost of mistakes, straight-through share, and cost and time per case.

#### Scenario: The scoreboard shows the measures
- **GIVEN** finished evaluations
- **WHEN** the user opens the scoreboard
- **THEN** the page shows the measures for each evaluation
