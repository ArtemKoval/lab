"""Tests for the allowlisted machine reads. Parsing runs against
fixture files; host-dependent values stay tolerant assertions."""

import sys
from pathlib import Path

from handover_telemetry import machine

FIXTURES = Path(__file__).parent / "fixtures"


def test_os_release_prefers_pretty_name():
    path = FIXTURES / "machine" / "os-release"
    assert machine.read_os_release(path) == "Ubuntu 24.04 LTS"


def test_os_release_missing_is_none(tmp_path):
    assert machine.read_os_release(tmp_path / "none") is None


def test_cpu_model_from_proc():
    path = FIXTURES / "machine" / "cpuinfo"
    assert machine.read_cpu_model(path) == "AMD Ryzen 9 Test CPU"


def test_cpu_model_missing_is_none(tmp_path):
    assert machine.read_cpu_model(tmp_path / "none") is None


def test_mem_kb_from_meminfo():
    path = FIXTURES / "machine" / "meminfo"
    assert machine.read_mem_kb(path) == 32 * 1024 * 1024


def test_mem_kb_missing_is_none(tmp_path):
    assert machine.read_mem_kb(tmp_path / "none") is None


def test_container_from_dockerenv(tmp_path):
    (tmp_path / ".dockerenv").write_text("", encoding="utf-8")
    assert machine.detect_container(tmp_path, tmp_path / "cgroup") == "docker"


def test_container_from_cgroup(tmp_path):
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("12:blkio:/docker/abc123\n", encoding="utf-8")
    assert machine.detect_container(tmp_path / "nope", cgroup) == "docker"


def test_container_none_on_bare_host(tmp_path):
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("12:blkio:/init.scope\n", encoding="utf-8")
    assert machine.detect_container(tmp_path / "nope", cgroup) is None


def test_disk_total_gb_on_repo(tmp_path):
    (tmp_path / "x").write_text("x", encoding="utf-8")
    gb = machine.disk_total_gb(tmp_path)
    assert gb is not None and gb > 0


def test_gpu_none_without_query_tool(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: None)
    assert machine.read_gpu() is None


def test_versions_carry_python_and_git():
    got = machine.versions()
    assert got["python"].startswith("3.")
    assert got["git"].startswith("git version")


def test_collect_returns_allowlisted_fields(tmp_path):
    got = machine.collect(repo=tmp_path)
    expected = {
        "kernel",
        "arch",
        "distro",
        "cpu_model",
        "cpu_count",
        "mem_total_gb",
        "disk_total_gb",
        "python",
        "git",
        "node",
        "container",
        "gpu",
    }
    assert expected == set(got)
    assert "hostname" not in got
    dumped = str(got)
    assert "/home/" not in dumped


def test_collect_reads_linux_files(monkeypatch, tmp_path):
    monkeypatch.setattr(machine, "_is_mac", lambda: False)
    monkeypatch.setattr(machine, "read_os_release", lambda path=None: "Test Linux")
    monkeypatch.setattr(machine, "read_cpu_model", lambda path=None: "Test CPU")
    monkeypatch.setattr(machine, "read_mem_kb", lambda path=None: 1024 * 1024)
    monkeypatch.setattr(machine, "read_mac_cpu", lambda: "unused")
    monkeypatch.setattr(machine, "read_mac_mem", lambda: 0)
    got = machine.collect(repo=tmp_path)
    assert got["distro"] == "Test Linux"
    assert got["cpu_model"] == "Test CPU"
    assert got["mem_total_gb"] == pytest_approx(1.0)


def pytest_approx(value):
    import pytest

    return pytest.approx(value)


def test_collect_reads_mac_files(monkeypatch, tmp_path):
    monkeypatch.setattr(machine, "_is_mac", lambda: True)
    monkeypatch.setattr(machine, "read_os_release", lambda path=None: None)
    monkeypatch.setattr(machine, "read_cpu_model", lambda path=None: None)
    monkeypatch.setattr(machine, "read_mem_kb", lambda path=None: None)
    monkeypatch.setattr(machine, "read_mac_cpu", lambda: "Apple M Test")
    monkeypatch.setattr(machine, "read_mac_mem", lambda: 16 * 1024**3)
    monkeypatch.setattr(sys, "platform", "darwin")
    got = machine.collect(repo=tmp_path)
    assert got["cpu_model"] == "Apple M Test"
    assert got["mem_total_gb"] == pytest_approx(16.0)
