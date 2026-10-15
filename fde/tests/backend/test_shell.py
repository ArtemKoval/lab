"""Tests for the stdio shell, including one real-interpreter spawn."""

import io
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from backend import codec
from backend.errors import KIND_API, KIND_AUTH, KIND_NETWORK, ClientError
from backend.shell import Shell, serve

ROOT = Path(__file__).resolve().parents[2]


class StubClient:
    def __init__(self):
        self.validate_side_effect = None
        self.models_result = []
        self.stream_factory = None

    def validate_key(self, key):
        if isinstance(self.validate_side_effect, Exception):
            raise self.validate_side_effect
        return True

    def list_models(self):
        return self.models_result

    def chat_stream(self, key, model, messages, should_stop=None):
        return self.stream_factory(key, model, messages, should_stop)


def make_shell(client=None):
    out = io.StringIO()
    shell = Shell(client or StubClient(), out, "python-fake")
    return shell, out


def out_messages(out):
    text = out.getvalue()
    if not text:
        return []
    return [json.loads(line) for line in text.splitlines()]


def methods_of(messages):
    return [m.get("method") for m in messages]


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def request(message_id, method, params):
    return codec.encode_line(codec.encode_request(message_id, method, params))


def test_ready_line_comes_first_with_version_and_interpreter():
    shell, out = make_shell()
    shell.run(iter([]))
    messages = out_messages(out)
    assert len(messages) == 1
    assert messages[0]["method"] == "ready"
    assert messages[0]["params"] == {
        "version": codec.PROTOCOL_VERSION,
        "interpreter": "python-fake",
    }


def test_validate_key_ok():
    shell, out = make_shell()
    shell.run([request(1, "validate_key", {"key": "k"})])
    messages = out_messages(out)
    assert messages[1] == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"valid": True},
    }


def test_validate_key_error_maps_kind():
    client = StubClient()
    client.validate_side_effect = ClientError(KIND_AUTH, "Invalid key")
    shell, out = make_shell(client)
    shell.run([request(2, "validate_key", {"key": "bad"})])
    messages = out_messages(out)
    assert messages[1]["id"] == 2
    error = messages[1]["error"]
    assert error["data"] == {"kind": "auth"}
    assert error["message"] == "Invalid key"


def test_list_models_wraps_result():
    client = StubClient()
    client.models_result = [{"id": "m1", "name": "Model One"}]
    shell, out = make_shell(client)
    shell.run([request(3, "list_models", {})])
    assert out_messages(out)[1]["result"] == {
        "models": [{"id": "m1", "name": "Model One"}]
    }


def test_unknown_method_is_an_api_error():
    shell, out = make_shell()
    shell.run([request(4, "nope", {})])
    messages = out_messages(out)
    assert messages[1]["id"] == 4
    error = messages[1]["error"]
    assert error["data"] == {"kind": "api"}
    assert "nope" in error["message"]


def test_unknown_method_does_not_stop_the_loop():
    shell, out = make_shell()
    shell.run([request(1, "nope", {}), request(2, "shutdown", {})])
    messages = out_messages(out)
    assert [m.get("id") for m in messages if "id" in m] == [1, 2]


def test_missing_parameter_is_an_api_error():
    shell, out = make_shell()
    shell.run([request(5, "validate_key", {})])
    messages = out_messages(out)
    assert messages[1]["id"] == 5
    error = messages[1]["error"]
    assert error["data"] == {"kind": "api"}
    assert "key" in error["message"]


def test_malformed_line_is_dropped_and_logged(caplog):
    shell, out = make_shell()
    with caplog.at_level(logging.WARNING, logger="backend.shell"):
        shell.run(["not json\n"])
    assert len(out_messages(out)) == 1  # the ready line only
    assert caplog.records[0].getMessage() == "dropped malformed line: not json\n"


def test_malformed_line_does_not_stop_the_loop():
    shell, out = make_shell()
    shell.run(["not json\n", request(1, "shutdown", {})])
    assert [m.get("id") for m in out_messages(out) if "id" in m] == [1]


def test_message_without_method_is_dropped(caplog):
    shell, out = make_shell()
    stray = codec.encode_line(codec.encode_response(9, {"x": 1}))
    with caplog.at_level(logging.WARNING, logger="backend.shell"):
        shell.run([stray])
    assert len(out_messages(out)) == 1
    assert caplog.records[0].getMessage().startswith("dropped message without a method: ")
    assert "9" in caplog.records[0].getMessage()


def test_message_without_method_does_not_stop_the_loop():
    shell, out = make_shell()
    stray = codec.encode_line(codec.encode_response(9, {"x": 1}))
    shell.run([stray, request(1, "shutdown", {})])
    assert [m.get("id") for m in out_messages(out) if "id" in m] == [1]


def test_notification_from_parent_is_dropped(caplog):
    shell, out = make_shell()
    stray = codec.encode_line(codec.encode_notification("ping", {}))
    with caplog.at_level(logging.WARNING, logger="backend.shell"):
        shell.run([stray])
    assert len(out_messages(out)) == 1
    assert caplog.records[0].getMessage() == "dropped notification from the parent: ping"


def test_notification_from_parent_does_not_stop_the_loop():
    shell, out = make_shell()
    stray = codec.encode_line(codec.encode_notification("ping", {}))
    shell.run([stray, request(1, "shutdown", {})])
    assert [m.get("id") for m in out_messages(out) if "id" in m] == [1]


def test_stream_without_terminal_event_cleans_up():
    def factory(key, model, messages, should_stop=None):
        return iter(())

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "any", "messages": []})])
    assert wait_for(lambda: shell._stop_events == {})
    extra = [m for m in out_messages(out) if m.get("method") in ("chat/done", "chat/error")]
    assert extra == []


def test_serve_runs_ready_line_and_shutdown_in_process(caplog, monkeypatch):
    config_calls = []

    def spy_basic_config(**kwargs):
        config_calls.append(kwargs)

    monkeypatch.setattr("backend.shell.logging.basicConfig", spy_basic_config)
    out = io.StringIO()
    with caplog.at_level(logging.INFO, logger="backend.shell"):
        serve([request(1, "list_models", {}), request(2, "shutdown", {})], out,
              StubClient(), "python-fake")
    messages = out_messages(out)
    assert messages[0]["method"] == "ready"
    assert messages[0]["params"]["interpreter"] == "python-fake"
    assert messages[1]["id"] == 1
    assert messages[1]["result"] == {"models": []}
    assert messages[2]["result"] == {"stopping": True}
    assert config_calls == [{
        "stream": sys.stderr,
        "level": logging.INFO,
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
    }]
    assert caplog.records[-1].getMessage() == "backend stopped"


def test_shutdown_stops_the_loop():
    shell, out = make_shell()
    shell.run([request(1, "shutdown", {}), request(2, "list_models", {})])
    messages = out_messages(out)
    assert len(messages) == 2  # ready + the shutdown reply, nothing more
    assert messages[1]["result"] == {"stopping": True}


def test_chat_start_streams_chunks_then_done():
    def factory(key, model, messages, should_stop=None):
        def gen():
            yield "chunk", "a"
            yield "chunk", "b"
            yield "done", {"text": "ab", "stopped": False}

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "any", "messages": []})])
    assert wait_for(lambda: "chat/done" in methods_of(out_messages(out)))
    messages = out_messages(out)
    reply = [m for m in messages if m.get("id") == 1][0]
    assert reply["result"] == {"stream_id": 1}
    chunks = [m for m in messages if m.get("method") == "chat/chunk"]
    assert [m["params"]["text"] for m in chunks] == ["a", "b"]
    assert all(m["params"]["stream_id"] == 1 for m in chunks)
    done = [m for m in messages if m.get("method") == "chat/done"][0]
    assert done["params"] == {"stream_id": 1, "text": "ab", "stopped": False}


def test_chat_stop_ends_stream_with_stopped_mark():
    release = threading.Event()

    def factory(key, model, messages, should_stop=None):
        def gen():
            yield "chunk", "a"
            while not should_stop():
                release.wait(0.01)
            yield "done", {"text": "a", "stopped": True}

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "m1", "messages": []})])
    assert wait_for(lambda: "chat/chunk" in methods_of(out_messages(out)))
    shell.handle_line(request(2, "chat_stop", {"stream_id": 1}))
    assert wait_for(lambda: "chat/done" in methods_of(out_messages(out)))
    messages = out_messages(out)
    stop_reply = [m for m in messages if m.get("id") == 2][0]
    assert stop_reply["result"] == {"stopping": True}
    done = [m for m in messages if m.get("method") == "chat/done"][0]
    assert done["params"]["stopped"] is True


def test_chat_stop_unknown_stream_errors():
    shell, out = make_shell()
    shell.run([request(1, "chat_stop", {"stream_id": 99})])
    messages = out_messages(out)
    assert messages[1]["id"] == 1
    assert messages[1]["error"]["data"] == {"kind": "api"}
    assert messages[1]["error"]["message"] == "Unknown stream"


def test_chat_worker_runs_as_daemon_with_the_request_args(monkeypatch):
    captured = []
    real_thread_init = threading.Thread.__init__

    def spy_init(self, *args, **kwargs):
        captured.append({"args": args, "kwargs": dict(kwargs)})
        real_thread_init(self, *args, **kwargs)

    monkeypatch.setattr(threading.Thread, "__init__", spy_init)

    def factory(key, model, messages, should_stop=None):
        def gen():
            yield "done", {"text": "", "stopped": False}

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "any", "messages": []})])
    assert wait_for(lambda: "chat/done" in methods_of(out_messages(out)))
    daemon_flags = [c["kwargs"].get("daemon") for c in captured]
    assert daemon_flags == [True]


def test_chat_start_without_model_uses_any_and_passes_request_args():
    seen = {}

    def factory(key, model, messages, should_stop=None):
        seen["key"] = key
        seen["model"] = model
        seen["messages"] = messages

        def gen():
            yield "done", {"text": "", "stopped": False}

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "messages": []})])
    assert wait_for(lambda: "chat/done" in methods_of(out_messages(out)))
    assert seen == {"key": "k", "model": "any", "messages": []}


def test_chat_start_with_model_passes_the_model_through():
    seen = {}

    def factory(key, model, messages, should_stop=None):
        seen["model"] = model

        def gen():
            yield "done", {"text": "", "stopped": False}

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "m1", "messages": []})])
    assert wait_for(lambda: "chat/done" in methods_of(out_messages(out)))
    assert seen["model"] == "m1"


def test_chat_client_error_reaches_the_window_as_notification():
    def factory(key, model, messages, should_stop=None):
        def gen():
            yield "error", ClientError(KIND_NETWORK, "no route")

        return gen()

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    shell.run([request(1, "chat_start", {"key": "k", "model": "any", "messages": []})])
    assert wait_for(lambda: "chat/error" in methods_of(out_messages(out)))
    error = [m for m in out_messages(out) if m.get("method") == "chat/error"][0]
    assert error["params"] == {"stream_id": 1, "kind": "network", "message": "no route"}


def test_chat_worker_crash_reports_api_error(caplog):
    def factory(key, model, messages, should_stop=None):
        raise RuntimeError("boom")

    client = StubClient()
    client.stream_factory = factory
    shell, out = make_shell(client)
    with caplog.at_level(logging.ERROR, logger="backend.shell"):
        shell.run([request(1, "chat_start", {"key": "k", "model": "any", "messages": []})])
    assert wait_for(lambda: "chat/error" in methods_of(out_messages(out)))
    error = [m for m in out_messages(out) if m.get("method") == "chat/error"][0]
    assert error["params"] == {
        "stream_id": 1,
        "kind": KIND_API,
        "message": "The chat stream failed inside the backend",
    }
    crash_logs = [r for r in caplog.records if "crashed" in r.getMessage()]
    assert len(crash_logs) == 1
    assert crash_logs[0].getMessage() == "chat stream 1 crashed"


def test_stdout_carries_only_protocol_lines():
    shell, out = make_shell()
    shell.run([
        "garbage\n",
        request(1, "shutdown", {}),
    ])
    for line in out.getvalue().splitlines():
        message = json.loads(line)
        assert message["jsonrpc"] == "2.0"


def test_real_interpreter_serves_ready_line_shutdown_and_exit():
    env = {"PYTHONPATH": str(ROOT), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "backend"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        env=env,
        text=True,
    )
    try:
        ready = json.loads(proc.stdout.readline())
        assert ready["method"] == "ready"
        assert ready["params"]["version"] == codec.PROTOCOL_VERSION
        assert ready["params"]["interpreter"] == sys.executable
        proc.stdin.write(request(1, "shutdown", {}))
        proc.stdin.flush()
        reply = json.loads(proc.stdout.readline())
        assert reply["id"] == 1
        assert reply["result"] == {"stopping": True}
        proc.stdin.close()
        assert proc.wait(timeout=5) == 0
        assert "backend stopped" in proc.stderr.read()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
