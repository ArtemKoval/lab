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

# The verbs every pack's protocol module carries, and the loader validates.
PROTOCOL_VERBS = ("resolve", "gate", "execute", "summarize", "metric")

# The manifest keys an engine_api 2 pack declares its domain with.
DECLARED_KEYS = ("resolutions", "outcomes", "config", "effects")

# The core writes an effect's record can declare.
CORE_WRITES = ("payments",)


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
        import importlib

        name = self.manifest.get("rules", "rules")
        return importlib.import_module(f"domains.{self.name}.{name}")

    def protocol_module(self):
        """Import the pack's protocol module, and refuse a pack whose
        protocol lacks one of the verbs."""
        import importlib

        name = self.manifest.get("protocol", "protocol")
        module = importlib.import_module(f"domains.{self.name}.{name}")
        missing = [
            verb for verb in PROTOCOL_VERBS if not callable(getattr(module, verb, None))
        ]
        if missing:
            raise PackError(
                f"pack {self.name!r} protocol lacks {', '.join(missing)}"
            )
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
    return Pack(name=name, root=root, manifest=manifest)


def check_declarations(name: str, manifest: dict[str, Any]) -> None:
    """Refuse an engine_api 2 pack whose declarations are missing or name
    things the pack does not declare."""
    if manifest.get("engine_api", 1) < 2:
        return
    missing = [key for key in DECLARED_KEYS if key not in manifest]
    if missing:
        raise PackError(f"pack {name!r} manifest lacks {', '.join(missing)}")
    outcomes = manifest["outcomes"]
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
        records = declared.get("records")
        if records is not None and records not in CORE_WRITES:
            raise PackError(
                f"pack {name!r} effect {effect!r} records into the unknown write "
                f"{records!r}"
            )
