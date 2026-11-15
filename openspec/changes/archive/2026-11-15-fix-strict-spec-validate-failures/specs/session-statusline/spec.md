## MODIFIED Requirements

### Requirement: The status line renders the session summary
The tool SHALL read one JSON payload on standard input and print one
summary line. The line SHALL carry the session summary fields. The
line SHALL join neighboring blocks with the ` | ` separator. The
effort field SHALL show the coding plan effort of z.ai. The tool
SHALL map the payload effort level through the coding plan table.
The table maps `none`, `minimal`, and `low` to `low`. The table
maps `medium` and `high` to `high`. The table maps `xhigh` and
`max` to `max`.

#### Scenario: A complete payload renders every field
- **GIVEN** the payload carries `model.display_name` `GLM-5.3-Flash`,
  `effort.level` `xhigh`, `rate_limits.five_hour.used_percentage`
  `9`, `rate_limits.seven_day.used_percentage` `83`,
  `prompt_cache.hit_ratio` `0.98`, and transcript usage that sums to
  606225 input and 205336 output tokens
- **WHEN** the tool renders the line
- **THEN** the line carries `GLM-5.3-Flash`, `effort max`, `5h 9%`,
  `wk 83%`, `cache 98%`, `in 0.61M`, `out 0.21M`, a `HH:MM UTC`
  time, and the ` | ` separator between neighboring blocks

#### Scenario: An absent cache object falls back to the transcript
- **GIVEN** the payload carries no `prompt_cache`, and the transcript
  usage sums carry cache reads over the input side
- **WHEN** the tool renders the line
- **THEN** the cache field carries the transcript-derived rate, and a
  transcript with no usage rows reads `cache n/a`

#### Scenario: An absent effort renders n/a
- **GIVEN** the payload carries no `effort.level`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `n/a`

#### Scenario: The map applies without a model name
- **GIVEN** the payload carries no `model` object and `effort.level`
  `xhigh`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `max`

#### Scenario: A low-family level maps to low
- **GIVEN** the payload carries `effort.level` `minimal`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `low`

#### Scenario: A medium level maps to high
- **GIVEN** the payload carries `effort.level` `medium`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `high`

#### Scenario: A mixed-case level maps to high
- **GIVEN** the payload carries `effort.level` `HIGH`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `high`

#### Scenario: An unknown level stays raw
- **GIVEN** the payload carries `effort.level` `turbo`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `turbo`

#### Scenario: The line carries seven separators
- **GIVEN** the payload of the complete payload scenario
- **WHEN** the tool renders the line
- **THEN** the line carries exactly seven ` | ` separators between
  its eight blocks

#### Scenario: The JSON effort field carries the mapped value
- **GIVEN** the payload carries `effort.level` `xhigh`
- **WHEN** the tool renders the `--json` fields
- **THEN** the `effort` field of the fields dict reads `max`

#### Scenario: The table maps none to low
- **GIVEN** the payload carries `effort.level` `none`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `low`

#### Scenario: The table maps low to low
- **GIVEN** the payload carries `effort.level` `low`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `low`

#### Scenario: The table maps high to high
- **GIVEN** the payload carries `effort.level` `high`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `high`

#### Scenario: The table maps max to max
- **GIVEN** the payload carries `effort.level` `max`
- **WHEN** the tool renders the line
- **THEN** the effort field reads `max`
