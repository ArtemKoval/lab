"""The bridge hook: verify the generated artifacts after a spec edit.

A Write or Edit under openspec/changes/<id>/specs/ runs the fast
staleness check for that change. A stale generation injects context
that names the regeneration command; the hook never blocks.
"""

import json
import sys
from pathlib import Path

from .hooksupport import repo_root


def _change_id(path):
    """Return the change id when the path sits in a change specs tree."""
    parts = Path(path).parts
    if "openspec" not in parts:
        return None
    index = parts.index("openspec")
    if (
        len(parts) > index + 3
        and parts[index + 1] == "changes"
        and parts[index + 3] == "specs"
    ):
        return parts[index + 2]
    return None


def context_json(text):
    """The PostToolUse additionalContext payload."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text,
        }
    }


def main(payload=None):
    """Verify the edited change; report staleness as context."""
    try:
        event = json.loads(payload if payload is not None else sys.stdin.read())
        path = str(event["tool_input"]["file_path"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return 0
    change_id = _change_id(path)
    if change_id is None:
        return 0
    from . import cli

    root = repo_root()
    code, report = cli.cmd_verify(str(root), change_id, cli._load_modules(str(root)))
    if code != 0:
        print(
            json.dumps(
                context_json(
                    "GATE: the spec edit made the generated artifacts stale"
                    f" for {change_id} ({report.get('error', 'stale')})."
                    " Run: python -m dspy_gate regen "
                    + change_id
                )
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - shim entry
    sys.exit(main())
