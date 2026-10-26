"""The plan_exec CLI: exit 0 on success, 2 on operational failure."""
import argparse
import json
import sys
from pathlib import Path

from plan_exec import brief as brief_mod
from plan_exec import ledger as ledger_mod
from plan_exec import package as package_mod


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="plan_exec",
        allow_abbrev=False,
        description=(
            "Task briefs, review packages, and execution ledgers for plan runs."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable output"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_brief = sub.add_parser(
        "brief", allow_abbrev=False, help="extract one task as a brief"
    )
    p_brief.add_argument("--plan", required=True, type=Path)
    p_brief.add_argument("--task", required=True)
    p_brief.add_argument("--out", required=True, type=Path)

    p_pkg = sub.add_parser(
        "package", allow_abbrev=False, help="package a commit range for review"
    )
    p_pkg.add_argument("--repo", required=True, type=Path)
    p_pkg.add_argument("--base", required=True)
    p_pkg.add_argument("--head", default="HEAD")
    p_pkg.add_argument("--out", required=True, type=Path)

    p_led = sub.add_parser(
        "ledger", allow_abbrev=False, help="append-only execution ledger"
    )
    p_led.add_argument("--plan", required=True, type=Path)
    p_led.add_argument("--dir", dest="out_dir", default=None, type=Path)
    p_led.add_argument("action", choices=["init", "complete", "task-rule", "show"])
    p_led.add_argument("--task", dest="task_id")
    p_led.add_argument("--tests")
    p_led.add_argument("--result")
    p_led.add_argument("--what")
    p_led.add_argument("--why")
    p_led.add_argument("--cost")
    return parser


def _emit(args, payload):
    if args.json:
        print(json.dumps({"ok": True, **payload}))
    else:
        for value in payload.values():
            print(value)


def _run_brief(args):
    target = brief_mod.write_brief(args.plan, args.task, args.out)
    _emit(args, {"path": str(target)})
    return 0


def _run_package(args):
    target = package_mod.write_package(args.repo, args.base, args.head, args.out)
    _emit(args, {"path": str(target)})
    return 0


def _run_ledger(args):
    if args.action == "init":
        path = ledger_mod.init(args.plan, args.out_dir)
        _emit(args, {"path": str(path)})
    elif args.action == "complete":
        if not args.task_id or not args.tests or not args.result:
            raise ledger_mod.LedgerError(
                "complete needs --task, --tests, and --result"
            )
        path = ledger_mod.complete(
            args.plan, args.out_dir, args.task_id, args.tests, args.result
        )
        _emit(args, {"path": str(path)})
    elif args.action == "task-rule":
        if not args.task_id or not (args.what and args.why and args.cost):
            raise ledger_mod.LedgerError(
                "task-rule needs --task, --what, --why, and --cost"
            )
        path = ledger_mod.task_rule(
            args.plan, args.out_dir, args.task_id, args.what, args.why, args.cost
        )
        _emit(args, {"path": str(path)})
    else:
        lines = ledger_mod.show(args.plan, args.out_dir)
        if args.json:
            print(json.dumps({"ok": True, "lines": lines}))
        else:
            print("\n".join(lines))
    return 0


def main(argv=None):
    args = _build_parser().parse_args(argv)
    handlers = {"brief": _run_brief, "package": _run_package, "ledger": _run_ledger}
    try:
        return handlers[args.command](args)
    except (
        brief_mod.TaskNotFound,
        package_mod.PackageError,
        ledger_mod.LedgerError,
    ) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2
