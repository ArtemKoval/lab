"""Tests of the domain pack loader, the one seam to the packs."""

import json
import shutil
from pathlib import Path

import pytest

from domains import loader


@pytest.fixture(autouse=True)
def insurance(monkeypatch):
    """Point every test at the insurance pack."""
    monkeypatch.delenv("CRM_DOMAIN", raising=False)


def test_the_default_pack_is_insurance():
    active = loader.pack()
    assert active.name == "insurance"
    assert active.root.name == "insurance"
    assert active.manifest["name"] == "insurance"


def test_crm_domain_names_the_pack(monkeypatch):
    monkeypatch.setenv("CRM_DOMAIN", "insurance")
    assert loader.pack().name == "insurance"


def test_the_pack_serves_its_settings():
    active = loader.pack()
    assert active.settings["award_approval_limit"] == 1000.0


def test_the_pack_reads_its_data_and_documents():
    active = loader.pack()
    cases = active.load_json("cases.json")
    assert isinstance(cases, list)
    assert cases
    assert "## 11. How to claim" in active.read_doc("wording")
    assert active.instruction("queue").startswith("#")


def test_a_missing_data_file_names_the_file():
    active = loader.pack()
    with pytest.raises(loader.PackError, match="missing pack file"):
        active.load_json("absent.json")


def test_a_missing_document_names_the_file():
    active = loader.pack()
    with pytest.raises(loader.PackError, match="missing pack document"):
        active.read_doc("absent")


def test_a_missing_instruction_names_the_file():
    active = loader.pack()
    with pytest.raises(loader.PackError, match="missing pack instruction"):
        active.instruction("absent")


def test_an_unknown_pack_names_the_manifest(monkeypatch):
    monkeypatch.setenv("CRM_DOMAIN", "absent")
    with pytest.raises(loader.PackError, match="missing pack manifest"):
        loader.pack()


def test_a_manifest_name_must_match_its_folder(monkeypatch, tmp_path):
    pack_dir = loader.DOMAINS / "misnamed"
    pack_dir.mkdir()
    (pack_dir / "manifest.json").write_text('{"name": "other"}', encoding="utf-8")
    try:
        monkeypatch.setenv("CRM_DOMAIN", "misnamed")
        with pytest.raises(loader.PackError, match="does not match folder"):
            loader.pack()
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def _write_vocabulary_pack(tmp_path, vocabulary):
    """A pack folder over the insurance declarations, with the vocabulary given."""
    base = loader.pack()
    manifest = {
        "name": "vocabtest",
        "engine_api": 2,
        "resolutions": base.manifest["resolutions"],
        "outcomes": base.manifest["outcomes"],
        "config": base.manifest["config"],
        "effects": base.manifest["effects"],
    }
    if vocabulary is not None:
        manifest["vocabulary"] = vocabulary
    pack_dir = loader.DOMAINS / "vocabtest"
    shutil.rmtree(pack_dir, ignore_errors=True)
    pack_dir.mkdir()
    (pack_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return pack_dir


def test_a_pack_with_no_vocabulary_section_loads(monkeypatch, tmp_path):
    pack_dir = _write_vocabulary_pack(tmp_path, None)
    try:
        monkeypatch.setenv("CRM_DOMAIN", "vocabtest")
        assert loader.pack().manifest.get("vocabulary") is None
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def test_an_unknown_award_format_is_refused(monkeypatch, tmp_path):
    vocabulary = {"labels": {}, "award_format": "pages"}
    pack_dir = _write_vocabulary_pack(tmp_path, vocabulary)
    try:
        monkeypatch.setenv("CRM_DOMAIN", "vocabtest")
        with pytest.raises(loader.PackError, match="award_format"):
            loader.pack()
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def test_an_unknown_row_format_is_refused(monkeypatch, tmp_path):
    vocabulary = {
        "contract": {"title": "X", "rows": [{"label": "L", "field": "f", "format": "verse"}]},
    }
    pack_dir = _write_vocabulary_pack(tmp_path, vocabulary)
    try:
        monkeypatch.setenv("CRM_DOMAIN", "vocabtest")
        with pytest.raises(loader.PackError, match="format"):
            loader.pack()
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def test_a_row_with_neither_field_nor_template_is_refused(monkeypatch, tmp_path):
    vocabulary = {"contract": {"title": "X", "rows": [{"label": "L"}]}}
    pack_dir = _write_vocabulary_pack(tmp_path, vocabulary)
    try:
        monkeypatch.setenv("CRM_DOMAIN", "vocabtest")
        with pytest.raises(loader.PackError, match="neither a field nor a template"):
            loader.pack()
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def test_a_vocabulary_with_all_four_keys_loads(monkeypatch, tmp_path):
    vocabulary = {
        "labels": {"case.incident": "Received at"},
        "contract": {
            "title": "Membership",
            "rows": [{"label": "Card", "field": "contract_id", "format": "text"}],
        },
        "award_format": "days",
        "messages": {"over_limit": "x", "contract_not_found": "y", "senior": "z", "cant_sign_off": "w"},
    }
    pack_dir = _write_vocabulary_pack(tmp_path, vocabulary)
    try:
        monkeypatch.setenv("CRM_DOMAIN", "vocabtest")
        assert loader.pack().manifest["vocabulary"]["award_format"] == "days"
    finally:
        (pack_dir / "manifest.json").unlink()
        pack_dir.rmdir()


def test_the_pack_rules_module_matches_the_contract():
    """The pack carries the deterministic rules under the engine's contract."""
    import inspect

    rules = loader.pack().rules_module()
    work = inspect.signature(rules.work_out_award)
    assert list(work.parameters) == ["contract", "plans", "request", "approval_limit"]
    sign_off = inspect.signature(rules.needs_sign_off)
    assert list(sign_off.parameters) == ["award", "approval_limit"]


def test_the_days_award_text_drops_the_trailing_zero():
    pack = loader.Pack(
        name="days",
        root=Path("."),
        manifest={"vocabulary": {"award_format": "days"}},
    )
    assert pack.award_text(14.5) == "14.5 days"
    assert pack.award_text(14) == "14 days"


def test_the_money_award_text_keeps_the_cents():
    pack = loader.Pack(name="money", root=Path("."), manifest={})
    assert pack.award_text(1500) == "$1,500.00"


def test_a_contract_without_a_title_is_refused():
    with pytest.raises(loader.PackError, match="carries no title"):
        loader.check_vocabulary("p", {"vocabulary": {"contract": {"rows": []}}})


def test_a_malformed_contract_shape_is_refused_with_a_pack_error():
    with pytest.raises(loader.PackError, match="not an object"):
        loader.check_vocabulary("p", {"vocabulary": {"contract": "cards"}})
    with pytest.raises(loader.PackError, match="not a list"):
        loader.check_vocabulary(
            "p", {"vocabulary": {"contract": {"title": "T", "rows": "many"}}}
        )
    with pytest.raises(loader.PackError, match="not an object"):
        loader.check_vocabulary(
            "p",
            {"vocabulary": {"contract": {"title": "T", "rows": ["plain"]}}},
        )


def test_a_null_contract_and_null_rows_load_with_no_words():
    loader.check_vocabulary("p", {"vocabulary": {"contract": None}})
    loader.check_vocabulary(
        "p", {"vocabulary": {"contract": {"title": "T", "rows": None}}}
    )
