# devcontainer-init

One command that writes a complete `.devcontainer/devcontainer.json` into an existing project directory. The generated config gives a VS Code devcontainer with these parts:

- the `ubuntu:26.04` image, the latest LTS Ubuntu at the time of writing,
- `common-utils:2` for the `vscode` user, sudo, and locale,
- `git:1` with the `os-provided` version, so git installs through apt in seconds,
- `node:2` with the `lts` version, so each build takes the current Node LTS,
- `uv:1` with the `latest` version, so each build takes the current uv stable release,
- `remoteUser` set to `vscode`.

There is no Dockerfile. Image plus features is the fastest standard assembly. The image has no Python interpreter. Run `uv python install` inside the container when a project must have one.

## Usage

Run from `tools/devcontainer_init/` with any Python 3.11 or newer:

```bash
cd tools/devcontainer_init
python3 -m devcontainer_init /path/to/project
python3 -m devcontainer_init /path/to/project --os 24.04 --extension ms-python.python --json
```

The target directory must exist. When the user omits the target, the tool uses the current directory. The tool writes `<target>/.devcontainer/devcontainer.json` and creates the `.devcontainer` directory when the directory is absent.

| Flag | Meaning |
|---|---|
| `--os VERSION` | Ubuntu version for the base image. The default is `26.04` |
| `--extension ID` | Add one VS Code extension to the config. Repeat the flag for more. The tool removes duplicates and keeps the order |
| `--force` | Overwrite an existing `devcontainer.json` |
| `--json` | Print one JSON object with `ok`, the written path, `os`, and `extensions` |

Exit code is 0 on success and 2 on operational failure. The failure cases are a missing target, an existing config without `--force`, and a config the tool cannot write. A refusal leaves the existing file unchanged. The refusal test does not follow symlinks.

## Tests

The root suite runs the hermetic tests. The root venv interpreter runs it:

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/devcontainer_init
```

The e2e suite builds the container and examines `node`, `uv`, `git`, and the OS release inside it. It must have Docker and `npx`, and it downloads feature images. It stays opt-in:

```bash
DEVCONTAINER_INIT_E2E=1 tools/zai_routing_audit/.venv/bin/python -m pytest tests/devcontainer_init -m e2e
```

## Mutation run

Run mutmut on an out-of-tree copy, never inside the repository:

```bash
rm -rf /tmp/dcinit_mut && mkdir -p /tmp/dcinit_mut
rsync -a --exclude __pycache__ tools/devcontainer_init/ /tmp/dcinit_mut/
mkdir -p /tmp/dcinit_mut/tests
cp -r tests/devcontainer_init/. /tmp/dcinit_mut/tests/
cd /tmp/dcinit_mut
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut run
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut results
```

The last measured run killed 203 of 206 mutants, a score of 98.5 percent. Run the recipe again after each code change, and write down the new score here. The 3 survivors sit in one equivalence class that behaves identically by construction:

| Class | Where | Why the mutant behaves the same |
|---|---|---|
| codec forms | `write_text` in `scaffold` | `utf-8` and `UTF-8` name the same codec. The default encoding of the runner locale is UTF-8. The written JSON is ASCII because `json.dumps` escapes non-ASCII. Every form writes identical bytes. |

The behavior spec lives at `openspec/specs/devcontainer-init/` after the change `add-devcontainer-init` archives.
