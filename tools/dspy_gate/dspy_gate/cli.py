"""The dspy_gate CLI: lint, regen, verify, and check-manifest.

Exit contract: 0 on success, 2 on operational failure. --json switches
the human report for one machine payload with an exit field.
"""

import argparse
import json
import sys
from pathlib import Path

from . import codegen, gatepolicy, lint, manifest

DEFAULT_POLICY = Path("tools") / "dspy_gate" / "gates.yaml"


def find_repo_root(start="."):
    """Walk up to the directory holding openspec/changes."""
    current = Path(start).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "openspec" / "changes").is_dir():
            return candidate
    raise SystemExit("no openspec/changes found above the working directory")


def change_dir(root, change_id):
    """Return the change directory or None."""
    path = Path(root) / "openspec" / "changes" / change_id
    return path if path.is_dir() else None


def load_policy(root):
    """Load the effective policy file."""
    return gatepolicy.load(Path(root) / DEFAULT_POLICY)


def cmd_lint(root, change_id, modules=None):
    """Gate 0: lint one change; return (exit, payload)."""
    directory = change_dir(root, change_id)
    if directory is None:
        return 2, {"error": f"no change named {change_id}"}
    violations = lint.lint_change(directory, load_policy(root), modules)
    return (0 if not violations else 2), {"change": change_id, "violations": violations}


def _regenerated(root, change_id, modules):
    """Build the manifest dict and the generated module bytes."""
    from . import scenarioparse

    parsed = scenarioparse.parse_change(change_dir(root, change_id))
    data = manifest.build(parsed, modules)
    return parsed, data, codegen.generate(data)


def _on_disk(root, change_id):
    """Read back the on-disk manifest and generated module, or None."""
    manifest_path = Path(root) / "openspec" / "eval_manifest.json"
    generated = (
        Path(root) / "tests" / "dspy_gate" / "generated" / "test_spec_conformance.py"
    )
    if not manifest_path.is_file():
        return None
    data = manifest.load(manifest_path)
    content = generated.read_text(encoding="utf-8") if generated.is_file() else None
    return data, content


def cmd_regen(root, change_id, modules):
    """Regenerate the manifest, datasets, and conformance module."""
    from . import datasets

    directory = change_dir(root, change_id)
    if directory is None:
        return 2, {"error": f"no change named {change_id}"}
    parsed, data, content = _regenerated(root, change_id, modules)
    violations = manifest.verify(data, parsed, modules)
    if violations:
        return 2, {"violations": violations}
    manifest.write(data, Path(root) / "openspec" / "eval_manifest.json")
    for case in data["changes"][change_id]["eval_cases"]:
        datasets.write_case(directory, case, modules)
    codegen.write(Path(root) / "tests" / "dspy_gate" / "generated", content)
    return 0, {"regenerated": change_id}


def cmd_verify(root, change_id, modules):
    """Fast staleness check: regeneration must match the bytes on disk."""
    directory = change_dir(root, change_id)
    if directory is None:
        return 2, {"error": f"no change named {change_id}"}
    disk = _on_disk(root, change_id)
    if disk is None:
        return 2, {"error": "stale generated artifacts; run regen"}
    _, data, content = _regenerated(root, change_id, modules)
    disk_data, disk_content = disk
    disk_data = dict(disk_data)
    disk_data.pop("_generated", None)
    data.pop("_generated", None)
    if disk_data != data or disk_content != content:
        return 2, {"error": "stale generated artifacts; run regen"}
    return 0, {"verified": change_id}


def cmd_check_manifest(root, change_id, modules):
    """Gate 1: bidirectional coverage of the on-disk manifest."""
    from . import scenarioparse

    disk = _on_disk(root, change_id)
    if disk is None:
        return 2, {"error": "no eval manifest on disk"}
    parsed = scenarioparse.parse_change(change_dir(root, change_id))
    violations = manifest.verify(disk[0], parsed, modules)
    return (0 if not violations else 2), {"violations": violations}


def cmd_status(root, change_id, modules):
    """Gate state, computed live from the on-disk artifacts."""
    directory = change_dir(root, change_id)
    if directory is None:
        return 2, {"error": f"no change named {change_id}"}
    violations = lint.lint_change(directory, load_policy(root), modules)
    disk = _on_disk(root, change_id)
    if disk is None:
        gates = {"gate_0": "green", "gate_1": "red", "generated": "red"}
        return 2, {"gates": gates, "rows": []}
    disk_data, _ = disk
    regenerated = _regenerated(root, change_id, modules)
    parsed, fresh_data = regenerated[0], regenerated[1]
    disk_data = dict(disk_data)
    disk_data.pop("_generated", None)
    fresh_data.pop("_generated", None)
    rows = _status_rows(disk_data, change_id, modules)
    gates = {
        "gate_0": "green" if not violations else "red",
        "gate_1": "green" if not manifest.verify(disk_data, parsed, modules) else "red",
        "generated": "green" if disk_data == fresh_data else "red",
    }
    code = 0 if all(state == "green" for state in gates.values()) else 2
    return code, {"change": change_id, "gates": gates, "rows": rows}


def _status_rows(disk_data, change_id, modules):
    """One matrix row per dspy-eval case in the on-disk manifest."""
    from . import evals, harness

    rows = []
    for case in disk_data.get("changes", {}).get(change_id, {}).get("eval_cases", []):
        if case.get("surface") != "dspy-eval":
            continue
        try:
            pred, trace = harness.run(case, modules)
            tier_a = all(
                entry["tier"] != "A" for entry in case.get("checks", [])
            ) or _tier_a_green(case, pred, trace)
            rows.append(
                {
                    "scenario_id": case["scenario_id"],
                    "green": tier_a,
                    "deferred": any(entry["tier"] == "B" for entry in case["checks"]),
                    "detail": "",
                    "route": "",
                    "tiers": {"A": tier_a},
                }
            )
        except Exception as exc:  # noqa: BLE001 - a row reports, not crashes
            rows.append(
                {
                    "scenario_id": case["scenario_id"],
                    "green": False,
                    "deferred": False,
                    "detail": f"environment error: {exc}",
                    "route": evals.ROUTE_ENVIRONMENT,
                    "tiers": {},
                }
            )
    return rows


def _tier_a_green(case, pred, trace):
    from . import checks

    assertions = [entry for entry in case.get("checks", []) if entry["tier"] == "A"]
    return checks.run_tier_a(assertions, pred, trace).passed


def _budgets(root):
    """The per-capability budget map from the effective policy."""
    return load_policy(root).get("capabilities", {})


def cmd_evals(root, change_id, modules):
    """Gate 3: run the delta suite and print the failure routes."""
    from . import evals, harness

    disk = _on_disk(root, change_id)
    if disk is None:
        return 2, {"error": "no eval manifest on disk"}
    cases = [
        case
        for case in disk[0]["changes"][change_id]["eval_cases"]
        if case.get("surface") == "dspy-eval"
    ]
    budgets = _budgets(root)

    def run_fn(case):
        return harness.run(_case_with_frozen_inputs(case), modules)

    def _case_with_frozen_inputs(case):
        from . import datasets
        from pathlib import Path

        source = Path(root) / "openspec" / "changes" / change_id / case["dataset_path"]
        if source.is_file():
            return {**case, "inputs": datasets.read_case(source)["inputs"]}
        return case

    def run_one(case):
        budget = (budgets.get(case["capability"], {}) or {}).get("budget", {})
        return evals.run_delta([case], budget, run_fn=run_fn).rows[0]

    rows = [run_one(case) for case in cases]
    report = evals.Report(0 if all(r["green"] for r in rows) else 2, rows)
    return report.exit, {"report": report}


def cmd_matrix(root, change_id, modules):
    """The conformance matrix for the pull request body."""
    code, payload = cmd_evals(root, change_id, modules)
    from . import matrix as matrix_mod

    return code, {"matrix": matrix_mod.render(payload["report"])}


def cmd_freeze(root, change_id, modules):
    """Gate 4: freeze the eval cases and thresholds at archive."""
    from . import freeze

    report = freeze.run(root, change_id)
    return 0, {"frozen": report}


def cmd_nightly(root, change_id, modules, from_report=None):
    """The seven-step learning loop over one run's failure rows."""
    from . import harness, manifest as manifest_mod, nightly

    if from_report is None:
        return 2, {"error": "nightly needs --from-report"}
    rows = json.loads(Path(from_report).read_text(encoding="utf-8"))["rows"]
    manifest_data = manifest_mod.load(Path(root) / "openspec" / "eval_manifest.json")
    drafts_root = Path(root) / "openspec" / "drafts"
    report = nightly.run(
        rows,
        manifest_data,
        drafts_root,
        _optimizer_fn(),
        lambda case: harness.run(case, modules),
        _budgets(root),
        _holdout_ratios(root),
    )
    return 0, {"steps": report["steps"]}


def _optimizer_fn():
    """The optimizer for the nightly loop.

    A hand module optimizes by identity: the behavior is code, and the
    gates still certify it. An optimized module swaps in the GEPA run
    behind the live extra; no governed module is optimized today.
    """
    return lambda program, train, val: program


def _holdout_ratios(root):
    capabilities = _budgets(root)
    return {
        name: block.get("holdout_ratio", 0.3)
        for name, block in capabilities.items()
    }


def build_parser():
    """Build the argparse parser."""
    parser = argparse.ArgumentParser(prog="dspy_gate", description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--json", action="store_true", help="machine output")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lint", "regen", "verify", "check-manifest", "status", "evals",
                 "matrix", "freeze"):
        child = sub.add_parser(name)
        child.add_argument("change_id")
    nightly = sub.add_parser("nightly")
    nightly.add_argument("change_id")
    nightly.add_argument("--from-report", required=True)
    return parser


def main(argv=None):
    """Run one command; print the report; return the exit code."""
    try:
        args = build_parser().parse_args(argv)
    except SystemExit:
        return 2
    try:
        root = find_repo_root(args.repo_root)
    except SystemExit as exc:
        print(exc)
        return 2
    modules = _load_modules(root)
    handlers = {
        "lint": cmd_lint,
        "regen": cmd_regen,
        "verify": cmd_verify,
        "check-manifest": cmd_check_manifest,
        "status": cmd_status,
        "evals": cmd_evals,
        "matrix": cmd_matrix,
        "freeze": cmd_freeze,
    }
    try:
        if args.command == "nightly":
            code, payload = cmd_nightly(
                root, args.change_id, modules, from_report=args.from_report
            )
        else:
            code, payload = handlers[args.command](root, args.change_id, modules)
    except Exception as exc:  # noqa: BLE001 - the CLI reports, not crashes
        code, payload = 2, {"error": str(exc)}
    if args.json:
        print(json.dumps(_jsonable({"exit": code, **payload}), sort_keys=True))
    else:
        for key, value in payload.items():
            printed = _printable(key, value)
            if printed is not None:
                print(printed)
    return code


def _jsonable(payload):
    """Make the payload JSON-safe: reports become their row lists."""
    report = payload.get("report")
    if report is not None:
        payload = dict(payload)
        payload["report"] = {"exit": report.exit, "rows": report.rows}
    return payload


def _printable(key, value):
    """One human line per payload entry; reports render as a matrix."""
    from . import matrix as matrix_mod

    if hasattr(value, "rows"):
        return matrix_mod.render(value)
    if isinstance(value, list):
        return "\n".join(f"{key}: {item}" for item in value) or None
    return f"{key}: {value}"


def _load_modules(root):
    """Load the harness registry when the package layout allows it."""
    try:
        from .harness import registry
    except ImportError:
        return {}
    del root
    return registry.modules()


if __name__ == "__main__":  # pragma: no cover - python -m entry
    sys.exit(main())
