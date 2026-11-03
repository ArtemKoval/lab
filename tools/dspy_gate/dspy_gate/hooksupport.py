"""Shared helpers for the two spec-gates hook modules."""

import os
from pathlib import Path


def repo_root():
    """The repository root: CLAUDE_PROJECT_DIR, else the package parent."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and (Path(env) / "tools" / "dspy_gate").is_dir():
        return Path(env)
    return Path(__file__).resolve().parents[3]
