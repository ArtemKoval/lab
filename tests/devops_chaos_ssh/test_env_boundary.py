"""The container boundary: argv assembly, exit handling, port math,
and error extraction, over a faked subprocess and socket."""

import socket
import subprocess
from pathlib import Path

import pytest

from chaos_ssh import env


class FakeRun:
    """One scripted subprocess.run with a call log."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, argv, stdout=None, stderr=None, check=False):
        self.calls.append(list(argv))
        result = self.results.pop(0)
        return subprocess.CompletedProcess(
            argv, result[0], stdout=result[1].encode(), stderr=result[2].encode()
        )


@pytest.fixture
def fake_run(monkeypatch):
    fake = FakeRun([])
    monkeypatch.setattr(env.subprocess, "run", fake)
    return fake


def test_up_builds_the_devcontainer_argv(fake_run):
    fake_run.results = [(0, "", "")]
    env.up(Path("/area"))
    assert fake_run.calls[0][:4] == [
        "npx",
        "--yes",
        "@devcontainers/cli",
        "up",
    ]
    assert "--remove-existing-container" in fake_run.calls[0]
    assert "/area" in fake_run.calls[0]


def test_up_failure_raises_env_error_with_remediation(fake_run):
    fake_run.results = [(9, "", "daemon not running")]
    with pytest.raises(env.EnvError) as exc:
        env.up(Path("/area"))
    assert "daemon not running" in str(exc.value)
    assert "sg docker" in exc.value.remediation


def test_exec_in_builds_the_exec_argv(fake_run):
    fake_run.results = [(0, "", "")]
    code = env.exec_in(Path("/area"), "/opt/chaos/inject/x.sh", ("arg1",))
    assert code == 0
    call = fake_run.calls[0]
    assert "exec" in call
    assert call[-3:] == ["bash", "/opt/chaos/inject/x.sh", "arg1"]


def test_exec_in_failure_raises(fake_run):
    fake_run.results = [(3, "", "no such script")]
    with pytest.raises(env.EnvError):
        env.exec_in(Path("/area"), "/nope.sh")


def test_rm_container_removes_the_listed_ids(fake_run):
    fake_run.results = [(0, "abc\ndef\n", ""), (0, "", "")]
    assert env.rm_container(Path("/area")) is True
    assert fake_run.calls[1][:3] == ["docker", "rm", "-f"]
    assert "abc" in fake_run.calls[1] and "def" in fake_run.calls[1]


def test_rm_container_without_container_returns_false(fake_run):
    fake_run.results = [(0, "", "")]
    assert env.rm_container(Path("/area")) is False


def test_rm_container_failure_raises(fake_run):
    fake_run.results = [(0, "abc\n", ""), (1, "", "denied")]
    with pytest.raises(env.EnvError):
        env.rm_container(Path("/area"))


class FakeBindSocket:
    setsockopt_calls = []

    def __init__(self, fail):
        self.fail = fail

    def setsockopt(self, *a, **k):
        FakeBindSocket.setsockopt_calls.append(a)

    def bind(self, *a, **k):
        if self.fail:
            raise OSError("held")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_port_status_sets_the_reuse_flag(monkeypatch):
    FakeBindSocket.setsockopt_calls = []
    monkeypatch.setattr(env.socket, "socket", lambda *a: FakeBindSocket(False))
    assert env.port_status(2222) is True
    assert FakeBindSocket.setsockopt_calls == [
        (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ]


def test_port_status_true_when_bind_succeeds(monkeypatch):
    monkeypatch.setattr(env.socket, "socket", lambda *a: FakeBindSocket(False))
    assert env.port_status(2222) is True


def test_port_status_false_when_bind_fails(monkeypatch):
    monkeypatch.setattr(env.socket, "socket", lambda *a: FakeBindSocket(True))
    assert env.port_status(2222) is False


def test_run_returns_the_decoded_result(monkeypatch):
    seen = {}

    def fake_run(argv, stdout=None, stderr=None, check=False):
        seen["stdout"] = stdout
        seen["argv"] = argv
        return subprocess.CompletedProcess(
            argv, 0, stdout=b"line\n", stderr=b""
        )

    monkeypatch.setattr(env.subprocess, "run", fake_run)
    result = env.run(["tool"], capture=True)
    assert result == {"returncode": 0, "stdout": "line\n", "stderr": ""}
    assert seen["stdout"] == subprocess.PIPE
    env.run(["quiet"])
    assert seen["stdout"] == subprocess.DEVNULL
    assert seen["argv"] == ["quiet"]


def test_container_error_names_the_last_stderr_line(fake_run):
    fake_run.results = [(9, "", "context line\nreal fault")]
    with pytest.raises(env.EnvError) as exc:
        env.up(Path("/area"))
    assert "real fault" in str(exc.value)
    assert "context line" not in str(exc.value)


def test_wait_ready_returns_true_on_first_connect(monkeypatch):
    attempts = []
    sleeps = []
    timeouts = []

    def fake_connect_ex(self, address):
        attempts.append(address)
        return 0

    class FakeSocket:
        def __init__(self, *a, **k):
            pass

        def settimeout(self, t):
            timeouts.append(t)

        def connect_ex(self, address):
            return fake_connect_ex(self, address)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(env.socket, "socket", lambda *a: FakeSocket())
    monkeypatch.setattr(env.time, "sleep", lambda s: sleeps.append(s))
    assert env.wait_ready(2222, timeout_s=5) is True
    assert attempts == [("127.0.0.1", 2222)]
    assert sleeps == []
    assert timeouts == [1]


def test_wait_ready_times_out(monkeypatch):
    class RefusingSocket:
        def __init__(self, *a, **k):
            pass

        def settimeout(self, t):
            pass

        def connect_ex(self, address):
            return 111

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(env.socket, "socket", lambda *a: RefusingSocket())
    clock = {"now": 0.0}
    slept = []
    monkeypatch.setattr(env.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        env.time,
        "sleep",
        lambda s: slept.append(s) or clock.__setitem__("now", clock["now"] + s),
    )
    assert env.wait_ready(2222, timeout_s=2) is False
    assert slept and all(s == 0.5 for s in slept)
    assert clock["now"] >= 2


def test_wait_ready_stops_at_the_deadline(monkeypatch):
    class RefusingSocket:
        def __init__(self, *a, **k):
            pass

        def settimeout(self, t):
            pass

        def connect_ex(self, address):
            return 111

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(env.socket, "socket", lambda *a: RefusingSocket())
    checks = []
    clock = {"now": 0.0, "checks": 0}

    def fake_monotonic():
        return clock["now"]

    def fake_connect(self, address):
        clock["checks"] += 1
        checks.append(clock["now"])
        return 111

    monkeypatch.setattr(env.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(env.time, "sleep", lambda s: clock.__setitem__("now", clock["now"] + s))
    monkeypatch.setattr(env.socket, "socket", lambda *a: RefusingSocket())
    import unittest.mock as mock

    with mock.patch.object(
        RefusingSocket, "connect_ex", fake_connect
    ):
        assert env.wait_ready(2222, timeout_s=1) is False
    assert checks == [0.0, 0.5]
    assert clock["now"] >= 1
