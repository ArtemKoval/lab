---
name: project-setup
description: Prepare or repair a clean clone of this repository. Use this skill when the clone does not have a tool or a command is not found. Also use it when the user asks to prepare the project or the machine. Also use it when the feature-pipeline skill must have a gate tool. The skill reads tools/project_setup/registry.json and examines each unit. It installs each unit that the clone does not have after the user gives permission.
---

# Project setup

The file `tools/project_setup/registry.json` names each item that a clean clone must have. Each item is a unit.

## Examine and repair a clone

1. Read `tools/project_setup/registry.json`.
2. Run the `check` command of each unit.
3. Report each unit whose `check` command exits with a code other than 0.
4. Show the `install` command of each failed unit to the user.
5. Ask the user for permission to run each `install` command.

> **CAUTION:** Do not run an `install` command before the user gives permission. Some `install` commands change the whole machine.

6. If the user gives permission, run the `install` command.
7. Run the `check` command again.
8. Report the result to the user.

## Unit fields

The `version` key of the file is the version of the file format.

| Field | Description |
|---|---|
| `id` | A unique name in kebab-case. |
| `kind` | The type of the unit, for example `system-tool`. |
| `purpose` | The reason that the repository uses the unit. |
| `check` | A command as a list of words. Exit code 0 means that the unit is ready. |
| `install` | The command that installs the unit. |
| `requires` | What you must have before you install the unit. |

## Add a unit

If a change adds an item that a clean clone must have, add one unit to the registry. Do this in the same change.

Examples of an item are a dependency file, a system tool, and a gate tool.

The repository has no setup doctor script. Claude Code examines the units and installs them with this skill.
