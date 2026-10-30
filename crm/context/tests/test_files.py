"""The context layer's lookups, against the real files in context/."""

from pathlib import Path

import pytest

from context import files

GLOSSARY_SOURCE = {
    "file": "glossary.yaml",
    "system": "The contract wording, version 2026.1",
    "owner": "Legal",
    "reviewed": "2026-09-01",
}
MANUAL_SOURCE = {
    "file": "manual.md",
    "system": "Claims operations",
    "owner": "Head of claims operations",
    "reviewed": "2026-09-01",
}


def test_a_term_whatever_its_case():
    found = files.lookup_term("UNATTENDED")
    assert found["term"] == "Unattended"
    assert found["definition"].startswith("Out of your sight and out of your reach")
    assert found["sections"] == [5]
    assert found["sources"] == [GLOSSARY_SOURCE]


def test_an_unknown_term_gets_the_terms_the_glossary_defines():
    unknown = files.lookup_term("zeppelin")
    assert unknown["answer"] == (
        'The glossary doesn\'t define "zeppelin". These are the terms it does.'
    )
    assert {"Unattended", "Deductible", "Carrier"} <= set(unknown["terms"])
    assert unknown["sources"] == [GLOSSARY_SOURCE]


def test_a_records_fields():
    case = files.describe_fields("case")
    fields = [field["field"] for field in case["fields"]]
    assert "decision.manual_version" in fields
    assert case["sources"][0]["file"] == "data_dictionary.yaml"
    assert case["sources"][0]["owner"] == "Data governance"
    assert files.describe_fields("previous_case")["record"] == "previous_case"


def test_a_plan_with_its_deductible_and_the_add_ons():
    premium = files.get_plan("premium")
    assert premium["plan"]["deductible"] == 50.0
    assert premium["deductible_applies_to"] == ["baggage", "emergency_medical"]
    assert [a["add_on"] for a in premium["add_ons"]] == [
        "adventure_sports",
        "pre_existing_waiver",
        "electronics_plus",
    ]
    assert premium["sources"] == [
        {
            "file": "plans.yaml",
            "system": "Contract administration",
            "owner": "Product",
            "reviewed": "2026-09-01",
        }
    ]


def test_the_case_rules():
    rules = files.get_case_rules()
    assert [rule["rule"] for rule in rules["rules"]] == [
        "filing_window",
        "pre_existing_look_back",
        "repeat_cases",
        "meals_without_receipts",
    ]
    assert rules["sources"][0]["file"] == "case_rules.yaml"


def test_reference_data_with_every_word_whatever_its_case():
    found = files.search_reference_data("lisbon STRIKE")
    assert [fact["topic"] for fact in found["facts"]] == ["events"]
    assert found["facts"][0]["fact"].startswith("Lisbon, June 20, 2026")
    assert found["sources"][0]["file"] == "reference_data.yaml"
    strikes = files.search_reference_data("strike")["facts"]
    assert len(strikes) > 1
    nothing = files.search_reference_data("lisbon zeppelin")
    assert nothing == {"facts": [], "sources": []}


def test_searching_the_documents_names_each_sections_file():
    found = files.search_documents("unattended")
    # The sections the app's own search found before the context layer took it on.
    assert [(s["file"], s["number"]) for s in found["sections"]] == [
        ("wording.md", 5),
        ("manual.md", 7),
    ]
    assert [source["file"] for source in found["sources"]] == [
        "wording.md",
        "manual.md",
    ]
    wild = files.search_documents("wild animal")["sections"]
    assert [(s["document"], s["number"]) for s in wild] == [("manual", 7)]
    assert wild[0]["title"] == "Interpretation notes"
    assert wild[0]["excerpts"][0].startswith("**Wild animals.**")
    titled = files.search_documents("REPEAT CLAIMS")["sections"]
    assert ("manual", 9, []) in [
        (s["document"], s["number"], s["excerpts"]) for s in titled
    ]
    assert files.search_documents("zeppelin") == {"sections": [], "sources": []}


def test_reading_a_section():
    section = files.read_section("manual", 14)
    assert (section["document_title"], section["title"]) == ("Cases manual", "Records")
    assert section["version"] == "2026.2"
    assert section["text"].startswith("Every decision record holds the decision")
    assert section["sources"] == [MANUAL_SOURCE]
    delay = files.read_section("wording", 3)
    assert delay["title"] == "Trip Delay"
    assert "Baggage Delay" not in delay["text"]


@pytest.mark.parametrize(
    ("document", "number", "reason"),
    [
        ("manual", 99, "Section 99 of the cases manual not found"),
        ("wording", 13, "Section 13 of the contract wording not found"),
    ],
)
def test_a_section_that_doesnt_exist_is_refused(document, number, reason):
    with pytest.raises(files.Refused, match=f"^{reason}$"):
        files.read_section(document, number)


def test_the_documents_sections_hold_no_front_matter():
    assert {name: d.version for name, d in files.DOCUMENTS.items()} == {
        "wording": "2026.1",
        "manual": "2026.2",
    }
    for document in files.DOCUMENTS.values():
        assert list(document.sections) == list(range(1, len(document.sections) + 1))
        for section in document.sections.values():
            for front_matter in ("source:", "owner:", "reviewed:", 'version: "'):
                assert front_matter not in section.text


def test_the_files_are_read_once_at_import(monkeypatch):
    def no_reading(*args, **kwargs):
        raise AssertionError("A lookup read a file")

    monkeypatch.setattr(Path, "read_text", no_reading)
    files.lookup_term("unattended")
    files.describe_fields("contract")
    files.get_plan("first")
    files.get_case_rules()
    files.search_reference_data("strike")
    files.search_documents("strike")
    files.read_section("wording", 1)
