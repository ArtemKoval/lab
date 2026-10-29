from agent.tools import CASE_TOOLS


def operations(client):
    """Return the operation ids of the backend's API."""
    paths = client.get("/openapi.json").json()["paths"].values()
    return {operation["operationId"] for path in paths for operation in path.values()}


def test_case_tools_are_named_after_backend_operations(client):
    names = [t.name for t in CASE_TOOLS]
    assert names == [
        "get_case",
        "get_contract",
        "get_case_history",
        "search_documents",
        "read_section",
        "calculate_award",
        "record_decision",
    ]
    assert set(names) <= operations(client)


def test_a_case_agent_can_only_act_on_its_own_case():
    assert all("case_id" not in t.args for t in CASE_TOOLS)
