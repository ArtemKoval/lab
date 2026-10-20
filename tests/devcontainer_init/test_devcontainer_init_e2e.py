"""Live checks of the generated configuration. Opt-in through
DEVCONTAINER_INIT_E2E=1 with a running Docker daemon. The default suite
never builds anything."""

import json
import os
import subprocess

import pytest

from devcontainer_init.cli import main

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("DEVCONTAINER_INIT_E2E") != "1",
        reason="opt-in via DEVCONTAINER_INIT_E2E=1",
    ),
]


def _run_devcontainer(args, timeout):
    command = ["npx", "--yes", "@devcontainers/cli", *args]
    return subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )


def _parse_cli_json(text):
    # The CLI prints a one-line banner before the JSON on stdout.
    return json.loads(text[text.index("{"):])


def test_read_configuration_accepts_the_generated_config(tmp_path):
    project = tmp_path / "demo"
    project.mkdir()
    assert main([str(project)]) == 0
    result = _run_devcontainer(
        ["read-configuration", "--workspace-folder", str(project)], timeout=300
    )
    assert result.returncode == 0, result.stderr
    config = _parse_cli_json(result.stdout)["configuration"]
    assert config["image"] == "ubuntu:26.04"
    assert len(config["features"]) == 4


def test_built_container_carries_the_wired_tools(tmp_path):
    project = tmp_path / "demo"
    project.mkdir()
    assert main([str(project)]) == 0
    build = _run_devcontainer(
        ["up", "--remove-existing-container", "--workspace-folder", str(project)],
        timeout=1800,
    )
    assert build.returncode == 0, build.stderr[-4000:]
    exec_args = ["exec", "--workspace-folder", str(project), "--"]
    for tool in ("node", "uv", "git"):
        result = _run_devcontainer([*exec_args, tool, "--version"], timeout=300)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip()
    release = _run_devcontainer([*exec_args, "cat", "/etc/os-release"], timeout=300)
    assert 'VERSION_ID="26.04"' in release.stdout
