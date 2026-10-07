---
name: apfel-eval
description: Run or debug the DeepEval check that uses the local apfel server (the Apple on-device model) as the judge. Use this skill when the user asks to test the Apple model as a judge, to run the llm_ops/eval evaluation, or to find the cause of an apfel connection error in the devcontainer. The skill gives the commands, the exit codes, and the known problems.
---

# apfel eval

The project `llm_ops/eval` asks a local apfel server four fixed questions. It scores the answers with DeepEval. The same server is the judge.

The `llm_ops/eval/README.md` file has the full description.

## Before you start

1. Make sure that apfel runs on the host. Run `curl http://127.0.0.1:11434/health`.
2. If apfel does not run, ask the user to start it. The command is `apfel --serve`.
3. Start the devcontainer: `npx @devcontainers/cli up --workspace-folder llm_ops/eval`

The container reaches the host as `host.docker.internal`. The judge sends the header `Host: localhost:<port>` to this name. The apfel Host guard accepts this header.

## Run the evaluation

Run this command from the root of the repository:

```bash
npx @devcontainers/cli exec --workspace-folder llm_ops/eval python -m apfel_eval.run
```

Add `--json` to get one JSON document. The JSON has the keys `base_url`, `model`, `threshold`, `results`, and `summary`.

A run makes 9 calls to the server. A real run took 56 seconds. A slow server can take several minutes. Do not start two runs at the same time. The on-device model slows down.

## Read the result

The command prints one row for each question and one summary line:

```text
PASS 0.80 | <question> | expected: <expected> | answer: <answer>
total=4 passed=4 failed=0 errors=0
```

| Exit code | Description |
|---|---|
| 0 | All answers pass. |
| 1 | At least one answer fails. No question has an error. |
| 2 | The server does not work, the options are wrong, or a question has an error. |

A score is the integer that the judge gives (0 to 10) divided by 10. An answer passes if its score is equal to or higher than the threshold. The default threshold is 0.5.

## Options and settings

| Item | Default | Use |
|---|---|---|
| `--base-url` or `APFEL_BASE_URL` | `http://host.docker.internal:11434/v1` | The base URL of the server. The option has priority. |
| `--model` | `apple-foundationmodel` | The model name. |
| `--threshold` | `0.5` | The lowest score that passes. Use a number from 0 to 1. |
| `--json` | off | Print JSON in place of rows. |
| `APFEL_TOKEN` | none | The token, if you start apfel with `--token`. |

The command reads `APFEL_BASE_URL` and `APFEL_TOKEN` from the file `.env` in the current folder. The shell has priority over the file.

## Known problems

- **Exit code 2 and the status 403.** The base URL or the Host header is wrong. The message names the base URL. Do not use `--no-origin-check` unless the user agrees. The flag removes a protection of apfel.
- **Exit code 2 and `APIConnectionError`.** Nothing listens at the base URL. Ask the user to start `apfel --serve` on the host.
- **A question has the error `context window`.** The prompt is over 4096 tokens. The run records the error and continues.
- **A correct answer fails.** The judge is a small model. Its reasons can be wrong. Read the `reason` key in the JSON. A metric with only a `criteria` text gives bad scores, because the judge writes steps that drift. Use fixed `evaluation_steps`.
- **Telemetry.** DeepEval telemetry is off. The package sets `DEEPEVAL_TELEMETRY_OPT_OUT=YES` when you did not set it.

## Change the code

Run the tests and the gates from the README section "Run the quality gates". Do not lower a gate to make a change pass.
