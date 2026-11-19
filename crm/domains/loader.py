"""The domain pack loader.

This module is the one seam between the engine and the domain packs. It is
the only engine module that names a default pack. The engine reads every
pack file through this loader, and no other engine module imports a pack by
name.
"""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOMAINS = Path(__file__).resolve().parent
DEFAULT_DOMAIN = "insurance"

# The verbs every pack's protocol module carries, and the loader validates.
PROTOCOL_VERBS = ("resolve", "gate", "execute", "summarize", "metric")

# The manifest keys an engine_api 2 pack declares its domain with.
DECLARED_KEYS = ("resolutions", "outcomes", "config", "effects")

# The formats the vocabulary names, and the loader validates.
AWARD_FORMATS = ("money", "days")
ROW_FORMATS = ("text", "date", "money", "days", "list")

# The manifest contract the engine runs.
ENGINE_API = 2


class PackError(Exception):
    """A pack is absent, incomplete, or misnamed."""


@dataclass(frozen=True)
class Pack:
    """One domain pack: its folder, its manifest, and its readers."""

    name: str
    root: Path
    manifest: dict[str, Any]

    def award_text(self, value: float) -> str:
        """An award in the pack's unit: money as dollars, or days as a number
        of days with its unit. The number drops its trailing zero."""
        unit = self.manifest.get("vocabulary", {}).get("award_format", "money")
        if unit == "days":
            return f"{value:g} days"
        return f"${value:,.2f}"

    def message(self, key: str, default: str) -> str:
        """The pack's word for one of the refusals, or the engine's default
        words when the pack names none."""
        return self.manifest.get("vocabulary", {}).get("messages", {}).get(key, default)

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

    @property
    def resolutions(self) -> list[str]:
        return self.manifest.get("resolutions", [])

    @property
    def outcomes(self) -> dict[str, str]:
        return self.manifest.get("outcomes", {})

    @property
    def config(self) -> dict[str, str]:
        return self.manifest.get("config", {})

    @property
    def effects(self) -> dict[str, dict[str, Any]]:
        return self.manifest.get("effects", {})

    def load_json(self, name: str) -> Any:
        """Read one JSON file from the pack data folder."""
        return self._json(self.data, name, "pack file")

    def load_eval(self, name: str) -> Any:
        """Read one JSON file from the pack evals folder."""
        return self._json(self.evals, name, "pack eval file")

    def _json(self, folder: Path, name: str, kind: str) -> Any:
        """Read one JSON file of the pack, or name it in an error."""
        path = folder / name
        if not path.is_file():
            raise PackError(f"missing {kind}: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def read_doc(self, name: str) -> str:
        """Read one policy document by its short name, such as wording."""
        return self._read(self.policy, name, "pack document")

    def instruction(self, name: str) -> str:
        """Read one instruction text by name, such as case or queue."""
        return self._read(self.instructions, name, "pack instruction")

    def rules_module(self):
        """Import the pack's deterministic rules module by its manifest name."""
        name = self.manifest.get("rules", "rules")
        return importlib.import_module(f"domains.{self.name}.{name}")

    def protocol_module(self):
        """Import the pack's protocol module, and refuse a pack whose
        protocol lacks one of the verbs."""
        name = self.manifest.get("protocol", "protocol")
        module = importlib.import_module(f"domains.{self.name}.{name}")
        missing = [
            verb for verb in PROTOCOL_VERBS if not callable(getattr(module, verb, None))
        ]
        if missing:
            raise PackError(f"pack {self.name!r} protocol lacks {', '.join(missing)}")
        return module

    def _read(self, folder: Path, name: str, kind: str) -> str:
        """Read one markdown file of the pack, or name it in an error."""
        path = folder / f"{name}.md"
        if not path.is_file():
            raise PackError(f"missing {kind}: {path}")
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
    check_declarations(name, manifest)
    check_vocabulary(name, manifest)
    return Pack(name=name, root=root, manifest=manifest)


def check_declarations(name: str, manifest: dict[str, Any]) -> None:
    """Refuse a pack the engine cannot run: one the declarations do not
    describe, or one that resolves no outcome at all."""
    if manifest.get("engine_api", 1) < ENGINE_API:
        raise PackError(
            f"pack {name!r} declares engine_api {manifest.get('engine_api')!r}; "
            "the engine runs engine_api 2 packs only"
        )
    missing = [key for key in DECLARED_KEYS if key not in manifest]
    if missing:
        raise PackError(f"pack {name!r} manifest lacks {', '.join(missing)}")
    outcomes = manifest["outcomes"]
    if not outcomes:
        raise PackError(f"pack {name!r} declares no outcomes")
    for outcome, verb in outcomes.items():
        if verb not in PROTOCOL_VERBS:
            raise PackError(
                f"pack {name!r} outcome {outcome!r} binds the unknown verb {verb!r}"
            )
    for effect, declared in manifest["effects"].items():
        if declared.get("outcome") not in outcomes:
            raise PackError(
                f"pack {name!r} effect {effect!r} names the undeclared outcome "
                f"{declared.get('outcome')!r}"
            )


def check_vocabulary(name: str, manifest: dict[str, Any]) -> None:
    """Refuse a pack whose vocabulary names a format the renderer cannot
    draw. A pack with no vocabulary section loads with the default words."""
    vocabulary = manifest.get("vocabulary")
    if not vocabulary:
        return
    _check_award_format(name, vocabulary)
    _check_contract(name, vocabulary)


def _check_award_format(name: str, vocabulary: dict[str, Any]) -> None:
    """Refuse an award format the renderer cannot draw."""
    award = vocabulary.get("award_format")
    if award is not None and award not in AWARD_FORMATS:
        raise PackError(
            f"pack {name!r} vocabulary names the unknown award_format {award!r}"
        )


def _check_contract(name: str, vocabulary: dict[str, Any]) -> None:
    """Refuse a contract presentation with no title or a shapeless row."""
    contract = vocabulary.get("contract")
    if contract is None:
        return
    if not isinstance(contract, dict):
        raise PackError(
            f"pack {name!r} vocabulary contract is not an object"
        )
    if contract and not contract.get("title"):
        raise PackError(f"pack {name!r} vocabulary contract carries no title")
    rows = contract.get("rows")
    if rows is None:
        return
    if not isinstance(rows, list):
        raise PackError(f"pack {name!r} vocabulary contract rows is not a list")
    for row in rows:
        _check_row(name, row)


def _check_row(name: str, row: dict[str, Any]) -> None:
    """Refuse one contract row that names no source or an unknown format."""
    if not isinstance(row, dict):
        raise PackError(
            f"pack {name!r} vocabulary contract row {row!r} is not an object"
        )
    if not row.get("template") and not row.get("field"):
        raise PackError(
            f"pack {name!r} vocabulary row {row.get('label')!r} names "
            "neither a field nor a template"
        )
    named = (
        [row["format"]]
        if "format" in row
        else list(row.get("formats", {}).values())
    )
    for key in named:
        if key not in ROW_FORMATS:
            raise PackError(
                f"pack {name!r} vocabulary row {row.get('label')!r} names "
                f"the unknown format {key!r}"
            )
