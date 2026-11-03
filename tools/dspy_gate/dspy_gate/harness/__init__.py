"""The harness layer: hand modules, the registry, and the run
resolution. Structure is code; prompts stay with the optimizer."""

import importlib
from pathlib import Path

from .registry import modules


def run(case, registry_modules=None):
    """Run one manifest case through its registry module.

    Returns (prediction, trace). The prediction is a plain dict; the
    trace is the ordered list of tool calls and steps. The entry point
    resolves as <dotted module>::<callable> from the registry. Explicit
    case inputs win: they are the examples the datasets froze at
    regeneration time.
    """
    modules_map = modules() if registry_modules is None else registry_modules
    module_entry = modules_map[case["capability"]]
    if module_entry.get("impl") == "optimized":
        _require_artifacts(module_entry)
    call = resolve_entry(module_entry["entry"])
    inputs = case.get("inputs")
    if inputs is None:
        inputs = case_inputs(case, module_entry)
    return call(**inputs)


def _require_artifacts(module_entry):
    """Refuse an optimized module whose artifacts directory is absent.

    The real artifact load runs behind the live extra; this gate keeps
    CI off an un-optimized seed program.
    """
    artifacts = module_entry.get("artifacts", "")
    if not artifacts:
        raise FileNotFoundError(
            f"optimized module {module_entry['module']} names no artifacts directory"
        )
    pointer = Path(artifacts) / "pointer.json"
    if not pointer.is_file():
        raise FileNotFoundError(
            f"optimized module {module_entry['module']} has no artifacts at {artifacts}"
        )


def case_inputs(case, module_entry):
    """Collect the example inputs of the case, or the WHEN text."""
    examples = module_entry.get("examples", {})
    if case["scenario_id"] in examples:
        return dict(examples[case["scenario_id"]])
    return {"when": case.get("when", "")}


def resolve_entry(entry):
    """Resolve a '<dotted module>::<callable>' entry into a callable."""
    path_text, name = entry.split("::")
    module = importlib.import_module(path_text)
    return getattr(module, name)
