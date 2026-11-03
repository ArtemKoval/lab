"""The gates.yaml policy reader.

The effective policy file carries the model role pins and the policy
bounds. Each change carries its own thresholds, and Gate 0 rejects a
threshold outside the bounds. Threshold edits arrive only inside a
reviewed change proposal.
"""

from pathlib import Path

THRESHOLD_KEYS = ("tier_a", "tier_b_min", "holdout_ratio", "judge_ensemble")


def load(path):
    """Read one gates.yaml file into a dict.

    The yaml import stays lazy: the stdlib core imports this module
    without PyYAML installed, and only reading a policy needs it.
    """
    import yaml

    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def roles(policy):
    """Return the model role pin map."""
    return policy.get("models", {}).get("roles", {})


def bounds(policy):
    """Return the policy bounds map."""
    return policy.get("policy_bounds", {})


def threshold_in_bounds(policy, name, value):
    """True when the value sits within the named bound, edges included.

    A name with no bound entry passes: the policy governs only the
    thresholds it names.
    """
    rule = bounds(policy).get(name)
    if rule is None:
        return True
    return rule["min"] <= value <= rule["max"]


def _threshold_pairs(node):
    """Yield (name, numeric value) pairs from a nested gate block."""
    for key, value in node.items():
        if isinstance(value, dict):
            yield from _threshold_pairs(value)
        elif isinstance(value, (int, float)):
            yield key, value


def violations(policy, change_gates):
    """Return the change thresholds outside the policy bounds.

    Every numeric threshold in the change's capabilities block is
    examined against the bound of the same name.
    """
    found = []
    capabilities = change_gates.get("capabilities", {})
    for cap, block in capabilities.items():
        for name, value in _threshold_pairs(block):
            if not threshold_in_bounds(policy, name, value):
                found.append(f"{cap}: {name}={value} outside policy bounds")
    return found
