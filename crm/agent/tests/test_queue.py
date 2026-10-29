import sqlite3
from contextlib import closing

import pytest
from langchain_core.messages import AIMessage

from agent import __main__ as cli
from agent import main
from agent.tests.test_agent import StubModel, call


@pytest.fixture
def three_waiting(database):
    """Leave only CLM-1001, CLM-1002 and CLM-1003 waiting in the queue."""
    with closing(sqlite3.connect(database)) as db, db:
        db.execute(
            "UPDATE cases SET status = 'decided'"
            " WHERE case_id NOT IN ('CLM-1001', 'CLM-1002', 'CLM-1003')"
        )


def decide(case_id, decision, award, *extra):
    return [
        call("get_case", case_id=case_id),
        call(
            "record_decision",
            case_id=case_id,
            decision=decision,
            award=award,
            section="Section 3, Trip Delay",
            reason="Covered.",
        ),
        *extra,
        AIMessage(content="Done."),
    ]


def test_work_queue_with_a_stub_model(monkeypatch, capsys, client, three_waiting):
    stub = StubModel(
        messages=iter(
            decide(
                "CLM-1001",
                "approve",
                420.0,
                call("pay_case", case_id="CLM-1001", amount=420.0),
            )
            + decide("CLM-1002", "approve", 1350.0)
            + decide("CLM-1003", "refer", 0)
        )
    )
    real_run = main.run
    worked = []

    def run(case_id, thread_id):
        worked.append(case_id)
        return real_run(case_id, thread_id, stub)

    monkeypatch.setattr(main, "run", run)
    cli.main([])

    assert worked == ["CLM-1001", "CLM-1002", "CLM-1003"]
    assert capsys.readouterr().out.splitlines() == [
        "CLM-1001  approve  $420.00",
        "CLM-1002  approve  $1,350.00",
        "CLM-1003  refer  $0.00",
        "Worked 3 cases: 2 approve, 1 refer",
    ]
    cases = {c["case_id"]: c for c in client.get("/api/cases").json()}
    assert cases["CLM-1001"]["status"] == "decided"
    assert cases["CLM-1002"]["status"] == "waiting_for_sign_off"


def test_work_queue_reports_failures_and_moves_on(
    monkeypatch, capsys, client, three_waiting
):
    def run(case_id, thread_id):
        client.post(f"/api/cases/{case_id}/start", json={"thread_id": thread_id})
        if case_id == "CLM-1001":
            raise main.BackendError("503: The model is unavailable")
        if case_id == "CLM-1003":
            client.post(
                f"/api/cases/{case_id}/decision",
                json={
                    "decision": "decline",
                    "award": 0,
                    "section": "Section 9",
                    "reason": "Excluded.",
                },
            )
        return "Done."

    monkeypatch.setattr(main, "run", run)
    main.work_queue()

    assert capsys.readouterr().out.splitlines() == [
        "CLM-1001  failed: 503: The model is unavailable",
        "CLM-1002  undecided",
        "CLM-1003  decline  $0.00",
        "Worked 3 cases: 1 decline, 1 failed, 1 undecided",
    ]


def test_work_queue_with_nothing_waiting(capsys, database):
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("UPDATE cases SET status = 'decided'")
    main.work_queue()
    assert capsys.readouterr().out == "Worked 0 cases: none waiting\n"
