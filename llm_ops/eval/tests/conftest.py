import os
import tempfile
from pathlib import Path

import httpx2
import pytest
from fake_apfel import FakeApfel

from apfel_eval import run
from apfel_eval.judge import ApfelJudge

BASE_URL = "http://127.0.0.1:11434/v1"
SETTING_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID",
    "APFEL_BASE_URL",
    "APFEL_TOKEN",
    # A proxy variable changes where a request goes, so no test can rely on it.
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
)


@pytest.fixture
def tmp_path():
    """A private folder for one test.

    The folder of pytest is shared by all pytest processes of a user. Parallel mutmut
    workers delete each other files there, and a worker can then exit with an error.
    """
    with tempfile.TemporaryDirectory() as folder:
        yield Path(folder)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    """Run each test in an empty folder with a copy of the environment."""
    environment = {k: v for k, v in os.environ.items() if k not in SETTING_NAMES}
    monkeypatch.setattr(os, "environ", environment)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def fake():
    return FakeApfel()


@pytest.fixture
def make_judge():
    def make(handler, base_url=BASE_URL, **kwargs):
        client = httpx2.Client(transport=httpx2.MockTransport(handler))
        return ApfelJudge(base_url, http_client=client, **kwargs)

    return make


@pytest.fixture
def serve(monkeypatch):
    """Make `main` talk to a handler. Without it, `main` would open a real connection."""

    def install(handler):
        client = httpx2.Client(transport=httpx2.MockTransport(handler))

        def factory(*args, **kwargs):
            return ApfelJudge(*args, http_client=client, **kwargs)

        monkeypatch.setattr(run, "ApfelJudge", factory)

    return install
