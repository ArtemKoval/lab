"""Run the vendored mutator over the owned tools and hold the ratchet.

The pass parses the printed per-function table of the mutator,
aggregates it into per-module scores by the namespace column, and
compares every module score against the committed store at
reports/saturation/scores.json. A drop fails the run. The store moves
only through pull requests.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

TOOL_TABLE = (
    ("plan_exec", "tools/plan_exec/plan_exec", "tests/plan_exec"),
    ("spec_ste_check", "tools/spec_ste_check/spec_ste_check",
     "tests/spec_ste_check"),
    ("devcontainer_init", "tools/devcontainer_init/devcontainer_init",
     "tests/devcontainer_init"),
    ("handover_telemetry", "tools/handover_telemetry/handover_telemetry",
     "tests/handover_telemetry"),
    ("handover_telemetry_setup",
     "tools/handover_telemetry_setup/handover_telemetry_setup.py",
     "tests/handover_telemetry"),
    ("dspy_gate", "tools/dspy_gate/dspy_gate", "tests/dspy_gate"),
    ("dspy_gate_setup", "tools/dspy_gate_setup/dspy_gate_setup.py",
     "tests/dspy_gate_setup"),
    ("peak_hours_gate", "tools/peak_hours_gate/peak_hours_gate",
     "tests/peak_hours_gate"),
    ("process_issues", "tools/process_issues/process_issues",
     "tests/process_issues"),
    ("chaos_ssh", "devops/chaos/ssh/tutor/chaos_ssh",
     "tests/devops_chaos_ssh"),
)

COVERAGE_PATH = "target/coverage/python/lcov.info"
STORE_PATH = "reports/saturation/scores.json"
PYTHON = "tools/zai_routing_audit/.venv/bin/python"
MUTATOR = "tools/mutator/mutator"


def parse_table(text):
    """Parse the printed per-function table. Return one row per namespace."""
    rows = {}
    in_table = False
    for line in text.splitlines():
        parts = line.split()
        if parts[:2] == ["Function", "Namespace"]:
            in_table = True
            continue
        if not in_table or not parts:
            continue
        if set(parts[0]) == {"-"}:
            continue
        if parts[0] == "Total" and len(parts) == 6:
            break
        row = rows.setdefault(parts[1], {
            "killed": 0, "survived": 0, "uncovered": 0, "sites": 0,
        })
        row["killed"] += int(parts[2])
        row["survived"] += int(parts[3])
        row["uncovered"] += int(parts[4])
        row["sites"] += int(parts[5])
    return rows


def module_scores(text):
    """Aggregate the table into per-module scores for one tool."""
    scores = {}
    for namespace, row in parse_table(text).items():
        if row["sites"] == 0:
            continue
        executed = row["killed"] + row["survived"]
        score = None if executed == 0 else round(
            100 * row["killed"] / executed, 1)
        scores[namespace] = {"sites": row["sites"], "score": score}
    return scores


def compare(tool, run_modules, stored_modules):
    """Compare run scores against the store. Return one verdict per module."""
    verdicts = []
    for namespace, run in run_modules.items():
        stored = stored_modules.get(namespace)
        if run["score"] is None:
            verdict = "no-score"
            stored_score = None if stored is None else stored["score"]
        elif stored is None:
            verdict = "new"
            stored_score = None
        elif run["score"] < stored["score"]:
            verdict = "drop"
            stored_score = stored["score"]
        else:
            verdict = "hold"
            stored_score = stored["score"]
        verdicts.append(_verdict(tool, namespace, verdict, stored_score, run))
    return verdicts


def _verdict(tool, namespace, kind, stored, run):
    """Return one comparison verdict for the report."""
    return {
        "tool": tool,
        "module": namespace,
        "verdict": kind,
        "stored": stored,
        "run": run["score"],
    }


def mutator_argv(entry):
    """Return one mutator argv for one table entry."""
    return [
        MUTATOR, "--use-existing-coverage", "--max-workers", "4",
        "--test-command", f"{PYTHON} -m pytest -q {entry[2]}",
        entry[1],
    ]


def run_mutator(argv):
    """Run one mutator command. Return (code, out, err)."""
    proc = subprocess.run(argv, check=False, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def load_store(path):
    """Load the store JSON. Return None when it is missing or unusable."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def write_store(path, store):
    """Write the store JSON with a stable key order."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2)
        handle.write("\n")


def run_tool(entry, mutator):
    """Run one tool. Return its report dict."""
    name, _product, _suite = entry
    code, out, err = mutator(mutator_argv(entry))
    modules = module_scores(out)
    report = {"modules": modules, "verdicts": [], "dropped": [],
              "mutator_code": code, "error": None}
    if code not in (0, 3):
        report["error"] = f"{name}: the mutator exited with code {code}: {err.strip()}"
        return report
    if not modules:
        report["error"] = (f"{name}: the mutator printed no table "
                           f"(exit {code})")
        return report
    return report


def compare_tool(entry, report, store):
    """Attach the comparison verdicts to one tool report."""
    name = entry[0]
    stored = store.get("tools", {}).get(name, {}).get("modules", {})
    report["verdicts"] = compare(name, report["modules"], stored)
    return report


def pass_notes(entry, report):
    """Return the refusal notes of one tool report."""
    name = entry[0]
    notes = []
    if report["error"]:
        notes.append(report["error"])
    for verdict in report["verdicts"]:
        if verdict["verdict"] == "drop":
            notes.append(
                f"{name}: {verdict['module']} dropped from "
                f"{verdict['stored']} to {verdict['run']}")
        if verdict["verdict"] == "no-score":
            notes.append(
                f"{name}: {verdict['module']} carries no score")
    return notes


def run_pass(entries, store, mutator):
    """Run every entry and compare against the store. Return the report."""
    tools = {}
    failed = False
    for entry in entries:
        report = compare_tool(entry, run_tool(entry, mutator), store)
        notes = pass_notes(entry, report)
        report["notes"] = notes
        tools[entry[0]] = report
        failed = failed or bool(notes)
    return {"schema": 1, "tools": tools, "failed": failed}


def _parse_args(argv):
    """Parse the CLI arguments. Return None on a usage refusal."""
    parser = argparse.ArgumentParser(prog="saturation_pass")
    parser.add_argument("--init", action="store_true", dest="init")
    parser.add_argument("--update", action="store_true", dest="update")
    parser.add_argument("--tool", action="append", dest="tools")
    parser.add_argument("--coverage", default=COVERAGE_PATH)
    parser.add_argument("--store", default=STORE_PATH)
    parser.add_argument("--json", dest="report_path")
    return parser.parse_args(argv)


def _print(message):
    """Print one line to stderr."""
    print(message, file=sys.stderr)


def _report_verdict(report):
    """Name the run verdict for the JSON report."""
    return "failed" if report["failed"] else "clean"


def _write_report(path, report):
    """Write the JSON run report when a path is set."""
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


def _select_entries(names):
    """Return the table entries for the requested tools. None on unknown.

    The selection runs in table order and deduplicates repeats.
    """
    if not names:
        return list(TOOL_TABLE)
    picked_names = set()
    picked = []
    for entry in TOOL_TABLE:
        if entry[0] in names:
            picked_names.add(entry[0])
            picked.append(entry)
    for name in names:
        if name not in picked_names:
            _print(f"saturation_pass: unknown tool {name}; "
                   f"the table holds {[e[0] for e in TOOL_TABLE]}")
            return None
    return picked


def _coverage_note(coverage):
    """Return the discovery note when the coverage path is not the default."""
    if coverage == COVERAGE_PATH:
        return None
    return ("saturation_pass: the mutator discovers the house lcov "
            "path itself; --coverage only verifies the file exists")


def main(argv=None, mutator=None, clock=None):
    """Run one pass action. Return the exit code."""
    mutator = mutator or run_mutator
    clock = clock or (lambda: datetime.now(UTC).isoformat())
    args = _parse_args(argv)
    if args.init and args.update:
        _print("saturation_pass: --init and --update refuse each other")
        return 2
    entries = _select_entries(args.tools)
    if entries is None:
        return 2
    if not Path(args.coverage).is_file():
        _print(f"saturation_pass: no coverage report at {args.coverage}; "
               f"pass --coverage or run the gate coverage pass first")
        return 2
    if args.coverage != COVERAGE_PATH:
        _print(_coverage_note(args.coverage))
    store = load_store(args.store)
    if args.init:
        return _init_action(args, entries, store, mutator, clock)
    if store is None:
        _print(f"saturation_pass: no store at {args.store}; run --init first")
        return 2
    report = run_pass(entries, store, mutator)
    return _finish(args, entries, report, store, clock)


def _init_action(args, entries, store, mutator, clock):
    """Write the first baseline. Return the exit code."""
    if store is not None:
        _print(f"saturation_pass: the store at {args.store} exists; "
               f"--init refuses to overwrite it")
        return 2
    report = run_pass(entries, {}, mutator)
    if report["failed"]:
        for tool in report["tools"].values():
            for note in tool["notes"]:
                _print(f"saturation_pass: {note}")
        _print("saturation_pass: --init refuses a failing run")
        return 2
    tools = {}
    for entry in entries:
        tools[entry[0]] = {"stamp": clock(),
                           "modules": report["tools"][entry[0]]["modules"]}
    write_store(args.store, {"schema": 1, "tools": tools})
    report["stamp"] = clock()
    report["exit"] = "clean"
    _write_report(args.report_path, report)
    return 0


def _finish(args, entries, report, store, clock):
    """Apply the action verdicts and exit code. Return the exit code."""
    for tool in report["tools"].values():
        for note in tool["notes"]:
            _print(f"saturation_pass: {note}")
    stamp = clock()
    if args.update and not report["failed"]:
        _apply_update(entries, report, store, args.store, stamp)
    for name, tool in report["tools"].items():
        for namespace, module in tool["modules"].items():
            print(f"{name}: {namespace} score {module['score']} "
                  f"at {module['sites']} sites")
    report["stamp"] = stamp
    report["exit"] = _report_verdict(report)
    _write_report(args.report_path, report)
    return 2 if report["failed"] else 0


def _apply_update(entries, report, store, store_path, stamp):
    """Merge clean tool reports into the store and drop stale modules."""
    tools = store.setdefault("tools", {})
    for entry in entries:
        name = entry[0]
        run_modules = report["tools"][name]["modules"]
        dropped = sorted(set(tools.get(name, {}).get("modules", {}))
                         - set(run_modules))
        report["tools"][name]["dropped"] = dropped
        for module in dropped:
            _print(f"saturation_pass: dropped stale module {module}")
        tools[name] = {"stamp": stamp, "modules": run_modules}
    write_store(store_path, store)


if __name__ == "__main__":
    sys.exit(main())
