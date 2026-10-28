#!/usr/bin/env bash
# Run the knights-and-knaves notebook inside the fde devcontainer.
# The executed copy goes next to the source. The source stays clean.
set -euo pipefail
RUN_DIR=/workspaces/undercover/lab/tools/knights_notebook_run
export PYTHONPATH="$RUN_DIR"
set -a
# shellcheck disable=SC1091
. /workspaces/undercover/lab/.env
set +a
pip install --quiet openai requests ipython nbconvert ipykernel datasets
cd /workspaces/undercover/lab/notebooks
exec jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=-1 \
  --output executed-knights-and-knaves-agent.ipynb \
  knights-and-knaves-agent.ipynb
