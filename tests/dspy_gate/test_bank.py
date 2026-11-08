"""Tests for the example bank: judge-gated writes, eviction on
regression, and similarity retrieval."""

from dspy_gate import bank


def entry(
    scenario_id="outage-keywords-route-to-on-call",
    verdicts=None,
    inputs=None,
    prediction=None,
):
    return {
        "scenario_id": scenario_id,
        "inputs": inputs or {"ticket": "production down"},
        "prediction": prediction or {"severity": "P0", "team": "on-call"},
        "trace": [{"tool": "escalate"}, {"step": "reply"}],
        "gate_verdicts": verdicts or {"A": True, "C": True},
    }


def test_a_green_trajectory_enters_the_bank(tmp_path):
    path = tmp_path / "bank.jsonl"
    assert bank.write(path, entry()) is True
    assert bank.read_all(path)[0]["scenario_id"] == "outage-keywords-route-to-on-call"


def test_a_red_trajectory_stays_out(tmp_path):
    path = tmp_path / "bank.jsonl"
    assert bank.write(path, entry(verdicts={"A": True, "C": False})) is False
    assert bank.read_all(path) == []


def test_a_regressed_entry_leaves_the_bank(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(path, entry())
    bank.write(path, entry(scenario_id="billing-disputes-route-to-billing"))
    bank.evict(path, "outage-keywords-route-to-on-call")
    ids = [e["scenario_id"] for e in bank.read_all(path)]
    assert ids == ["billing-disputes-route-to-billing"]


def test_retrieval_returns_the_most_similar_first(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(path, entry())
    bank.write(
        path,
        entry(
            scenario_id="billing-disputes-route-to-billing",
            verdicts={"A": True},
            inputs={"ticket": "refund the June charge, invoice looks wrong"},
            prediction={"severity": "P2", "team": "billing"},
        ),
    )
    hits = bank.retrieve(path, "refund the June charge invoice", k=1)
    assert hits[0]["scenario_id"] == "billing-disputes-route-to-billing"


def test_retrieve_holds_the_union_floor_on_empty_text(tmp_path):
    path = tmp_path / "bank.jsonl"
    path.write_text('{"scenario_id": "bare-entry"}\n', encoding="utf-8")
    assert bank.retrieve(path, "") == [{"scenario_id": "bare-entry"}]


def test_retrieve_orders_equal_overlaps_by_union_size(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(
        path,
        entry(
            scenario_id="wide-entry",
            inputs="alpha beta gamma delta",
            prediction="",
        ),
    )
    bank.write(
        path,
        entry(scenario_id="exact-entry", inputs="alpha beta", prediction=""),
    )
    hits = bank.retrieve(path, "alpha beta")
    assert [hit["scenario_id"] for hit in hits] == ["exact-entry", "wide-entry"]


def test_the_bank_file_holds_one_json_object_per_line(tmp_path):
    path = tmp_path / "bank.jsonl"
    bank.write(path, entry())
    bank.write(path, entry(scenario_id="billing-disputes-route-to-billing"))
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert all(line.startswith("{") for line in lines)
