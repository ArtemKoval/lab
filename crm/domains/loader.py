"""The domain pack loader.

This module is the one seam between the engine and the domain packs. It is
the only engine module that names a default pack. The engine reads every
pack file through this loader, and no other engine module imports a pack by
name.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOMAINS = Path(__file__).resolve().parent
DEFAULT_DOMAIN = "insurance"


class PackError(Exception):
    """A pack is absent, incomplete, or misnamed."""


@dataclass(frozen=True)
class Pack:
    """One domain pack: its folder, its manifest, and its readers."""

    name: str
    root: Path
    manifest: dict[str, Any]

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def policy(self) -> Path:
        return self.root / "policy"

    @property
    def instructions(self) -> Path:
        return self.root / "instructions"

    @property
    def evals(self) -> Path:
        return self.root / "evals"

    @property
    def settings(self) -> dict[str, Any]:
        return self.manifest.get("settings", {})

    def load_json(self, name: str) -> Any:
        """Read one JSON file from the pack data folder."""
        path = self.data / name
        if not path.is_file():
            raise PackError(f"missing pack file: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def read_doc(self, name: str) -> str:
        """Read one policy document by its short name, such as wording."""
        path = self.policy / f"{name}.md"
        if not path.is_file():
            raise PackError(f"missing pack document: {path}")
        return path.read_text(encoding="utf-8")

    def instruction(self, name: str) -> str:
        """Read one instruction text by name, such as case or queue."""
        path = self.instructions / f"{name}.md"
        if not path.is_file():
            raise PackError(f"missing pack instruction: {path}")
        return path.read_text(encoding="utf-8")


def pack() -> Pack:
    """Return the active pack named by CRM_DOMAIN, or the default pack."""
    name = os.getenv("CRM_DOMAIN", DEFAULT_DOMAIN)
    root = DOMAINS / name
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise PackError(f"missing pack manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != name:
        raise PackError(
            f"manifest name {manifest.get('name')!r} does not match folder {name!r}"
        )
    return Pack(name=name, root=root, manifest=manifest)
