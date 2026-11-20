"""The garage assignment's own records: the smoke run works three cases on
the stub model, the policy documents name the EV gate and the threshold,
the over-limit refusal carries no engine money prefix, and the eval set
covers the assignment rules."""

import json
import subprocess
import sys
from pathlib import Path

from domains import loader

CRM_DIR = Path(__file__).resolve().parents[3]
PACK_DIR = Path(__file__).resolve().parents[1]


def the_garage_pack() -> loader.Pack:
    manifest = json.loads((PACK_DIR / "manifest.json").read_text())
    return loader.Pack(name="garage", root=PACK_DIR, manifest=manifest)


def test_the_smoke_run_works_three_cases():
    """The smoke command seeds a temporary database, works three cases on
    the stub model, and exits 0 with no network and no model key."""
    run = subprocess.run(
        [sys.executable, "smoke.py", "garage"],
        cwd=CRM_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    lines = [
        line for line in run.stdout.splitlines() if line.strip().startswith("JOB-")
    ]
    assert len(lines) == 3


def test_the_wording_names_the_ev_gate():
    wording = (PACK_DIR / "policy" / "wording.md").read_text()
    assert "certified EV mark" in wording
    assert "goes only to a garage with the certified EV mark" in wording
    assert "500 pounds" in wording
    assert "400 pounds" in wording
    assert "900 pounds" in wording


def test_the_manual_names_the_routing_order_and_the_threshold():
    manual = (PACK_DIR / "policy" / "manual.md").read_text()
    brand = manual.find("Brand first")
    specialisms = manual.find("Specialisms next")
    location = manual.find("Location next")
    capacity = manual.find("Queue capacity last")
    assert 0 < brand < specialisms < location < capacity
    assert "600 pounds" in manual
    assert "sign-off" in manual


def test_the_over_limit_refusal_carries_no_money_prefix():
    pack = the_garage_pack()
    message = pack.message("over_limit", "missing")
    assert message != "missing"
    assert "$" not in message
    assert "600" not in message


def test_the_eval_set_covers_the_five_decision_shapes():
    decisions = json.loads((PACK_DIR / "evals" / "decisions.json").read_text())
    shapes = {record["decision"] for record in decisions}
    assert {"approve", "decline", "refer"} <= shapes
    over_limit = [
        record for record in decisions if record["over_approval_limit"]
    ]
    assert over_limit and all(
        record["decision"] == "approve" for record in over_limit
    )
    refer = [record for record in decisions if record["decision"] == "refer"]
    assert refer and all(record["award"] == 0.0 for record in refer)
