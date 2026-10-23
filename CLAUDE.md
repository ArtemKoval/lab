# A Personal Lab of Art Koval

## Communication Style

Write messages, reports, code comments, commit messages, and documentation in ASD-STE100 Simplified Technical English (STE), Issue 9. Do not use STE rules for code, commands, paths, identifiers, error messages, quoted text, or names. If the user tells you to use a different style for content, use that style. Use approved STE words, technical nouns, and technical verbs, each with one meaning and one part of speech. Write "do" (not "perform"), "use" (not "utilize"), "make sure" (not "ensure"), "give" (not "provide"), and "examine" (not "check"). Use the active voice. Do not use perfect tenses, progressive tenses, phrasal verbs, contractions, or semicolons. Use "-ing" forms only in technical nouns. Write one topic in each sentence. Use a maximum of 20 words in a procedural sentence and 25 words in a descriptive sentence. Do not write multi-word nouns of more than three words. In procedures, write each step as one imperative instruction, with the condition first. The ASD-STE100 output style at .claude/output_styles/asd-ste100.md has the full rules.

## Workflow
- Every repository change goes through the `feature-pipeline` skill; questions that change nothing don't.
- Change discipline: the proposal PR merges to `main` before implementation starts. The implementation PR merges before the archive PR. The `openspec-git-discipline` skill owns the gates. Durable decisions go to `adr/NNNN-kebab-title.md`. An accepted ADR changes only through a superseding ADR.
- VCS: Git on GitHub. Mainline is `main`; review via pull requests (`gh`); squash-merge, then delete the branch.
- Worktrees: when an agent or a team of agents works on a feature branch, it must make its own worktree and work in that worktree. In Claude Code, use the `EnterWorktree` tool. Outside Claude Code, use `git worktree add`.

## Working rules
- Build a tool first. When a task includes computation, data processing, or analysis, write a script that does the work without an LLM. Call the LLM only for the steps where judgment is necessary: plan review, vision, analysis of results, and code writing.
- Keep reusable artifacts under version control. Put logs, metrics, scripts, and reports in the repository at a stable path. Do not put them in `/tmp` or another scratch location. A scratch file is only for output that no one will read again.
- Open a handover issue after you solve a task. When the run produces logs, metrics, or observations that later work can use, open a handover issue. Use the `handover` issue template on GitHub after the merge. Remove secrets before you put artifacts in the issue.

## Specs
- Behavior specs: `openspec/specs/` (source of truth). In-flight changes: `openspec/changes/`. Active schema: `intent-driven` (`openspec/schemas/intent-driven/`).
- Harness surfaces: skills in `.claude/skills/`, agents in `.claude/agents/` (ported from the intent-driven template at `b5bda460a2180a55fc508fdedc4ef058d95355db`). Glossary terms: `glossary/`. Upstream template: `github.com/intent-driven-dev/intent-driven-template`.
- To make an OpenSpec change, run `/opsx:propose`. To build it, run `/opsx:apply`. To archive it, run `/opsx:archive`.

## Setup
- A clean clone must have the units in `tools/project_setup/registry.json`. The `project-setup` skill examines them and installs each unit that the clone does not have.
- If a change adds an item that a clean clone must have, add a unit to the registry.

## Projects
- `llm_ops/eval`: a DeepEval script that uses a local apfel server as the judge. It runs in a devcontainer. The README at `llm_ops/eval/README.md` and the `apfel-eval` skill give the commands.
- `fde`: an Electron chat desktop app for OpenRouter with an embedded Python backend. The README at `fde/README.md` and the `fde-app` skill give the commands.
- `tools/zai_routing_audit`: a stdlib CLI that audits the z.ai GLM model routing behind Claude Code. The README at `tools/zai_routing_audit/README.md` and the `zai-routing-audit` skill give the commands. Its venv interpreter runs the root test suite: `tools/zai_routing_audit/.venv/bin/python -m pytest`.
- `tools/devcontainer_init`: a stdlib CLI that scaffolds a devcontainer with the latest Ubuntu LTS, git, node, and uv configured for VS Code. The README at `tools/devcontainer_init/README.md` and the `devcontainer-init` skill give the commands. Its e2e build check runs only with `DEVCONTAINER_INIT_E2E=1` and a running Docker daemon.
- `notebooks`: standalone teaching notebooks. Tests in `tests/notebooks/` read each notebook as JSON and run its cells against stubs. They use the standard library only. Notebooks that go to a public course repo must pass that repo's checklist: cleared outputs, no secrets, no emojis.
