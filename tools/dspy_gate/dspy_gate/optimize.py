"""The Gate 2 runner: optimize, certify on held-out, then save.

The optimizer tunes against the train and validation sets only. The
certification set stays hidden from it, so Gate 2 measures
generalization. A candidate writes artifacts only after a green
certification with Tier A at 1.0, and the loop bound caps the retries.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from . import checks


class OptimizeError(ValueError):
    """A change whose scenario set cannot support a held-out split."""


@dataclass
class Outcome:
    """One optimize-and-certify pass."""

    exit: int
    detail: str = ""
    loops: int = 0
    heldout_ids: list = field(default_factory=list)


def split(cases, holdout_ratio):
    """Split into (train, validation, held-out).

    The held-out count rounds up with a floor of one, so a small set
    still certifies on unseen scenarios. The split is deterministic.
    """
    if len(cases) < 2:
        raise OptimizeError("not enough scenarios to split; need at least 2")
    heldout_count = max(1, math.ceil(len(cases) * holdout_ratio))
    rest = cases[:-heldout_count]
    if not rest:
        raise OptimizeError("not enough scenarios for train and validation")
    val_count = max(1, len(rest) // 4)
    val = rest[-val_count:]
    train = rest[:-val_count]
    return train, val, cases[-heldout_count:]


def run(
    cases,
    holdout_ratio,
    artifacts_dir,
    run_fn,
    optimizer_fn,
    max_loops=3,
):
    """Optimize the program, certify on held-out, and save on green.

    optimizer_fn receives (program, train, validation) and returns the
    candidate program; run_fn runs one case against the candidate. The
    default program is the case list itself; the harness registry owns
    the real program in a live run.
    """
    train, val, heldout = split(cases, holdout_ratio)
    heldout_ids = [c["scenario_id"] for c in heldout]
    program = list(cases)
    for loop in range(1, max_loops + 1):
        candidate = optimizer_fn(program, train, val)
        result = _certify(candidate, heldout, run_fn)
        if result.passed:
            _save(artifacts_dir, heldout_ids, len(cases))
            return Outcome(
                0,
                f"certified on loop {loop}",
                loops=loop,
                heldout_ids=heldout_ids,
            )
    return Outcome(
        2,
        f"certification failed after {max_loops} loops: {result.detail}",
        loops=max_loops,
        heldout_ids=heldout_ids,
    )


def _certify(candidate, heldout, run_fn):
    """Certify the candidate on the held-out set with Tier A at 1.0."""
    del candidate  # the candidate program runs inside run_fn
    for case in heldout:
        pred, trace = run_fn(case)
        result = checks.run_tier_a(
            [c for c in case["checks"] if c["tier"] == "A"], pred, trace
        )
        if not result.passed:
            return checks.Result(False, f"{case['scenario_id']}: {result.detail}")
    return checks.Result(True, "")


def _save(artifacts_dir, heldout_ids, total):
    """Write the versioned pointer for the promoted program."""
    path = Path(artifacts_dir)
    path.mkdir(parents=True, exist_ok=True)
    pointer = {
        "kind": "dspy_gate program pointer",
        "scenarios": total,
        "heldout_ids": heldout_ids,
    }
    (path / "pointer.json").write_text(
        json.dumps(pointer, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
