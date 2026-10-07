# eval

This folder is the `eval` project of `llm_ops`. It has a DeepEval script that uses a local apfel server as the judge. The code is in the package `apfel_eval`.

apfel is a command line tool for macOS. It runs the Apple on-device model as an OpenAI-compatible server. No cloud key is necessary.

| Path | Description |
|---|---|
| `apfel_eval/judge.py` | `ApfelJudge`, a DeepEval judge model that calls the apfel server. |
| `apfel_eval/run.py` | The command that asks four questions and scores the answers. |
| `tests/` | Unit tests that use no network. One file uses the real server. |
| `pyproject.toml` | The settings for pytest, coverage, ruff, and mutmut. |
| `requirements.txt` | The packages that the code uses, with exact versions. |
| `requirements-dev.txt` | The packages of `requirements.txt` and the test and gate tools. |

## Start the apfel server

The server runs on your computer, not in the container. Run this command in a terminal on your computer:

```bash
apfel --serve
```

The server listens on `127.0.0.1:11434`. To examine it, run `curl http://127.0.0.1:11434/health`.

## Run in a devcontainer

The devcontainer uses Python 3.12 on Debian Trixie. After Docker creates the container, the devcontainer tool runs `pip install -r requirements-dev.txt` in the container. You do not make a virtual environment in the container.

Before you start, make sure that you have these items:

- Docker Desktop or Docker Engine. The Docker daemon must run.
- For the command line: Node.js 20 or newer.
- For VS Code: the Dev Containers extension.

### With VS Code

1. Open the `llm_ops/eval` folder in VS Code.
2. Run the command `Dev Containers: Reopen in Container`.
3. Wait for the container to start.
4. Open a terminal in VS Code. The terminal runs in the container.

To make the container again, run the command `Dev Containers: Rebuild Container`.

### With the command line

1. Open a terminal in the `llm_ops/eval` folder.
2. Run `npx @devcontainers/cli up --workspace-folder .`
3. Run `npx @devcontainers/cli exec --workspace-folder . bash`

The `up` command is slow the first time, because Docker pulls the image.

When the container starts, the `up` command shows `"outcome":"success"`.

To leave the shell, run `exit`.

To run one command in the container, put the command after `--workspace-folder .`:

```bash
npx @devcontainers/cli exec --workspace-folder . python --version
```

The container uses the files in the folder on your computer. You do not copy files into the container. The CLI mounts the whole repository in `/workspaces/<name>`. The `<name>` is the name of the repository folder on your computer.

The shell starts in the `llm_ops/eval` folder of the repository. The shell user is `vscode`.

To delete the container on macOS or Linux, run this command in a Bash terminal in the `llm_ops/eval` folder:

```bash
docker rm -f $(docker ps -aq --filter "label=devcontainer.local_folder=$(pwd -P)")
```

If no container matches the folder, Docker shows an error that has the text `requires at least 1 argument`.

The delete command for Windows is TBD.

### Install

The project has two files of packages. Both files use exact versions.

| File | Use |
|---|---|
| `requirements.txt` | The packages to run the code: `deepeval`, `openai`, and `python-dotenv`. |
| `requirements-dev.txt` | The packages of `requirements.txt`, `pytest`, `pytest-cov`, `ruff`, `mutmut`, and `httpx2`. |

The devcontainer installs `requirements-dev.txt`. To install the packages again, run this command in the container:

```bash
pip install -r requirements-dev.txt
```

### Add a package

1. Add the package to `requirements.txt` with an exact version. For a test tool, use `requirements-dev.txt`.
2. Run `pip install -r requirements-dev.txt` in the container.

To run the command from a terminal on your computer, use this command:

```bash
npx @devcontainers/cli exec --workspace-folder . pip install -r requirements-dev.txt
```

A new container installs the packages automatically. Pip shows the notice `Defaulting to user installation`. This notice is normal, because the system folder of Python belongs to `root`.

### If a package fails to install

The first `up` command shows the pip error and returns exit code 1. A second `up` command shows `"outcome":"success"`, but it does not install the packages. Do these steps:

1. Correct `requirements.txt` or `requirements-dev.txt`.
2. Run `npx @devcontainers/cli up --workspace-folder . --remove-existing-container`

### Change the devcontainer

If you change `.devcontainer/devcontainer.json`, make the container again:

```bash
npx @devcontainers/cli up --workspace-folder . --remove-existing-container
```

## Run the evaluation

Start the apfel server. Then run this command in the container:

```bash
python -m apfel_eval.run
```

The command asks apfel four questions with temperature 0. It scores each answer with the DeepEval metric GEval. The same apfel server is the judge.

This is the output of a real run in the devcontainer against apfel 1.10.0:

```text
PASS 0.90 | What is the capital of France? | expected: Paris | answer: Paris
PASS 0.90 | How many days are in a leap year? | expected: 366 | answer: 366
PASS 0.90 | What is the chemical symbol for water? | expected: H2O | answer: H2O
PASS 0.90 | Who wrote the play Romeo and Juliet? | expected: William Shakespeare | answer: Shakespeare
total=4 passed=4 failed=0 errors=0
```

Your scores can be different. The judge is a model, and it is not a proof of correctness.

### Exit codes

| Exit code | Description |
|---|---|
| 0 | All answers pass. |
| 1 | At least one answer fails. No question has an error. |
| 2 | The server does not work, an option is wrong, or a question has an error. |

### Options and settings

| Item | Default | Description |
|---|---|---|
| `--base-url` | `http://host.docker.internal:11434/v1` | The base URL of the server. |
| `APFEL_BASE_URL` | none | The base URL of the server. The option has priority. |
| `--model` | `apple-foundationmodel` | The model name. |
| `--threshold` | `0.5` | The lowest score that passes. Use a number from 0 to 1. |
| `--json` | off | Print one JSON document in place of rows. |
| `APFEL_TOKEN` | none | The token. Use it if you start apfel with `--token`. |

The command reads `APFEL_BASE_URL` and `APFEL_TOKEN` from the file `.env` in the current folder. The shell has priority over the file. The `.env` file is not in Git.

### Time

A run makes 1 call to list the models and 8 model calls. The run above took 56 seconds. The e2e tests took 95 seconds.

A call takes 6 to 40 seconds. A slow server can make a run take several minutes. The judge stops a call after 120 seconds.

Do not start two runs at the same time. The on-device model slows down when it has parallel calls.

A socket log of a real run shows one DNS name, `host.docker.internal`, and one connection to the apfel server. The run sends nothing to a cloud host.

### The Host header

The apfel server answers HTTP 403 to a Host name that is not a loopback name. The container reaches the host as `host.docker.internal`. For a host that is not `localhost`, `127.0.0.1`, or `::1`, the judge sends the header `Host: localhost:<port>`. The port is the port of the base URL. The judge changes nothing for a loopback host.

It is not necessary to start apfel with `--no-origin-check`.

### Limits of the judge

The judge is a small on-device model. It makes mistakes. Its reasons can be wrong. The context window has 4096 tokens. Use the scores to find a change, not as a proof.

The steps of the metric decide the quality of the scores. The command uses three fixed steps. If you give GEval only a `criteria` text, the judge writes the steps and they drift. In one test with this option, the answer `366` for the expected `366` got the score 0.1.

With the fixed steps, the answer `Da Vinci` for the expected `Leonardo da Vinci` still got the score 0.0. The design file in `openspec/changes/` has the measured scores.

### Telemetry

DeepEval sends telemetry to a cloud host unless the variable `DEEPEVAL_TELEMETRY_OPT_OUT` is set. The package `apfel_eval` sets it to `YES` when it loads, if you did not set it. To turn telemetry on, set the variable to `NO` before the code loads.

## Use the judge in your own script

`ApfelJudge` is a DeepEval judge model. Give it to any metric:

```python
from apfel_eval.judge import ApfelJudge  # Keep this import first. It turns telemetry off.
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

judge = ApfelJudge("http://host.docker.internal:11434/v1")
metric = GEval(
    name="Correctness",
    evaluation_steps=[
        "Read the expected output and the actual output.",
        "If the actual output states the same fact as the expected output, give a score of 9 or 10.",
        "If the actual output states a different fact, give a score of 0 or 1.",
    ],
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    model=judge,
    async_mode=False,
)
case = LLMTestCase(input="Capital of France?", actual_output="Paris", expected_output="Paris")
metric.measure(case, _show_indicator=False)
print(metric.score, metric.reason)
```

Import `apfel_eval` before you import DeepEval in your own script. DeepEval reads the telemetry variable when it loads.

Write the evaluation steps yourself. Do not give only a `criteria` text, because the judge then writes steps that drift.

The judge sends one request at a time, makes no retry, and stops a request after 120 seconds. It never sends the value of `OPENAI_API_KEY`.

## Run the tests

Run the unit tests in the container. They use no network and no apfel server:

```bash
pytest
```

To run the e2e tests, start apfel on your computer. Then run this command in the container:

```bash
APFEL_E2E=1 pytest -m e2e
```

## Run the quality gates

Run each gate in the container, in the `llm_ops/eval` folder. Each gate must pass.

1. Run the tests with 100% line and branch coverage:

   ```bash
   pytest --cov=apfel_eval --cov-branch --cov-fail-under=100
   ```

2. Run the style and complexity gate. The complexity limit is 10.

   ```bash
   ruff check
   ruff check --select C901
   ```

3. Run the mutation tests. They make a copy of the code in `mutants/`.

   ```bash
   mutmut run
   mutmut export-cicd-stats
   ```

4. Compute the mutation score. It must be 0.95 or more.

   ```bash
   python -c "import json; d = json.load(open('mutants/mutmut-cicd-stats.json')); print((d['killed'] + d['timeout']) / (d['total'] - d['skipped']))"
   ```

## Run without a devcontainer

On some computers, the command `python` does not exist. On these computers, use `python3`.

1. Make a virtual environment: `python -m venv .venv`
2. Activate the virtual environment:
   - On Windows (Git Bash), run `source .venv/Scripts/activate`.
   - On macOS and Linux, run `source .venv/bin/activate`.
3. Run `pip install -r requirements-dev.txt`

The default base URL names `host.docker.internal`. Outside a container, use `--base-url http://127.0.0.1:11434/v1`.
