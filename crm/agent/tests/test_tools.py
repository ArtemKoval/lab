from agent.direct import CONTEXT_LAYER
from agent.json_text import as_json
from agent.mcp_tools import McpTools
from agent.tools import APP_TOOLS, CASE_TOOLS, CONTEXT_TOOLS


def operations(client):
    """Return the operation ids of the backend's API."""
    paths = client.get("/openapi.json").json()["paths"].values()
    return {operation["operationId"] for path in paths for operation in path.values()}


def test_the_app_tools_are_named_after_backend_operations(client):
    names = [t.name for t in APP_TOOLS]
    assert names == [
        "get_case",
        "get_contract",
        "get_case_history",
        "calculate_award",
        "record_decision",
    ]
    assert set(names) <= operations(client)


def test_the_context_tools_are_the_context_layers_with_its_inputs(context_at):
    served = McpTools(CONTEXT_LAYER, context_at).tools
    assert {t.name for t in CONTEXT_TOOLS} == set(served)
    for tool in CONTEXT_TOOLS:
        inputs = served[tool.name].args
        assert set(tool.args) == set(inputs), tool.name
        for name, schema in tool.args.items():
            for rule in ("type", "enum", "minLength"):
                assert schema.get(rule) == inputs[name].get(rule), (tool.name, name)


def test_a_case_agent_can_only_act_on_its_own_case_and_customer():
    ids = {"case_id", "contract_id", "customer_id"}
    assert all(ids & set(t.args) == set() for t in CASE_TOOLS)


def test_the_agent_writes_json_with_characters_as_themselves():
    section = {"title": "Contract wording §2", "note": "the plan’s limit"}
    assert as_json(section) == (
        '{"title": "Contract wording §2", "note": "the plan’s limit"}'
    )
