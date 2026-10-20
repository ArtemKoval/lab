"""Pin the generated configuration and the render format."""

import json

from devcontainer_init.core import build_config, render


def test_default_config_matches_the_contract():
    assert build_config("proj") == {
        "name": "proj",
        "image": "ubuntu:26.04",
        "features": {
            "ghcr.io/devcontainers/features/common-utils:2": {},
            "ghcr.io/devcontainers/features/git:1": {"version": "os-provided"},
            "ghcr.io/devcontainers/features/node:2": {"version": "lts"},
            "ghcr.io/devcontainers-extra/features/uv:1": {"version": "latest"},
        },
        "remoteUser": "vscode",
        "customizations": {"vscode": {"extensions": []}},
    }


def test_os_override_replaces_the_image_tag():
    config = build_config("proj", os_version="24.04")
    assert config["image"] == "ubuntu:24.04"


def test_extensions_keep_order_and_drop_duplicates():
    config = build_config("proj", extensions=["a", "b", "a", "c", "b"])
    assert config["customizations"]["vscode"]["extensions"] == ["a", "b", "c"]


def test_render_round_trips_and_ends_with_a_newline():
    config = build_config("proj")
    text = render(config)
    assert text.endswith("\n")
    assert json.loads(text) == config
    assert text.splitlines()[1].startswith("  \"name\"")
