# Spec Delta

## Purpose

Lets DeepEval metrics use a local apfel server as their judge model. The judge works with no cloud key. Its output always matches the schema that the metric asks for.

## ADDED Requirements

### Requirement: Judge calls the server at the given base URL
The judge MUST send each request to the apfel server at the base URL that the user gives. Each request MUST use the chat completion endpoint and name the model that the user chose.

#### Scenario: Request goes to the base URL
- **WHEN** the base URL is `http://127.0.0.1:11434/v1` and a metric asks the judge for text
- **THEN** the judge sends one POST request to `http://127.0.0.1:11434/v1/chat/completions`
- **AND** the request names the chosen model

### Requirement: Judge passes the apfel Host guard
If the base URL has a host that is not a loopback host, the judge MUST send the header `Host: localhost:<port>`. The port is the port of the base URL. If the host is a loopback host, the judge MUST NOT change the Host header.

#### Scenario: Request from a container
- **WHEN** the base URL is `http://host.docker.internal:11434/v1`
- **THEN** each request carries the header `Host: localhost:11434`

#### Scenario: Request on the same computer
- **WHEN** the base URL is `http://127.0.0.1:11434/v1`
- **THEN** each request carries the header `Host: 127.0.0.1:11434`

#### Scenario: Base URL with no port
- **WHEN** the base URL is `http://host.docker.internal/v1`
- **THEN** each request carries the header `Host: localhost`

### Requirement: Judge returns the text reply
When a metric gives no schema, the judge MUST return the text of the reply. The judge MUST ask for temperature 0.

#### Scenario: Text reply
- **WHEN** a metric asks for text and the server replies with the text `Paris`
- **THEN** the judge returns `Paris`
- **AND** the request has temperature 0 and no response format

### Requirement: Judge returns an object that matches the schema
When a metric gives a schema, the judge MUST ask the server to constrain the reply to that schema. The judge MUST return an object of that schema.

#### Scenario: Reply matches the schema
- **WHEN** a metric gives a schema with the fields `score` (integer) and `reason` (text) and the server replies `{"score": 8, "reason": "ok"}`
- **THEN** the judge returns an object with `score` 8 and `reason` `ok`
- **AND** the request holds the schema as the JSON schema response format

### Requirement: Judge rejects a reply that does not match the schema
If the reply does not match the schema, the judge MUST raise an error. The judge MUST NOT return a partial object.

#### Scenario: Reply has the wrong type
- **WHEN** the schema has an integer field `score` and the server replies `{"score": "high"}`
- **THEN** the judge raises a validation error

#### Scenario: Reply has no text
- **WHEN** the server replies with an empty message
- **THEN** the judge raises an error and returns no object

### Requirement: Schema has no references
The schema that the judge sends MUST NOT contain `$ref` or `$defs`. The judge MUST replace each reference with the definition that it names. A reference with other keys keeps those keys, and they win over the definition.

#### Scenario: Nested schema
- **WHEN** a metric gives a schema whose list items are a second model
- **THEN** the schema in the request holds the definition of the second model in place of the reference
- **AND** the schema in the request has no `$ref` and no `$defs`

#### Scenario: One definition used twice
- **WHEN** a metric gives a schema that uses the same second model in two fields
- **THEN** the schema in the request holds the definition in both fields
- **AND** the judge raises no error

#### Scenario: Reference with a description
- **WHEN** a field holds a reference and a description
- **THEN** the schema in the request holds the definition and the description of the field

#### Scenario: Optional nested model
- **WHEN** a field is an optional second model
- **THEN** the schema in the request holds the definition of the second model in the optional field

#### Scenario: Schema that refers to itself
- **WHEN** a metric gives a schema with a definition that refers to itself, directly or through other definitions
- **THEN** the judge raises an error that tells the user the schema is recursive
- **AND** the judge sends no request

### Requirement: Judge sends the token and never an OpenAI key
The judge MUST send the token that the user gives as the bearer token. If the user gives no token, the judge MUST send the placeholder `apfel-no-token`. The judge MUST NOT send the value of `OPENAI_API_KEY`, `OPENAI_ORG_ID`, or `OPENAI_PROJECT_ID`.

#### Scenario: Token given
- **WHEN** the user gives the token `secret`
- **THEN** each request carries the header `Authorization: Bearer secret`

#### Scenario: No token and no OpenAI key
- **WHEN** the user gives no token and `OPENAI_API_KEY` is not set
- **THEN** the judge starts with no error
- **AND** each request carries the header `Authorization: Bearer apfel-no-token`

#### Scenario: OpenAI key in the environment
- **WHEN** the user gives no token and `OPENAI_API_KEY` is `sk-secret`
- **THEN** no request header holds `sk-secret`
- **AND** each request carries the header `Authorization: Bearer apfel-no-token`

#### Scenario: OpenAI organization and project in the environment
- **WHEN** `OPENAI_ORG_ID` and `OPENAI_PROJECT_ID` are set
- **THEN** no request carries the headers `OpenAI-Organization` or `OpenAI-Project`

### Requirement: Judge sends one request at a time
The judge MUST have at most one request in flight. A second request MUST start after the reply to the first request arrives.

#### Scenario: Two calls at the same time
- **WHEN** two calls to the judge start at the same time
- **THEN** the server never has two open requests from the judge

### Requirement: Judge raises a server error without a retry
If the server returns an error status or does not answer, the judge MUST raise an error. The judge MUST NOT send the request again. The judge MUST stop a request that has no reply after 120 seconds.

#### Scenario: Error status
- **WHEN** the server answers HTTP 500
- **THEN** the judge raises an error after exactly one request

#### Scenario: No answer
- **WHEN** the connection to the server fails
- **THEN** the judge raises an error after exactly one attempt

#### Scenario: No reply in time
- **WHEN** the server accepts the connection and sends no reply
- **THEN** the judge stops the request after 120 seconds and raises an error after exactly one request

### Requirement: Judge sends no telemetry by default
A metric run with the judge MUST open no network connection except the connection to the apfel server. The user MAY turn telemetry on if the user sets the variable `DEEPEVAL_TELEMETRY_OPT_OUT` to `NO` before the judge code loads. The judge MUST NOT change a value that the user set.

#### Scenario: Variable not set
- **WHEN** the variable `DEEPEVAL_TELEMETRY_OPT_OUT` is not set and a metric runs with the judge
- **THEN** the only network connection is the connection to the apfel server

#### Scenario: Variable set by the user
- **WHEN** the user sets the variable `DEEPEVAL_TELEMETRY_OPT_OUT` to `NO` and the judge code loads
- **THEN** the variable is still `NO`

### Requirement: Async call gives the same result
An async call to the judge MUST return the same result as the sync call with the same input.

#### Scenario: Async text reply
- **WHEN** a metric makes an async call and the server replies with the text `Paris`
- **THEN** the judge returns `Paris`
