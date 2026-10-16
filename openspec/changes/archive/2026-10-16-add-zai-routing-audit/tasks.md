# Tasks

## 1. Scaffolding

- [x] 1.1 Create `tools/zai_routing_audit/` with the package layout (`zai_routing_audit/__init__.py`, `core.py`, `cli.py`, `mcp_server.py`), `requirements.txt`, `requirements-dev.txt`, `ruff.toml`, and `README.md`. Verify `ls` shows all files.
- [x] 1.2 Create the venv `tools/zai_routing_audit/.venv` and install the requirement files. Verify `.venv/bin/python -c "import mcp, pytest, pytest_cov, ruff, mutmut"` exits 0.
- [x] 1.3 Register the dependency unit `zai-routing-audit-python-deps` in `tools/project_setup/registry.json` after the `fde-python-dev` pattern. Verify the registry still parses as JSON and the check command runs.

## 2. Core audit functions

- [x] 2.1 Implement `redact()`, settings loading, and the tolerant JSON parser in `core.py` with unit tests for the redacted prefix, the missing file error, and the control-character fallback. Verify `pytest tests/zai_routing_audit -k core` is green.
- [x] 2.2 Implement the transport objects (urllib-backed live transport with `post_json` and `get_json`) and the injected fake used by tests. Verify the fake drives one post and one get without network.
- [x] 2.3 Implement `scan_transcripts()` with unit tests for both model directions, usage sums, a malformed line, and a control-character line. Verify the transcript tests pass.
- [x] 2.4 Implement the console report parsing (`model-usage` rows, `quota/limit` pools, both envelope variants, schema-drift excerpt) with unit tests per shape. Verify the parsing tests pass.

## 3. Commands

- [x] 3.1 Implement the `config` command and its tests (token redacted in text and JSON, missing file exits 2). Verify the tests pass and the real command prints a redacted token.
- [x] 3.2 Implement the `transcripts` command and its tests (counts, sums, empty directory exits 0, `--json` parses). Verify the tests pass.
- [x] 3.3 Implement the `echo` command and its tests (match exits 0, mismatch exits 2, transport failure exits 2 without traceback). Verify the tests pass.
- [x] 3.4 Implement the `usage` command and its tests (rows, pools, alternate envelope, drift excerpt). Verify the tests pass.
- [x] 3.5 Implement the `throughput` command with an injected clock and its test for the tokens-per-second math. Verify the test passes.
- [x] 3.6 Implement the `burn` command with the `--spend-credits` gate and its tests (no flag sends nothing, flag measures deltas from the fixture). Verify the tests pass.
- [x] 3.7 Implement the argparse CLI with `--json`, exit codes 0 and 2, and a test that scans every command output for the full token. Verify `--help` shows all six commands.

## 4. MCP wrapper and Claude surfaces

- [x] 4.1 Implement `mcp_server.py` as a thin FastMCP wrapper over the commands and add an import test. Verify the wrapper imports with the tool venv interpreter.
- [x] 4.2 Add `.mcp.json`, the `enabledMcpjsonServers` entry, and the permission entries in `.claude/settings.json`. Verify the file set parses as JSON.
- [x] 4.3 Add `.claude/skills/zai-routing-audit/SKILL.md` with triggers, commands, exit codes, and cost notes. Verify the directory name matches the skill name.
- [x] 4.4 Update `CLAUDE.md` (projects list) and finish the tool `README.md` (purpose, commands, costs, endpoint disclaimer). Verify the documented commands run as written.

## 5. Repo test integration

- [x] 5.1 Add the root `pytest.ini` with `testpaths = tests` and the `e2e` marker. Verify `python -m pytest` from the repo root collects only `tests/` and is green without network.
- [x] 5.2 Add the live `e2e` tests gated by `ZAI_ROUTING_AUDIT_E2E`. Verify the suite skips them without the variable.

## 6. Gates

- [x] 6.1 Run branch coverage over the package with `--cov-branch --fail-under=100` and add the missing branch tests. Verify the coverage command passes.
- [x] 6.2 Run `ruff check` with `C901` at max-complexity 10 over the package and split any function above the limit. Verify the checker passes.
- [x] 6.3 Run `mutmut` against an out-of-tree copy of the package (repo tools, tests, and config stay untouched) and reach a mutation score of 95 percent or higher; write the per-mutant reason for every excluded equivalent mutant. Verify the score report.

## 7. Integration checks

- [x] 7.1 Run the full hermetic suite from the repo root. Verify it is green. (The repo has no Claude-infra contract test directory yet, so that check does not exist to run.)
- [x] 7.2 Run `openspec validate add-zai-routing-audit`. Verify it passes.

## Workflow follow-up

- Commit, publish, open the pull request, run the adversarial review, fix findings, merge, archive the change, delete the branch.
- Write the STE blog post to `~/Desktop/zai-claude-code-model-routing.md` (not a repo change).
