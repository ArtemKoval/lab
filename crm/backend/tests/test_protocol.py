"""The pack protocol: the loader's verb gate, the stored outcomes, and the
generic execute route."""

import importlib.util
import sys
import types

import pytest
from sqlalchemy import insert, select

from backend.database import engine, outcomes
from backend.tests.case_requests import decide, line, start, work_out_award
from backend.tests.settings_requests import change_settings
from domains import loader as domain_loader
from domains.insurance import protocol as insurance_protocol
from domains.loader import Pack, PackError, check_declarations

DECLARED = {
    "engine_api": 2,
    "resolutions": ["approve", "decline", "refer"],
    "outcomes": {"award": "resolve"},
    "config": {},
    "effects": {"award": {"outcome": "award", "gated": True, "records": "payments"}},
}

TRIP_DELAY = [
    line("Hotel", 245, "hotel", nights=1),
    line("Meals", 95, "expense"),
    line("Taxis", 80, "expense"),
]

GOOD = '''"""A protocol."""


def resolve(case, config, request):
    raise NotImplementedError


def gate(outcome, config):
    raise NotImplementedError


def execute(case, outcome):
    raise NotImplementedError


def summarize(outcome):
    raise NotImplementedError


def metric(payload):
    raise NotImplementedError
'''


def a_pack(monkeypatch, source: str, tmp_path) -> Pack:
    """A throwaway pack whose protocol module is the given source."""
    root = tmp_path / "protocolcheck"
    root.mkdir()
    (root / "protocol.py").write_text(source)
    package = types.ModuleType("domains.protocolcheck")
    package.__path__ = [str(root)]
    name = "domains.protocolcheck.protocol"
    spec = importlib.util.spec_from_file_location(name, root / "protocol.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setitem(sys.modules, "domains.protocolcheck", package)
    monkeypatch.setitem(sys.modules, name, module)
    return Pack(name="protocolcheck", root=root, manifest={})


def test_the_loader_takes_a_protocol_with_all_five_verbs(monkeypatch, tmp_path):
    module = a_pack(monkeypatch, GOOD, tmp_path).protocol_module()
    verbs = ("resolve", "gate", "execute", "summarize", "metric")
    seen = [callable(getattr(module, verb, None)) for verb in verbs]
    assert seen == [True] * 5


@pytest.mark.parametrize("verb", ["resolve", "gate", "execute", "summarize", "metric"])
def test_the_loader_refuses_a_protocol_that_lacks_a_verb(monkeypatch, verb, tmp_path):
    body = GOOD.replace(f"def {verb}", f"def moved_{verb}")
    with pytest.raises(PackError) as error:
        a_pack(monkeypatch, body, tmp_path).protocol_module()
    assert f"lacks {verb}" in str(error.value)


def test_the_loader_refuses_a_verb_that_is_not_callable(monkeypatch, tmp_path):
    with pytest.raises(PackError) as error:
        a_pack(
            monkeypatch, GOOD + "\n\nresolve = None\n", tmp_path
        ).protocol_module()
    assert "lacks resolve" in str(error.value)


def test_the_declarations_of_a_full_pack_pass():
    check_declarations("tiny", {"name": "tiny", **DECLARED})


def test_an_engine_api_1_pack_needs_no_declarations():
    check_declarations("tiny", {"engine_api": 1})


def test_missing_declarations_are_refused():
    with pytest.raises(PackError) as error:
        check_declarations(
            "tiny",
            {"engine_api": 2, "resolutions": [], "outcomes": {}, "config": {}},
        )
    assert "lacks effects" in str(error.value)


def test_an_outcome_on_an_unknown_verb_is_refused():
    manifest = DECLARED | {"outcomes": {"award": "compute"}}
    with pytest.raises(PackError) as error:
        check_declarations("tiny", manifest)
    assert "unknown verb" in str(error.value)


def test_an_effect_on_an_undeclared_outcome_is_refused():
    manifest = DECLARED | {"effects": {"award": {"outcome": "credit"}}}
    with pytest.raises(PackError) as error:
        check_declarations("tiny", manifest)
    assert "undeclared outcome" in str(error.value)


def test_an_effect_into_an_unknown_write_is_refused():
    manifest = DECLARED | {
        "effects": {"award": {"outcome": "award", "records": "ledger"}}
    }
    with pytest.raises(PackError) as error:
        check_declarations("tiny", manifest)
    assert "unknown write" in str(error.value)


def an_approved_case(client, approval_limit=None):
    """CLM-1001 started, its award worked out, and approved at $420.00."""
    if approval_limit is not None:
        change_settings(client, approval_limit=approval_limit)
    start(client, "CLM-1001")
    work_out_award(client, "CLM-1001", "trip_delay", TRIP_DELAY)
    decide(client, "CLM-1001", "approve", 420.0)


def test_an_effect_runs_once_through_the_pack(client):
    an_approved_case(client)
    response = client.post("/api/cases/CLM-1001/effects/award")
    assert response.status_code == 200
    run = response.json()
    assert (run["case_id"], run["effect"]) == ("CLM-1001", "award")
    assert run["result"] == {"amount": 420.0}
    assert run["ran_at"]
    case = client.get("/api/cases/CLM-1001").json()
    assert (case["status"], case["payment"]["amount"]) == ("decided", 420.0)


def test_a_repeated_effect_is_refused_with_the_recorded_run(client):
    an_approved_case(client)
    client.post("/api/cases/CLM-1001/effects/award")
    repeat = client.post("/api/cases/CLM-1001/effects/award")
    assert repeat.status_code == 409
    assert repeat.json()["detail"] == "Case CLM-1001 already ran the effect 'award'"


def test_an_undeclared_effect_is_refused(client):
    an_approved_case(client)
    missing = client.post("/api/cases/CLM-1001/effects/refund")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "The pack serves no effect called 'refund'"


def test_a_declared_effect_needs_a_resolved_outcome(client):
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "approve", 420.0)
    missing = client.post("/api/cases/CLM-1001/effects/award")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Case CLM-1001 has no resolved outcome 'award'"


def test_only_an_approved_case_runs_an_effect(client):
    start(client, "CLM-1001")
    response = client.post("/api/cases/CLM-1001/effects/award")
    assert response.status_code == 409
    assert response.json()["detail"] == "Case CLM-1001 has not been approved"


def test_a_held_case_runs_no_effect(client):
    an_approved_case(client, approval_limit=400.0)
    case = client.get("/api/cases/CLM-1001").json()
    assert case["status"] == "waiting_for_sign_off"
    response = client.post("/api/cases/CLM-1001/effects/award")
    assert response.status_code == 403
    refused = "An award over $400.00 needs a worker's sign-off"
    assert response.json()["detail"] == refused


def test_a_calculated_award_is_stored_as_one_outcome_payload(client):
    start(client, "CLM-1001")
    work_out_award(client, "CLM-1001", "trip_delay", TRIP_DELAY)
    work_out_award(client, "CLM-1001", "trip_delay", TRIP_DELAY)
    with engine().connect() as db:
        rows = db.execute(
            select(outcomes.c.case_id, outcomes.c.outcome, outcomes.c.payload)
        ).mappings().all()
    assert len(rows) == 1
    assert (rows[0]["case_id"], rows[0]["outcome"]) == ("CLM-1001", "award")
    assert rows[0]["payload"]["award"] == 420.0


def test_an_approval_carries_the_outcome_payload(client):
    an_approved_case(client)
    case = client.get("/api/cases/CLM-1001").json()
    assert case["decision"]["outcome"] == "award"
    assert case["decision"]["payload"]["award"] == 420.0


def test_a_decline_carries_no_outcome(client):
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "decline", 0)
    decision = client.get("/api/cases/CLM-1001").json()["decision"]
    assert (decision["outcome"], decision["payload"]) == (None, None)


def test_an_outcome_over_the_limit_waits_through_the_gate(client):
    an_approved_case(client, approval_limit=400.0)
    case = client.get("/api/cases/CLM-1001").json()
    assert case["status"] == "waiting_for_sign_off"


def test_a_payload_that_does_not_fit_the_gate_is_refused(client):
    start(client, "CLM-1001")
    with engine().begin() as db:
        db.execute(
            insert(outcomes).values(
                case_id="CLM-1001",
                outcome="award",
                payload={"money": 420.0},
                resolved_at="2026-01-01T00:00:00+00:00",
            )
        )
    response = decide(client, "CLM-1001", "approve", 420.0)
    assert response.status_code == 422
    assert "does not fit the pack's gate" in response.json()["detail"]


def test_the_metric_gives_the_number_the_scoring_reads(client):
    assert insurance_protocol.metric({"award": 420.0}) == 420.0


def test_the_pack_serves_its_declarations(client):
    declared = client.get("/api/pack").json()
    assert declared["name"] == "insurance"
    assert declared["resolutions"] == ["approve", "decline", "refer"]
    assert declared["outcomes"] == {"award": "resolve"}
    assert declared["effects"] == {
        "award": {"outcome": "award", "gated": True, "records": "payments"}
    }
    assert "award_approval_limit" in declared["config"]


def test_an_effect_under_another_outcome_name_records_no_payment(client, monkeypatch):
    """A pack that names its outcome differently runs its effect through the
    declarations, and no payment row moves."""
    declared = domain_loader.pack()
    manifest = declared.manifest | {
        "outcomes": {"effort": "resolve"},
        "effects": {"effort": {"outcome": "effort", "gated": True}},
    }
    monkeypatch.setattr(
        domain_loader, "pack", lambda: Pack(declared.name, declared.root, manifest)
    )
    start(client, "CLM-1001")
    work_out_award(client, "CLM-1001", "trip_delay", TRIP_DELAY)
    decide(client, "CLM-1001", "approve", 420.0)
    run = client.post("/api/cases/CLM-1001/effects/effort").json()
    assert run["effect"] == "effort"
    case = client.get("/api/cases/CLM-1001").json()
    assert (case["status"], case["payment"]) == ("decided", None)
    assert run["result"] == {"amount": 420.0}
