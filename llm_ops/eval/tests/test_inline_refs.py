import json

import pytest
from pydantic import BaseModel, Field

from apfel_eval.judge import inline_refs


class Item(BaseModel):
    name: str


class Nested(BaseModel):
    items: list[Item]


class Twice(BaseModel):
    first: Item
    second: Item


class Described(BaseModel):
    item: Item = Field(description="the item of the field")


class Optional_(BaseModel):
    item: Item | None = None


class Node(BaseModel):
    children: list["Node"]


class Plain(BaseModel):
    score: int
    reason: str


ITEM = {
    "properties": {"name": {"title": "Name", "type": "string"}},
    "required": ["name"],
    "title": "Item",
    "type": "object",
}


def test_nested_model_is_inlined():
    schema = inline_refs(Nested.model_json_schema())
    assert schema["properties"]["items"] == {"items": ITEM, "title": "Items", "type": "array"}
    assert "$ref" not in json.dumps(schema)
    assert "$defs" not in schema


def test_schema_without_references_is_equal():
    original = Plain.model_json_schema()
    assert inline_refs(original) == original


def test_input_is_not_changed():
    original = Nested.model_json_schema()
    snapshot = json.dumps(original)
    inline_refs(original)
    assert json.dumps(original) == snapshot


def test_shared_definition_is_inlined_in_both_places():
    schema = inline_refs(Twice.model_json_schema())
    assert schema["properties"]["first"] == ITEM
    assert schema["properties"]["second"] == ITEM
    assert "$ref" not in json.dumps(schema)


def test_other_keys_next_to_a_reference_win():
    schema = {
        "$defs": {"X": {"type": "object", "description": "from the definition", "title": "X"}},
        "properties": {"field": {"$ref": "#/$defs/X", "description": "from the field"}},
        "type": "object",
    }
    field = inline_refs(schema)["properties"]["field"]
    assert field == {"type": "object", "description": "from the field", "title": "X"}


def test_description_of_a_model_field_is_kept():
    field = inline_refs(Described.model_json_schema())["properties"]["item"]
    assert field["description"] == "the item of the field"
    assert field["properties"] == ITEM["properties"]


def test_optional_model_is_inlined_in_any_of():
    field = inline_refs(Optional_.model_json_schema())["properties"]["item"]
    assert field["anyOf"][0] == ITEM
    assert field["anyOf"][1] == {"type": "null"}
    assert "$ref" not in json.dumps(field)


def test_references_inside_a_list_of_schemas_are_inlined():
    schema = {
        "$defs": {"A": {"type": "string"}},
        "anyOf": [{"$ref": "#/$defs/A"}, {"type": "integer"}],
    }
    assert inline_refs(schema) == {"anyOf": [{"type": "string"}, {"type": "integer"}]}


def test_definition_that_uses_another_definition_is_inlined():
    schema = {
        "$defs": {"A": {"properties": {"b": {"$ref": "#/$defs/B"}}}, "B": {"type": "string"}},
        "properties": {"a": {"$ref": "#/$defs/A"}},
    }
    assert inline_refs(schema) == {"properties": {"a": {"properties": {"b": {"type": "string"}}}}}


def test_direct_cycle_raises():
    with pytest.raises(ValueError, match="recursive"):
        inline_refs(Node.model_json_schema())


def test_indirect_cycle_raises():
    schema = {
        "$defs": {
            "A": {"properties": {"b": {"$ref": "#/$defs/B"}}},
            "B": {"items": {"$ref": "#/$defs/A"}},
        },
        "properties": {"a": {"$ref": "#/$defs/A"}},
    }
    with pytest.raises(ValueError, match="recursive"):
        inline_refs(schema)


def test_cycle_message_names_the_definition():
    with pytest.raises(ValueError, match="definition Node refers to itself"):
        inline_refs(Node.model_json_schema())


def test_reference_to_a_missing_definition_raises():
    schema = {"$defs": {"A": {"type": "string"}}, "properties": {"a": {"$ref": "#/$defs/B"}}}
    with pytest.raises(ValueError, match="definition B, which it does not have"):
        inline_refs(schema)


def test_reference_in_a_schema_with_no_definitions_raises():
    with pytest.raises(ValueError, match="definition A, which it does not have"):
        inline_refs({"properties": {"a": {"$ref": "#/$defs/A"}}})


def test_reference_with_no_slash_names_the_definition():
    schema = {"$defs": {"A": {"type": "string"}}, "properties": {"a": {"$ref": "A"}}}
    assert inline_refs(schema) == {"properties": {"a": {"type": "string"}}}


def test_scalars_in_a_schema_are_kept():
    schema = {"type": "object", "required": ["a"], "additionalProperties": False, "minimum": 0}
    assert inline_refs(schema) == schema
