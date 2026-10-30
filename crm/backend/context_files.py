"""The context layer's files that seeding reads: the plans, and each document's
body and version. The files live in the active pack, so a second domain brings
its own."""

import os
from typing import Any, NamedTuple

import yaml

from domains import loader

# A document's front matter, its source and version, sits between two lines of ---.
FRONT_MATTER = "---\n"


class Document(NamedTuple):
    """A document's body, without its front matter, and its version."""

    text: str
    version: str


def read(file: str) -> str:
    """Read a governed file: everything comes from the active pack."""
    if file.endswith(".md"):
        return loader.pack().read_doc(file.removesuffix(".md"))
    pack_root = loader.DOMAINS / os.environ.get("CRM_DOMAIN", "insurance")
    return (pack_root / "context" / file).read_text(encoding="utf-8")


def plans() -> dict[str, Any]:
    """The plans, the benefits the deductible applies to and the add-ons, without
    the file's source."""
    rules = yaml.safe_load(read("plans.yaml"))
    del rules["source"]
    return rules


def document(name: str) -> Document:
    """A document's body and the version its front matter gives."""
    _, front, body = read(f"{name}.md").split(FRONT_MATTER, 2)
    return Document(body.lstrip("\n"), yaml.safe_load(front)["version"])
