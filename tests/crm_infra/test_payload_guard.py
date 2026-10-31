"""The core never reads inside a pack's outcome payload: any subscript or
.get on a payload name in engine code fails the suite. The engine moves a
payload opaque and reads it only through the pack's summarize and metric,
which the loader-mediated helpers call."""

import ast
from pathlib import Path

CRM = Path(__file__).parents[2] / "crm"
ENGINE_DIRS = ("crm/backend", "crm/agent")


def payload_reads():
    """Every place engine code subscripts or .gets a payload name."""
    found = []
    for directory in ENGINE_DIRS:
        for path in sorted((CRM / directory).rglob("*.py")):
            if "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                values = []
                if isinstance(node, ast.Subscript):
                    values = [node.value]
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get"
                ):
                    values = [node.func.value]
                for value in values:
                    if isinstance(value, ast.Name) and "payload" in value.id.lower():
                        found.append(f"{path.relative_to(CRM)}:{node.lineno}")
    return found


def test_the_engine_never_parses_a_payload():
    assert payload_reads() == []
