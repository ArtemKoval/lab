"""The chaos_ssh command line interface.

Five subcommands serve the tutor flow: list, start, hint, reveal,
and stop. The house contract holds: argparse, --json for machine
output, exit 0 on success, and exit 2 on an operational failure with
one named next action in the message.
"""

import argparse
import json
import sys
from pathlib import Path

from chaos_ssh import env
from chaos_ssh.catalog import CatalogError, index, load_catalog
from chaos_ssh.scratch import Scratch

# absolute(), not resolve(): the mutator overlay must keep the
# derived area root inside the copy under test.
AREA_ROOT = Path(__file__).absolute().parents[2]

HOST_PORTS = (2222, 2223)

SETUP_KEY_SCRIPT = "environments/inject/_setup/install-practice-key.sh"


def main(argv=None) -> int:
    """Run one tutor command and return the process exit code."""
    parser = build_parser()
    options = parser.parse_args(argv)
    try:
        scenarios = load_catalog(AREA_ROOT / "catalog")
    except CatalogError as error:
        return _fail(f"{error} Repair the catalog before the run.")
    table = index(scenarios)
    handler = {
        "list": _cmd_list,
        "start": _cmd_start,
        "hint": _cmd_hint,
        "reveal": _cmd_reveal,
        "stop": _cmd_stop,
    }[options.command]
    try:
        return handler(options, scenarios, table)
    except env.EnvError as error:
        return _fail(f"{error} Next action: {error.remediation}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser of the tutor."""
    parser = argparse.ArgumentParser(
        prog="chaos_ssh",
        description="The ssh chaos tutor: arm one failure scenario, "
        "think, take hints, and reveal the fault.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable output",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="print the catalog rows")
    start = subparsers.add_parser("start", help="arm one scenario")
    start.add_argument("scenario_id")
    hint = subparsers.add_parser("hint", help="print the next hint")
    hint.add_argument("scenario_id")
    reveal = subparsers.add_parser("reveal", help="reveal the fault")
    reveal.add_argument("scenario_id")
    stop = subparsers.add_parser("stop", help="stop the scenario")
    stop.add_argument("scenario_id")
    return parser


def _cmd_list(options, scenarios, table) -> int:
    if options.json:
        rows = [
            {"id": s.id, "phase": s.phase, "title": s.title}
            for s in scenarios
        ]
        print(json.dumps(rows, indent=2))
        return 0
    for scenario in scenarios:
        print(f"{scenario.id}\t{scenario.phase}\t{scenario.title}")
    return 0


def _cmd_start(options, scenarios, table) -> int:
    scenario = _require(options.scenario_id, table)
    env.rm_container(AREA_ROOT)
    held = [str(port) for port in HOST_PORTS if not env.port_status(port)]
    if held:
        return _fail(
            f"a pinned host port ({', '.join(held)}) is in use by "
            "another process. Next action: examine the process that "
            "holds the port, or change the port override in "
            ".devcontainer/devcontainer.json."
        )
    env.up(AREA_ROOT)
    if not env.wait_ready(scenario.connection["port"]):
        return _fail(
            "the container did not answer on the forwarded port. "
            "Next action: run the devcontainer up command by hand, "
            "and examine the container logs."
        )
    scratch = Scratch(AREA_ROOT, scenario.id)
    scratch.ensure()
    scratch.generate_key()
    scratch.write_config(
        target=scenario.connection["target"],
        port=scenario.connection["port"],
        user=scenario.connection["user"],
        identity=scenario.connection["identity"],
        hostkeyalias=scenario.connection["hostkeyalias"],
    )
    _install_key(scratch)
    scratch.seed_known_hosts(scenario.connection["port"],
                             scenario.connection["hostkeyalias"])
    if scenario.connection["hostkeyalias"]:
        scratch.seed_known_hosts(2223, scenario.connection["hostkeyalias"])
    if scenario.inject:
        env.exec_in(AREA_ROOT, _container_script(scenario.inject))
    scratch.apply_arm(scenario.connection["arm"])
    if scenario.connection["agent"]:
        scratch.agent_start()
    scratch.reset_position()
    command = scenario.command.format(
        scratch=str(scratch.root), target=scenario.connection["target"]
    )
    if scenario.connection["agent"]:
        command = f"SSH_AUTH_SOCK={scratch.agent_sock} {command}"
    notice = [
        f"Armed {scenario.id}: {scenario.title}.",
        f"Fault class: {scenario.fault}",
        "Connection command:",
        command,
        "Think about it:",
        scenario.prompts[0],
    ]
    if options.json:
        print(
            json.dumps(
                {
                    "id": scenario.id,
                    "armed": True,
                    "command": command,
                    "prompt": scenario.prompts[0],
                    "signature": scenario.signature,
                },
                indent=2,
            )
        )
    else:
        print("\n".join(notice))
    return 0


def _cmd_hint(options, scenarios, table) -> int:
    scenario = _require(options.scenario_id, table)
    scratch = Scratch(AREA_ROOT, scenario.id)
    hint = scratch.next_hint(scenario.hints)
    if options.json:
        print(json.dumps({"id": scenario.id, "hint": hint}, indent=2))
    else:
        print(hint)
    return 0


def _cmd_reveal(options, scenarios, table) -> int:
    scenario = _require(options.scenario_id, table)
    if options.json:
        print(
            json.dumps(
                {
                    "id": scenario.id,
                    "wrong": scenario.reveal_wrong,
                    "signature": scenario.signature,
                    "fix": scenario.reveal_fix,
                },
                indent=2,
            )
        )
    else:
        print(
            "\n".join(
                [
                    f"What is wrong: {scenario.reveal_wrong}",
                    f"What the client sees: {scenario.signature}",
                    f"The fix: {scenario.reveal_fix}",
                ]
            )
        )
    return 0


def _cmd_stop(options, scenarios, table) -> int:
    scenario = _require(options.scenario_id, table)
    scratch = Scratch(AREA_ROOT, scenario.id)
    scratch.agent_stop()
    removed = env.rm_container(AREA_ROOT)
    scratch.cleanup()
    if options.json:
        print(
            json.dumps({"id": scenario.id, "removed": removed}, indent=2)
        )
    elif removed:
        print(f"Stopped {scenario.id}: container removed, scratch state deleted.")
    else:
        print(f"no container runs for {scenario.id}")
    return 0


def _require(scenario_id: str, table: dict):
    """Return the scenario, or exit 2 with the valid ids."""
    scenario = table.get(scenario_id)
    if scenario is None:
        valid = ", ".join(sorted(table))
        _fail(
            f"unknown scenario id {scenario_id}. The valid ids are: "
            f"{valid}."
        )
    return scenario


def _install_key(scratch: Scratch) -> None:
    """Install the practice public key into the container account."""
    public_key = scratch.key.with_suffix(".pub")
    key_text = public_key.read_text(encoding="utf-8").strip()
    env.exec_in(
        AREA_ROOT, _container_script(SETUP_KEY_SCRIPT), args=(key_text,)
    )


def _container_script(inject_path: str) -> str:
    """Map the catalog inject path to its container path."""
    prefix = "environments/inject/"
    if not inject_path.startswith(prefix):
        raise env.EnvError(
            f"the inject path {inject_path} sits outside the inject "
            "directory",
            "examine the catalog file, and keep the inject paths "
            "under environments/inject/",
        )
    return "/opt/chaos/inject/" + inject_path[len(prefix):]


def _fail(message: str) -> None:
    """Print one operational failure message to stderr and exit 2."""
    print(message, file=sys.stderr)
    raise SystemExit(2)
