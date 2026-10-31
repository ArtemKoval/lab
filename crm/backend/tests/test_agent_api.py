"""The case agent's own API document, which the Gateway turns into tools."""

from api_rules import rule_breaks
from backend.agent_api import operations
from backend.tests.dashboard_reads import read

PATH = "/api/agent/openapi.json"


def operations_in(document):
    return {
        operation["operationId"]: operation
        for methods in document["paths"].values()
        for operation in methods.values()
    }


def test_the_document_holds_the_case_agents_six_operations(client):
    document = client.get(PATH).json()
    served = operations_in(document)
    assert (
        set(served)
        == operations()
        == {
            "get_case",
            "get_contract",
            "get_case_history",
            "calculate_award",
            "record_decision",
            "run_effect",
        }
    )
    app_operations = operations_in(client.get("/openapi.json").json())
    for name, operation in served.items():
        assert operation["description"] == app_operations[name]["description"]
    assert rule_breaks(document) == []


def test_the_document_has_no_servers_and_nothing_about_the_key(client):
    document = client.get(PATH).json()
    assert "servers" not in document
    assert "securitySchemes" not in document["components"]
    for operation in operations_in(document).values():
        assert "security" not in operation
        assert not [p for p in operation.get("parameters", []) if p["in"] == "header"]


def test_the_effect_route_takes_no_body(client):
    document = client.get(PATH).json()
    run_effect = operations_in(document)["run_effect"]
    assert "requestBody" not in run_effect


def test_the_document_needs_the_key_or_a_sign_in(dashboard):
    assert read(dashboard, PATH).status_code == 200
    assert dashboard.get(PATH).status_code == 401


def test_the_app_no_longer_serves_the_documents(client):
    operations = operations_in(client.get("/openapi.json").json())
    assert {"search_documents", "read_section"} & set(operations) == set()
    assert client.get("/api/documents/search", params={"query": "x"}).status_code == 404


def test_the_decision_body_requires_its_maker(client):
    document = client.get(PATH).json()
    operation = operations_in(document)["record_decision"]
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    model = document["components"]["schemas"][body["$ref"].split("/")[-1]]
    assert "decided_by" in model["required"]
