## ADDED Requirements

### Requirement: The CI mutation gate holds the saturation bar
The CI mutator step SHALL fail the pull request on any non-zero
mutator exit. The step SHALL carry no score resolution. A mutator
exit 3 names the survivor and fails the pull request at any score. A
mutator exit 2 names the failed baseline and fails the pull request.

#### Scenario: A surviving mutant fails the pull request at a high score
- **GIVEN** a changed product file whose mutation run reports one
  survivor and a score above 95 percent
- **WHEN** the CI mutator step finishes
- **THEN** the step exits non-zero and the pull request fails

#### Scenario: A clean run passes the step
- **GIVEN** a changed product file whose mutation run kills every
  executed mutant
- **WHEN** the CI mutator step finishes
- **THEN** the step exits 0 and the pull request passes the gate
