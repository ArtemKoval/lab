"""The execution ledger: one append-only progress.md per plan.

The ledger survives compaction; the durable record stays in tasks.md
and git. Single-writer by design: one agent works one plan.
"""
import subprocess
from pathlib import Path

IDENTITY_PREFIX = "# plan_exec ledger - plan: "


class LedgerError(Exception):
    """The ledger operation cannot proceed."""


def _repo_root():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd()


def ledger_path(plan_file, out_dir):
    """Resolve the ledger file path for a plan."""
    plan_abs = Path(plan_file).resolve()
    if out_dir is not None:
        return plan_abs, Path(out_dir) / "progress.md"
    name = plan_abs.name
    return plan_abs, _repo_root() / ".plan_exec" / name / "progress.md"


def _identity(plan_abs):
    return IDENTITY_PREFIX + str(plan_abs)


def _read_ledger(path):
    if not path.is_file():
        raise LedgerError(f"no ledger at {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith(IDENTITY_PREFIX):
        raise LedgerError(f"ledger at {path} carries no identity line")
    return lines


def init(plan_file, out_dir):
    """Create the ledger, or accept an identical identity. Returns the path."""
    plan_abs, path = ledger_path(plan_file, out_dir)
    if path.is_file():
        lines = _read_ledger(path)
        if lines[0] == _identity(plan_abs):
            return path
        raise LedgerError(
            f"ledger at {path} belongs to {lines[0][len(IDENTITY_PREFIX):]!r},"
            f" not {str(plan_abs)!r}"
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_identity(plan_abs) + "\n", encoding="utf-8")
    except OSError as exc:
        raise LedgerError(f"cannot write ledger {path}: {exc}") from exc
    return path


def _append(plan_file, out_dir, line):
    plan_abs, path = ledger_path(plan_file, out_dir)
    lines = _read_ledger(path)
    if lines[0] != _identity(plan_abs):
        raise LedgerError(
            f"ledger at {path} belongs to {lines[0][len(IDENTITY_PREFIX):]!r},"
            f" not {str(plan_abs)!r}"
        )
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        raise LedgerError(f"cannot write ledger {path}: {exc}") from exc
    return path


def complete(plan_file, out_dir, task_id, tests, result):
    """Append one completion line."""
    line = f"Task {task_id}: complete (tests: {tests} -> {result})"
    return _append(plan_file, out_dir, line)


def task_rule(plan_file, out_dir, task_id, what, why, cost):
    """Append one ruling line."""
    line = f"Task {task_id}: Ruling: {what} - {why} - {cost}"
    return _append(plan_file, out_dir, line)


def show(plan_file, out_dir):
    """Print the ledger content."""
    _, path = ledger_path(plan_file, out_dir)
    return _read_ledger(path)
