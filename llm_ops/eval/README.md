# eval

This folder is the `eval` project of `llm_ops`. The project has no code yet. Put the Python packages in `requirements.txt`.

## Run in a devcontainer

The devcontainer uses Python 3.12 on Debian Trixie. After Docker creates the container, the devcontainer tool runs `pip install -r requirements.txt` in the container. You do not make a virtual environment in the container.

Before you start, make sure that you have these items:

- Docker Desktop or Docker Engine. The Docker daemon must run.
- For the command line: Node.js 20 or newer.
- For VS Code: the Dev Containers extension.

### With VS Code

1. Open the `llm_ops/eval` folder in VS Code.
2. Run the command `Dev Containers: Reopen in Container`.
3. Wait for the container to start.
4. Open a terminal in VS Code. The terminal runs in the container.

To make the container again, run the command `Dev Containers: Rebuild Container`.

### With the command line

1. Open a terminal in the `llm_ops/eval` folder.
2. Run `npx @devcontainers/cli up --workspace-folder .`
3. Run `npx @devcontainers/cli exec --workspace-folder . bash`

The `up` command is slow the first time, because Docker pulls the image.

When the container starts, the `up` command shows `"outcome":"success"`.

To leave the shell, run `exit`.

To run one command in the container, put the command after `--workspace-folder .`:

```bash
npx @devcontainers/cli exec --workspace-folder . python --version
```

The container uses the files in the folder on your computer. You do not copy files into the container. The CLI mounts the whole repository in `/workspaces/<name>`. The `<name>` is the name of the repository folder on your computer.

The shell starts in the `llm_ops/eval` folder of the repository. The shell user is `vscode`.

To delete the container on macOS or Linux, run this command in a Bash terminal in the `llm_ops/eval` folder:

```bash
docker rm -f $(docker ps -aq --filter "label=devcontainer.local_folder=$(pwd -P)")
```

If no container matches the folder, Docker shows an error that has the text `requires at least 1 argument`.

The delete command for Windows is TBD.

### Add a package

1. Add the package to `requirements.txt`.
2. Run `pip install -r requirements.txt` in the container.

To run the command from a terminal on your computer, use this command:

```bash
npx @devcontainers/cli exec --workspace-folder . pip install -r requirements.txt
```

A new container installs the packages from `requirements.txt` automatically. Pip shows the notice `Defaulting to user installation`. This notice is normal, because the system folder of Python belongs to `root`.

### If a package fails to install

The first `up` command shows the pip error and returns exit code 1. A second `up` command shows `"outcome":"success"`, but it does not install the packages. Do these steps:

1. Correct `requirements.txt`.
2. Run `npx @devcontainers/cli up --workspace-folder . --remove-existing-container`

### Change the devcontainer

If you change `.devcontainer/devcontainer.json`, make the container again:

```bash
npx @devcontainers/cli up --workspace-folder . --remove-existing-container
```

## Run without a devcontainer

On some computers, the command `python` does not exist. On these computers, use `python3`.

1. Make a virtual environment: `python -m venv .venv`
2. Activate the virtual environment:
   - On Windows (Git Bash), run `source .venv/Scripts/activate`.
   - On macOS and Linux, run `source .venv/bin/activate`.
3. Run `pip install -r requirements.txt`
