## ADDED Requirements

### Requirement: The executed copy lands beside the source
The runner at `tools/knights_notebook_run/run_notebook.sh` SHALL write
the executed notebook as `notebooks/executed-knights-and-knaves-agent.ipynb`,
next to the source, and SHALL leave the source notebook unchanged.
The runner SHALL run inside the `fde` devcontainer through the recipe
command in the README. The runner SHALL source `.env` at the repo root
for its secrets.

#### Scenario: The source stays clean
- **WHEN** the runner executes the notebook
- **THEN** the executed copy lands at
  `notebooks/executed-knights-and-knaves-agent.ipynb`, and the source
  notebook carries no outputs

### Requirement: The shim serves the secret from the environment
The shim at `tools/knights_notebook_run/google/colab/userdata.py`
SHALL read the secret from the environment in place of
`google.colab.userdata`. On an absent name the shim SHALL raise
`KeyError` with guidance that names the `.env` file at the repo root.

#### Scenario: An absent name gets guidance
- **WHEN** the shim reads a name the environment does not carry
- **THEN** the shim raises `KeyError` and the message names the `.env`
  file at the repo root

### Requirement: The runner installs its packages
The runner SHALL install its packages (`openai`, `requests`, `ipython`,
`nbconvert`, `ipykernel`, `datasets`) in the container before the
execute step, so the notebook's `%pip` cell needs no Colab hosting.

#### Scenario: The packages install before the execute
- **WHEN** the runner runs in a fresh container
- **THEN** it installs the six packages before the notebook executes
