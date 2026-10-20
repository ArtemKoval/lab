# Tasks

## 1. Core tool

- [x] 1.1 Create `tools/devcontainer_init/devcontainer_init/` with `core.py` (`DEFAULT_UBUNTU_LTS` constant, `build_config`, `render`), `cli.py` (argparse, `--json`, `--force`, `--os`, `--extension`, exit 0 and 2), `__init__.py`, and `__main__.py`
- [x] 1.2 Implement the safe-write path: require an existing target, refuse an existing `devcontainer.json` without `--force`, machine-readable output with `--json`
- [x] 1.3 Add `tools/devcontainer_init/README.md` with purpose, commands, exit codes, and the e2e gate

## 2. Tests

- [x] 2.1 Add `tests/devcontainer_init/` with the dual-path conftest and hermetic unit tests for `build_config` and `render`
- [x] 2.2 Add hermetic CLI tests: scaffold, refusal without `--force`, overwrite with `--force`, missing target, `--os`, `--extension` order and duplicates, `--json` success and failure shapes
- [x] 2.3 Add the e2e module gated on `DEVCONTAINER_INIT_E2E=1` with the `e2e` marker: `read-configuration` validation, build, and in-container checks for `node`, `uv`, `git`, and the OS release

## 3. Claude surfaces and docs

- [x] 3.1 Add `.claude/skills/devcontainer-init/SKILL.md` with the trigger description, the CLI command, exit codes, and the build command
- [x] 3.2 Add the tool to the Projects list in CLAUDE.md

## 4. Gates and review

- [x] 4.1 Run the full hermetic suite, branch coverage of the new code, and the `C901` complexity check with the root venv
- [x] 4.2 Run the mutation gate with mutmut on a flattened out-of-tree copy and reach a score of at least 95 percent, with written reasons for any equivalent-mutant exclusions
- [x] 4.3 Run `openspec validate add-devcontainer-init` and confirm every spec scenario has a test
- [ ] 4.4 Commit, open the pull request, run the adversarial review, fix the confirmed findings, and merge
