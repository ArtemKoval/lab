"""Command-line entry for the devcontainer scaffold tool."""

import argparse
import json
import sys
from pathlib import Path

from .core import DEFAULT_UBUNTU_LTS, build_config, render

CONFIG_RELATIVE_PATH = Path(".devcontainer") / "devcontainer.json"


def build_parser():
    """Return the argument parser. The tests pin the surface."""
    parser = argparse.ArgumentParser(
        prog="devcontainer-init",
        description=(
            "Scaffold a devcontainer.json with Ubuntu LTS, git, node, "
            "and uv wired up for VS Code."
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="project directory that receives the .devcontainer directory",
    )
    parser.add_argument(
        "--os",
        dest="os_version",
        default=DEFAULT_UBUNTU_LTS,
        help="Ubuntu version for the base image",
    )
    parser.add_argument(
        "--extension",
        action="append",
        default=[],
        dest="extensions",
        metavar="ID",
        help="VS Code extension to add to the config; repeatable",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing devcontainer.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="print machine-readable JSON output",
    )
    return parser


def scaffold(target, os_version, extensions, force):
    """Write the config into the target. Return (path, None) or (None, error)."""
    target_path = Path(target)
    if not target_path.is_dir():
        return None, f"target directory does not exist: {target}"
    config_path = target_path / CONFIG_RELATIVE_PATH
    if config_path.exists() and not force:
        return None, f"refusing to overwrite an existing config without --force: {config_path}"
    config = build_config(target_path.resolve().name, os_version, extensions)
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(render(config), encoding="utf-8")
    return config_path, None


def main(argv=None):
    """Run one scaffold command. Return the process exit code."""
    args = build_parser().parse_args(argv)
    written, error = scaffold(args.target, args.os_version, args.extensions, args.force)
    if written is not None:
        if args.as_json:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "written": str(written),
                        "os": args.os_version,
                        "extensions": args.extensions,
                    }
                )
            )
        else:
            print(f"wrote {written}")
        return 0
    if args.as_json:
        print(json.dumps({"ok": False, "error": error}))
    else:
        print(f"error: {error}", file=sys.stderr)
    return 2
