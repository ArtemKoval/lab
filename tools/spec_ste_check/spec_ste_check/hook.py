"""PreToolUse hook glue for the STE gate.

The module receives the hook event JSON on stdin, filters to the gate
paths, rebuilds the text after the edit, and runs the shared rules over
it. Exit 2 blocks the write. Every unexpected condition fails open with
exit 0 and a note on stderr, because the pytest gate stays the backstop.
The bash wrapper in `.claude/hooks/` only resolves the root and the
interpreter; no rule lives there.
"""

import json
import os
import sys

from . import rules

EDIT_TOOLS = ("Write", "Edit", "MultiEdit")


def in_gate_scope(rel_path):
    """Tell a gate path from everything else.

    In scope: `openspec/specs/**` and the active directories under
    `openspec/changes/**`. Out of scope: `openspec/changes/archive/**`.
    """
    parts = rel_path.split("/")
    if len(parts) < 3 or parts[0] != "openspec":
        return False
    if parts[1] == "specs":
        return True
    return parts[1] == "changes" and parts[2] != "archive"


def _post_edit_text(event, root):
    """Rebuild the text the tool is about to leave behind, or None when
    the write cannot carry a spec-text change."""
    tool_input = event.get("tool_input") or {}
    tool = event.get("tool_name")
    target = tool_input.get("file_path")
    if not target:
        return None
    path = os.path.join(root, target) if not os.path.isabs(target) else target
    if tool == "Write":
        return tool_input.get("content")
    if tool in ("Edit", "MultiEdit"):
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except OSError:
            return None
        edits = tool_input.get("edits") if tool == "MultiEdit" else [tool_input]
        for edit in edits:
            old = edit.get("old_string", "")
            new = edit.get("new_string", "")
            if old not in text:
                return None
            if edit.get("replace_all"):
                text = text.replace(old, new)
            else:
                text = text.replace(old, new, 1)
        return text
    return None


def evaluate(event, root):
    """Score one hook event. Returns the hook exit code: 0 passes the
    write, 2 blocks it. Any failure fails open with 0."""
    try:
        tool = event.get("tool_name")
        if tool not in EDIT_TOOLS:
            return 0
        target = (event.get("tool_input") or {}).get("file_path")
        if not target:
            return 0
        rel = os.path.relpath(os.path.abspath(target), os.path.abspath(root))
        rel = rel.replace(os.sep, "/")
        if rel.startswith("..") or not in_gate_scope(rel):
            return 0
        text = _post_edit_text(event, root)
        if text is None:
            return 0
        violations = rules.check_text(text, rel)
        errors = [v for v in violations if v["severity"] == "error"]
        warnings = [v for v in violations if v["severity"] == "warning"]
        for violation in errors:
            print(
                f"SPEC-STE blocked {violation['file']}:{violation['line']}"
                f": {violation['rule']}: {violation['text'][:120]}",
                file=sys.stderr,
            )
        for warning in warnings:
            print(
                f"SPEC-STE note {warning['file']}:{warning['line']}"
                f": {warning['rule']}",
                file=sys.stderr,
            )
        if errors:
            print(
                "SPEC-STE: fix the listed sentences, then write again. "
                "Run the checker for the full report.",
                file=sys.stderr,
            )
            return 2
        return 0
    except Exception as error:  # noqa: BLE001 - the hook must fail open
        print(f"spec-ste-gate: checker fails open: {error}", file=sys.stderr)
        return 0


def main():
    try:
        event = json.loads(sys.stdin.read())
    except ValueError as error:
        print(f"spec-ste-gate: unreadable event, fails open: {error}", file=sys.stderr)
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return evaluate(event, root)


if __name__ == "__main__":
    raise SystemExit(main())
