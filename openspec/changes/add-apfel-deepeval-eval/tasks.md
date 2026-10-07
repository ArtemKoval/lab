# Tasks

## 1. Project setup

- [ ] 1.1 Add `pyproject.toml` with the settings for `pytest`, coverage, `ruff`, and `mutmut` (design D11). Done when `pytest --collect-only` shows no configuration error in the devcontainer. Exit code 5 (no tests) is expected.
- [ ] 1.2 Pin the versions in `requirements.txt`. Add `requirements-dev.txt`. Change the `postCreateCommand` of the devcontainer. Done when a new container installs both files and `python -c "import deepeval, openai, dotenv, pytest"` exits 0. Add the import of the test HTTP package.
- [ ] 1.3 Prove that `mutmut run` works on this layout. Use a scratch copy in the devcontainer with a small judge subclass and a subprocess test. Done when `mutmut results --all true` lists killed mutants and `mutmut export-cicd-stats` writes a readable JSON file.
- [ ] 1.4 Add the entries `.env`, `.deepeval/`, `.coverage`, `mutants/`, and the tool caches to `llm_ops/eval/.gitignore`. Done when `git status` shows none of these paths after a test run.
- [ ] 1.5 Update `llm_ops/eval/README.md`: the intro, the install sentences, "Add a package", and "If a package fails to install". Add the section "Install". Done when no README sentence contradicts `devcontainer.json` and `requirements-dev.txt`.

## 2. Judge

- [ ] 2.1 Write `apfel_eval/__init__.py` with the function `_opt_out_of_telemetry()`. Write subprocess tests for both scenarios of the telemetry requirement. Done when both tests pass.
- [ ] 2.2 Write `inline_refs`. Write unit tests for these schemas: nested, no references, shared definition, other keys, and optional model. Add tests for a direct and an indirect cycle. Done when the tests pass.
- [ ] 2.3 Write `host_headers`. Write unit tests for a container host, the three loopback hosts, a URL with no port, and an IPv6 URL. Done when the tests pass.
- [ ] 2.4 Write `ApfelJudge` with the four abstract methods and `ping`. Write one test for each scenario of the judge spec, with a mock transport. Include the key, organization, and project cases, the empty reply, the timeout, and the kept `http_client`. Done when the tests pass.
- [ ] 2.5 Write the socket test of the telemetry requirement. A subprocess runs the real GEval metric with the judge and a mock transport. It records each connection and DNS name. Done when no non-loopback target exists.

## 3. Run command

- [ ] 3.1 Write `cases()`, the answer prompt, the metric builder, and the per-question run with its error boundary. Write tests with the fake apfel function and the real GEval metric. Include a test that `measure` accepts the arguments of the run. Done when the scenarios of the question, scoring, and error requirements pass.
- [ ] 3.2 Write the row formatter, the summary line, and the JSON report. Write tests that compare exact strings. Done when the report scenarios pass and the standard output holds no DeepEval text.
- [ ] 3.3 Write the command line with the options, the variables, the `.env` file, the server call, and the exit codes. Add the `runpy` test of the entry point. Done when the scenarios of the settings, threshold, server, and exit code requirements pass.

## 4. Real server

- [ ] 4.1 Write the e2e tests for a text call, a nested schema call, a scored right answer, a scored wrong answer, and a full run. Done when `APFEL_E2E=1 pytest -m e2e` passes in the devcontainer against the apfel server on the host.
- [ ] 4.2 Run `python -m apfel_eval.run` in the devcontainer against the real server. Done when the output has four rows and the exit code is 0 or 1. Save the output and the wall time for the pull request.
- [ ] 4.3 Run the same command with the socket recorder of task 2.5. Done when the record shows connections only to the apfel server.
- [ ] 4.4 Add the sections "Use the judge in your own script" and "Run the evaluation" to the README. They name the command to start apfel, the exit codes, and the Host override. They also give the measured time from task 4.2 and the limits of the judge. Done when each documented command runs as written against the real server.

## 5. Quality gates

- [ ] 5.1 Run `pytest --cov=apfel_eval --cov-branch --cov-fail-under=100`. Done when the run passes with 100% line and branch coverage.
- [ ] 5.2 Run `ruff check` and `ruff check --select C901`. Done when both runs report no error and the largest complexity is 10 or less.
- [ ] 5.3 Run `mutmut run` in the devcontainer. Add a test for each survivor. Done when the score command of D11 prints 0.95 or more. Write the score and each pragma reason in the pull request.
- [ ] 5.4 Add the section "Run the quality gates" to the README, with the score command. Done when each command in the section runs as written.

## 6. Claude surface and setup

- [ ] 6.1 Write `.claude/skills/apfel-eval/SKILL.md`. It names when to run the evaluation, the commands, the exit codes, and the known problems. Done when each command in the skill runs as written.
- [ ] 6.2 Add one entry for the eval project to `CLAUDE.md`. Repair the path of the style file in the same file. Done when the entry names the README and the skill, and the style file path exists.
- [ ] 6.3 Add the units `apfel-cli` and `eval-python-deps` to `tools/project_setup/registry.json`. Done when the `check` command of each unit exits with code 0 in its environment.
- [ ] 6.4 Examine all new prose against section 11 of the STE style file. Use a word-count script that is not committed. Done when no sentence is over the limit and no word from the "Do not write" table remains.

## 7. Integration

- [ ] 7.1 Run `openspec validate add-apfel-deepeval-eval --strict`. Done when it reports no error.
- [ ] 7.2 Run all the gates one more time. Examine the repository for stray files. Done when all gates pass and `git status` lists only the planned files.

## Workflow follow-up

- Open the pull request with the gate results, the mutation score, the wall time, and the real-server output.
- Run the adversarial review. Repair each confirmed finding.
- Archive the change as the last commit before the squash-merge.
- Delete the branch and examine the merged `main`.
