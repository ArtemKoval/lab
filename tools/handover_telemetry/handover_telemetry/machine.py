"""Allowlisted host reads for the machine section.

Every field here is identity-free: no hostname, no username, no
serial numbers, no hardware addresses, and no paths under a home
directory. Each read degrades to None, and an absent field stays a
valid state. The gpu name is best effort and needs a query tool.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

_GB = 1024**3


def _is_mac() -> bool:
    return sys.platform == "darwin"


def kernel_arch() -> tuple[str, str]:
    info = os.uname()
    return info.sysname, info.machine


def read_os_release(path: str | Path = "/etc/os-release") -> str | None:
    # the locale default equals utf-8, so the encoding alternatives behave the same
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()  # pragma: no mutate
    except OSError:
        return None
    values = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"')
    return values.get("PRETTY_NAME") or values.get("NAME")


def read_cpu_model(path: str | Path = "/proc/cpuinfo") -> str | None:
    # the locale default equals utf-8, so the encoding alternatives behave the same
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()  # pragma: no mutate
    except OSError:
        return None
    for line in lines:
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def read_mem_kb(path: str | Path = "/proc/meminfo") -> int | None:
    # the locale default equals utf-8, so the encoding alternatives behave the same
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()  # pragma: no mutate
    except OSError:
        return None
    for line in lines:
        if line.startswith("MemTotal"):
            return int(line.split(":")[1].strip().split()[0])
    return None


def read_mac_cpu() -> str | None:
    return _sysctl("machdep.cpu.brand_string")


def read_mac_mem() -> int | None:
    raw = _sysctl("hw.memsize")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _sysctl(name: str) -> str | None:
    try:
        out = subprocess.run(
            ["sysctl", "-n", name],
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def detect_container(
    docker_env: Path = Path("/.dockerenv"),
    cgroup: Path = Path("/proc/1/cgroup"),
) -> str | None:
    if docker_env.exists():
        return "docker"
    try:
        # the locale default equals utf-8, so the encoding alternatives behave the same
        text = cgroup.read_text(encoding="utf-8", errors="replace")  # pragma: no mutate
    except OSError:
        return None
    for mark in ("docker", "containerd", "kubepods", "lxc"):
        if mark in text:
            return mark
    return None


def disk_total_gb(repo: Path | None) -> float | None:
    try:
        total = shutil.disk_usage(repo or Path.cwd()).total
    except OSError:
        return None
    return round(total / _GB, 1)


def read_gpu() -> str | None:
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip().splitlines()[0] if out.stdout.strip() else None


def versions() -> dict:
    return {
        "python": sys.version.split()[0],
        "git": _tool_version("git"),
    }


def _tool_version(name: str) -> str | None:
    if shutil.which(name) is None:
        return None
    try:
        out = subprocess.run(
            [name, "--version"], capture_output=True, text=True, timeout=5, shell=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip().splitlines()[0] if out.stdout.strip() else None


def collect(repo: Path | None = None) -> dict:
    kernel, arch = kernel_arch()
    if _is_mac():
        cpu_model = read_mac_cpu()
        mem = read_mac_mem()
        mem_gb = round(mem / _GB, 1) if mem else None
    else:
        cpu_model = read_cpu_model()
        mem_kb = read_mem_kb()
        mem_gb = round(mem_kb * 1024 / _GB, 1) if mem_kb else None
    return {
        "kernel": kernel,
        "arch": arch,
        "distro": None if _is_mac() else read_os_release(),
        "cpu_model": cpu_model,
        "cpu_count": os.cpu_count(),
        "mem_total_gb": mem_gb,
        "disk_total_gb": disk_total_gb(repo),
        **versions(),
        "container": detect_container(),
        "gpu": read_gpu(),
    }
