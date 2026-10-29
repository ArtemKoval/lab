"""Tolerance tests for the machine reads: missing files, broken
tools, and absent fields all degrade to None."""

import subprocess
from pathlib import Path

from handover_telemetry import machine


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_os_release_without_equals_signs(tmp_path):
    path = _write(tmp_path / "os-release", "junk line\n")
    assert machine.read_os_release(path) is None


def test_cpuinfo_without_model_name(tmp_path):
    path = _write(tmp_path / "cpuinfo", "processor : 0\n")
    assert machine.read_cpu_model(path) is None


def test_meminfo_without_total(tmp_path):
    path = _write(tmp_path / "meminfo", "MemFree: 1 kB\n")
    assert machine.read_mem_kb(path) is None


def test_container_cgroup_missing(tmp_path):
    assert machine.detect_container(tmp_path / "nope", tmp_path / "also-none") is None


def test_sysctl_missing_tool_returns_none(monkeypatch):
    monkeypatch.setattr(machine.subprocess, "run", _raise_os_error)
    assert machine.read_mac_cpu() is None
    assert machine.read_mac_mem() is None


def _raise_os_error(*args, **kwargs):
    raise OSError("no sysctl here")


def test_sysctl_failed_run_returns_none(monkeypatch):
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _failed_out())
    assert machine.read_mac_cpu() is None


class _FailedOut:
    returncode = 1
    stdout = ""


def _failed_out():
    return _FailedOut()


def test_sysctl_bad_number_returns_none(monkeypatch):
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _ok_out("not-a-number"))
    assert machine.read_mac_mem() is None


class _OkOut:
    def __init__(self, text):
        self.returncode = 0
        self.stdout = text


def _ok_out(text):
    return _OkOut(text)


def test_tool_version_when_tool_is_missing(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: None)
    assert machine._tool_version("git") is None


def test_tool_version_when_tool_fails(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _failed_out())
    assert machine._tool_version("git") is None


def test_tool_version_when_tool_times_out(monkeypatch):
    def slow(*args, **kwargs):
        raise subprocess.TimeoutExpired("git", 5)

    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(machine.subprocess, "run", slow)
    assert machine._tool_version("git") is None


def test_tool_version_with_empty_output(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/git")
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _ok_out(""))
    assert machine._tool_version("git") is None


def test_gpu_when_query_tool_fails(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _failed_out())
    assert machine.read_gpu() is None


def test_gpu_with_empty_output(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _ok_out(""))
    assert machine.read_gpu() is None


def test_gpu_with_a_name(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(machine.subprocess, "run", lambda *a, **k: _ok_out("Test GPU A\nTest GPU B\n"))
    assert machine.read_gpu() == "Test GPU A"


def test_disk_total_gb_on_missing_path(tmp_path):
    assert machine.disk_total_gb(tmp_path / "missing") is None


def test_mac_collect_uses_mac_reads(monkeypatch, tmp_path):
    monkeypatch.setattr(machine, "_is_mac", lambda: True)
    monkeypatch.setattr(machine, "read_mac_cpu", lambda: "Apple Test")
    monkeypatch.setattr(machine, "read_mac_mem", lambda: 2 * 1024**3)
    got = machine.collect(repo=tmp_path)
    assert got["cpu_model"] == "Apple Test"
    assert got["mem_total_gb"] == 2.0
    assert got["distro"] is None


def test_gpu_when_query_tool_raises(monkeypatch):
    def slow(*args, **kwargs):
        raise subprocess.TimeoutExpired("nvidia-smi", 5)

    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(machine.subprocess, "run", slow)
    assert machine.read_gpu() is None
