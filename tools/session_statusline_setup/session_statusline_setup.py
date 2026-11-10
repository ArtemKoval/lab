"""Setup doctor for the session status line wiring.

The check examines three things: the tool file, the shared venv
interpreter, and the statusLine block in the project settings. The
block command must carry this checkout's absolute paths, so a doctor
run on another checkout repairs the path.

Read-only by default. --install writes or repairs the block. --json
prints a report with an ok field. Exit 0 wired and 2 broken.

Usage:
    python3 session_statusline_setup.py --repo-root . [--install] [--json]
"""

import argparse
import json
import sys
from pathlib import Path


def expected_command(root):
    """Return the status line command for this checkout."""
    venv = root / "tools" / "zai_routing_audit" / ".venv" / "bin" / "python"
    tool = root / "tools" / "session_statusline" / "session_statusline.py"
    return f"{venv} {tool}"


def examine(root):
    """Return (problems, status) for the wiring at this checkout."""
    problems = []
    status = {"tool": "present", "venv": "present", "settings": "wired"}
    if not (root / "tools" / "session_statusline" / "session_statusline.py").is_file():
        problems.append("the tool file is missing at tools/session_statusline/")
        status["tool"] = "missing"
    venv_path = root / "tools" / "zai_routing_audit" / ".venv" / "bin" / "python"
    if not venv_path.is_file():
        problems.append(
            "the shared venv interpreter is missing. Install the "
            "zai-routing-audit-python-deps unit first."
        )
        status["venv"] = "missing"
    command = expected_command(root)
    settings_path = root / ".claude" / "settings.json"
    current = None
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        block = data.get("statusLine")
        if isinstance(block, dict):
            current = block.get("command")
    except (OSError, ValueError):
        problems.append(
            "the project settings are unreadable. Examine "
            ".claude/settings.json by hand."
        )
        status["settings"] = "unreadable"
    if current is None and status["settings"] == "wired":
        problems.append(
            "the statusLine block is missing. Run with --install."
        )
        status["settings"] = "absent"
    elif current not in (None, command) and status["settings"] == "wired":
        problems.append(
            "the statusLine command points elsewhere. Run with --install "
            "to repair it for this checkout."
        )
        status["settings"] = "foreign"
    return problems, status


def install(root):
    """Write or repair the statusLine block for this checkout."""
    settings_path = root / ".claude" / "settings.json"
    data = {}
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    data["statusLine"] = {
        "type": "command",
        "command": expected_command(root),
        "padding": 0,
        "refreshInterval": 15,
    }
    settings_path.write_text(
        json.dumps(data, indent=4) + "\n", encoding="utf-8"
    )


def main(argv=None):
    """Run the doctor. Exit 0 wired and 2 broken."""
    parser = argparse.ArgumentParser(
        prog="session_statusline_setup",
        description="Examine and repair the session status line wiring.",
    )
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--install", action="store_true", help="write the block")
    parser.add_argument("--json", action="store_true", help="machine output")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    problems, status = examine(root)
    if args.install and (root / "tools" / "session_statusline").is_dir():
        install(root)
        problems, status = examine(root)
    report = {"ok": not problems, "problems": problems, "status": status}
    if args.json:
        print(json.dumps(report))
    else:
        for problem in problems:
            print(problem, file=sys.stderr)
        verdict = "ok" if report["ok"] else "broken"
        print(f"session-statusline wiring: {verdict}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
