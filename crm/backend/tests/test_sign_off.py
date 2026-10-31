"""A worker's sign-off of a held award: it pays the case once, commits, then asks
the agent to resume the case, and stands whatever happens to that call."""

import json
import logging
import threading

import httpx
import pytest

from backend import main
from backend.database import effect_runs
from backend.tests.agent_answers import broken, refusing, slow, unreachable
from backend.tests.case_requests import held, sign_off
from backend.tests.rows import committed_case, count


def test_a_sign_off_pays_the_case_then_asks_the_agent_to_resume_it(
    client, agent_answers
):
    held(client, "CLM-1002", 1350.0)
    calls, seen = [], []

    def accept(request):
        calls.append(json.loads(request.content))
        case = committed_case("CLM-1002")
        seen.append((case["status"], case["signed_off_by"]))
        return httpx.Response(200, json={"accepted": True})

    agent_answers(accept)
    response = sign_off(client, "CLM-1002")
    assert response.status_code == 200
    case = response.json()
    assert case["status"] == "decided"
    assert case["effect"]["result"]["amount"] == 1350.0
    assert case["decision"]["signed_off_by"] == "Dana Whitfield"
    assert case["decision"]["signed_off_at"] is not None
    assert calls == [{"operation": "resume_case", "case_id": "CLM-1002"}]
    assert seen == [("decided", "Dana Whitfield")]


def undecodable(request):
    return httpx.Response(
        200, content=b"x", headers={"Content-Encoding": "unknown-encoding-x"}
    )


@pytest.mark.parametrize("answer", [unreachable, slow, refusing, broken, undecodable])
def test_a_sign_off_stands_whatever_happens_to_the_call(
    client, agent_answers, caplog, answer
):
    held(client, "CLM-1002", 1350.0)
    agent_answers(answer)
    response = sign_off(client, "CLM-1002")
    assert response.status_code == 200
    assert response.json()["effect"]["result"]["amount"] == 1350.0
    assert committed_case("CLM-1002")["status"] == "decided"
    [warning] = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warning.getMessage().startswith("CLM-1002 wasn't resumed: ")


def test_a_sign_off_pays_the_decision_its_move_found(client, monkeypatch):
    held(client, "CLM-1002", 1350.0)
    # The case as read before a send back and a new decision held it again.
    as_read = dict(committed_case("CLM-1002")) | {"award": 1999.0}
    find_case, reads = main.find_case, []

    def first_read_is_old(db, case_id):
        reads.append(case_id)
        return as_read if len(reads) == 1 else find_case(db, case_id)

    monkeypatch.setattr(main, "find_case", first_read_is_old)
    assert sign_off(client, "CLM-1002").json()["effect"]["result"]["amount"] == 1350.0


def test_two_sign_offs_at_the_same_moment_pay_the_case_once(client, agent_calls):
    held(client, "CLM-1002", 1350.0)
    together = threading.Barrier(2)
    answers = []

    def sign():
        together.wait()
        answers.append(sign_off(client, "CLM-1002"))

    signing = [threading.Thread(target=sign) for _ in range(2)]
    for thread in signing:
        thread.start()
    for thread in signing:
        thread.join(10)
    assert sorted(a.status_code for a in answers) == [200, 409]
    [refused] = [a for a in answers if a.status_code == 409]
    assert refused.json()["detail"] == "Case CLM-1002 is not waiting for sign-off"
    assert count(effect_runs) == 1
    assert agent_calls == [{"operation": "resume_case", "case_id": "CLM-1002"}]
