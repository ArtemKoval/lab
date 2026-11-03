"""The Gate 4 archive freeze.

At archive time the freeze step copies the change's eval cases into
openspec/specs/<capability>/evals/ and extracts the capability's
threshold block into openspec/specs/<capability>/gates.yaml. The step
is idempotent, so an archive sync cannot lose the frozen suite.
"""

from pathlib import Path

from . import gatepolicy, manifest


def run(repo_root, change_id):
    """Freeze one change's governed artifacts; return the per-capability report.

    Baselines stay where the change PR authored them
    (openspec/specs/<capability>/visual/); the freeze verifies their
    presence instead of copying hand-authored pixels.
    """
    repo_root = Path(repo_root)
    data = manifest.load(repo_root / "openspec" / "eval_manifest.json")
    change = data["changes"][change_id]
    from . import surface

    violations = surface.baseline_violations(data, repo_root)
    if violations:
        raise ValueError("; ".join(violations))
    capabilities = {}
    for case in change["eval_cases"]:
        capability = case["capability"]
        capabilities.setdefault(capability, {"evals": 0, "gates": False})
        source = (
            repo_root
            / "openspec"
            / "changes"
            / change_id
            / manifest.dataset_relpath(case)
        )
        target = _capability_dir(repo_root, capability) / "evals" / Path(source).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        capabilities[capability]["evals"] += 1
    gates_path = repo_root / "openspec" / "changes" / change_id / "gates.yaml"
    if gates_path.is_file():
        _freeze_gates(repo_root, gatepolicy.load(gates_path), capabilities)
    return capabilities


def _freeze_gates(repo_root, change_gates, capabilities):
    """Extract each capability's threshold block beside its frozen suite."""
    for capability, block in change_gates.get("capabilities", {}).items():
        if capability not in capabilities:
            continue
        payload = {
            "version": change_gates.get("version", 1),
            "capabilities": {capability: block},
        }
        target = _capability_dir(repo_root, capability) / "gates.yaml"
        target.write_text(_dump(payload), encoding="utf-8")
        capabilities[capability]["gates"] = True


def _capability_dir(repo_root, capability):
    path = repo_root / "openspec" / "specs" / capability
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dump(payload):
    """Emit the frozen gates block as deterministic, readable YAML."""
    import yaml

    body = yaml.safe_dump(payload, sort_keys=True)
    return "# Frozen by python -m dspy_gate freeze; governed thresholds.\n" + body
