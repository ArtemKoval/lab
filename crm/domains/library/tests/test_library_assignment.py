"""The library assignment's own records: the smoke run works three cases on
the stub model, the policy documents name the cap and the threshold, the
eval set covers the assignment rules, and the over-limit refusal speaks
days."""

import json
import subprocess
import sys
from pathlib import Path

from domains import loader

CRM_DIR = Path(__file__).resolve().parents[3]
PACK_DIR = Path(__file__).resolve().parents[1]


def the_library_pack() -> loader.Pack:
    manifest = json.loads((PACK_DIR / "manifest.json").read_text())
    return loader.Pack(name="library", root=PACK_DIR, manifest=manifest)


def test_the_smoke_run_works_three_cases():
    """The smoke command seeds a temporary database, works three cases on
    the stub model, and exits 0 with no network and no model key."""
    run = subprocess.run(
        [sys.executable, "smoke.py", "library"],
        cwd=CRM_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "smoke clean" in run.stdout


def test_the_wording_names_the_loan_cap():
    wording = (PACK_DIR / "policy" / "wording.md").read_text()
    assert "A borrower holds at most 3 loans at the same time" in wording
    assert "14 days" in wording


def test_the_manual_names_the_sign_off_threshold():
    manual = (PACK_DIR / "policy" / "manual.md").read_text()
    assert "approves loans of 14 days or fewer" in manual
    assert (
        "A loan term over 14 days needs the lead librarian's sign-off"
        in manual
    )


def test_the_eval_set_covers_the_assignment_rules():
    decisions = json.loads(
        (PACK_DIR / "evals" / "decisions.json").read_text()
    )
    kinds = {record["decision"] for record in decisions}
    assert {"approve", "decline", "refer"} <= kinds
    assert any(record["over_approval_limit"] for record in decisions)
    assert any(record["award"] == 14.0 for record in decisions)


def test_the_over_limit_refusal_names_days():
    """The pack's over-limit message fills its limit slot with the award
    text in days, so the refusal reads a term, not a dollar figure."""
    pack = the_library_pack()
    limit = 14
    words = pack.message(
        "over_limit",
        "An award over {limit} needs a worker's sign-off",
    ).replace("{limit}", pack.award_text(limit))
    assert "14 days" in words
    assert "$" not in words
