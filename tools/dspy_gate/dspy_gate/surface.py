"""The surface dimension helpers: baseline governance.

A visual baseline lives under openspec/specs/<capability>/visual/ and
carries its scenario ID in its name. CI enforces both directions: no
visual scenario without a baseline, and no baseline without a visual
scenario. A baseline update rides the change pull request that alters
the rendered surface.
"""

import re
from pathlib import Path

BASELINE_RE = re.compile(r"^(?P<scenario_id>.+)\.(?P<capability>[\w-]+)\.png$")


def _visual_scenarios(manifest_data):
    """Yield (capability, scenario_id) of every visual case."""
    for change in manifest_data.get("changes", {}).values():
        for case in change.get("eval_cases", []):
            if case.get("surface") == "e2e-visual":
                yield case["capability"], case["scenario_id"]


def _baselines(specs_root):
    """Yield (capability, scenario_id) of every baseline file."""
    root = Path(specs_root) / "openspec" / "specs"
    if not root.is_dir():
        return
    for capability_dir in sorted(root.iterdir()):
        visual = capability_dir / "visual"
        if not visual.is_dir():
            continue
        for path in sorted(visual.glob("*.png")):
            match = BASELINE_RE.match(path.name)
            if match:
                yield match.group("capability"), match.group("scenario_id")


def baseline_violations(manifest_data, repo_root):
    """Return the bidirectional baseline violations (both directions)."""
    scenarios = set(_visual_scenarios(manifest_data))
    baselines = set(_baselines(repo_root))
    found = []
    for capability, scenario_id in sorted(scenarios - baselines):
        found.append(
            f"visual scenario {scenario_id} has no baseline under {capability}/visual/"
        )
    for capability, scenario_id in sorted(baselines - scenarios):
        found.append(
            f"baseline {scenario_id} in {capability}/visual/ cites no visual scenario"
        )
    return found
