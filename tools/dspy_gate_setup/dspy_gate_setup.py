#!/usr/bin/env python3
"""The setup doctor for the dspy-gate tool.

Read-only check by default: the stdlib core imports, the effective
gates.yaml parses with policy bounds, the harness registry loads, the
hooks sit in project settings, and the shims run. --install marks the
shims executable and builds the tool venv with the run extras. --json
carries an ok field. Exit 0 when ok and 2 when not.
"""

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SHIMS = [
    Path(".claude/hooks/spec-gates-protect.sh"),
    Path(".claude/hooks/spec-gates-bridge.sh"),
]
POLICY_REL = Path("tools/dspy_gate/gates.yaml")
SETTINGS_REL = Path(".claude/settings.json")
TOOL_DIR = Path("tools/dspy_gate")


def main(argv=None):
    """Run the doctor; print the report; return 0 or 2."""
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


def install(root):
    """Mark the shims executable; build the tool venv when missing."""
    for shim in SHIMS:
        path = root / shim
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    venv = root / TOOL_DIR / ".venv"
    if not (venv / "bin" / "python").exists():
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv)], check=False
        )
        pip = venv / "bin" / "pip"
        if pip.exists():
            subprocess.run(
                [str(pip), "install", "-r", str(root / TOOL_DIR / "requirements.txt")],
                check=False,
            )


def _checks(root):
    return {
        "stdlib core imports": _core_imports(root),
        "gates.yaml parses with bounds": _policy_ok(root),
        "harness registry loads": _registry_ok(root),
        "shims exist and run": all(_shim_ok(root, shim) for shim in SHIMS),
        "hook groups wired": _hooks_wired(root),
    }


def _core_imports(root):
    tool_dir = root / TOOL_DIR
    if not tool_dir.is_dir():
        return False
    probe = (
        f"import sys; sys.path.insert(0, r'{tool_dir}'); "
        + "import dspy_gate.cli, dspy_gate.lint, dspy_gate.manifest"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], check=False, capture_output=True, text=True
    )
    return result.returncode == 0


def _policy_ok(root):
    policy = root / POLICY_REL
    if not policy.is_file():
        return False
    probe = (
        f"import sys; sys.path.insert(0, r'{root / TOOL_DIR}'); "
        + "from dspy_gate import gatepolicy; "
        + f"p = gatepolicy.load(r'{policy}'); "
        + "assert gatepolicy.roles(p); assert gatepolicy.bounds(p)"
    )
    return subprocess.run(
        [sys.executable, "-c", probe], check=False, capture_output=True
    ).returncode == 0


def _registry_ok(root):
    probe = (
        "import sys; sys.path.insert(0, r'%s'); "
        "from dspy_gate.harness import registry; assert registry.modules()"
        % (root / TOOL_DIR)
    )
    return subprocess.run(
        [sys.executable, "-c", probe], check=False, capture_output=True
    ).returncode == 0


def _shim_ok(root, shim):
    path = root / shim
    return path.is_file() and os.access(path, os.X_OK)


def _hooks_wired(root):
    settings = root / SETTINGS_REL
    if not settings.is_file():
        return False
    try:
        hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
    except json.JSONDecodeError:
        return False
    pre = json.dumps(hooks.get("PreToolUse", []))
    post = json.dumps(hooks.get("PostToolUse", []))
    return "spec-gates-protect.sh" in pre and "spec-gates-bridge.sh" in post


if __name__ == "__main__":  # pragma: no cover - entry guard
    sys.exit(main())
