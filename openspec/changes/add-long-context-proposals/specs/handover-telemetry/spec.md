## MODIFIED Requirements

### Requirement: The report carries the funnel, the tokens, the models, and the cost
For every tool call the report SHALL list the tool name, the agent, the start time, and the duration. The report SHALL give token sums per model with the cache splits, and the served and the requested model names. The report SHALL compute cost from a versioned price table with cache-tier multipliers, and SHALL mark a model with no known price as unknown. The report SHALL give the cache hit rate and the cost split per agent. The report SHALL give the per-call input-token median and peak over the session's assistant messages, beside the token sums. The report SHALL render a median or a peak with no usage data as not available.

#### Scenario: Both model names appear
- **WHEN** a turn records a requested model and a different served model
- **THEN** the report shows both names for that turn

#### Scenario: An unknown price renders as unknown
- **WHEN** the served model has no rate in the price table
- **THEN** the cost for that model renders as unknown, and the run total names the gap

#### Scenario: The cache split appears
- **WHEN** a turn records cache read and cache creation tokens
- **THEN** the report shows the three token kinds and the cache hit rate

#### Scenario: The context block renders the spread
- **WHEN** the session's assistant messages carry per-call `input_tokens`
- **THEN** the report gives the median and the peak beside the token sums

#### Scenario: No usage data renders as not available
- **WHEN** the session carries no assistant message with usage data
- **THEN** the median and the peak render as not available, and the build exits 0
