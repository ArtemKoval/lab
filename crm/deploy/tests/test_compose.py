"""The compose file's contract: the emulator stays unprofiled, the Langfuse
services carry the langfuse profile, the object store is the emulator's S3,
and only the documented dev credentials sit in the tracked file."""

from pathlib import Path

import yaml
from yaml.nodes import SequenceNode

COMPOSE = Path(__file__).resolve().parents[1] / "compose.yaml"

LANGFUSE_SERVICES = (
    "langfuse-web",
    "langfuse-worker",
    "clickhouse",
    "redis",
    "langfuse-db",
)

# The dev credentials the tracked file may carry. A credential-looking value
# of sixteen characters or more must be one of these, so a real key can never
# land here.
DEV_CREDENTIALS = frozenset(
    {
        "pk-lf-crm-local-aaaaaaaaaaaaaaaa",
        "sk-lf-crm-local-aaaaaaaaaaaaaaaa",
        "crmdevsecret-crmdevsecret-crmdevsecret",
        "0" * 64,
    }
)

# The one database address the tracked file may carry, dev password inside.
DEV_DATABASE_URL = "postgresql://postgres:crmlocaldevpg@langfuse-db:5432/postgres"


def compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text())


def credentialish(name: str) -> bool:
    upper = name.upper()
    if upper.endswith("_URL"):
        return False
    words = ("KEY", "SECRET", "PASSWORD", "PASSWD", "TOKEN", "AUTH")
    return any(word in upper for word in words)


def test_the_emulator_stays_unprofiled():
    services = compose()["services"]
    assert "profiles" not in services["emulator"]


def test_the_langfuse_services_carry_the_profile():
    services = compose()["services"]
    for name in LANGFUSE_SERVICES:
        assert services[name]["profiles"] == ["langfuse"], name


def test_the_object_store_is_the_emulator():
    services = compose()["services"]
    for name in ("langfuse-web", "langfuse-worker"):
        env = services[name]["environment"]
        assert env["LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT"] == "http://emulator:4566"


def test_the_database_url_is_the_dev_shape():
    services = compose()["services"]
    for name in ("langfuse-web", "langfuse-worker"):
        assert services[name]["environment"]["DATABASE_URL"] == DEV_DATABASE_URL


def test_only_dev_credentials_sit_in_the_tracked_file():
    services = compose()["services"]
    for name, service in services.items():
        for key, value in (service.get("environment") or {}).items():
            if credentialish(str(key)) and len(str(value)) >= 16:
                assert str(value) in DEV_CREDENTIALS, f"{name}.{key}"


class ComposeLoader(yaml.SafeLoader):
    """The safe loader with compose's !override tag registered."""


def _override_sequence(loader: ComposeLoader, node: SequenceNode) -> list:
    """Build the override ports list from the !override sequence."""
    return loader.construct_sequence(node)


ComposeLoader.add_constructor("!override", _override_sequence)

OVERRIDE = Path(__file__).resolve().parents[1] / "compose.demo.yaml"


def override_compose() -> dict:
    # ComposeLoader extends SafeLoader, so the load stays safe; the ruff S506
    # finding is about yaml.load with an unknown loader in general.
    return yaml.load(OVERRIDE.read_text(), Loader=ComposeLoader)  # noqa: S506


def test_the_demo_db_binds_the_loopback_in_the_base():
    ports = compose()["services"]["db"]["ports"]
    assert ports == ["127.0.0.1:5433:5432"]


def test_the_demo_override_publishes_the_db():
    ports = override_compose()["services"]["db"]["ports"]
    assert ports == ["5433:5432"]


def test_the_db_service_stays_unprofiled():
    assert "profiles" not in compose()["services"]["db"]
