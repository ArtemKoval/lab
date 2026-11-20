"""The AutoFix pack's own tests: the manifest, the loader, the seed
records against the engine models, the evals, the instructions, the
examiner, and the fleet match."""

import json
import os
import re
import sys
from pathlib import Path

import yaml

import pytest

PACK = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def in_the_garage_domain():
    """Run with the pack active, and put the variable back after."""
    saved = os.environ.get("CRM_DOMAIN")
    os.environ["CRM_DOMAIN"] = "garage"
    yield
    if saved is None:
        os.environ.pop("CRM_DOMAIN", None)
    else:
        os.environ["CRM_DOMAIN"] = saved


def test_the_manifest_declares_the_pack():
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert manifest["name"] == "garage"
    assert manifest["engine_api"] == 2
    assert manifest["display_name"] == "AutoFix Vehicle Repair"
    assert manifest["outcomes"] == {"authorization": "resolve"}
    assert manifest["effects"]["authorization"]["gated"] is True
    assert manifest["settings"]["award_approval_limit"] == 600.0
    assert manifest["documents"] == ["wording", "manual"]


def load_the_engine_loader():
    """Load the engine's pack loader by path. The copy root carries it in a
    normal run, and the working directory carries it under the mutation
    runner, whose tree mirrors the pack only."""
    import importlib.util

    for base in (Path.cwd(), *PACK.parents):
        path = base / "domains" / "loader.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("garage_loader", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["garage_loader"] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("loader.py not found beside the pack")


def test_the_loader_loads_the_pack():
    loader = load_the_engine_loader()
    pack = loader.pack()
    assert pack.name == "garage"
    assert pack.settings["award_approval_limit"] == 600.0
    assert pack.load_eval is not None


def _records(name):
    return json.loads((PACK / "data" / f"{name}.json").read_text())


ENGINE_CASE_DEFAULTS = dict(
    customer_name="Test Customer",
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


def test_the_eval_set_covers_the_five_decision_shapes():
    decisions = json.loads((PACK / "evals" / "decisions.json").read_text())
    by_id = {record["case_id"]: record for record in decisions}
    assert by_id["JOB-1001"]["decision"] == "approve"
    assert by_id["JOB-1006"]["decision"] == "decline"
    assert by_id["JOB-1007"]["decision"] == "decline"
    assert by_id["JOB-1008"]["decision"] == "refer"
    assert by_id["JOB-1005"]["decision"] == "approve"
    assert by_id["JOB-1005"]["over_approval_limit"] is True


def test_the_instructions_name_served_tools_only():
    from validate import SERVED_TOOLS

    tokens = set()
    for name in ("case.md", "queue.md", "recipe.md", "improver.md"):
        text = (PACK / "instructions" / name).read_text()
        tokens |= set(re.findall(r"`([a-z]+_[a-z_]+)`", text))
    assert tokens <= set(SERVED_TOOLS)


def test_the_examiner_raises_no_finding():
    from validate import Examiner

    findings = Examiner("garage").examine()
    assert [str(finding) for finding in findings] == []


def _fleet_facts():
    reference = yaml.safe_load(
        (PACK / "context" / "reference_data.yaml").read_text()
    )
    topics = {topic["topic"]: topic for topic in reference["topics"]}
    return [
        fact
        for fact in topics["garage network"]["facts"]
    ]


def _fleet_garages():
    garages = []
    for fact in _fleet_facts():
        name = fact.split(" in ")[0]
        city = fact.split(" in ")[1].split(" services")[0]
        certified = "certified EV yes" in fact
        garages.append({"name": name, "city": city, "certified_ev": certified})
    return garages


def test_every_seed_case_matches_a_fleet_garage_in_its_city():
    cases = _records("cases")
    garages = _fleet_garages()
    cities = {garage["city"] for garage in garages}
    for case in cases:
        city = case["incident_location"]
        assert city in cities, f"{case['case_id']} names the unserved city {city}"


def _list(chunk):
    """Split one Oxford-comma fact list into its clean items."""
    items = chunk.replace(", and ", ", ").replace(" and ", ", ").split(",")
    return [item.strip() for item in items if item.strip()]


def _fleet_garages_full():
    """The fleet facts, parsed to name, city, brands, specialisms, and the
    certified EV mark."""
    garages = []
    for fact in _fleet_facts():
        name = fact.split(" in ")[0]
        city = fact.split(" in ")[1].split(" services")[0]
        brands = _list(fact.split(" services ")[1].split("; specialisms ")[0])
        specialisms = _list(
            fact.split("; specialisms ")[1].split("; certified EV")[0]
        )
        certified = "certified EV yes" in fact
        garages.append(
            {
                "name": name,
                "city": city,
                "brands": brands,
                "specialisms": specialisms,
                "certified_ev": certified,
            }
        )
    return garages


def _decisions_by_id():
    decisions = json.loads((PACK / "evals" / "decisions.json").read_text())
    return {record["case_id"]: record for record in decisions}


def _case_make(case):
    contracts = {c["contract_id"]: c for c in _records("contracts")}
    return contracts[case["contract_id"]]["trip"]["destination"]


def test_every_approved_case_matches_a_local_garage_on_make_and_specialisms():
    decisions = _decisions_by_id()
    garages = _fleet_garages_full()
    for case in _records("cases"):
        if decisions[case["case_id"]]["decision"] != "approve":
            continue
        make = _case_make(case)
        categories = {item["category"] for item in case["items"]}
        city = case["incident_location"]
        match = any(
            garage["city"] == city
            and make in garage["brands"]
            and categories <= set(garage["specialisms"])
            for garage in garages
        )
        assert match, (
            f"{case['case_id']} finds no garage in {city} for {make} "
            f"with {sorted(categories)}"
        )


def test_the_referred_ev_case_finds_no_certified_garage_in_its_city():
    garages = _fleet_garages_full()
    case = next(c for c in _records("cases") if c["case_id"] == "JOB-1008")
    local = [g for g in garages if g["city"] == case["incident_location"]]
    certified = [g for g in local if g["certified_ev"]]
    assert certified == [], "JOB-1008 needs the certified gap in Birmingham"


def test_the_agreement_card_names_no_engine_word():
    manifest = json.loads((PACK / "manifest.json").read_text())
    card = manifest["vocabulary"]["contract"]
    assert card["title"] == "Agreement"
    labels = [row["label"] for row in card["rows"]]
    assert labels == [
        "Agreement",
        "Tier",
        "Covered vehicle",
        "Vehicle make",
        "First registered",
        "Service due",
        "Purchased",
        "Sold through",
    ]
    for word in ("plan", "add-ons", "trip", "travelers"):
        assert all(word not in label.lower() for label in labels), word


def test_the_seed_records_carry_the_pinned_counts():
    from backend.models import Worker

    workers = _records("workers")
    for record in workers:
        assert Worker(**record).worker_id
    assert len(workers) == 2
    assert sum(1 for w in workers if w["can_approve_over_limit"]) == 1
    assert len(_records("customers")) == 6
    cases = _records("cases")
    assert len(cases) == 8
    assert all(case["status"] == "waiting" for case in cases)
    tiers = {c["plan"] for c in _records("contracts")}
    assert {"standard", "ev", "fleet"} <= tiers
