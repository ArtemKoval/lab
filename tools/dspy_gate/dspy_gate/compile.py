"""THEN-to-tier compilation (the bridge's constrained vocabulary).

Every THEN clause compiles into one assertion object:

- Tier A: an equality, a membership, or a schema claim.
- Tier C: a tool-order claim over the module trajectory.
- Tier B: a judged claim with a rubric reference and an ensemble of 3.

An AND under a judged THEN that fits no deterministic form folds into
that scenario's Tier-B reference. An AND that parses becomes its own
assertion. A THEN that fits nothing and carries no judge tag is a
CompileError: the CLI exits 2 and names the scenario.
"""

import re

ENSEMBLE = 3

EQ_RE = re.compile(r"^(?P<field>[\w ]+?)\s*=\s*(?P<value>.+)$")
IN_RE = re.compile(
    r"^(?P<field>[\w ]+?) is one of (?P<values>.+)$"
)
SCHEMA_RE = re.compile(
    r"^the output carries the fields (?P<fields>[\w ]+)$"
)
ORDER_RE = re.compile(
    r"^the (?P<before>[\w-]+) tool runs before the (?P<after>[\w-]+) (?:step|tool)$"
)
INLINE_JUDGE_RE = re.compile(
    r"\s*\[judge\s*:\s*rubric\s*=\s*(?P<rubric>[^\]]+)\]\s*$", re.I
)


class CompileError(ValueError):
    """A THEN the compiler cannot consume and no rubric can judge."""


def _strip_inline_judge(text):
    """Split an inline judge tag off the THEN text."""
    m = INLINE_JUDGE_RE.search(text)
    if not m:
        return text, None
    return text[: m.start()].strip(), m.group("rubric").strip()


def _parse_one(text, scenario_id, capability):
    """Compile one THEN text into check dicts, or None when unknown."""
    m = EQ_RE.match(text)
    if m:
        value = m.group("value").strip().strip('"')
        return [
            {
                "tier": "A",
                "kind": "eq",
                "field": m.group("field").strip(),
                "value": value,
            }
        ]
    m = IN_RE.match(text)
    if m:
        values = [v.strip() for v in m.group("values").split(",")]
        return [
            {
                "tier": "A",
                "kind": "in",
                "field": m.group("field").strip(),
                "values": values,
            }
        ]
    m = SCHEMA_RE.match(text)
    if m:
        fields = [f.strip() for f in m.group("fields").split(" and ")]
        return [{"tier": "A", "kind": "schema", "fields": fields}]
    m = ORDER_RE.match(text)
    if m:
        return [
            {
                "tier": "C",
                "kind": "call_order",
                "before": m.group("before"),
                "after": m.group("after"),
            }
        ]
    return None


def compile_scenario(scenario):
    """Compile one parsed scenario into its check list.

    The judged reference carries the scenario's rubric, taken from the
    inline tag first and the heading tag second.
    """
    checks = []
    judged_thens = 0
    has_judge = scenario["judged"] or any(
        INLINE_JUDGE_RE.search(t) for t in scenario["thens"]
    )
    for then_text in scenario["thens"]:
        additions, inline_rubric = _compile_then(then_text, scenario, has_judge)
        checks.extend(additions)
        if inline_rubric:
            judged_thens += 1
            checks.append(_judge_ref(inline_rubric))
    if scenario["judged"] and judged_thens == 0:
        checks.append(_judge_ref(_heading_rubric(scenario)))
    if not checks:
        raise CompileError(
            f"Scenario compiled to no assertions in {scenario['capability']}"
            f"/{scenario['scenario_id']}"
        )
    return checks


def _compile_then(then_text, scenario, has_judge):
    """Compile one THEN into (check list, inline rubric or None)."""
    text, inline_rubric = _strip_inline_judge(then_text)
    parsed = _parse_one(text, scenario["scenario_id"], scenario["capability"])
    if parsed:
        return parsed, inline_rubric
    if inline_rubric:
        return [], inline_rubric
    if not has_judge:
        raise CompileError(
            f"Uncompilable THEN in {scenario['capability']}"
            f"/{scenario['scenario_id']}: {then_text!r}"
        )
    return [], None


def _heading_rubric(scenario):
    """The rubric of a heading-tagged judged scenario, or the refusal."""
    rubric = scenario.get("rubric") or ""
    if not rubric:
        raise CompileError(
            f"Judged scenario without a rubric in {scenario['capability']}"
            f"/{scenario['scenario_id']}"
        )
    return rubric


def _judge_ref(rubric):
    """The Tier-B reference object for one rubric."""
    return {"tier": "B", "kind": "judge", "rubric": rubric, "ensemble": ENSEMBLE}
