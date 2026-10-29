import pytest
from sqlalchemy import select

from backend.database import documents, engine
from backend.documents import sections


@pytest.mark.parametrize(
    ("document", "count", "first", "last"),
    [
        ("wording", 12, "Your plan", "Definitions"),
        ("manual", 14, "Purpose and scope", "Records"),
    ],
)
def test_documents_split_into_numbered_sections(document, count, first, last):
    with engine().connect() as db:
        found = sections(db, document)
    assert [s.number for s in found] == list(range(1, count + 1))
    assert (found[0].title, found[-1].title) == (first, last)


def test_read_a_section_of_the_manual(client):
    section = client.get("/api/documents/manual/sections/9").json()
    assert (section["document"], section["number"]) == ("manual", 9)
    assert section["document_title"] == "Cases manual"
    assert section["title"] == "Repeat claims"
    assert section["text"].startswith(
        "Before deciding any claim, check the customer's claim history"
    )


def test_read_a_section_of_the_wording(client):
    section = client.get("/api/documents/wording/sections/3").json()
    assert section["title"] == "Trip Delay"
    assert len(section["text"].split("\n\n")) == 2
    assert "Baggage Delay" not in section["text"]


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/api/documents/wording/sections/13", 404),
        ("/api/documents/manual/sections/15", 404),
        ("/api/documents/handbook/sections/1", 422),
        ("/api/documents/manual/sections/nine", 422),
    ],
)
def test_unknown_sections(client, path, status):
    assert client.get(path).status_code == status


def test_unknown_section_says_what_was_missing(client):
    response = client.get("/api/documents/manual/sections/15")
    assert response.json()["detail"] == "Section 15 of the cases manual not found"


def search(client, query):
    return client.get("/api/documents/search", params={"query": query})


def test_search_finds_the_paragraphs(client):
    matches = search(client, "wild animal").json()
    assert [(m["document"], m["number"]) for m in matches] == [("manual", 7)]
    assert matches[0]["title"] == "Interpretation notes"
    assert len(matches[0]["excerpts"]) == 1
    assert matches[0]["excerpts"][0].startswith("**Wild animals.**")


def test_search_ignores_case_and_looks_at_titles(client):
    assert [m["number"] for m in search(client, "GIRAFFE").json()] == [7]
    titled = [
        (m["document"], m["number"], m["excerpts"])
        for m in search(client, "repeat claims").json()
    ]
    assert ("manual", 9, []) in titled


def test_search_with_no_matches(client):
    assert search(client, "zeppelin").json() == []
    assert search(client, "").status_code == 422
    assert client.get("/api/documents/search").status_code == 422


def test_the_case_instructions(client):
    instructions = client.get("/api/instructions").json()
    assert list(instructions) == ["case"]
    case = instructions["case"]
    assert case.startswith("# UnderCover Agent: working a claim")
    contents = case[case.index("## Contents of the contract wording") :]
    assert "\n3. Trip Delay\n" in contents
    assert "## Contents of the cases manual" in contents
    assert contents.endswith("14. Records\n")
    assert "Unattended means out of your sight" not in case
    assert "Monkeys, gulls, bears, giraffes" not in case


def test_both_documents_are_seeded():
    with engine().connect() as db:
        query = select(documents).order_by(documents.c.position)
        rows = db.execute(query).mappings().all()
    assert [(row["name"], row["title"]) for row in rows] == [
        ("wording", "Contract wording"),
        ("manual", "Cases manual"),
    ]
    assert rows[1]["text"].startswith("# UnderCover Claims Handling Manual")
