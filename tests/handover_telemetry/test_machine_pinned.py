"""Pinned tests for the machine reads: the exact argv and kwargs of
every subprocess query, the exact parse results for the proc files,
the exact rounding, and the exact collect dict on a stubbed host."""

import sys
from pathlib import Path

import pytest

from handover_telemetry import machine

PROC_KWARGS = {"capture_output": True, "text": True, "timeout": 5, "shell": False}


class _Out:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def _capture(monkeypatch, stdout=""):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        return _Out(0, stdout)

    monkeypatch.setattr(machine.subprocess, "run", fake_run)
    return calls


def test_sysctl_runs_the_pinned_query(monkeypatch):
    calls = _capture(monkeypatch, stdout="  2147483648\n")
    assert machine._sysctl("hw.memsize") == "2147483648"
    assert calls == [(["sysctl", "-n", "hw.memsize"], PROC_KWARGS)]


def test_sysctl_blank_output_is_none(monkeypatch):
    _capture(monkeypatch, stdout="   \n")
    assert machine._sysctl("hw.memsize") is None


def test_read_mac_cpu_queries_the_brand_string(monkeypatch):
    calls = _capture(monkeypatch, stdout="Apple M4 Pro\n")
    assert machine.read_mac_cpu() == "Apple M4 Pro"
    assert calls == [(["sysctl", "-n", "machdep.cpu.brand_string"], PROC_KWARGS)]


def test_read_mac_mem_parses_the_byte_count(monkeypatch):
    calls = _capture(monkeypatch, stdout="2147483648\n")
    assert machine.read_mac_mem() == 2147483648
    assert calls == [(["sysctl", "-n", "hw.memsize"], PROC_KWARGS)]


def test_read_mac_mem_rejects_text(monkeypatch):
    _capture(monkeypatch, stdout="not-a-number\n")
    assert machine.read_mac_mem() is None


def test_gpu_queries_nvidia_smi(monkeypatch):
    calls = _capture(monkeypatch, stdout="GPU A\nGPU B\n")
    monkeypatch.setattr(
        machine.shutil,
        "which",
        lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None,
    )
    assert machine.read_gpu() == "GPU A"
    assert calls == [
        (["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], PROC_KWARGS)
    ]


def test_gpu_without_the_tool_skips_the_query(monkeypatch):
    calls = _capture(monkeypatch)
    monkeypatch.setattr(machine.shutil, "which", lambda name: None)
    assert machine.read_gpu() is None
    assert calls == []


def test_tool_version_queries_the_tool(monkeypatch):
    calls = _capture(monkeypatch, stdout="git version 2.43.0\nmore\n")
    monkeypatch.setattr(machine.shutil, "which", lambda name: "/usr/bin/git")
    assert machine._tool_version("git") == "git version 2.43.0"
    assert calls == [(["git", "--version"], PROC_KWARGS)]


def test_versions_pin_the_two_tools(monkeypatch):
    monkeypatch.setattr(machine.shutil, "which", lambda name: f"/usr/bin/{name}")
    outs = {"git": _Out(0, "git version 2.43.0\n")}

    def fake_run(argv, **kwargs):
        return outs[argv[0]]

    monkeypatch.setattr(machine.subprocess, "run", fake_run)
    assert machine.versions() == {
        "python": sys.version.split()[0],
        "git": "git version 2.43.0",
    }


def test_os_release_strips_quotes_and_spaces(tmp_path):
    path = tmp_path / "os-release"
    path.write_text('  PRETTY_NAME = "Ubuntu 24.04.3 LTS"  \n', encoding="utf-8")
    assert machine.read_os_release(path) == "Ubuntu 24.04.3 LTS"


def test_os_release_falls_back_to_the_name(tmp_path):
    path = tmp_path / "os-release"
    path.write_text("NAME=Debian\n", encoding="utf-8")
    assert machine.read_os_release(path) == "Debian"


def test_os_release_empty_pretty_name_falls_back(tmp_path):
    path = tmp_path / "os-release"
    path.write_text('PRETTY_NAME=""\nNAME=Debian\n', encoding="utf-8")
    assert machine.read_os_release(path) == "Debian"


def test_os_release_splits_on_the_first_equals_sign(tmp_path):
    path = tmp_path / "os-release"
    path.write_text('PRETTY_NAME="Ubuntu=24.04"\nNAME=Debian\n', encoding="utf-8")
    assert machine.read_os_release(path) == "Ubuntu=24.04"


def test_os_release_quote_strip_leaves_neighbors(tmp_path):
    path = tmp_path / "os-release"
    path.write_text('PRETTY_NAME=X"Xanadu OS"\n', encoding="utf-8")
    assert machine.read_os_release(path) == 'X"Xanadu OS'


def test_os_release_reads_the_default_path():
    if not Path("/etc/os-release").is_file():
        pytest.skip("no /etc/os-release on this host")
    assert machine.read_os_release() is not None


def test_cpu_model_stops_at_the_first_model_name(tmp_path):
    path = tmp_path / "cpuinfo"
    path.write_text(
        "processor : 0\nmodel name\t: First CPU\nmodel name: Second CPU\n",
        encoding="utf-8",
    )
    assert machine.read_cpu_model(path) == "First CPU"


def test_cpu_model_strips_the_value(tmp_path):
    path = tmp_path / "cpuinfo"
    path.write_text("model name:   Spaced CPU  \n", encoding="utf-8")
    assert machine.read_cpu_model(path) == "Spaced CPU"


def test_cpu_model_splits_on_the_first_colon(tmp_path):
    path = tmp_path / "cpuinfo"
    path.write_text("model name: X: Y CPU\n", encoding="utf-8")
    assert machine.read_cpu_model(path) == "X: Y CPU"


def test_cpu_model_reads_the_default_path():
    if not Path("/proc/cpuinfo").is_file():
        pytest.skip("no /proc/cpuinfo on this host")
    assert machine.read_cpu_model() is not None


def test_mem_kb_reads_the_first_total(tmp_path):
    path = tmp_path / "meminfo"
    path.write_text("MemTotal:  12345 kB junk\nMemTotal: 999 kB\n", encoding="utf-8")
    assert machine.read_mem_kb(path) == 12345


def test_mem_kb_reads_a_value_without_a_space(tmp_path):
    path = tmp_path / "meminfo"
    path.write_text("MemTotal:12345 kB\n", encoding="utf-8")
    assert machine.read_mem_kb(path) == 12345


def test_mem_kb_reads_the_default_path():
    if not Path("/proc/meminfo").is_file():
        pytest.skip("no /proc/meminfo on this host")
    assert machine.read_mem_kb() is not None


@pytest.mark.parametrize("mark", ["docker", "containerd", "kubepods", "lxc"])
def test_container_detects_each_runtime(tmp_path, mark):
    cgroup = tmp_path / "cgroup"
    cgroup.write_text(f"12:pids:/system.slice/{mark}-scope\n", encoding="utf-8")
    assert machine.detect_container(tmp_path / "nope", cgroup) == mark


def test_container_docker_env_wins_over_the_cgroup(tmp_path):
    (tmp_path / ".dockerenv").write_text("", encoding="utf-8")
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("12:blkio:/lxc/abc\n", encoding="utf-8")
    assert machine.detect_container(tmp_path / ".dockerenv", cgroup) == "docker"


def test_container_replaces_bad_bytes(tmp_path):
    cgroup = tmp_path / "cgroup"
    cgroup.write_bytes(b"\xff\ndocker\n")
    assert machine.detect_container(tmp_path / "nope", cgroup) == "docker"


class _Usage:
    def __init__(self, total):
        self.total = total


def test_disk_total_gb_rounds_to_one_decimal(monkeypatch, tmp_path):
    seen = []

    def fake_usage(path):
        seen.append(path)
        return _Usage(int(1234.567 * 1024**3))

    monkeypatch.setattr(machine.shutil, "disk_usage", fake_usage)
    assert machine.disk_total_gb(tmp_path) == 1234.6
    assert seen == [tmp_path]


def test_disk_total_gb_uses_the_cwd_without_a_repo(monkeypatch):
    seen = []

    def fake_usage(path):
        seen.append(path)
        return _Usage(1024**3)

    monkeypatch.setattr(machine.shutil, "disk_usage", fake_usage)
    assert machine.disk_total_gb(None) == 1.0
    assert seen == [Path.cwd()]


def test_is_mac_follows_sys_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert machine._is_mac() is True
    monkeypatch.setattr(sys, "platform", "linux")
    assert machine._is_mac() is False


def _stub_linux_reads(monkeypatch, mem_kb):
    monkeypatch.setattr(machine, "_is_mac", lambda: False)
    monkeypatch.setattr(machine, "kernel_arch", lambda: ("Linux", "x86_64"))
    monkeypatch.setattr(
        machine, "read_os_release", lambda path="/etc/os-release": "Ubuntu 24.04.3 LTS"
    )
    monkeypatch.setattr(
        machine, "read_cpu_model", lambda path="/proc/cpuinfo": "AMD Ryzen 9 7950X"
    )
    monkeypatch.setattr(machine, "read_mem_kb", lambda path="/proc/meminfo": mem_kb)
    monkeypatch.setattr(
        machine, "read_mac_cpu", lambda: pytest.fail("mac read on linux")
    )
    monkeypatch.setattr(
        machine, "read_mac_mem", lambda: pytest.fail("mac read on linux")
    )
    monkeypatch.setattr(machine, "read_gpu", lambda: "NVIDIA GeForce RTX 4090")
    monkeypatch.setattr(
        machine,
        "detect_container",
        lambda docker_env=None, cgroup=None: "docker",
    )
    monkeypatch.setattr(
        machine,
        "versions",
        lambda: {
            "python": "3.12.3",
            "git": "git version 2.43.0",
        },
    )
    monkeypatch.setattr(machine.os, "cpu_count", lambda: 32)


LINUX_DICT = {
    "kernel": "Linux",
    "arch": "x86_64",
    "distro": "Ubuntu 24.04.3 LTS",
    "cpu_model": "AMD Ryzen 9 7950X",
    "cpu_count": 32,
    "mem_total_gb": 62.4,
    "disk_total_gb": 500.0,
    "python": "3.12.3",
    "git": "git version 2.43.0",
    "container": "docker",
    "gpu": "NVIDIA GeForce RTX 4090",
}


def test_collect_pins_the_linux_dict(monkeypatch, tmp_path):
    _stub_linux_reads(monkeypatch, mem_kb=65478656)
    seen = []

    def fake_disk(repo):
        seen.append(repo)
        return 500.0

    monkeypatch.setattr(machine, "disk_total_gb", fake_disk)
    assert machine.collect(repo=tmp_path) == LINUX_DICT
    assert seen == [tmp_path]


def test_collect_linux_zero_memory_is_none(monkeypatch, tmp_path):
    _stub_linux_reads(monkeypatch, mem_kb=0)
    monkeypatch.setattr(machine, "disk_total_gb", lambda repo: 500.0)
    got = machine.collect(repo=tmp_path)
    assert got["mem_total_gb"] is None


def _stub_mac_reads(monkeypatch, mem_bytes):
    monkeypatch.setattr(machine, "_is_mac", lambda: True)
    monkeypatch.setattr(machine, "kernel_arch", lambda: ("Darwin", "arm64"))
    monkeypatch.setattr(
        machine, "read_os_release", lambda path="/etc/os-release": pytest.fail("mac")
    )
    monkeypatch.setattr(
        machine, "read_cpu_model", lambda path="/proc/cpuinfo": pytest.fail("mac")
    )
    monkeypatch.setattr(
        machine, "read_mem_kb", lambda path="/proc/meminfo": pytest.fail("mac")
    )
    monkeypatch.setattr(machine, "read_mac_cpu", lambda: "Apple M4 Pro")
    monkeypatch.setattr(machine, "read_mac_mem", lambda: mem_bytes)
    monkeypatch.setattr(machine, "read_gpu", lambda: "NVIDIA GeForce RTX 4090")
    monkeypatch.setattr(
        machine,
        "detect_container",
        lambda docker_env=None, cgroup=None: "docker",
    )
    monkeypatch.setattr(
        machine,
        "versions",
        lambda: {
            "python": "3.12.3",
            "git": "git version 2.43.0",
        },
    )
    monkeypatch.setattr(machine.os, "cpu_count", lambda: 32)


def test_collect_pins_the_mac_dict(monkeypatch, tmp_path):
    _stub_mac_reads(monkeypatch, mem_bytes=18721873664)
    monkeypatch.setattr(machine, "disk_total_gb", lambda repo: 500.0)
    assert machine.collect(repo=tmp_path) == {
        "kernel": "Darwin",
        "arch": "arm64",
        "distro": None,
        "cpu_model": "Apple M4 Pro",
        "cpu_count": 32,
        "mem_total_gb": 17.4,
        "disk_total_gb": 500.0,
        "python": "3.12.3",
        "git": "git version 2.43.0",
        "container": "docker",
        "gpu": "NVIDIA GeForce RTX 4090",
    }


def test_collect_mac_zero_memory_is_none(monkeypatch, tmp_path):
    _stub_mac_reads(monkeypatch, mem_bytes=0)
    monkeypatch.setattr(machine, "disk_total_gb", lambda repo: 500.0)
    assert machine.collect(repo=tmp_path)["mem_total_gb"] is None
