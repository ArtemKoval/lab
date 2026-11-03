"""Tests for the Gate 5 certification ledger: the pins digest, the
record append, the drift comparison, and the CLI commands."""

import json

from dspy_gate import certs, cli

POLICY = "version: 1\nmodels:\n  roles:\n    runtime: {model: glm-5.3-flash}\n"


def write_policy(tmp_path):
    (tmp_path / "tools" / "dspy_gate").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tools" / "dspy_gate" / "gates.yaml").write_text(POLICY, encoding="utf-8")


def test_the_digest_is_stable_and_covers_the_roles():
    first = certs.pins_digest(POLICY)
    second = certs.pins_digest(POLICY)
    assert first == second
    assert len(first) == 12


def test_the_digest_moves_when_a_pin_moves():
    assert certs.pins_digest(POLICY) != certs.pins_digest(
        POLICY.replace("glm-5.3-flash", "glm-5.3")
    )


def test_record_appends_one_row(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins="abc123", source="delta suite", green=True)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["pins"] == "abc123"
    assert rows[0]["green"] is True


def test_drift_passes_when_the_last_row_carries_the_current_pins(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins=certs.pins_digest(POLICY), source="delta suite", green=True)
    assert certs.drift(path, certs.pins_digest(POLICY)) == []


def test_drift_names_a_stale_digest(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins="old-pins", source="delta suite", green=True)
    found = certs.drift(path, certs.pins_digest(POLICY))
    assert len(found) == 1
    assert "old-pins" in found[0]


def test_drift_passes_when_no_ledger_exists_yet(tmp_path):
    path = tmp_path / "certs" / "absent.jsonl"
    assert certs.drift(path, certs.pins_digest(POLICY)) == []


def test_drift_names_a_red_last_row(tmp_path):
    path = tmp_path / "certs" / "triage.jsonl"
    certs.record(path, pins=certs.pins_digest(POLICY), source="delta suite", green=False)
    found = certs.drift(path, certs.pins_digest(POLICY))
    assert len(found) == 1
    assert "red" in found[0]


def make_repo(tmp_path):
    root = tmp_path / "repo"
    change = root / "openspec" / "changes" / "demo" / "specs" / "triage"
    change.mkdir(parents=True)
    (change / "spec.md").write_text(
        "## ADDED Requirements\n\n### Requirement: Triage\n\n"
        "#### Scenario: Outage routes to on-call [surface: dspy-eval]\n"
        "- **WHEN** the ticket arrives\n- **THEN** severity = P0\n",
        encoding="utf-8",
    )
    tool = root / "tools" / "dspy_gate"
    tool.mkdir(parents=True)
    (tool / "gates.yaml").write_text(
        "version: 1\nmodels:\n  roles:\n    runtime: {model: glm-5.3-flash}\n"
        "policy_bounds:\n  tier_b_min: {min: 0.6, max: 1.0}\n"
        "capabilities:\n  triage:\n    gate_2: {tier_a: 1.0, tier_b_min: 0.8}\n",
        encoding="utf-8",
    )
    return root


def test_certify_records_the_ledger_after_a_green_run(tmp_path, capsys, monkeypatch):
    from test_gate_cli import run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["--json", "certify", "demo"], root, monkeypatch) == 0
    ledger = root / "tools" / "dspy_gate" / "certs" / "triage.jsonl"
    row = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert row["green"] is True


def test_pin_drift_passes_after_a_certification(tmp_path, capsys, monkeypatch):
    from test_gate_cli import run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    run(["certify", "demo"], root, monkeypatch)
    capsys.readouterr()
    assert run(["pin-drift"], root, monkeypatch) == 0


def test_pin_drift_fails_on_a_stale_ledger(tmp_path, capsys, monkeypatch):
    from test_gate_cli import run

    root = make_repo(tmp_path)
    run(["regen", "demo"], root, monkeypatch)
    run(["certify", "demo"], root, monkeypatch)
    capsys.readouterr()
    gates = root / "tools" / "dspy_gate" / "gates.yaml"
    gates.write_text(
        gates.read_text(encoding="utf-8").replace("glm-5.3-flash", "glm-5.3-air"),
        encoding="utf-8",
    )
    assert run(["pin-drift"], root, monkeypatch) == 2
    assert "stale" in capsys.readouterr().out
