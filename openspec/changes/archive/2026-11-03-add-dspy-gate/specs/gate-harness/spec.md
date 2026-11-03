## ADDED Requirements

### Requirement: One model factory reads the pins from gates.yaml
The module `lm.py` SHALL build the model instance for every role from the `models.roles` section of `gates.yaml`. No other module SHALL construct a model client. The factory SHALL read the base URL, the temperature, the thinking mode, and the token ceiling of the role. A live construction SHALL require the `ZAI_API_KEY` variable.

#### Scenario: The factory builds a role from the pins
- **WHEN** the factory builds the runtime role
- **THEN** the instance carries the pinned model name, temperature, thinking mode, and token ceiling of that role

#### Scenario: The factory refuses a live build without the key
- **WHEN** the factory builds a live role with no `ZAI_API_KEY` in the environment
- **THEN** the factory raises an error that names the missing variable

### Requirement: The role policy pins glm-5.3-flash everywhere
The `gates.yaml` roles section SHALL pin these roles. Every role SHALL carry the model glm-5.3-flash. Every role SHALL carry thinking disabled. The judge and vision judge roles SHALL carry temperature 0. The policy SHALL differ from the guide values, and `gates.yaml` SHALL record that in a comment.

#### Scenario: The pins match the flash policy
- **WHEN** a reader opens the roles section of `gates.yaml`
- **THEN** every role carries glm-5.3-flash and no role enables thinking

### Requirement: The assertion tiers set the passing rules
The gate runner SHALL apply one passing rule per tier. Tier A SHALL pass only at 100 percent. Tier B SHALL pass at or above the `tier_b_min` threshold with an ensemble of 3 judges at temperature 0. Tier C SHALL pass at 100 percent on the asserted orderings. Tier D SHALL pass within the `gates.yaml` ceilings for p95 tokens and latency.

#### Scenario: Tier A demands a perfect score
- **WHEN** a Tier-A assertion fails for one scenario
- **THEN** the gate marks the scenario red with no threshold relief

#### Scenario: Tier B passes at the threshold
- **WHEN** the judge ensemble returns a mean of 0.85 and the threshold is 0.85
- **THEN** the gate marks Tier B green

#### Scenario: Tier D holds the budget line
- **WHEN** the p95 token count of a scenario exceeds its ceiling
- **THEN** the gate marks Tier D red and names the ceiling

### Requirement: Hand modules run plain and optimized modules load artifacts
A hand module SHALL be plain Python with no model call at eval time. The harness loader SHALL resolve a hand module by its entry point in the manifest. The loader SHALL load an optimized module from its versioned artifacts directory in the manifest.

#### Scenario: The loader resolves a hand module
- **WHEN** the loader reads a manifest entry with impl hand and an entry path
- **THEN** the loader returns the callable at that entry point

#### Scenario: The loader refuses a missing artifact directory
- **WHEN** the loader reads a manifest entry with impl optimized and no artifacts directory on disk
- **THEN** the loader raises an error that names the directory
