"""The pack validator's examinations, against minimal broken-pack fixtures."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate import Examiner  # noqa: E402

GOOD_MANIFEST = {
    "name": "tiny",
    "display_name": "Tiny",
    "engine_api": 1,
    "rules": "rules",
    "settings": {"award_approval_limit": 100.0},
    "documents": ["wording"],
    "seed": {
        "cases": "cases.json",
        "customers": "customers.json",
        "contracts": "contracts.json",
        "workers": "workers.json",
        "company": "company.json",
    },
}

GOOD_RULES = '''"""Tiny rules."""

from backend.models import Award, AwardRequest, CalculationStep, Contract, Plan, Plans


def needs_sign_off(award: float, approval_limit: float) -> bool:
    return award > approval_limit


def work_out_award(
    contract: Contract, plans: Plans, request: AwardRequest, approval_limit: float
) -> Award:
    total = sum(line.amount for line in request.lines)
    award = round(max(total, 0.0), 2)
    return Award(calculation=[], award=award, needs_sign_off=needs_sign_off(award, approval_limit))
'''

GOOD_DOC = """---
source:
  system: Tiny
  owner: Head of Tiny
  reviewed: "2026-10-01"
version: "2026.1"
---

# Tiny wording

## 1. The credit
We credit what the lines carry.
"""

GOOD_CASE = {
    "case_id": "TIN-1",
    "customer_id": "CUS-1",
    "contract_id": "CON-1",
    "case_type": "tiny",
    "submitted_on": "2026-10-01",
    "incident_date": "2026-10-01",
    "incident_location": "remote",
    "summary": "A tiny case",
    "story": "It happened.",
    "items": [{"description": "The thing", "category": "expense", "amount": 50.0}],
    "amount_claimed": 50.0,
    "documents": [],
    "status": "waiting",
}


def make_pack(root: Path, **overrides) -> Path:
    """Write a minimal good pack at root, with the given overrides applied."""
    root.mkdir(parents=True, exist_ok=True)
    manifest = overrides.get("manifest", GOOD_MANIFEST.copy())
    manifest["name"] = root.name
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "rules.py").write_text(overrides.get("rules", GOOD_RULES))
    policy = root / "policy"
    policy.mkdir(parents=True, exist_ok=True)
    (policy / "wording.md").write_text(overrides.get("wording", GOOD_DOC))
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "cases.json").write_text(json.dumps(overrides.get("cases", [GOOD_CASE])))
    (data / "customers.json").write_text(
        json.dumps(
            overrides.get("customers", [{"customer_id": "CUS-1", "name": "Tiny"}])
        )
    )
    (data / "contracts.json").write_text(
        json.dumps(
            overrides.get(
                "contracts", [{"contract_id": "CON-1", "customer_id": "CUS-1"}]
            )
        )
    )
    (data / "workers.json").write_text(
        json.dumps(
            overrides.get(
                "workers",
                [
                    {
                        "worker_id": "W-1",
                        "name": "Lead",
                        "role": "lead",
                        "email": "lead@tiny.example",
                        "can_approve_over_limit": True,
                    }
                ],
            )
        )
    )
    (data / "company.json").write_text(json.dumps({"name": "Tiny"}))
    evals = root / "evals"
    evals.mkdir(parents=True, exist_ok=True)
    (evals / "decisions.json").write_text(
        json.dumps(
            overrides.get(
                "evals",
                [
                    {
                        "case_id": "TIN-1",
                        "decision": "decline",
                        "award": 0,
                        "reason": "r",
                        "worker_id": "W-1",
                    }
                ],
            )
        )
    )
    instructions = root / "instructions"
    instructions.mkdir(parents=True, exist_ok=True)
    (instructions / "case.md").write_text(
        overrides.get("case_md", "Use get_case. Use record_decision.")
    )
    return root


def findings_for(root: Path) -> dict[str, list[str]]:
    examiner = Examiner(root.name)
    examiner.root = root
    findings = examiner.examine()
    grouped: dict[str, list[str]] = {}
    for finding in findings:
        grouped.setdefault(finding.file, []).append(finding.message)
    return grouped


def test_a_good_pack_is_clean(tmp_path):
    make_pack(tmp_path / "tiny")
    assert findings_for(tmp_path / "tiny") == {}


def test_a_manifest_name_mismatch_is_named(tmp_path):
    make_pack(tmp_path / "tiny")
    (tmp_path / "tiny" / "manifest.json").write_text(
        json.dumps({**GOOD_MANIFEST, "name": "other"})
    )
    assert "does not match" in findings_for(tmp_path / "tiny")["manifest.json"][0]


def test_a_missing_manifest_key_is_named(tmp_path):
    manifest = GOOD_MANIFEST.copy()
    del manifest["documents"]
    make_pack(tmp_path / "tiny", manifest=manifest)
    assert any(
        "documents" in message
        for message in findings_for(tmp_path / "tiny")["manifest.json"]
    )


def test_a_rules_signature_drift_is_named(tmp_path):
    make_pack(
        tmp_path / "tiny",
        rules=GOOD_RULES.replace("award: float, approval_limit: float", "award: float"),
    )
    assert any(
        "needs_sign_off" in message
        for message in findings_for(tmp_path / "tiny")["rules.py"]
    )


def test_a_document_without_front_matter_is_named(tmp_path):
    make_pack(tmp_path / "tiny", wording="# Tiny wording\n\nNo front matter.\n")
    assert any(
        "front matter" in message
        for message in findings_for(tmp_path / "tiny")["policy/wording.md"]
    )


def test_a_missing_seed_reference_is_named(tmp_path):
    case = {**GOOD_CASE, "customer_id": "CUS-404"}
    make_pack(tmp_path / "tiny", cases=[case])
    findings = findings_for(tmp_path / "tiny")["data/cases.json"]
    assert any("CUS-404" in message for message in findings)


def test_an_illegal_eval_decision_is_named(tmp_path):
    make_pack(
        tmp_path / "tiny", evals=[{"case_id": "TIN-1", "decision": "maybe", "award": 0}]
    )
    assert any(
        "maybe" in message
        for message in findings_for(tmp_path / "tiny")["evals/decisions.json"]
    )


def test_an_upstream_tool_name_in_instructions_is_named(tmp_path):
    make_pack(tmp_path / "tiny", case_md="Use work_claim to take the case.")
    findings = findings_for(tmp_path / "tiny")["instructions/case.md"]
    assert any("work_claim" in message for message in findings)


def test_a_domain_noun_in_a_file_name_is_named(tmp_path):
    root = make_pack(tmp_path / "tiny")
    (root / "data" / "claims.json").write_text("[]")
    assert any(
        "claims.json" in message for message in findings_for(root)["data/claims.json"]
    )
