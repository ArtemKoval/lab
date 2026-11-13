"""Load and validate the scenario catalog of the ssh tutor.

One JSON file per scenario sits in the catalog directory. The loader
parses each file, validates the required fields, and returns the
scenarios sorted by id. The file name must equal the scenario id.
"""

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED = (
    "id",
    "title",
    "phase",
    "fault",
    "inject",
    "command",
    "signature",
    "prompts",
    "hints",
    "reveal",
    "connection",
)

REVEAL_KEYS = ("wrong", "fix")

CONNECTION_KEYS = (
    "target",
    "hostname",
    "user",
    "port",
    "identity",
    "hostkeyalias",
    "arm",
    "agent",
)


class CatalogError(Exception):
    """One catalog file fails validation, so the run cannot proceed."""


@dataclass
class Scenario:
    """One failure scenario of the catalog."""

    id: str
    title: str
    phase: str
    fault: str
    inject: str | None
    command: str
    signature: str
    prompts: list
    hints: list
    reveal_wrong: str
    reveal_fix: str
    connection: dict


def load_catalog(catalog_dir: Path) -> list:
    """Load every scenario file of the directory, sorted by id."""
    area_root = catalog_dir.parent
    paths = sorted(catalog_dir.glob("*.json"))
    if not paths:
        raise CatalogError(
            f"the catalog directory {catalog_dir} holds no scenario "
            "files; restore the catalog files of the change"
        )
    # The id-equals-file-name rule keeps the ids unique by
    # construction, so no duplicate scan runs here.
    return [_load_one(path, area_root) for path in paths]


def index(scenarios: list) -> dict:
    """Map the scenario ids to the scenarios."""
    return {scenario.id: scenario for scenario in scenarios}


def _load_one(path: Path, area_root: Path) -> Scenario:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CatalogError(f"{path.name}: the file is not valid JSON: {error}") from None
    _require_keys(path.name, None, data, REQUIRED)
    _require_keys(path.name, "reveal", data, REVEAL_KEYS)
    _require_keys(path.name, "connection", data, CONNECTION_KEYS)
    _validate_lists(path.name, data)
    _validate_command(path.name, data)
    _validate_inject(path.name, data, area_root)
    if data["id"] != path.stem:
        raise CatalogError(
            f"{path.name}: the id {data['id']} differs from the file name"
        )
    return Scenario(
        id=data["id"],
        title=data["title"],
        phase=data["phase"],
        fault=data["fault"],
        inject=data["inject"],
        command=data["command"],
        signature=data["signature"],
        prompts=data["prompts"],
        hints=data["hints"],
        reveal_wrong=data["reveal"]["wrong"],
        reveal_fix=data["reveal"]["fix"],
        connection=data["connection"],
    )


def _require_keys(name: str, label: str, data: dict, keys: tuple) -> None:
    """Raise when one key of the section misses from the file."""
    section = data[label] if label else data
    missing = [key for key in keys if key not in section]
    if missing:
        owner = label or "file"
        raise CatalogError(f"{name}: the {owner} misses {missing}")


def _validate_lists(name: str, data: dict) -> None:
    for key in ("prompts", "hints"):
        if not isinstance(data[key], list) or not data[key]:
            raise CatalogError(f"{name}: {key} must be a non-empty list")


def _validate_command(name: str, data: dict) -> None:
    command = data["command"]
    if not isinstance(command, str):
        raise CatalogError(f"{name}: the command must be a string")
    try:
        command.format(scratch="", target="")
    except (KeyError, IndexError, ValueError) as error:
        raise CatalogError(
            f"{name}: the command template is invalid: {error}"
        ) from None


def _validate_inject(name: str, data: dict, area_root: Path) -> None:
    inject = data["inject"]
    if inject and not (area_root / inject).exists():
        raise CatalogError(
            f"{name}: the inject script {inject} does not exist"
        )
