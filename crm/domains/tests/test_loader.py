"""Tests of the domain pack loader, the one seam to the packs."""

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


def test_the_pack_rules_module_matches_the_contract():
    """The pack carries the deterministic rules under the engine's contract."""
    import inspect

    rules = loader.pack().rules_module()
    work = inspect.signature(rules.work_out_award)
    assert list(work.parameters) == ["contract", "plans", "request", "approval_limit"]
    sign_off = inspect.signature(rules.needs_sign_off)
    assert list(sign_off.parameters) == ["award", "approval_limit"]
