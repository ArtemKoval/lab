"""The assertion runners (Tiers A, C, D).

Tier A is hard and deterministic: it runs free on every push with no
model call. Tier C reads the tool-call orderings off the trace. Tier D
reads token and latency usage from a live run record; a hermetic run
reports n-a and stays green. Every failure names its scenario through
the caller, and the detail names the field and both sides.
"""

from dataclasses import dataclass


@dataclass
class Result:
    """The outcome of one assertion list."""

    passed: bool
    detail: str


def _fail(detail):
    return Result(False, detail)


def _eq(check, pred):
    field, want = check["field"], check["value"]
    got = pred.get(field)
    if got != want:
        return _fail(f"{field}: expected {want!r}, got {got!r}")
    return Result(True, "")


def _in(check, pred):
    field, values = check["field"], check["values"]
    got = pred.get(field)
    if got not in values:
        return _fail(f"{field}: expected one of {values}, got {got!r}")
    return Result(True, "")


def _schema(check, pred):
    missing = [f for f in check["fields"] if f not in pred]
    if missing:
        return _fail(f"missing fields: {', '.join(missing)}")
    return Result(True, "")


_KINDS = {"eq": _eq, "in": _in, "schema": _schema}


def run_tier_a(assertions, pred, trace=None):
    """Run the Tier-A assertions; the first failure decides the detail."""
    del trace  # Tier A reads the prediction only
    failures = []
    for assertion in assertions:
        runner = _KINDS[assertion["kind"]]
        result = runner(assertion, pred)
        if not result.passed:
            failures.append(result.detail)
    if failures:
        return _fail("; ".join(failures))
    return Result(True, "")


def run_tier_c(assertions, trace):
    """Run the Tier-C orderings; a missing call fails its ordering."""
    failures = []
    positions = []
    for assertion in assertions:
        before, after = assertion["before"], assertion["after"]
        first = _first_position(trace, "tool", before)
        second = _first_position(trace, "step", after)
        if first is None or second is None or first >= second:
            failures.append(
                f"call_order: {before} must precede {after}"
                + ("" if first is not None else f" (no {before} call)")
                + ("" if second is not None else f" (no {after} step)")
            )
        else:
            positions.append((first, second))
    if failures:
        return _fail("; ".join(failures))
    return Result(True, "")


def _first_position(trace, key, value):
    for index, entry in enumerate(trace):
        if entry.get(key) == value:
            return index
    return None


def run_tier_d(budget, usage):
    """Run the Tier-D budget assertions against one live usage record.

    Without a usage record the tier reports n-a and stays green: a
    hermetic run carries no token or latency spend to bound.
    """
    if usage is None:
        return Result(True, "n/a: no live usage record")
    failures = []
    tokens = usage.get("p95_tokens")
    ceiling = budget.get("p95_tokens_per_scenario")
    if tokens is not None and ceiling is not None and tokens > ceiling:
        failures.append(f"p95_tokens_per_scenario: {tokens} over ceiling {ceiling}")
    latency = usage.get("p95_latency_s")
    ceiling = budget.get("p95_latency_s")
    if latency is not None and ceiling is not None and latency > ceiling:
        failures.append(f"p95_latency_s: {latency} over ceiling {ceiling}")
    if failures:
        return _fail("; ".join(failures))
    return Result(True, "")
