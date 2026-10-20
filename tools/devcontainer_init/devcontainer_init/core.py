"""Build the default devcontainer configuration. Pure module, no I/O."""

import json

# The latest long-term-support Ubuntu at the time of writing. Bump this
# constant when a new LTS releases, and update the tests with it.
DEFAULT_UBUNTU_LTS = "26.04"

# Feature references examined against ghcr on 2026-10-20. The majors
# have pins. The version options float, so each build takes the current
# node LTS and the current uv stable release.
COMMON_UTILS_FEATURE = "ghcr.io/devcontainers/features/common-utils:2"
GIT_FEATURE = "ghcr.io/devcontainers/features/git:1"
NODE_FEATURE = "ghcr.io/devcontainers/features/node:2"
UV_FEATURE = "ghcr.io/devcontainers-extra/features/uv:1"


def dedupe(extensions):
    """Return the extensions in first-seen order without duplicates."""
    seen = set()
    ordered = []
    for extension in extensions:
        if extension not in seen:
            seen.add(extension)
            ordered.append(extension)
    return ordered


def build_config(name, os_version=DEFAULT_UBUNTU_LTS, extensions=()):
    """Return the devcontainer configuration as a plain dictionary."""
    return {
        "name": name,
        "image": f"ubuntu:{os_version}",
        "features": {
            COMMON_UTILS_FEATURE: {},
            GIT_FEATURE: {"version": "os-provided"},
            NODE_FEATURE: {"version": "lts"},
            UV_FEATURE: {"version": "latest"},
        },
        "remoteUser": "vscode",
        "customizations": {"vscode": {"extensions": dedupe(extensions)}},
    }


def render(config):
    """Return the configuration as JSON text with a trailing newline."""
    return json.dumps(config, indent=2) + "\n"
