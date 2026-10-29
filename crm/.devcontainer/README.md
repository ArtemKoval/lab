# The crm dev container

The container gives the crm project Python 3.12, Node 22, uv, and the
Python and Node dependency sets. Open this folder in VS Code and rebuild
the container. The post-create step installs uv, runs `uv sync`, and runs
`npm install`.

Run the product with `npm run dev`, and the checks with `npm run check`,
from `/workspaces/crm`. The `OPENROUTER_API_KEY` variable is optional: the
tests and the e2e never call a model, and the `MODEL_NAME` variable names
another model when set.

This container is separate from the UnderCover contribution masters under
`fde/.devcontainer/` in the repository root, which the root suite guards
for byte identity with the upstream contribution.
