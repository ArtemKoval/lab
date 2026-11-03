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
    from . import surface

    violations = manifest.verify(disk[0], parsed, modules)
    violations.extend(surface.baseline_violations(disk[0], root))
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
    disk_data, disk_content = disk
    regenerated = _regenerated(root, change_id, modules)
    parsed, fresh_data, fresh_content = regenerated
    disk_data = dict(disk_data)
    disk_data.pop("_generated", None)
    fresh_data.pop("_generated", None)
    rows = _status_rows(disk_data, change_id, modules)
    gates = {
        "gate_0": "green" if not violations else "red",
        "gate_1": "green" if not manifest.verify(disk_data, parsed, modules) else "red",
        "generated": (
            "green"
            if disk_data == fresh_data and disk_content == fresh_content
            else "red"
        ),
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


def cmd_evals(root, change_id, modules, out=None):
    """Gate 3: run the delta suite and print the failure routes."""
    from . import evals

    disk = _on_disk(root, change_id)
    if disk is None:
        return 2, {"error": "no eval manifest on disk"}
    cases = [
        case
        for case in disk[0]["changes"][change_id]["eval_cases"]
        if case.get("surface") == "dspy-eval"
    ]
    budgets = _budgets(root)
    run_fn = _suite_run_fn(root, change_id, modules)
    rows = [_delta_row(case, budget_of(budgets, case), run_fn) for case in cases]
    report = evals.Report(0 if all(r["green"] for r in rows) else 2, rows)
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(stable_report(report), encoding="utf-8")
    return report.exit, {"report": report}


def stable_report(report):
    """The deterministic report JSON one --out file carries."""
    from .manifest import stable_json

    return stable_json({"exit": report.exit, "rows": report.rows})


def _suite_run_fn(root, change_id, modules):
    """The suite runner: the harness on the dataset's frozen inputs."""
    from . import datasets, harness

    def run_fn(case):
        source = Path(root) / "openspec" / "changes" / change_id / case["dataset_path"]
        if source.is_file():
            frozen = {**case, "inputs": datasets.read_case(source)["inputs"]}
            return harness.run(frozen, modules)
        return harness.run(case, modules)

    return run_fn


def budget_of(budgets, case):
    """The budget block of one case's capability."""
    return (budgets.get(case["capability"], {}) or {}).get("budget", {})


def _delta_row(case, budget, run_fn):
    """One suite row for one case."""
    from . import evals

    return evals.run_delta([case], budget, run_fn=run_fn).rows[0]


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


def cmd_certify(root, change_id, modules):
    """Gate 5: record a certification row per governed capability.

    A green delta run records the current pins digest; a red run
    records a red row, so a later drift check sees the failure.
    """
    from . import certs, evals, harness

    code, payload = cmd_evals(root, change_id, modules)
    report = payload["report"]
    policy_text = (Path(root) / DEFAULT_POLICY).read_text(encoding="utf-8")
    digest = certs.pins_digest(policy_text)
    recorded = []
    for capability in {row["capability"] for row in report.rows}:
        green = all(
            row["green"] for row in report.rows if row["capability"] == capability
        )
        certs.record(
            certs.ledger_path(root, capability),
            pins=digest,
            source=f"delta suite of {change_id}",
            green=green,
        )
        recorded.append(capability)
    del evals, harness
    return (0 if not recorded and report.exit == 0 else report.exit), {
        "certified": recorded,
        "report": report,
    }


def cmd_pin_drift(root, change_id=None, modules=None):
    """Gate 5: fail when a governed ledger holds stale or red pins."""
    from . import certs, manifest as manifest_mod

    manifest_path = Path(root) / "openspec" / "eval_manifest.json"
    capabilities = set()
    if manifest_path.is_file():
        data = manifest_mod.load(manifest_path)
        for change in data.get("changes", {}).values():
            for case in change.get("eval_cases", []):
                capabilities.add(case["capability"])
    policy_text = (Path(root) / DEFAULT_POLICY).read_text(encoding="utf-8")
    digest = certs.pins_digest(policy_text)
    found = []
    for capability in sorted(capabilities):
        found.extend(
            certs.drift(certs.ledger_path(root, capability), digest)
        )
    return (0 if not found else 2), {"violations": found}


def cmd_optimize(root, change_id, modules):
    """Gate 2: optimize and certify the modules with impl optimized."""
    from . import optimize

    disk = _on_disk(root, change_id)
    if disk is None:
        return 2, {"error": "no eval manifest on disk"}
    optimized = [
        entry
        for entry in disk[0]["changes"][change_id]["modules"]
        if entry.get("impl") == "optimized"
    ]
    if not optimized:
        return 0, {"outcome": "no optimized modules"}
    budgets = _budgets(root)
    outcomes = []
    for module in optimized:
        capability = module["capability"]
        cases = [
            case
            for case in disk[0]["changes"][change_id]["eval_cases"]
            if case["capability"] == capability
        ]
        result = optimize.run(
            cases,
            (budgets.get(capability, {}) or {}).get("holdout_ratio", 0.3),
            artifacts_dir=Path(root) / "tools" / "dspy_gate" / "artifacts" / change_id,
            run_fn=_suite_run_fn(root, change_id, modules),
            optimizer_fn=_optimizer_fn(),
            max_loops=(budgets.get(capability, {}) or {}).get("max_optimize_loops", 3),
        )
        outcomes.append(f"{module['module']}: {result.detail}")
    exit_code = 0 if all("certified" in o for o in outcomes) else 2
    return exit_code, {"outcomes": outcomes}


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
    sub.choices["evals"].add_argument("--out", default=None)
    sub.add_parser("certify").add_argument("change_id")
    sub.add_parser("pin-drift")
    sub.add_parser("optimize").add_argument("change_id")
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
    try:
        code, payload = _dispatch(args, root, modules)
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


def _dispatch(args, root, modules):
    """Run one command and return its (exit, payload)."""
    if args.command == "nightly":
        return cmd_nightly(root, args.change_id, modules, from_report=args.from_report)
    if args.command == "evals":
        return cmd_evals(root, args.change_id, modules, out=args.out)
    if args.command == "certify":
        return cmd_certify(root, args.change_id, modules)
    if args.command == "pin-drift":
        return cmd_pin_drift(root)
    if args.command == "optimize":
        return cmd_optimize(root, args.change_id, modules)
    return handlers_map()[args.command](root, args.change_id, modules)


def handlers_map():
    """The change-id commands and their handlers."""
    return {
        "lint": cmd_lint,
        "regen": cmd_regen,
        "verify": cmd_verify,
        "check-manifest": cmd_check_manifest,
        "status": cmd_status,
        "freeze": cmd_freeze,
        "matrix": cmd_matrix,
    }


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
