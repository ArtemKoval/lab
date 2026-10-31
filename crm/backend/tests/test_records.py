"""A complete decision record, as cases manual section 14 asks: the outcome the
pack resolved for the attempt, who or what made the decision, when, and the
manual's version."""

from pathlib import Path

import pytest
import yaml

from backend.database import decisions
from backend.models import Decision
from backend.tests.case_requests import (
    MAKER,
    decide,
    fail,
    line,
    record_decision,
    resolve_outcome,
    sign_off,
    start,
)
from backend.tests.rows import count
from backend.tests.settings_requests import change_settings


def work_out(client, case_id, amount=293.0):
    """Resolve an emergency medical outcome on a case from one bill."""
    body = {
        "benefit": "emergency_medical",
        "lines": [line("Hospital bill", amount, "expense")],
        "paid_by_others": 0,
    }
    return resolve_outcome(client, case_id, "award", body)


def record(client, case_id, **changes):
    """Ask to record an approval of the outcome on file, unless told otherwise."""
    approval = {"decision": "approve"} | changes
    return record_decision(client, case_id, **approval)


def test_a_new_attempt_starts_with_no_outcome(client):
    start(client, "CLM-1005")
    work_out(client, "CLM-1005")
    fail(client, "CLM-1005")
    client.post("/api/cases/CLM-1005/start", json={"thread_id": "t-2"})
    response = record(client, "CLM-1005")
    assert response.status_code == 422
    assert count(decisions) == 0
    assert response.json()["detail"] == (
        "Cases manual section 14: an approval needs the outcome the pack "
        "resolved for this attempt. Work it out with resolve_outcome"
    )


def test_only_a_case_in_progress_has_its_award_worked_out(client):
    start(client, "CLM-1005")
    fail(client, "CLM-1005")
    response = work_out(client, "CLM-1005")
    assert response.status_code == 409
    assert response.json()["detail"] == "Case CLM-1005 is not in progress"


def test_a_repeated_approval_is_returned_before_its_calculation_is_checked(client):
    start(client, "CLM-1005")
    work_out(client, "CLM-1005")
    first = record(client, "CLM-1005").json()
    work_out(client, "CLM-1005", 593.0)
    again = record(client, "CLM-1005")
    assert again.status_code == 200
    assert again.json() == first


def test_a_case_never_started_has_no_outcome(client):
    response = work_out(client, "CLM-1005")
    assert response.status_code == 409
    assert response.json()["detail"] == "Case CLM-1005 has not been started"


@pytest.mark.parametrize(
    ("changes", "missing"),
    [
        ({"reason": " "}, "a decision record needs a reason in plain language"),
        ({"section": ""}, "a decision record needs the section relied on"),
        (
            {"decided_by": ""},
            "a decision record needs who or what made the decision",
        ),
    ],
)
@pytest.mark.parametrize("case_id", ["CLM-1005", "CLM-9999"])
def test_a_record_that_falls_short_is_refused_before_the_case_is_read(
    client, changes, missing, case_id
):
    start(client, "CLM-1005")
    work_out(client, "CLM-1005")
    response = record(client, case_id, **changes)
    assert response.status_code == 422
    assert response.json()["detail"] == f"Cases manual section 14: {missing}"
    assert count(decisions) == 0


def test_a_decision_outside_the_three_is_pydantics_refusal(client):
    start(client, "CLM-1005")
    response = record(client, "CLM-1005", decision="maybe")
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_an_approval_needs_the_outcome_on_file(client):
    start(client, "CLM-1005")
    refused = record(client, "CLM-1005")
    assert refused.status_code == 422
    assert refused.json()["detail"] == (
        "Cases manual section 14: an approval needs the outcome the pack "
        "resolved for this attempt. Work it out with resolve_outcome"
    )
    work_out(client, "CLM-1005")
    assert record(client, "CLM-1005").status_code == 200
    assert count(decisions) == 1


def test_a_complete_approval(client):
    start(client, "CLM-1005")
    resolved = work_out(client, "CLM-1005").json()
    decision = record(client, "CLM-1005").json()["decision"]
    assert decision["payload"] == resolved
    assert [line["step"] for line in decision["payload"]["calculation"]][-1] == (
        "Less the deductible"
    )
    assert decision["decided_by"] == MAKER
    assert decision["decided_at"]
    assert decision["manual_version"] == "2026.2"


@pytest.mark.parametrize("kind", ["decline", "refer"])
def test_a_decline_or_a_referral_holds_no_outcome(client, kind):
    start(client, "CLM-1003")
    decision = decide(client, "CLM-1003", kind, 0).json()["decision"]
    assert (decision["outcome"], decision["payload"]) == (None, None)
    assert (decision["decided_by"], decision["manual_version"]) == (MAKER, "2026.2")


def test_a_sign_off_adds_who_signed_off_and_when(client):
    change_settings(client, approval_limit=100.0)
    start(client, "CLM-1005")
    work_out(client, "CLM-1005")
    record(client, "CLM-1005")
    decision = sign_off(client, "CLM-1005").json()["decision"]
    assert decision["signed_off_by"] == "Dana Whitfield"
    assert decision["signed_off_at"]
    assert decision["payload"]["award"] == 243.0


def test_the_record_holds_every_field_the_data_dictionary_names():
    dictionary = (
        Path(__file__).parents[2]
        / "domains"
        / "insurance"
        / "context"
        / "data_dictionary.yaml"
    ).read_text(encoding="utf-8")
    [case] = [r for r in yaml.safe_load(dictionary)["records"] if r["record"] == "case"]
    named = {
        field["field"].removeprefix("decision.")
        for field in case["fields"]
        if field["field"].startswith("decision.")
    }
    assert named <= set(Decision.model_fields)
    assert {"payload", "decided_by", "manual_version"} <= named
