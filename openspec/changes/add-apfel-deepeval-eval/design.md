# Design

## Context

- `llm_ops/eval` holds a devcontainer (Python 3.12 on Debian Trixie) and a `requirements.txt` that lists `python-dotenv` and `deepeval` with no versions.
- apfel 1.10.0 runs on the macOS host with `apfel --serve`, on 127.0.0.1 port 11434. It has an OpenAI-compatible API: `/v1/chat/completions`, `/v1/models`, and `/health`. The context window is 4096 tokens. The server rejects `stop`, `n`, `logprobs`, and the penalty parameters with HTTP 400.
- A container reaches the host as `host.docker.internal`. The apfel Host guard answers HTTP 403 to that name. The header `Host: localhost:11434` passes. The user chose this client header on 2026-10-07. The other choice was to restart apfel with `--no-origin-check`.
- DeepEval 4.2.8 calls `generate_with_schema(prompt, schema=...)` on a custom judge. The base class passes the schema to `generate`. The reply can be a schema object or a JSON string. A custom judge is not a native model, so it returns no cost value.
- A fresh install of `deepeval` 4.2.8 resolves `openai` 3.26.0. That `openai` version uses the HTTP package `httpx2`, and a fresh install has no `httpx`.
- DeepEval connects to `us.i.posthog.com` unless `DEEPEVAL_TELEMETRY_OPT_OUT` is `YES`. I measured this with a socket log. DeepEval also loads a `.env` file in the current folder when it loads.
- One run makes 9 model calls: 4 answers, 1 steps call, and 4 score calls. A call takes about 10 seconds, and up to 40 seconds in my earlier runs. Parallel calls starve the on-device model.
- The GEval score is the model reply (an integer from 0 to 10) divided by 10.

## Goals / Non-Goals

**Goals:**
- Keep the code small: one judge module and one run module.
- Test all the code with no network and no apfel. Use the real `openai` client and the real DeepEval metric.
- Make the judge reusable in other DeepEval scripts.

**Non-Goals:**
- Other metrics, other models, a stream of the reply, and retries.
- The `deepeval test run` pytest plugin and the Confident AI cloud.
- An MCP tool and a CI job. The repository has no CI.

## Decisions

### D1. A new judge class, not the DeepEval `LocalModel`
The judge subclasses `DeepEvalBaseLLM`. `LocalModel` sends no `response_format`, so a metric gets free text that it must parse. `LocalModel` is a native model. A subclass must override both generate methods and return cost tuples. A plain subclass of `DeepEvalBaseLLM` is smaller.

The subclass implements the four abstract methods: `load_model`, `generate`, `a_generate`, and `get_model_name`. The base `__init__` calls `load_model`. The judge sets the attributes that `load_model` reads before it calls `super().__init__`.

The base class calls `generate` again without the schema if `generate` raises `TypeError`. The judge raises only `ValueError`, `ValidationError`, and `openai` errors, so no hidden second request happens.

Alternative: `deepeval set-local-model` with `LocalModel`. I rejected it because the reply is not constrained and the settings are global.

### D2. The `openai` client is the transport
The judge builds an `OpenAI` client with `base_url`, `default_headers`, `max_retries=0`, `timeout=120`, and an optional `http_client`.

The client always gets an explicit `api_key`. It is the token, or the fixed text `apfel-no-token`. The client also gets an empty `organization` and an empty `project`. Without these values, the `openai` client reads `OPENAI_API_KEY`, `OPENAI_ORG_ID`, and `OPENAI_PROJECT_ID`. It then fails with no key, or it sends a real cloud key to the apfel server. I proved both results with a mock transport. The judge never reads an OpenAI variable.

DeepEval already depends on `openai`. Tests give a mock transport from the HTTP package that `openai` uses (`httpx2` with `openai` 3.26.0). They see the real URL, headers, and body.

Alternative: `httpx` or `requests` alone. I rejected it because the code must then parse the reply format.

### D3. The schema goes to the server with no references
`response_format` is `json_schema`. The schema is `model_json_schema()` after a pure function `inline_refs` replaces each `$ref` with its definition and drops `$defs`.

- A `$ref` node with other keys becomes the definition with those keys on top. The other keys win.
- A definition that two fields use is valid. A cycle is a definition that is already on the current path. The function raises `ValueError` for a cycle.
- A `$ref` inside `anyOf` (an optional field) is replaced like any other `$ref`.

I measured that GEval and AnswerRelevancy both work after this change.

Alternative: ask for JSON in the prompt and parse the text. I rejected it because a small model can break the format.

### D4. The Host header changes only for a non-loopback host
`host_headers(base_url)` returns `{"Host": "localhost:<port>"}` when the host is not `localhost`, `127.0.0.1`, or `::1`. It returns `{}` for those hosts. The port part is empty when the URL has no port. The common case on the host computer is not changed.

### D5. One request at a time
A `threading.Lock` surrounds the client call in `generate`. The async method runs `generate` in a worker thread. The sync path and the async path share one code path.

Alternative: `AsyncOpenAI`. I rejected it because it doubles the code, and parallel calls starve apfel.

### D6. The metric is GEval correctness
The run builds one GEval metric. The metric compares the actual output with the expected output. The criteria text is: "Is the actual output factually consistent with the expected output?" I measured that the wording matters. The criteria "Ignore the wording" made the judge fail all answers. The parameters are `SingleTurnParams.ACTUAL_OUTPUT` and `SingleTurnParams.EXPECTED_OUTPUT`. The metric uses `async_mode=False` and the user threshold.

The call is `measure(test_case, _show_indicator=False)`. `_show_indicator` is the only private argument. DeepEval 4.2.8 has no `_log_metric_to_confident`. The run sets no Confident AI key, so DeepEval logs nothing to the cloud. All DeepEval console output goes to the standard error stream, so the standard output holds only the report.

A test with the real metric proves that `measure` accepts the arguments that the run passes. The per-question error boundary would hide a `TypeError` from `measure`. This test makes sure that a break of the private argument fails a test.

### D7. The questions are code constants
A function returns a tuple of `Case(question, expected)` for the four questions. The answer prompt asks for the answer only, in as few words as possible. This reduces the length difference between the answer and the expected text. The judge class does the answer call, so the run uses no second client.

### D8. Errors, settings, and exit codes
`ApfelJudge.ping()` lists the models on the server. The run calls it first. `main` catches `openai.OpenAIError` around `ping()`. It prints the base URL, the error, and the command `apfel --serve` to the standard error stream, and it returns 2.

A per-question block catches `Exception`. The line has the comment `# noqa: BLE001` with the reason: one bad question must not stop the other questions. The result holds the error text as `ClassName: message`. `KeyboardInterrupt` is not caught.

The exit code is 2 if any error exists, else 1 if any answer fails, else 0.

`main` calls `load_dotenv(Path.cwd() / ".env")`. The call does not override a variable that the shell sets. A bare `load_dotenv()` looks in the folder of the file that has the call. It does not look in the current folder. The tests use an autouse fixture that changes to a temporary folder and restores `os.environ`.

### D9. Layout
```
llm_ops/eval/
  apfel_eval/__init__.py   sets the telemetry default
  apfel_eval/judge.py      ApfelJudge, inline_refs, host_headers
  apfel_eval/run.py        cases, metric, report, main
  tests/                   unit tests and one opt-in e2e module
  pyproject.toml           pytest, coverage, ruff, and mutmut settings
```
The command is `python -m apfel_eval.run`. A package `__init__` runs before any submodule import, so the telemetry default is set before DeepEval loads. No `noqa` is necessary.

mutmut mutates only code inside functions. The telemetry default and the questions are therefore in functions (`_opt_out_of_telemetry()` and `cases()`). The package calls the first function when it loads.

### D10. Tests
- Judge tests use the real `openai` client with a mock transport.
- Run tests use the real GEval metric. A fake apfel function in `tests/conftest.py` gives the replies. It reads the schema title in the request body (`Steps`, `ReasonScore`). It returns an integer score from 0 to 10, and the metric divides it by 10. It also reads the question text.
- A subprocess test examines the telemetry default in a new interpreter. A second subprocess test runs a metric with the mock transport. It records every socket connection and the DNS names, and it asserts that no non-loopback target exists.
- A `runpy` test runs `apfel_eval.run` as `__main__` with `--threshold 2` and expects exit code 2. It covers the entry guard with a real test.
- The e2e module has the marker `e2e`. It runs only if `APFEL_E2E=1`. It uses the real apfel server from the devcontainer.
- The default `pytest` run excludes `e2e`.

### D11. Gates
- Coverage: `pytest --cov=apfel_eval --cov-branch --cov-fail-under=100`. No `exclude_also` setting. The only accepted exclusion is an inline `# pragma: no cover` with a reason.
- Complexity: `ruff check --select C901` with `max-complexity = 10`. `ruff` is pinned. The code uses `X | None` annotations.
- Mutation: `mutmut run` in the devcontainer. After the run, `mutmut export-cicd-stats` writes `mutants/mutmut-cicd-stats.json`. The score is (killed + timeout) divided by (total − skipped). Mutants with the status suspicious, segfault, or no tests count as not killed. One `python -c` command in the README computes the score. It must print 0.95 or more.
- mutmut writes a copy of `apfel_eval/`, `tests/`, and `pyproject.toml` to `llm_ops/eval/mutants/`. The folder is in the tree, but git ignores it, and no source file changes. This meets the pipeline rule "mutate a copy, never the repo". `pyproject.toml` sets `testpaths = ["tests"]` and `norecursedirs = ["mutants"]` for pytest, and `extend-exclude = ["mutants"]` for ruff.
- A `# pragma: no mutate` comment works only at the end of a one-line statement. It hides all mutants on that line. Each equivalent construct stands alone on a one-line statement. The pull request lists each hidden mutant and its reason. The tool settings do not change to raise the score.

### D12. Dependencies and devcontainer
`requirements.txt` holds the run dependencies with exact versions: `deepeval`, `openai`, and `python-dotenv`. `requirements-dev.txt` starts with `-r requirements.txt`. It adds `pytest`, `pytest-cov`, `ruff`, `mutmut`, and the HTTP package that the tests import. The `postCreateCommand` installs `requirements-dev.txt`. The exact versions come from a clean install in the devcontainer (task 1.3). The pins keep the measured DeepEval contract stable.

### D13. Report format
A row is `<VERDICT> <score> | <question> | expected: <expected> | answer: <answer>`. The spec has the full rules and the examples. A function formats one row, so tests compare exact strings. The summary line is `total=<n> passed=<n> failed=<n> errors=<n>`.

## ASIT pass

**Closed world:** DeepEval (GEval, `DeepEvalBaseLLM`), the `openai` client (already a DeepEval dependency), the apfel server, the devcontainer, and `requirements.txt`.

**New components and the reason for each:**
- The judge class: `LocalModel` cannot send a per-call schema (D1).
- `inline_refs`: apfel ignores `$ref` (D3).
- `host_headers`: the apfel Host guard gives HTTP 403 to a container (D4).
- The lock: parallel calls starve apfel (D5).
- `pytest`, `pytest-cov`, `ruff`, and `mutmut`: the pipeline rules say that the repository must have each gate. It has none.
- The option `--json`: the pipeline Step 2 convention is machine output for each command.
- The option `--threshold`: the pass limit is the choice of the user. The default is the GEval default.
- The option `--model`: the apfel model name can change. The default is the current name.
- The variable `APFEL_TOKEN`: the user can start apfel with `--token`.
- The `.env` file: the user added `python-dotenv` to `requirements.txt`.
- `ping()`: it stops the run in a second, and not after the first slow call.
- The row formatter: it gives the report that a person reads.

**Skipped steps:** Step 4 (MCP tool) does not apply. The run is a developer command that Claude Code starts with Bash, and the skill in Step 5 describes it.

**Removed or reused:** the `openai` client does the transport (Object Removal of a custom HTTP layer). The judge class does the answer call (Unification: one client for the answers and the scores).

**Qualitative change:** the primary problem factor is the format discipline of a small judge model. Constrained decoding makes the output valid for every schema. The code has no retry and no repair. It does not cut the JSON text.

## Risks / Trade-offs

- Slow calls: a full run takes about 1.5 to 3 minutes, and up to 6 minutes on a slow server. → The README gives the measured time from task 4.2. The e2e module is opt-in.
- A server that hangs. → The 120 second limit stops the request, and the run records the error.
- The 4096-token window can overflow on a long answer. → The error goes into the result and the exit code is 2.
- The judge makes mistakes on a correct answer with more words, and its reasons can be wrong. → The prompt asks for short answers. The e2e test examines the structure and not exact scores. The README states this limit.
- apfel can change. The host runs 1.10.0 and Homebrew has 1.16.0. → The e2e test finds a changed contract.
- The Host override sends a name that differs from the real name. → It applies only to non-loopback hosts, and the README states the reason.
- The code passes one private DeepEval argument to `measure`. → The pinned version and the test with the real metric find a break.
- mutmut can fail on this layout. → Task 1.2 proves that `mutmut run` works, with a subprocess test in the sample, before any code depends on it. The fallback is `cosmic-ray`.
- Greedy decoding gives stable answers, but a model update can change them. → The e2e test examines the structure only.
- A `.env` file can hold an OpenAI key, and DeepEval loads that file. → The judge never reads an OpenAI variable (D2).

## Plan examination

Four reviewers examined the first version of this plan by experiment. Their topics were request fit, library contracts, test and gate feasibility, and runtime facts. Each finding went to two skeptics who tried to disprove it.

The reviewers made 42 findings. The skeptics confirmed 27, split on 8, and rejected 7. I accepted the 27 and the 8.

The primary changes:
- D2: an explicit `api_key`, an empty organization and project, a 120 second timeout, and the HTTP package for the tests.
- D6: no `_log_metric_to_confident` argument, and a test with the real metric.
- D3: the rules for shared definitions, other keys next to a `$ref`, and cycles.
- D8: the `.env` path, the error status at the first call, and the lint reason for the broad `except`.
- D9 and D11: code that mutmut can mutate, the mutation score formula, the `mutants/` folder settings, and the `pragma` rules.
- D10: an isolated environment for each test. A socket test for the telemetry claim. A `runpy` test for the entry guard.
- Tasks: the order of the group 1 tasks and the README sections for the gates. Each "done when" statement has a way to examine it.

The skeptics rejected seven findings. Examples are a score outside 0 to 10 and a conflict between the JSON requirement and the error paths. I made the report format exact in the spec (D13). I kept the other items as they are.
