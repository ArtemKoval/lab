"""The core never reads inside a pack's outcome payload: any subscript or
.get on a payload name in engine code fails the suite. The engine moves a
payload opaque and reads it only through the pack's summarize and metric,
which the loader-mediated helpers call."""

import ast
from pathlib import Path

CRM = Path(__file__).parents[2] / "crm"
ENGINE_DIRS = ("crm/backend", "crm/agent")


def reads_of_node(node: ast.AST) -> list[ast.Name]:
    """The payload names one AST node reads, at its top level."""
    if isinstance(node, ast.Subscript):
        values = [node.value]
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
    ):
        values = [node.func.value]
    else:
        values = []
    return [value for value in values if isinstance(value, ast.Name)]


def reads_in_source(source: str) -> list[int]:
    """The lines of a module's source that read a payload name."""
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        for value in reads_of_node(node)
        if "payload" in value.id.lower()
    ]


def payload_reads() -> list[str]:
    """Every place engine code subscripts or .gets a payload name."""
    found = []
    for directory in ENGINE_DIRS:
        for path in sorted((CRM / directory).rglob("*.py")):
            if "tests" in path.parts:
                continue
            for line in reads_in_source(path.read_text(encoding="utf-8")):
                found.append(f"{path.relative_to(CRM)}:{line}")
    return found


def test_the_engine_never_parses_a_payload():
    assert payload_reads() == []


def test_a_payload_subscript_is_a_read():
    assert reads_in_source("x = payload['award']") == [1]


def test_a_payload_get_is_a_read():
    assert reads_in_source("x = payload.get('award')") == [1]


def test_other_names_are_not_reads():
    assert reads_in_source("x = row['payload']\ny = payload is None") == []


def test_calls_and_attributes_are_not_reads():
    assert reads_in_source("x = work(payload)\ny = payload.attr['k']") == []


def test_payload_reads_finds_and_names_the_place(tmp_path, monkeypatch):
    import sys

    engine = tmp_path / "crm" / "backend"
    engine.mkdir(parents=True)
    (engine / "mod.py").write_text("x = payload['award']\n")
    (engine / "tests").mkdir()
    (engine / "tests" / "t.py").write_text("x = payload['award']\n")
    monkeypatch.setattr(sys.modules[__name__], "CRM", tmp_path)
    assert payload_reads() == ["crm/backend/mod.py:1"]
