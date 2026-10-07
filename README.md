# lab
A vessel for the various engineering artifacts

## Installing OpenSpec
- https://github.com/Fission-AI/OpenSpec/blob/main/docs-lab/start/installation.md#install-with-your-ai-assistant

To install OpenSpec from the command line, run `npm install -g @fission-ai/openspec@latest`. You must have Node.js 20.19.0 or newer.

## Prepare a clean clone
The file `tools/project_setup/registry.json` names the units that a clean clone must have. In Claude Code, use the `project-setup` skill. The skill examines each unit. It installs each unit that the clone does not have after you give permission.
