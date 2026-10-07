---
name: project-setup
description: Set up or repair a clean clone of this repository. Use when a tool is missing, a command is not found, the user asks to set up the project or the machine, or the feature-pipeline skill needs a gate tool. Reads tools/project_setup/registry.json, checks each unit, and installs the missing units after the user agrees.
---

# Project setup

The file `tools/project_setup/registry.json` lists each item that a clean clone needs. Each item is a unit.

## Check and repair a clone

1. Read `tools/project_setup/registry.json`.
2. Run the `check` command of each unit. The unit passes when the command exits with code 0.
3. Report each unit that fails.
4. Show the `install` command of each failed unit. Ask the user to confirm.
5. After the user confirms, run the `install` command.
6. Run the `check` command again. Report the result.

Do not run an `install` command before the user confirms. Some install commands change the whole machine.

## Unit fields

| Field | Meaning |
|---|---|
| `id` | A unique kebab-case name. |
| `kind` | The type of unit, for example `system-tool`. |
| `purpose` | The reason that the repository needs the unit. |
| `check` | A command as a list of words. Exit code 0 means that the unit is ready. |
| `install` | The command that installs the unit. |
| `requires` | What the unit needs before you install it. |

## Add a unit

When a change adds an item that a clean clone needs, add one unit to the registry in the same change. Examples are a dependency file, a system tool, and a gate tool.

The registry has no setup doctor script yet. Claude Code does the check and the install with this skill.
