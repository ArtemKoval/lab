"""The Northgate pack's own tests: the manifest, the loader, the seed
records against the engine models, the evals, and the instructions."""

import json
import os
import re
import sys
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def in_the_library_domain():
    """Run with the pack active, and put the variable back after."""
    saved = os.environ.get("CRM_DOMAIN")
    os.environ["CRM_DOMAIN"] = "library"
    yield
    if saved is None:
        os.environ.pop("CRM_DOMAIN", None)
    else:
        os.environ["CRM_DOMAIN"] = saved


def test_the_manifest_declares_the_pack():
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert manifest["name"] == "library"
    assert manifest["engine_api"] == 2
    assert manifest["display_name"] == "Northgate Public Library"
    assert manifest["outcomes"] == {"loan": "resolve"}
    assert manifest["effects"]["loan"]["gated"] is True
    assert manifest["settings"]["award_approval_limit"] == 14.0
    assert manifest["documents"] == ["wording", "manual"]


def load_the_engine_loader():
    """Load the engine's pack loader by path. The copy root carries it in a
    normal run, and the working directory carries it under the mutation
    runner, whose tree mirrors the pack only."""
    import importlib.util

    for base in (Path.cwd(), *PACK.parents):
        path = base / "domains" / "loader.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("library_loader", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["library_loader"] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("loader.py not found beside the pack")


def test_the_loader_loads_the_pack():
    loader = load_the_engine_loader()
    pack = loader.pack()
    assert pack.name == "library"
    assert pack.settings["award_approval_limit"] == 14.0
    assert pack.load_eval is not None


def _records(name):
    return json.loads((PACK / "data" / f"{name}.json").read_text())


ENGINE_CASE_DEFAULTS = dict(
    customer_name="Test Borrower",
    thread_id=None,
    attempts=0,
    evaluation_id=None,
    copy_of=None,
    decision=None,
    sent_back_decisions=[],
)


def test_every_seed_contract_fits_the_engine_model():
    from backend.models import Contract

    for record in _records("contracts") + _records("security/contracts"):
        assert Contract(**record).contract_id


def test_every_seed_case_fits_the_engine_model():
    from backend.models import Case

    for record in _records("cases") + _records("security/cases"):
        assert Case(**record, **ENGINE_CASE_DEFAULTS).case_id


def test_every_seed_customer_carries_earlier_cases_that_fit():
    from backend.models import PreviousCase

    for record in _records("customers") + _records("security/customers"):
        for earlier in record["previous_cases"]:
            assert PreviousCase(**earlier).case_id


def test_every_queued_case_has_a_pinned_decision():
    decisions = json.loads((PACK / "evals" / "decisions.json").read_text())
    pinned = {record["case_id"] for record in decisions}
    queued = {record["case_id"] for record in _records("cases")}
    assert queued <= pinned


def test_every_decision_record_carries_the_seed_read_keys():
    decisions = json.loads((PACK / "evals" / "decisions.json").read_text())
    seed_reads = {"case_id", "decision", "award", "tiny", "reason", "reference"}
    for record in decisions:
        assert seed_reads <= set(record)


def test_no_held_out_case_names_a_queued_case():
    held = json.loads((PACK / "evals" / "held_out_cases.json").read_text())
    held_ids = {record["case_id"] for record in held}
    queued = {record["case_id"] for record in _records("cases")}
    queued |= {record["case_id"] for record in _records("security/cases")}
    assert held_ids.isdisjoint(queued)


def test_the_instructions_name_served_tools_only():
    from validate import SERVED_TOOLS

    tokens = set()
    for name in ("case.md", "queue.md", "recipe.md", "improver.md"):
        text = (PACK / "instructions" / name).read_text()
        tokens |= set(re.findall(r"`([a-z]+_[a-z_]+)`", text))
    assert tokens <= set(SERVED_TOOLS)


def test_the_examiner_raises_no_finding():
    from validate import Examiner

    findings = Examiner("library").examine()
    assert [str(finding) for finding in findings] == []
