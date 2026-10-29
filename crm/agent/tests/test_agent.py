import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage

from agent import __main__ as cli
from agent import main
from agent.tools import TOOLS


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies and keeps the prompts it was sent."""

    prompts: list[list[BaseMessage]] = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append(messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


def call(name, text="", **args):
    return AIMessage(
        content=text, tool_calls=[{"name": name, "args": args, "id": f"call-{name}"}]
    )


def script(case_id, contract_id, customer_id, decision, award, *extra):
    return StubModel(
        messages=iter(
            [
                call("get_case", case_id=case_id),
                call("get_contract", contract_id=contract_id),
                call("get_case_history", customer_id=customer_id),
                call(
                    "record_decision",
                    case_id=case_id,
                    decision=decision,
                    award=award,
                    section="Section 3, Trip Delay",
                    reason="The delay was covered.",
                ),
                *extra,
                AIMessage(content=f"Decision: {decision}."),
            ]
        )
    )


def test_tools_are_named_after_backend_operations(client):
    operations = {
        operation["operationId"]
        for path in client.get("/openapi.json").json()["paths"].values()
        for operation in path.values()
    }
    names = [t.name for t in TOOLS]
    assert names == [
        "get_case",
        "get_contract",
        "get_case_history",
        "record_decision",
        "pay_case",
    ]
    assert set(names) <= operations


def test_get_instructions(client):
    text = client.get("/api/instructions").json()["text"]
    assert text.startswith("# CRM Agent")
    assert "## 10. How we work out your payment" in text


def test_run_approves_and_pays_within_the_limit(client):
    stub = script(
        "CLM-1001",
        "POL-2001",
        "CUS-3001",
        "approve",
        420.0,
        call("pay_case", text="Paying now.", case_id="CLM-1001", amount=420.0),
    )
    assert main.run("CLM-1001", "thread-1", stub) == "Decision: approve."

    case = client.get("/api/cases/CLM-1001").json()
    assert case["status"] == "decided"
    assert case["thread_id"] == "thread-1"
    assert case["decision"]["award"] == 420.0
    assert case["payment"]["amount"] == 420.0

    steps = client.get("/api/cases/CLM-1001/steps").json()
    assert [s["kind"] for s in steps] == [
        *(["tool_call", "tool_result"] * 4),
        "message",
        "tool_call",
        "tool_result",
        "message",
    ]
    assert steps[0]["content"] == 'get_case(case_id="CLM-1001")'
    assert steps[1]["content"].startswith('get_case: {"case_id":"CLM-1001"')
    assert steps[8]["content"] == "Paying now."
    assert steps[9]["content"] == 'pay_case(case_id="CLM-1001", amount=420.0)'
    assert steps[-1]["content"] == "Decision: approve."
    assert {s["thread_id"] for s in steps} == {"thread-1"}


def test_run_uses_the_instructions_from_the_backend(client):
    stub = script("CLM-1003", "POL-2003", "CUS-3003", "refer", 0)
    main.run("CLM-1003", "thread-1", stub)
    system = stub.prompts[0][0]
    assert isinstance(system, SystemMessage)
    assert system.content == client.get("/api/instructions").json()["text"]


def test_payment_over_the_limit_is_refused(client):
    stub = script(
        "CLM-1002",
        "POL-2002",
        "CUS-3002",
        "approve",
        1350.0,
        call("pay_case", case_id="CLM-1002", amount=1350.0),
    )
    main.run("CLM-1002", "thread-2", stub)

    refusal = stub.prompts[-1][-1]
    assert isinstance(refusal, ToolMessage)
    assert "needs a worker's sign-off" in refusal.text
    assert refusal.text.startswith("Refused with status 403")

    case = client.get("/api/cases/CLM-1002").json()
    assert case["status"] == "waiting_for_sign_off"
    assert case["payment"] is None


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_run_declines_and_refers(client, decision):
    main.run(
        "CLM-1003", "thread-3", script("CLM-1003", "POL-2003", "CUS-3003", decision, 0)
    )
    case = client.get("/api/cases/CLM-1003").json()
    assert case["status"] == "decided"
    assert case["decision"]["decision"] == decision
    assert case["payment"] is None


def test_run_needs_a_waiting_case():
    main.run(
        "CLM-1003", "thread-3", script("CLM-1003", "POL-2003", "CUS-3003", "refer", 0)
    )
    with pytest.raises(main.BackendError, match="409: Case CLM-1003 is not waiting"):
        main.run("CLM-1003", "thread-4", StubModel(messages=iter([])))


def test_command_line(monkeypatch, capsys):
    runs = []
    monkeypatch.setattr(
        cli,
        "run",
        lambda case_id, thread_id: runs.append((case_id, thread_id)) or "Done.",
    )
    cli.main(["CLM-1001"])
    assert capsys.readouterr().out == "Done.\n"
    assert runs[0][0] == "CLM-1001"
    assert len(runs[0][1]) == 36


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
