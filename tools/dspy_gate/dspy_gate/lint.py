"""Gate 0: the spec linter.

Everything downstream trusts this pass, so it is deliberately strict.
The rules: openspec validate --strict passes, every requirement holds
at least one scenario, every THEN parses or carries a judge tag with an
existing rubric, every scenario carries a known surface tag, and every
change threshold sits inside the policy bounds.
"""

import subprocess
from pathlib import Path

from . import compile as compile_mod
from . import gatepolicy, scenarioparse


def openspec_validate(change_dir):
    """Run the openspec CLI strict validation for one change.

    Returns (ok, output). The subprocess is the only external call, and
    tests inject a fake through lint_change.
    """
    result = subprocess.run(
        [
            "openspec",
            "validate",
            Path(change_dir).name,
            "--type",
            "change",
            "--strict",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(change_dir).parents[2]),
    )
    return result.returncode == 0, result.stdout + result.stderr


def lint_change(change_dir, policy, modules=None, validate=None):
    """Return the list of violations for one change directory.

    validate stays None-bound so tests can replace the module attribute
    without rebinding this default. The registry scopes the eval rules:
    scenarios of a capability outside it stay with the ordinary suite.
    """
    if validate is None:
        validate = openspec_validate
    change_dir = Path(change_dir)
    found = []
    ok, output = validate(change_dir)
    if not ok:
        found.append(f"openspec validate failed: {output.strip()}")
    try:
        data = scenarioparse.parse_change(change_dir)
        parse_error = None
    except scenarioparse.ScenarioParseError as exc:
        data = {"change_id": "", "requirements": []}
        parse_error = str(exc)
    if parse_error:
        found.append(parse_error)
    for requirement in data["requirements"]:
        name = requirement["name"]
        if not requirement["scenarios"]:
            found.append(f"requirement {name!r} has no scenario")
        for scenario in requirement["scenarios"]:
            if modules is None or scenario["capability"] in modules:
                found.extend(_scenario_violations(change_dir, scenario))
    found.extend(_bounds_violations(change_dir, policy))
    return found


def _scenario_violations(change_dir, scenario):
    """Return the lint violations of one parsed scenario."""
    found = []
    sid = scenario["scenario_id"]
    surface = scenario["surface"]
    if not surface:
        found.append(f"scenario {sid} has no surface tag")
    elif surface not in scenarioparse.SURFACES:
        found.append(f"scenario {sid} has unknown surface {surface!r}")
    try:
        compile_mod.compile_scenario(scenario)
    except compile_mod.CompileError as exc:
        found.append(str(exc))
    if scenario["judged"]:
        rubric = scenario.get("rubric")
        if rubric and not (change_dir / rubric).is_file():
            found.append(f"scenario {sid} names a missing rubric {rubric}")
    return found


def _bounds_violations(change_dir, policy):
    """Return the threshold violations of the change gates.yaml."""
    gates_path = change_dir / "gates.yaml"
    if not gates_path.is_file():
        return []
    change_gates = gatepolicy.load(gates_path)
    return gatepolicy.violations(policy, change_gates)
