# zai-routing-audit Specification

## Purpose

Lets the user rerun the z.ai GLM routing audit. It shows which model name Claude Code sends, which name the endpoint echoes and reports, and what each name costs in credits.

## Requirements

### Requirement: The config command reports the routing setup with the token redacted
The `config` command SHALL read a Claude Code settings file and print the base URL and every model slot. It SHALL print the auth token in a redacted form and SHALL NOT print the full token on stdout, stderr, or in JSON output.

#### Scenario: Token stays hidden
- **WHEN** the command runs against a settings file that contains `ANTHROPIC_AUTH_TOKEN`
- **THEN** the output names the token slot and shows only a short redacted prefix
- **THEN** the full token value appears nowhere in the output

#### Scenario: Missing settings file
- **WHEN** the settings file does not exist at the given path
- **THEN** the command exits with code 2 and prints an error that names the missing path

### Requirement: The transcripts command counts requested and echoed models
The `transcripts` command SHALL scan transcript files in a directory. It SHALL count records per requested model and per echoed model, and sum the usage fields per model. It SHALL skip lines that do not parse and SHALL finish with exit code 0 when the directory holds no transcript files.

#### Scenario: Counts both directions
- **WHEN** the directory holds a transcript with a request record for model `glm-5.3-flash` and an assistant record whose echoed model is `glm-5.3-flash`
- **THEN** the report shows one count on the requested side and one count on the echoed side for that name

#### Scenario: Tolerates bad lines
- **WHEN** a file contains a malformed JSON line and a line with raw control characters inside a string
- **THEN** the command skips the malformed line, parses the tolerant line, and exits 0

### Requirement: The echo command compares requested and echoed model names
The `echo` command SHALL send one request with a bounded `max_tokens` for each model name it receives. It SHALL print the requested name, the echoed name, and the token usage per request. It SHALL exit 0 when every echo matches its request and exit 2 on any mismatch or request failure.

#### Scenario: Echo mismatch fails
- **WHEN** the endpoint echoes a different name than the request carried
- **THEN** the command reports the mismatch and exits 2

#### Scenario: Transport failure fails
- **WHEN** a request cannot reach the endpoint
- **THEN** the command prints an error message and exits 2 without a traceback

### Requirement: The usage command reports per-model rows and credit pools
The `usage` command SHALL read the console per-model usage report for a time window and the credit pool state. It SHALL print each model row with its token total and each pool with its consumed and remaining values. It SHALL exit 2 when a response does not carry the documented shape.

#### Scenario: Parses the documented envelopes
- **WHEN** the model report nests rows under `data.modelDataList` and the pool state nests limits under `data.limits`
- **THEN** the command prints one line per model row and one line per pool

#### Scenario: Falls back to the alternate envelope
- **WHEN** the pool state carries limits at the top level instead of under `data`
- **THEN** the command still prints the pools and exits 0

#### Scenario: Schema drift fails cleanly
- **WHEN** a response carries none of the documented shapes
- **THEN** the command exits 2 and prints a short body excerpt with the token redacted

### Requirement: The throughput command reports generation speed per name
The `throughput` command SHALL run one bounded generation per model name. It SHALL print the output token count, the elapsed time, and the tokens per second for each name.

#### Scenario: Computes the rate
- **WHEN** a generation returns 1024 output tokens and the injected clock measures 20.0 seconds
- **THEN** the report shows 51.2 tokens per second for that name

### Requirement: The burn command spends credits only on an explicit flag
The `burn` command SHALL, without `--spend-credits`, print what it would send and exit 0 without any request to the messages endpoint. With `--spend-credits`, it SHALL read the credit pools and send one identical bounded request per model name. It SHALL read the pools again and print the pool delta per name.

#### Scenario: Refuses to spend by default
- **WHEN** the command runs without `--spend-credits`
- **THEN** it makes no request to the messages endpoint and exits 0

#### Scenario: Measures the deltas
- **WHEN** the command runs with `--spend-credits` against pools that move from 2600 to 2613 after the first burn and to 2630 after the second
- **THEN** the report shows a delta of 13 for the first name and 17 for the second

### Requirement: The CLI speaks JSON on demand and uses exit code 2 for failures
Every command SHALL print human-readable text by default and parseable JSON with `--json`. JSON output SHALL carry the redacted token form only. Every command SHALL exit 0 on success and 2 on operational failure.

#### Scenario: JSON output parses and stays redacted
- **WHEN** any command runs with `--json`
- **THEN** stdout parses as JSON and contains no full token value

#### Scenario: Operational failure exits 2
- **WHEN** a network request or a required file fails
- **THEN** the command exits 2 and prints the cause

### Requirement: Live network checks stay opt-in
The test suite SHALL run hermetic by default with no network access. Tests that call the real endpoint SHALL carry the `e2e` marker and SHALL run only when the environment gives the gate variable `ZAI_ROUTING_AUDIT_E2E`.

#### Scenario: Default run touches no network
- **WHEN** the test suite runs without the gate variable
- **THEN** every test passes without any network connection

#### Scenario: Gated live run
- **WHEN** the suite runs with the gate variable set and the marker selected
- **THEN** the live tests run against the real endpoint

