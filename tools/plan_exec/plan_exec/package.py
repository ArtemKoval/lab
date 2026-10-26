"""Package a commit range for review: one markdown file with the commit
list, the stat summary, and the full diff. Read-only against the repo."""
import subprocess
from pathlib import Path


class PackageError(Exception):
    """The range cannot be packaged."""


def _git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PackageError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _resolve(repo, ref):
    return _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


def write_package(repo, base, head, out_dir):
    """Write review-package-<base7>-<head7>.md and return the path."""
    repo = Path(repo)
    base_sha = _resolve(repo, base)
    head_sha = _resolve(repo, head)
    if base_sha == head_sha:
        raise PackageError(f"base and head resolve to the same commit {base_sha[:7]}")
    log = _git(repo, "log", "--oneline", f"{base_sha}..{head_sha}")
    stat_summary = _git(repo, "diff", "--stat", f"{base_sha}..{head_sha}")
    diff = _git(repo, "diff", "-U10", f"{base_sha}..{head_sha}")
    out_dir = Path(out_dir)
    target = out_dir / f"review-package-{base_sha[:7]}-{head_sha[:7]}.md"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "# Review package "
            f"{base_sha[:7]}..{head_sha[:7]}\n\n"
            "## Commits\n\n```\n"
            f"{log.rstrip()}\n```\n\n"
            "## Stat\n\n```\n"
            f"{stat_summary.rstrip()}\n```\n\n"
            "## Diff\n\n```diff\n"
            f"{diff.rstrip()}\n```\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise PackageError(f"cannot write package {target}: {exc}") from exc
    return target
