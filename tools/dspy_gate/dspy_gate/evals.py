"""The Gate 3 suite runner: delta and frozen suites.

One row per scenario: the tier outcomes, the green flag, and the one
failure route from the routing table. A deferred Tier B keeps the
suite green and names the re-optimize route, because a judged scenario
certifies only through an opt-in live run. An exception inside a run
routes to repair the environment.
"""

from dataclasses import dataclass, field

from . import checks

ROUTE_OPTIMIZE = "re-optimize"
ROUTE_HARNESS = "fix the harness"
ROUTE_ENVIRONMENT = "repair the environment"


@dataclass
class Report:
    """One suite run: the exit code and one row per scenario."""

    exit: int
    rows: list = field(default_factory=list)


def run_delta(cases, budget, usage=None, run_fn=None):
    """Run the delta suite: the manifest cases of one change."""
    return _run_cases(cases, budget, usage, run_fn)


def run_frozen(cases, budget, usage=None, run_fn=None):
    """Run a frozen suite: the archived cases beside the capability."""
    return _run_cases(cases, budget, usage, run_fn)


def _run_cases(cases, budget, usage, run_fn):
    rows = []
    for case in cases:
        rows.append(_run_case(case, budget, usage, run_fn))
    exit_code = 0 if all(row["green"] for row in rows) else 2
    return Report(exit_code, rows)


def _run_case(case, budget, usage, run_fn):
    row = {
        "scenario_id": case["scenario_id"],
        "capability": case["capability"],
        "impl": case.get("impl", "hand"),
        "green": True,
        "deferred": False,
        "detail": "",
        "route": "",
        "tiers": {},
        "case": case,
    }
    try:
        pred, trace = _invoke(case, run_fn)
    except Exception as exc:  # noqa: BLE001 - the route decides
        row["green"] = False
        row["detail"] = f"environment error: {exc}"
        row["route"] = ROUTE_ENVIRONMENT
        return row
    if usage is not None:
        tier_d = checks.run_tier_d(budget, usage)
        row["tiers"]["D"] = tier_d.passed
        if not tier_d.passed:
            row["green"] = False
            row["detail"] = tier_d.detail
            row["route"] = ROUTE_HARNESS
            return row
    for assertion in case["checks"]:
        tier = assertion["tier"]
        if tier == "A":
            result = checks.run_tier_a([assertion], pred, trace)
            row["tiers"]["A"] = result.passed
            if not result.passed:
                row["green"] = False
                row["detail"] = result.detail
                row["route"] = _route_for(case)
                return row
        elif tier == "C":
            result = checks.run_tier_c([assertion], trace)
            row["tiers"]["C"] = result.passed
            if not result.passed:
                row["green"] = False
                row["detail"] = result.detail
                row["route"] = _route_for(case)
                return row
        elif tier == "B":
            row["deferred"] = True
            row["tiers"]["B"] = None
            row["route"] = ROUTE_OPTIMIZE
    return row


def _invoke(case, run_fn):
    """Resolve the harness call, or use the injected test runner."""
    if run_fn is None:
        from . import harness

        run_fn = harness.run
    return run_fn(case)


def _route_for(case):
    """The routing table row for a deterministic failure.

    An optimized module re-optimizes; a hand module fixes the harness.
    """
    if case.get("impl") == "optimized":
        return ROUTE_OPTIMIZE
    return ROUTE_HARNESS
