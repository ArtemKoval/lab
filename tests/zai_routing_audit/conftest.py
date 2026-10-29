"""Shared fixtures for the zai_routing_audit tests. Hermetic by default."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree, so the tests import the mutated copy.
REPO_ROOT = Path(__file__).absolute().parents[2]

# The package sits under tools/ in the repository and directly under the
# root in a flat mutation mirror. Import whichever copy is present, so a
# moved tree still tests its own source. Under mutmut, the variable
# MUTANT_UNDER_TEST is set and mutmut must control the import path, so
# the manual insert stands down and the mutants copy wins.
if "MUTANT_UNDER_TEST" not in os.environ:
    for _candidate in (REPO_ROOT / "tools" / "zai_routing_audit", REPO_ROOT):
        if (_candidate / "zai_routing_audit").is_dir():
            sys.path.insert(0, str(_candidate))
            break

from zai_routing_audit import core  # noqa: E402

TOKEN = "c05c9b94a19f4eeb9922fc0b4e359dfc.ZNPRSECRET"


class FakeTransport:
    """Scripted transport. Records every call and replays queued items."""

    def __init__(self, posts=None, gets=None):
        self.post_queue = list(posts or [])
        self.get_queue = list(gets or [])
        self.post_calls = []
        self.get_calls = []

    def post_json(self, path, payload):
        self.post_calls.append((path, payload))
        item = self.post_queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def get_json(self, url):
        self.get_calls.append(url)
        item = self.get_queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClock:
    """Monotonic clock that advances by a fixed step on every call."""

    def __init__(self, step=5.0):
        self.now = 100.0
        self.step = step

    def __call__(self):
        self.now += self.step
        return self.now


class _Handler(BaseHTTPRequestHandler):
    """Replays one scripted (status, body) pair and records the request."""

    def _respond(self):
        server = self.server
        length = int(self.headers.get("content-length", 0))
        server.received_body = self.rfile.read(length)
        server.received_headers = dict(self.headers)
        server.received_path = self.path
        status, raw = server.response
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(raw)

    do_POST = _respond
    do_GET = _respond

    def log_message(self, format, *args):  # noqa: A002
        pass


@pytest.fixture
def local_server():
    """A localhost HTTP server with one scripted response per test."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.response = (200, b'{"model": "glm-5.3-flash"}')
    thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def settings_file(tmp_path):
    """A settings file that mirrors the real user setup, with a fake token."""
    payload = {
        "env": {
            "ANTHROPIC_AUTH_TOKEN": TOKEN,
            "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.3-flash[1m]",
        }
    }
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture
def transcript_dir(tmp_path):
    """A transcript directory with both clean and hostile lines."""
    sub = tmp_path / "subagents"
    sub.mkdir()
    lines = [
        json.dumps({"type": "api-request", "params": {"model": "glm-5.3-flash"}}),
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "glm-5.3-flash",
                    "usage": {
                        "input_tokens": 13,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 5,
                        "output_tokens": 16,
                    },
                },
            }
        ),
        '{"type":"assistant","message":{"model":"glm-5.3"}}',
        '{"broken',
        "",
        '{"type":"summary"}',
        "[1, 2]",
    ]
    (tmp_path / "session.jsonl").write_text("\n".join(lines), encoding="utf-8")
    (sub / "agent.jsonl").write_text(
        json.dumps({"type": "assistant", "message": {"model": "glm-5.3-flash"}}),
        encoding="utf-8",
    )
    hostile = b'{"type":"assistant","message":{"model":"g\x01lm"}}\n'
    (tmp_path / "hostile.jsonl").write_bytes(hostile)
    (tmp_path / "notes.txt").write_text("not a transcript", encoding="utf-8")
    return tmp_path


@pytest.fixture
def model_usage_payload():
    """The documented per-model usage envelope."""
    return {
        "success": True,
        "code": 200,
        "data": {
            "modelDataList": [
                {"modelName": "GLM-5.3", "tokensUsage": [0, 1026439], "totalTokens": 1026439},
                {"modelName": "GLM-5.3-Flash", "tokensUsage": [400, 552]},
            ],
            "totalUsage": {"totalTokensUsage": 1027391},
        },
    }


@pytest.fixture
def quota_payload():
    """The documented credit pool envelope."""
    return {
        "data": {
            "planName": "GLM Coding Plan",
            "limits": [
                {"type": "CREDIT_LIMIT", "usage": 28000, "currentValue": 2263, "remaining": 25736},
                {"type": "CREDIT_LIMIT", "usage": 140000, "currentValue": 2392, "remaining": 137607},
            ],
        }
    }


@pytest.fixture
def quota_payload_alt():
    """The alternate top-level limits envelope."""
    return {
        "limits": [
            {"type": "CREDIT_LIMIT", "usage": 28000, "currentValue": 2263, "remaining": 25736}
        ]
    }


@pytest.fixture
def quota_step(quota_payload):
    """A quota payload whose consumed values the test can adjust.

    The two limits move together but keep their offset, so pool rows
    stay distinguishable in the burn deltas.
    """
    def make(consumed):
        import copy

        payload = copy.deepcopy(quota_payload)
        limits = payload["data"]["limits"]
        limits[0]["currentValue"] = consumed
        limits[1]["currentValue"] = consumed + 129
        return payload

    return make


__all__ = ["FakeTransport", "FakeClock", "core", "TOKEN"]
