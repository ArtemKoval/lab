"""Live end-to-end test against the real OpenRouter API.

Opt-in only: skipped unless the environment variable FDE_E2E_KEY holds a real
OpenRouter key. Spawns the real stdio shell (`python -m backend`) and drives
the same protocol the Electron main process speaks: ready handshake, key
validation, model listing, a real streamed completion, and a stop.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from backend.codec import PROTOCOL_VERSION

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("FDE_E2E_KEY"),
        reason="live API test: set FDE_E2E_KEY to run",
    ),
]

ROOT = Path(__file__).resolve().parents[2]


def send(proc, message_id, method, params):
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "id": message_id, "method": method, "params": params,
    }) + "\n")
    proc.stdin.flush()


def next_message(proc, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if line:
            return json.loads(line)
        time.sleep(0.05)
    raise TimeoutError(f"no protocol line within {timeout} seconds")


def wait_reply(proc, message_id, timeout=30):
    while True:
        message = next_message(proc, timeout)
        if message.get("id") == message_id:
            if "error" in message:
                raise AssertionError(f"request failed: {message['error']}")
            return message["result"]


def wait_stream_end(proc, stream_id, timeout=60):
    """Collect chunks of one stream until its terminal event; return (text, stopped, error)."""
    chunks = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = next_message(proc, timeout)
        params = message.get("params") or {}
        if params.get("stream_id") != stream_id:
            continue
        method = message.get("method")
        if method == "chat/chunk":
            chunks.append(params["text"])
        elif method == "chat/error":
            raise AssertionError(f"stream error: {params['message']}")
        elif method == "chat/done":
            text = params["text"] or "".join(chunks)
            return text, params["stopped"], None
    raise TimeoutError(f"stream {stream_id} never ended")


def test_live_openrouter_end_to_end(tmp_path):
    key = os.environ["FDE_E2E_KEY"]
    env = {"PYTHONPATH": str(ROOT), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "backend"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=ROOT,
        env=env,
        text=True,
    )
    try:
        ready = next_message(proc, 30)
        assert ready["method"] == "ready"
        assert ready["params"]["version"] == PROTOCOL_VERSION

        send(proc, 1, "validate_key", {"key": key})
        assert wait_reply(proc, 1) == {"valid": True}

        send(proc, 2, "list_models", {"base_url": None})
        models = wait_reply(proc, 2)["models"]
        assert len(models) > 0
        assert all("id" in model for model in models)

        send(proc, 3, "chat_start", {
            "key": key,
            "model": "any",
            "messages": [{"role": "user", "content": "Reply with the single word OK"}],
        })
        stream_id = wait_reply(proc, 3)["stream_id"]
        text, stopped, _ = wait_stream_end(proc, stream_id)
        assert stopped is False
        assert len(text) > 0

        send(proc, 4, "chat_start", {
            "key": key,
            "model": "any",
            "messages": [{"role": "user", "content": "Write a very long story about a lighthouse"}],
        })
        stream2 = wait_reply(proc, 4)["stream_id"]
        # Stop at once, before content flows: this is the one deterministic
        # way to stop a stream through the real API; fast routers can finish
        # a generation between our first chunk and the cancel.
        send(proc, 5, "chat_stop", {"stream_id": stream2})
        stopped_seen = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            message = next_message(proc, 10)
            params = message.get("params") or {}
            if params.get("stream_id") != stream2:
                continue
            method = message.get("method")
            if method == "chat/done":
                stopped_seen = params["stopped"]
                break
            elif method == "chat/error":
                raise AssertionError(f"stream error: {params['message']}")
        assert stopped_seen is True

        send(proc, 6, "shutdown", {})
        assert wait_reply(proc, 6) == {"stopping": True}
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            proc.kill()
