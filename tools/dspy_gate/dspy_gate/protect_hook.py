"""The protect hook: GENERATED paths deny a Write or Edit.

The bridge is the only writer of the generated artifacts. A hand edit
of a GENERATED path gets a deny decision with the regenerate hint. The
visual baselines stay exempt: a human authors them inside the change
pull request that alters the rendered surface.
"""

import fnmatch
import json
import sys

from .hooksupport import repo_root

DENY_PATTERNS = (
    "openspec/eval_manifest.json",
    "openspec/changes/*/evals/*",
    "openspec/specs/*/evals/*",
    "openspec/specs/*/certs.jsonl",
    "tests/dspy_gate/generated/*",
    "tools/dspy_gate/artifacts/*",
)


def deny_json(reason):
    """The PreToolUse deny decision for one blocked write."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def is_generated(path):
    """True when the path sits under a GENERATED artifact area.

    The event carries an absolute path; the patterns are repo-relative,
    so the root prefix comes off first when the path sits inside it.
    """
    root = str(repo_root())
    relative = path[len(root) + 1 :] if path.startswith(root + "/") else path
    return any(fnmatch.fnmatch(relative, pattern) for pattern in DENY_PATTERNS)


def main(payload=None):
    """Read the hook event, deny generated paths, allow the rest."""
    try:
        event = json.loads(payload if payload is not None else sys.stdin.read())
        path = str(event["tool_input"]["file_path"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return 0
    if is_generated(path):
        print(
            json.dumps(
                deny_json(
                    "DENIED: generated artifact - edit the spec and regenerate"
                )
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - shim entry
    sys.exit(main())
