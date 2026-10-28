# knights_notebook_run

This folder holds the recipe that runs the `notebooks/knights-and-knaves-agent.ipynb` notebook inside the `fde` devcontainer. The notebook is a Colab artifact. It imports `google.colab.userdata` for its secret and installs its packages with a `%pip` cell. This folder gives the notebook the pieces that Colab hosts for free:

- `google/colab/userdata.py` reads the API key from the environment.
- `run_notebook.sh` sources the key, installs the packages, and executes the notebook.

The executed copy lands next to the source as `notebooks/executed-knights-and-knaves-agent.ipynb`. The source notebook stays clean, so the notebook tests keep passing.

## Before you start

- Docker with a running daemon, and your user in the `docker` group
- A file `.env` at the repo root with the line `OPENROUTER_API_KEY=sk-or-v1-...`

## How to run

1. Build the container once: `npx @devcontainers/cli up --workspace-folder fde --skip-post-create`.
   The skip is necessary because the post-create command targets the upstream course layout at the mount root, and this repo does not use that layout.
2. Run the recipe: `sg docker -c 'npx @devcontainers/cli exec --workspace-folder fde bash /workspaces/undercover/lab/tools/knights_notebook_run/run_notebook.sh'`.
   The `sg` prefix gives the command the `docker` group when the shell session lacks it.
3. Read the result at `notebooks/executed-knights-and-knaves-agent.ipynb`.

A full run makes about 15 OpenRouter requests. The notebook caps itself at its own `DAILY_BUDGET` of 50 requests a day. A full run takes about 5 minutes.

## Provenance

The committed executed copy comes from a run on 2026-10-28 with devcontainer CLI 0.90.0 and Docker 29.1.3. The tournament results of that day live in the handover issues on GitHub. Free-model rosters on OpenRouter rotate, so a later run can rank other models.

## Shape of this folder

The deliverable is a container exec recipe, so the runner is one bash script and not a Python module with a CLI. The unit tests for the shim live in `tests/knights_notebook_run/`.
