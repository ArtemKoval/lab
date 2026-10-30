# crm-self-improvement Specification

## Purpose

The case agent's instructions, model, and reasoning effort live in
versions that workers approve. A judge grades explanations, an improver
follows recipes under spending limits, the backend keeps or rolls back
each version on the held-out runs, and workers sign in with roles.

## Requirements

### Requirement: Configurations in versions
The case agent's instructions, model, and reasoning effort SHALL make up one configuration kept in versions. Version one SHALL be the agent as ported. Each version SHALL record what changed, the reason, who proposed it, who approved it, and when. A dispatch and an evaluation SHALL record the version they used.

#### Scenario: A dispatch records its version
- **GIVEN** a current configuration version
- **WHEN** the user starts a dispatch
- **THEN** the dispatch records that version

#### Scenario: The configuration page shows versions
- **GIVEN** two versions of the configuration
- **WHEN** the user opens the configuration page
- **THEN** the page shows the current version, every version, and the diff to the one before

### Requirement: The judge
Each graded case SHALL carry a grade from F to A with a score from 0 to 3. It SHALL also carry two matches: the same grounds, and the same section. The judge's cost SHALL be recorded with its evaluation apart from the case agents' cost.

#### Scenario: The judge grades an explanation
- **GIVEN** an evaluation claim with the worker's reason and reference
- **WHEN** the judge grades the agent's explanation
- **THEN** the claim carries the grade, the score, and the two matches

### Requirement: Improver rounds
A worker who can sign off over the limit SHALL start and stop improver rounds. A round SHALL run the missing evaluations and follow its recipe. The round SHALL wait for a worker to approve or reject each proposal. The backend's keep-or-rollback verdict on the held-out runs SHALL end it. A proposal outside the models allowed SHALL go back without reaching a worker.

#### Scenario: A round proposes and waits
- **GIVEN** a round past its first evaluations
- **WHEN** the improver proposes a new version
- **THEN** the round waits and the improvement page shows the diff

#### Scenario: The verdict keeps or rolls back
- **GIVEN** an approved version with its held-out runs
- **WHEN** the backend applies the rule
- **THEN** a version that meets the objectives and improves one measure keeps, and any other rolls back

### Requirement: Spending limits
A round's spending limit SHALL cover the improver, its evaluations, and the judge. The round SHALL refuse an evaluation that costs more than what is left, and no new case SHALL start once the limit is spent.

#### Scenario: A round stops at its limit
- **GIVEN** a round at its spending limit
- **WHEN** the improver asks for another evaluation
- **THEN** the round refuses it and the affected version rolls back

### Requirement: Sign-in with roles
Workers SHALL sign in with an email and a password, with no sign-up. Every page SHALL need a signed-in worker. The backend SHALL examine the worker on every worker action. Only a worker who can sign off over the limit SHALL start or stop rounds, approve or reject proposals, or change settings.

#### Scenario: A worker signs in
- **GIVEN** a worker's email in the pack
- **WHEN** the worker signs in at the auth service
- **THEN** the dashboard shows the worker in the header with a way to sign out

#### Scenario: A worker without the role is refused
- **GIVEN** a signed-in worker who cannot approve over the limit
- **WHEN** the worker starts a round
- **THEN** the backend refuses with a named error

### Requirement: Settings
A worker who can approve over the limit SHALL change the settings. The settings are the approval limit, the objectives, the noise and tolerance, the round spending limit, and the agents at once. Each change SHALL record who made it and when. The models list SHALL come from the pack and SHALL not change on the page.

#### Scenario: A settings change records its author
- **GIVEN** a signed-in senior worker
- **WHEN** the worker changes the approval limit
- **THEN** the setting carries the worker and the time
