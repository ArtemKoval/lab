# llm-ops-eval/eval-run Specification

## Purpose
Gives the user one command that asks a local apfel server four fixed questions and scores the answers with DeepEval. The command shows that the local judge works end to end.

## Requirements

### Requirement: Run asks four fixed questions
The run MUST ask apfel these questions one after another, in this order, with temperature 0. Each reply is the answer to the question.

| Question | Expected answer |
|---|---|
| What is the capital of France? | Paris |
| How many days are in a leap year? | 366 |
| What is the chemical symbol for water? | H2O |
| Who wrote the play Romeo and Juliet? | William Shakespeare |

#### Scenario: Four questions in order
- **WHEN** the run starts and the server answers
- **THEN** the server gets the four questions in the order of the table, one request at a time

### Requirement: Run scores each answer with the same server
The run MUST score each answer against its expected answer with a correctness metric. The score is a number from 0 to 1. The judge of the metric MUST be the same apfel server. An answer passes if its score is equal to or higher than the threshold. The default threshold is 0.5.

#### Scenario: Score at or above the threshold
- **WHEN** the correctness score is 0.8 and the threshold is 0.5
- **THEN** the answer passes

#### Scenario: Score equal to the threshold
- **WHEN** the correctness score is 0.5 and the threshold is 0.5
- **THEN** the answer passes

#### Scenario: Score below the threshold
- **WHEN** the correctness score is 0.0 and the threshold is 0.5
- **THEN** the answer fails

### Requirement: Run reads its settings from the command line and the environment
The base URL MUST come from the option `--base-url`, then from the variable `APFEL_BASE_URL`, then from the default `http://host.docker.internal:11434/v1`. The model MUST come from the option `--model`, with the default `apple-foundationmodel`. The token MUST come from the variable `APFEL_TOKEN`. The run MUST read `APFEL_BASE_URL` and `APFEL_TOKEN` from the file `.env` in the current folder. The shell has priority over the file.

#### Scenario: Option wins over the variable
- **WHEN** the option `--base-url` and the variable `APFEL_BASE_URL` hold different values
- **THEN** the run uses the value of the option

#### Scenario: Variable wins over the default
- **WHEN** the variable `APFEL_BASE_URL` is set and the option `--base-url` is not set
- **THEN** the run uses the value of the variable

#### Scenario: Default base URL
- **WHEN** neither the option nor the variable is set
- **THEN** the run uses `http://host.docker.internal:11434/v1`

#### Scenario: Settings in a .env file
- **WHEN** the `.env` file sets `APFEL_BASE_URL` and the shell does not
- **THEN** the run uses the value in the `.env` file

#### Scenario: Shell wins over the .env file
- **WHEN** the `.env` file and the shell set `APFEL_BASE_URL` to different values
- **THEN** the run uses the value of the shell

### Requirement: Run stops when the .env file cannot be read
If the file `.env` is in the current folder and is not readable text, the run MUST print a message to the standard error stream. The message MUST name the error. The run MUST print nothing to the standard output, ask no question, and exit with code 2.

#### Scenario: File that is not text
- **WHEN** the `.env` file holds bytes that are not valid text
- **THEN** the run prints a message with the error to the standard error stream
- **AND** the server gets no request and the exit code is 2

### Requirement: Run rejects a threshold outside 0 to 1
The option `--threshold` MUST hold a number from 0 to 1. Both 0 and 1 are valid. If it does not, the run MUST print a usage error and exit with code 2. The run MUST ask no question.

#### Scenario: Threshold too high
- **WHEN** the option `--threshold` is 1.5
- **THEN** the run prints a usage error and exits with code 2
- **AND** the server gets no request

#### Scenario: Threshold is not a number
- **WHEN** the option `--threshold` is `high`
- **THEN** the run prints a usage error and exits with code 2

### Requirement: Run works without an OpenAI key
The run MUST complete with no OpenAI API key in the environment. The run MUST send model requests only to the apfel server. The run MUST NOT send an OpenAI key to the server.

#### Scenario: No OpenAI key
- **WHEN** the variable `OPENAI_API_KEY` is not set
- **THEN** the run asks the questions and scores the answers

#### Scenario: OpenAI key in the environment
- **WHEN** the variable `OPENAI_API_KEY` is `sk-secret`
- **THEN** no request to the server holds `sk-secret`

### Requirement: Run stops when the server does not work
Before the first question, the run MUST make one call to the server. If the server does not answer or gives an error status, the run MUST print a message to the standard error stream. The message MUST name the base URL, the error, and the command `apfel --serve`. The run MUST ask no question and exit with code 2.

#### Scenario: Server is off
- **WHEN** nothing listens at the base URL
- **THEN** the run prints the message to the standard error stream and nothing to the standard output
- **AND** the run exits with code 2

#### Scenario: Server answers with an error status
- **WHEN** the server answers HTTP 403 to the first call
- **THEN** the message holds the base URL and the status 403
- **AND** the standard output is empty and the exit code is 2
- **AND** the server gets no question

#### Scenario: First call gives a reply that is not a model list
- **WHEN** the server answers HTTP 200 to the first call with text that is not a list of models
- **THEN** the message holds the base URL and the error
- **AND** the standard output is empty and the exit code is 2

#### Scenario: Base URL that cannot be used
- **WHEN** the base URL has a control character, or a port that is not a number
- **THEN** the message holds the base URL and the error
- **AND** the standard output is empty and the exit code is 2

### Requirement: Run continues after an error in one question
If one question causes an error, the run MUST record the error and continue with the next question. At the end, the run MUST exit with code 2.

#### Scenario: Context window is full
- **WHEN** the server rejects the second question with an error
- **THEN** the run records the error for the second question
- **AND** the run asks the third and the fourth question
- **AND** the run exits with code 2

#### Scenario: Score reply that is not valid
- **WHEN** the score call of the first question gives a reply that does not match the schema
- **THEN** the first question has the verdict `ERROR`
- **AND** each of the other three questions is scored on its own result

### Requirement: Run prints one row for each question
By default, the run MUST print one row for each question to the standard output. A row has the form `<VERDICT> <score> | <question> | expected: <expected> | answer: <answer>`. The verdict is `PASS`, `FAIL`, or `ERROR`. The score has two decimals.

#### Scenario: Row for a passed answer
- **WHEN** the run ends, the option `--json` is not set, the score is 0.8, and the answer is `Paris`
- **THEN** the row for the first question is `PASS 0.80 | What is the capital of France? | expected: Paris | answer: Paris`

### Requirement: Run prints a row with the error for a question that fails to run
For a question with an error, the score MUST be `n/a`. The last part of the row MUST be `error: <error>` in place of the answer.

#### Scenario: Row for an error
- **WHEN** the question about water has the error `APIStatusError: context full`
- **THEN** its row is `ERROR n/a | What is the chemical symbol for water? | expected: H2O | error: APIStatusError: context full`

### Requirement: Run prints each row on one line
A line break in the answer or in the error MUST become a space in the row.

#### Scenario: Answer with a line break
- **WHEN** an answer is `Paris` and `France` on two lines
- **THEN** its row holds `answer: Paris France` on one line

### Requirement: Run prints a summary line
After the rows, the run MUST print the line `total=<n> passed=<n> failed=<n> errors=<n>`.

#### Scenario: All answers pass
- **WHEN** all four answers pass
- **THEN** the last line is `total=4 passed=4 failed=0 errors=0`

### Requirement: Run gives JSON with the option --json
If the option `--json` is set, the run MUST print one JSON document to the standard output. The run MUST print no other text to the standard output. The document has the keys `base_url`, `model`, `threshold`, `results`, and `summary`. Each item of `results` has the keys `question`, `expected`, `actual`, `score`, `passed`, `reason`, and `error`. The key `summary` has the keys `total`, `passed`, `failed`, and `errors`.

#### Scenario: JSON report
- **WHEN** the run ends and the option `--json` is set
- **THEN** the standard output parses as one JSON document with the listed keys
- **AND** `results` has four items

#### Scenario: Question with an error
- **WHEN** a question has an error and the option `--json` is set
- **THEN** its item has `score` null, `passed` false, and the error text in `error`

#### Scenario: No other text on the standard output
- **WHEN** the run ends and the option `--json` is set
- **THEN** the standard output holds no text from DeepEval

### Requirement: Run sets the exit code from the result
The run MUST exit with code 0 if all answers pass. The run MUST exit with code 1 if at least one answer fails and no question has an error. The run MUST exit with code 2 if the server does not answer or a question has an error.

#### Scenario: All pass
- **WHEN** all four answers pass
- **THEN** the exit code is 0

#### Scenario: One fails
- **WHEN** one answer fails and no question has an error
- **THEN** the exit code is 1

#### Scenario: One fails and one has an error
- **WHEN** one answer fails and another question has an error
- **THEN** the exit code is 2

#### Scenario: Started as a module
- **WHEN** the user starts the run with the command `python -m apfel_eval.run` and the option `--threshold` is 2
- **THEN** the process exits with code 2
