# fde/openrouter-client Specification

## Purpose

Lets the backend talk to the OpenRouter HTTP API. It validates the key, lists the models, and streams chat completions.

## Requirements

### Requirement: The client validates a key with a real API call
The client MUST validate an API key with an authenticated call to the OpenRouter API. A valid key MUST give the result kind `valid`. A key that the API rejects MUST give the result kind `auth` with the API error text.

#### Scenario: Valid key
- **WHEN** the client validates a key and the API accepts it
- **THEN** the result kind is `valid`

#### Scenario: Rejected key
- **WHEN** the client validates a key and the API answers 401
- **THEN** the result kind is `auth` and the message carries the API error text

### Requirement: The client lists the models
The client MUST read `GET /api/v1/models` and return the model id and name of each model. The wizard and the settings use this list. An API failure MUST become an error result with the failure reason.

#### Scenario: Model list arrives
- **WHEN** the client lists the models and the API answers 200
- **THEN** the result carries the id and name of each model

#### Scenario: Model list fails
- **WHEN** the API answers 500 on the models request
- **THEN** the result kind is `api` with the failure reason

### Requirement: The client streams chat completions
The client MUST send chat completions with `stream` set to true. Each server-sent event chunk MUST become one stream event on the backend channel, in order. After the stream ends, the client MUST send one completion result whose text equals the join of all chunk deltas.

#### Scenario: Chunks arrive in order
- **WHEN** the API sends five content chunks for one request
- **THEN** the app receives five stream events in the same order

#### Scenario: Final text equals the chunk join
- **WHEN** the stream ends
- **THEN** the completion result text equals the join of all chunk deltas in order

#### Scenario: Stream end marker
- **WHEN** the API sends the end-of-stream marker
- **THEN** the client sends the completion result and closes the stream

### Requirement: The default model routes automatically
The default model choice MUST be `any`. The `any` choice MUST map to the OpenRouter auto router, so the platform picks the model per request. A model that the user picked MUST be sent as the model of the request.

#### Scenario: Default choice maps to the auto router
- **WHEN** the user keeps the default `any` and sends a message
- **THEN** the request carries the OpenRouter auto router model

#### Scenario: Picked model is sent
- **WHEN** the user picks the model `openai/gpt-4o-mini` and sends a message
- **THEN** the request carries `openai/gpt-4o-mini`

### Requirement: API failures map to distinct error kinds
The client MUST map failures to error kinds: `auth` for 401, `rate` for 429, and `api` for other 4xx and 5xx answers. The client MUST map connection failures to the `network` error kind. Each error result MUST carry a user-readable message.

#### Scenario: Rate limit answer
- **WHEN** the API answers 429 on a chat completion
- **THEN** the error kind is `rate` with a message that names the rate limit

#### Scenario: Connection failure
- **WHEN** the machine has no route to the API
- **THEN** the error kind is `network` with a message that names the connection problem

### Requirement: The client keeps the key out of logs and errors
The client MUST send the key as a bearer header and MUST NOT write the key to logs or error messages.

#### Scenario: Key stays out of the log
- **WHEN** the client logs a request failure
- **THEN** the log line holds no key text

#### Scenario: Key stays out of the error message
- **WHEN** the client builds an error result for a failed request
- **THEN** the message holds no key text

### Requirement: A stop cancels the upstream request
The stop of a stream MUST cancel the HTTP request to the OpenRouter API. The backend MUST end the stream with one final notification that carries the stream id and marks the stop.

#### Scenario: Stop cancels the request
- **WHEN** the stop arrives while the upstream request runs
- **THEN** the client cancels the request and sends one final notification that marks the stop

### Requirement: Each API call carries a timeout
The validate and models calls MUST carry a timeout of 30 seconds. A timeout MUST map to the `network` error kind. A chat stream MUST end with an error notification for its stream id when no chunk arrives for 30 seconds.

#### Scenario: Validation call hangs
- **WHEN** the validate call gets no answer within 30 seconds
- **THEN** the result kind is `network`

#### Scenario: Stream stalls
- **WHEN** no chunk arrives for 30 seconds on a running stream
- **THEN** the backend ends the stream with an error notification for that stream id

### Requirement: The API base URL is a setting
The base URL MUST default to `https://openrouter.ai/api/v1`. A setting MUST override it, so tests and private gateways can point elsewhere.

#### Scenario: Default base URL
- **WHEN** no override exists
- **THEN** the client calls `https://openrouter.ai/api/v1`

#### Scenario: Overridden base URL
- **WHEN** the setting gives another base URL
- **THEN** the client calls that URL instead
