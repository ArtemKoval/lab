from pathlib import Path

import pytest
import yaml
from sqlalchemy import select

from backend import context_files
from backend.database import award_rules, documents, engine
from backend.documents import headings, manual_version
from domains import loader

"""The documents and the award rules seeding loads from the context layer's
files, and the contents of both documents the case agent's instructions end
with."""


@pytest.mark.parametrize(
    ("document", "count", "first", "last"),
    [
        ("wording", 12, "Your plan", "Definitions"),
        ("manual", 14, "Purpose and scope", "Records"),
    ],
)
def test_documents_split_into_numbered_sections(document, count, first, last):
    with engine().connect() as db:
        found = headings(db, document)
    assert [number for number, _ in found] == list(range(1, count + 1))
    assert (found[0][1], found[-1][1]) == (first, last)


def test_both_documents_are_seeded_from_the_context_layer_with_their_versions():
    with engine().connect() as db:
        query = select(documents).order_by(documents.c.position)
        rows = db.execute(query).mappings().all()
        version = manual_version(db)
    assert [(row["name"], row["title"], row["version"]) for row in rows] == [
        ("wording", "Contract wording", "2026.1"),
        ("manual", "Cases manual", "2026.2"),
    ]
    assert version == "2026.2"
    for row in rows:
        context = loader.pack().read_doc(row["name"])
        # The labs' copy in data/ is the same document without its front matter.
        labs = context_files.document(row["name"]).text
        assert row["text"] == labs
        assert context.startswith("---\nsource:\n")
        assert context.endswith(f"---\n\n{labs}")


def test_the_award_rules_are_the_context_layers_plans():
    plans = yaml.safe_load(
        (Path(__file__).parents[2] / "context" / "plans.yaml").read_text(
            encoding="utf-8"
        )
    )
    del plans["source"]
    with engine().connect() as db:
        assert db.execute(select(award_rules.c.plans)).scalar_one() == plans


def test_the_case_agent_reads_the_contents_of_both_documents(client):
    case = client.get("/api/versions/current").json()["instructions"]
    assert case.startswith("# UnderCover Agent: working a claim")
    contents = case[case.index("## Contents of the contract wording") :]
    assert "\n3. Trip Delay\n" in contents
    assert "## Contents of the cases manual" in contents
    assert contents.endswith("14. Records\n")
    assert "Unattended means out of your sight" not in case
    assert "Monkeys, gulls, bears, giraffes" not in case
