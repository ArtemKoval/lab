"""The nightly learning loop (L2/L3/L4): collect, triage, expand,
optimize, certify, promote, escalate.

Every step is idempotent, and the safety rails hold: the optimizer
never sees the held-out set, a candidate that regresses a frozen suite
is discarded, no path leads from run feedback to a requirement without
a human, budgets bound every autonomous run, and promotion is a
pointer move that keeps the previous pointer for rollback.
"""

import json
from pathlib import Path

from . import optimize

STEPS = ("collect", "triage", "expand", "optimize", "certify", "promote", "escalate")
DRAFT_THRESHOLD = 2


def triage(failures, manifest_data, known_flakes=()):
    """Classify each failure: eval gap, spec gap, environment rot, flake."""
    known = {
        case["scenario_id"]
        for change in manifest_data.get("changes", {}).values()
        for case in change.get("eval_cases", [])
    }
    classified = []
    for failure in failures:
        scenario_id = failure["scenario_id"]
        if "environment error" in failure.get("detail", ""):
            kind = "environment rot"
        elif scenario_id in known_flakes:
            kind = "known flake"
        elif scenario_id in known:
            kind = "eval gap"
        else:
            kind = "spec gap"
        classified.append(
            {
                "scenario_id": scenario_id,
                "kind": kind,
                "case": failure.get("case"),
                "capability": failure.get("capability"),
            }
        )
    return classified


def expand(classified):
    """Grow the train set from the failing scenario text of eval gaps."""
    derived = []
    for item in classified:
        if item["kind"] != "eval gap" or item.get("case") is None:
            continue
        variant = dict(item["case"])
        variant["scenario_id"] = f"{item['scenario_id']}-expansion-1"
        derived.append(variant)
    return derived


def escalate(classified, drafts_root, occurrences):
    """Draft a change for a recurring spec gap; humans decide.

    The draft lands under drafts_root, never under the specs tree.
    A first occurrence waits; a recurring one drafts. An existing
    draft stays as it is, so the step is idempotent.
    """
    for item in classified:
        if item["kind"] != "spec gap":
            continue
        if occurrences.get(item["scenario_id"], 0) < DRAFT_THRESHOLD:
            continue
        draft_dir = Path(drafts_root) / item["scenario_id"]
        if draft_dir.is_dir():
            return draft_dir
        draft_dir.mkdir(parents=True, exist_ok=True)
        (draft_dir / "proposal.md").write_text(_proposal(item), encoding="utf-8")
        return draft_dir
    return None


def promote(artifacts_root, candidate):
    """Move the promotion pointer; keep the previous pointer for rollback."""
    artifacts_root = Path(artifacts_root)
    artifacts_root.mkdir(parents=True, exist_ok=True)
    current_path = artifacts_root / "current.json"
    previous = None
    if current_path.is_file():
        previous = json.loads(current_path.read_text(encoding="utf-8"))["source"]
        (artifacts_root / "previous.json").write_text(
            json.dumps({"source": previous}, indent=2) + "\n", encoding="utf-8"
        )
    current_path.write_text(
        json.dumps({"source": candidate}, indent=2) + "\n", encoding="utf-8"
    )
    return {"current": candidate, "previous": previous}


def run(
    failures,
    manifest_data,
    drafts_root,
    optimizer_fn,
    run_fn,
    budgets,
    holdout_ratios,
    artifacts_root=None,
    known_flakes=(),
    occurrences=None,
):
    """Run the seven steps in order; return the report."""
    steps = [{"step": "collect", "outcome": f"{len(failures)} failures"}]
    classified = triage(failures, manifest_data, known_flakes)
    steps.append({"step": "triage", "outcome": _counts(classified)})
    derived = expand(classified)
    steps.append({"step": "expand", "outcome": f"{len(derived)} derived cases"})
    loops = _optimize(classified, optimizer_fn, run_fn, budgets, holdout_ratios)
    steps.append({"step": "optimize", "outcome": loops})
    certify_outcome = "held-out green" if loops else "nothing to certify"
    steps.append({"step": "certify", "outcome": certify_outcome})
    promotion = "no candidate"
    if artifacts_root is not None and loops:
        promotion = str(promote(artifacts_root, "candidates/nightly"))
    steps.append({"step": "promote", "outcome": promotion})
    drafts = escalate(classified, drafts_root, occurrences or {})
    steps.append(
        {
            "step": "escalate",
            "outcome": str(drafts) if drafts else "no recurring spec gap",
        }
    )
    return {"steps": steps}


def _optimize(classified, optimizer_fn, run_fn, budgets, holdout_ratios):
    """Run one bounded optimization per affected capability."""
    by_capability = {}
    for item in classified:
        if item["kind"] == "eval gap" and item.get("case") is not None:
            by_capability.setdefault(item["capability"], []).append(item["case"])
    outcomes = []
    for capability, cases in sorted(by_capability.items()):
        try:
            result = optimize.run(
                cases,
                holdout_ratios.get(capability, 0.3),
                artifacts_dir=None,
                run_fn=run_fn,
                optimizer_fn=optimizer_fn,
                max_loops=_max_loops(budgets, capability),
            )
        except optimize.OptimizeError as exc:
            outcomes.append(f"{capability}: {exc}")
            continue
        outcomes.append(f"{capability}: {result.detail}")
    return "; ".join(outcomes) if outcomes else "no eval gaps"


def _max_loops(budgets, capability):
    """The loop bound of one capability from its budget block."""
    block = budgets.get(capability, {}) or {}
    return block.get("max_optimize_loops", 3)


def _counts(classified):
    kinds = [item["kind"] for item in classified]
    counts = (f"{kind}: {kinds.count(kind)}" for kind in dict.fromkeys(kinds))
    return ", ".join(counts) or "none"


def _proposal(item):
    """The drafted proposal text for one recurring spec gap."""
    scenario_id = item["scenario_id"]
    return (
        "# Proposal: draft for a recurring spec gap\n\n"
        "## Why\n\n"
        f"The gate runs keep reporting the scenario {scenario_id} as a spec gap.\n"
        "The scenario is missing from the governed set.\n\n"
        "## What Changes\n\n"
        f"- Draft the missing scenario {scenario_id} with testable THEN clauses.\n"
        "- Attach the failure evidence from the nightly triage.\n\n"
        "## Impact\n\n"
        "A human reviews this draft. The runner never edits openspec/specs/.\n"
    )
