"""Per-scenario dataset emission.

Each scenario becomes one JSON file under the change's evals/ area,
with the example inputs the harness registry provides, or the WHEN text
as the generic input when no example exists. The first line of every
file is the GENERATED marker as a reserved key.
"""

import json
from pathlib import Path

from .manifest import GENERATED_MARKER, dataset_relpath


def example_inputs(case, modules):
    """Return the example inputs for one case.

    The registry entry may carry an examples map keyed by scenario_id.
    Without one, the WHEN text is the input under the generic key.
    """
    module = modules.get(case["capability"], {})
    examples = module.get("examples", {})
    if case["scenario_id"] in examples:
        return dict(examples[case["scenario_id"]])
    return {"when": case["when"]}


def write_case(eval_root, case, modules):
    """Write one case JSON under eval_root and return its path."""
    path = Path(eval_root) / dataset_relpath(case)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "_generated": GENERATED_MARKER,
        "scenario_id": case["scenario_id"],
        "inputs": example_inputs(case, modules),
        "expected": {"checks": case["checks"]},
    }
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def read_case(path):
    """Read one case JSON back."""
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)
