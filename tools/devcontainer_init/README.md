# devcontainer-init

One command that writes a complete `.devcontainer/devcontainer.json` into an existing project directory. The generated config gives a VS Code devcontainer with these parts wired up:

- the `ubuntu:26.04` image, the latest LTS Ubuntu at the time of writing,
- `common-utils:2` for the `vscode` user, sudo, and locale,
- `git:1` with the `os-provided` version, so git installs through apt in seconds,
- `node:2` with the `lts` version, so each build takes the current Node LTS,
- `uv:1` with the `latest` version, so each build takes the current uv stable release,
- `remoteUser` set to `vscode`.

There is no Dockerfile. Image plus features is the fastest standard assembly. The image has no Python interpreter; run `uv python install` inside the container when a project needs one.

## Usage

Run from `tools/devcontainer_init/` with any Python 3.11 or newer:

```bash
cd tools/devcontainer_init
python3 -m devcontainer_init /path/to/project
python3 -m devcontainer_init /path/to/project --os 24.04 --extension ms-python.python --json
```

The target directory must exist. The tool writes `<target>/.devcontainer/devcontainer.json` and creates the `.devcontainer` directory when needed.

| Flag | Meaning |
|---|---|
| `--os VERSION` | Ubuntu version for the base image; default `26.04` |
| `--extension ID` | Add one VS Code extension; repeatable; duplicates removed, order kept |
| `--force` | Overwrite an existing `devcontainer.json` |
| `--json` | Print one JSON object with `ok`, the written path, `os`, and `extensions` |

Exit code is 0 on success and 2 on operational failure: a missing target, or an existing config without `--force`. A refusal leaves the existing file unchanged.

## Tests

The root suite runs the hermetic tests; the root venv interpreter runs it:

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/devcontainer_init
```

The e2e suite builds the container and checks `node`, `uv`, `git`, and the OS release inside it. It needs Docker and `npx`, downloads feature images, and stays opt-in:

```bash
DEVCONTAINER_INIT_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest tests/devcontainer_init -m e2e
```

## Mutation run

Run mutmut on an out-of-tree copy, never inside the repository:

```bash
rm -rf /tmp/dcinit_mut && mkdir -p /tmp/dcinit_mut
rsync -a --exclude __pycache__ tools/devcontainer_init/ /tmp/dcinit_mut/dcinit/
mkdir -p /tmp/dcinit_mut/tests
cp -r tests/devcontainer_init/. /tmp/dcinit_mut/tests/
cd /tmp/dcinit_mut
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut run
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut results
```

The final run kills 194 of 197 mutants, a score of 98.5 percent. The 3 survivors sit in one equivalence class that behaves identically by construction:

| Class | Where | Why the mutant behaves the same |
|---|---|---|
| codec forms | `write_text` in `scaffold` | `utf-8` and `UTF-8` name the same codec, and the default encoding of the runner locale is UTF-8. The written JSON is ASCII because `json.dumps` escapes non-ASCII, so every form writes identical bytes. |

The behavior spec lives at `openspec/specs/devcontainer-init/` after the change `add-devcontainer-init` archives.
