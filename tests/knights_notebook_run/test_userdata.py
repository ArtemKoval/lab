"""Tests for the Colab userdata stand-in of the knights-and-knaves run recipe."""
import importlib.util
from pathlib import Path

import pytest

SHIM = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "knights_notebook_run"
    / "google"
    / "colab"
    / "userdata.py"
)


@pytest.fixture(scope="module")
def userdata():
    spec = importlib.util.spec_from_file_location("knights_run_userdata", SHIM)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_sits_on_the_module(userdata):
    # Colab exposes get on the module. An instance attribute breaks the import sites.
    assert callable(userdata.get)


def test_get_returns_the_secret_from_the_environment(userdata, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-testtoken")
    assert userdata.get("OPENROUTER_API_KEY") == "sk-or-v1-testtoken"


def test_get_raises_key_error_with_guidance(userdata, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(KeyError) as excinfo:
        userdata.get("OPENROUTER_API_KEY")
    assert excinfo.value.args[0] == (
        "Secret 'OPENROUTER_API_KEY' is not in the environment. Add it to the .env file at the repo root."
    )


def test_get_reads_any_secret_name(userdata, monkeypatch):
    monkeypatch.setenv("OTHER_SECRET", "hunter2")
    assert userdata.get("OTHER_SECRET") == "hunter2"


def test_get_leaves_type_errors_alone(userdata):
    # An unhashable name is a caller bug. It must not look like a missing secret.
    with pytest.raises(TypeError):
        userdata.get({"a": 1})
