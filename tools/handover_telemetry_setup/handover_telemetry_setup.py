#!/usr/bin/env python3
"""The setup doctor for the cc-logging hook wiring.

Read-only check by default: the shim exists and runs, the six hook
groups sit in project settings, and a python interpreter resolves.
--install wires the missing groups and marks the shim executable, and
never touches the other settings keys. --json carries an ok field.
Exit 0 when ok and 2 when not.
"""

import argparse
import json
import os
import shutil
import stat
from pathlib import Path

SHIM_REL = Path(".claude/hooks/cc-logging.sh")
SETTINGS_REL = Path(".claude/settings.json")
HOOK_COMMAND = "\"$CLAUDE_PROJECT_DIR/.claude/hooks/cc-logging.sh\""
EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "PermissionRequest",
    "SessionStart",
    "SessionEnd",
    "Stop",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    if args.install:
        install(root)
    report = {"ok": False, "repo_root": str(root), "checks": _checks(root)}
    report["ok"] = all(report["checks"].values())
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        for name, ok in report["checks"].items():
            print(f"{'ok' if ok else 'MISSING'}: {name}")
    return 0 if report["ok"] else 2


def _checks(root: Path) -> dict:
    shim = root / SHIM_REL
    settings = root / SETTINGS_REL
    groups = _wired_events(settings)
    return {
        "shim exists and runs": shim.is_file() and os.access(shim, os.X_OK),
        "hook groups wired": set(groups) == set(EVENTS),
        "charter group untouched": _charter_present(settings),
        "interpreter resolves": _interpreter(root) is not None,
    }


def _charter_present(settings: Path) -> bool:
    data = _read_settings(settings)
    if data is None:
        return False
    for group in (data.get("hooks") or {}).get("SessionStart") or []:
        for hook in group.get("hooks") or []:
            if "harness-charter.sh" in (hook.get("command") or ""):
                return True
    return False


def _wired_events(settings: Path) -> list[str]:
    data = _read_settings(settings)
    if data is None:
        return []
    hooks = data.get("hooks") or {}
    return [
        event
        for event in EVENTS
        if any(
            HOOK_COMMAND in (hook.get("command") or "")
            for group in hooks.get(event) or []
            for hook in group.get("hooks") or []
        )
    ]


def _read_settings(settings: Path) -> dict | None:
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _interpreter(root: Path) -> str | None:
    candidate = root / "tools/zai_routing_audit/.venv/bin/python"
    if candidate.is_file():
        return str(candidate)
    return shutil.which("python3")


def install(root: Path) -> None:
    shim = root / SHIM_REL
    if shim.is_file():
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    settings = root / SETTINGS_REL
    data = _read_settings(settings)
    if data is None:
        return
    hooks = data.setdefault("hooks", {})
    wired = set(_wired_events(settings))
    for event in EVENTS:
        if event in wired:
            continue
        entry = {
            "type": "command",
            "command": HOOK_COMMAND,
            "timeout": 10,
            "async": False,
        }
        group = {"hooks": [entry]}
        hooks.setdefault(event, []).append(group)
    settings.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
