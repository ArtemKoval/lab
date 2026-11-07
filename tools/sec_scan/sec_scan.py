"""Scan this repository for possibly exposed keys and secrets, and optionally
revoke what it found.

The scan walks the working tree, skipping vendored and dependency directories,
and matches known provider secret shapes plus high-entropy assignments to
credential-looking names. With --history it walks `git log -p` the same way.
Each finding names its file, line, provider, and the revoke path.

Revocation is destructive and provider-gated: it runs only behind --revoke.
An OpenRouter key is disabled through the provisioning API when
OPENROUTER_PROVISIONING_KEY is in the environment (disable, not delete —
recoverable). Every other provider gets its exact manual revoke command and
no network call. Without --revoke the tool makes no network call at all.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Directories never scanned: vendored code, dependency installs, build output,
# and the tool's own test fixtures.
SKIPPED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".metrics",
    ".cc_logging",
    "coverage",
}

# Known provider secret shapes, with each provider's revoke path.
PROVIDER_PATTERNS = [
    (
        "OpenRouter",
        re.compile(r"sk-or-v1-[0-9a-f]{64}"),
        "openrouter",
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "aws",
    ),
    (
        "GitHub token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{36,255}\b"),
        "github",
    ),
    (
        "GitHub fine-grained token",
        re.compile(r"\bgithub_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}\b"),
        "github",
    ),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
        "slack",
    ),
]

# An assignment to a credential-looking name, whose value is examined for
# entropy. The name patterns are deliberately broad; the entropy threshold
# keeps prose and ids out.
ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?:export\s+)?([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)"
    r"[A-Z0-9_]*)\s*=\s*[\"']?([^\s\"'#]{16,})",
    re.MULTILINE,
)

# A PEM private-key block.
PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"
)

# A Shannon entropy above this on an assignment value reads as a secret.
ENTROPY_THRESHOLD = 3.5

REVOKE_COMMANDS = {
    "openrouter": (
        "OpenRouter: revoke at https://openrouter.ai/keys (or let --revoke "
        "disable it through the provisioning API)"
    ),
    "aws": (
        "AWS: aws iam update-access-key --access-key-id <key> --status Inactive "
        "(then delete it)"
    ),
    "github": (
        "GitHub: Settings > Developer settings > Personal access tokens > "
        "the token > Delete, or gh api -X DELETE /orgs/<org>/actions/runners"
    ),
    "slack": "Slack: api.slack.com/apps > your app > OAuth & Permissions > Revoke",
    "private key": (
        "Private key: rotate the key pair everywhere it is trusted, then remove "
        "the file from history (git filter-repo)"
    ),
}


@dataclass
class Finding:
    """One possibly exposed secret, named by file and line."""

    file: str
    line: int
    provider: str
    kind: str
    preview: str
    revoke_path: str
    commit: str = ""
    key_hash: str = ""


@dataclass
class Report:
    """Everything the scan found, with the revocation outcomes."""

    findings: list[Finding] = field(default_factory=list)
    revoked: list[str] = field(default_factory=list)
    revoke_failures: list[str] = field(default_factory=list)
    manual: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "findings": [
                {
                    "file": f.file,
                    "line": f.line,
                    "provider": f.provider,
                    "kind": f.kind,
                    "preview": f.preview,
                    "revoke_path": f.revoke_path,
                    **({"commit": f.commit} if f.commit else {}),
                }
                for f in self.findings
            ],
            "revoked": self.revoked,
            "revoke_failures": self.revoke_failures,
            "manual": self.manual,
        }


def shannon_entropy(value: str) -> float:
    """The Shannon entropy of the value, in bits per character."""
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    total = len(value)
    return -sum(
        (count / total) * math.log2(count / total) for count in counts.values()
    )


def skipped(path: Path) -> bool:
    return any(part in SKIPPED_DIRS for part in path.parts)


def classify(match: str) -> tuple[str, str] | None:
    """Return (provider, kind) for a known provider shape, or None."""
    for provider, pattern, _ in PROVIDER_PATTERNS:
        if pattern.fullmatch(match):
            return provider, "provider key"
    if PRIVATE_KEY.search(match):
        return "private key", "private key block"
    return None


def _rule_hits(text: str) -> list[tuple[int, str, str, str, str | None]]:
    """Return one tuple per rule hit: (offset, provider, kind, source, revoke_key).

    The offset drives the line attribution of each caller. The tree scan
    maps it through the blob, the diff scan uses the hunk line counter.
    """
    hits: list[tuple[int, str, str, str, str | None]] = []
    for provider, pattern, revoke_key in PROVIDER_PATTERNS:
        for match in pattern.finditer(text):
            hits.append((match.start(), provider, "provider key", match.group(0), revoke_key))
    for match in ASSIGNMENT_PATTERN.finditer(text):
        name, value = match.group(1), match.group(2)
        if classify(value):
            continue
        if shannon_entropy(value) >= ENTROPY_THRESHOLD:
            hits.append((match.start(), "unknown", f"high-entropy assignment to {name}", value, None))
    if PRIVATE_KEY.search(text):
        hits.append((PRIVATE_KEY.search(text).start(), "private key", "private key block", "-----BEGIN …", None))
    return hits


def _finding_from_hit(
    rel: str,
    line: int,
    provider: str,
    kind: str,
    source: str,
    revoke_key: str | None,
    commit: str,
) -> Finding:
    """Build one Finding from a rule hit."""
    revoke_path = REVOKE_COMMANDS[revoke_key] if revoke_key else REVOKE_COMMANDS["private key"]
    return Finding(
        file=rel,
        line=line,
        provider=provider,
        kind=kind,
        preview=source[:12] + "…",
        revoke_path=revoke_path,
        commit=commit,
        key_hash=source if revoke_key else "",
    )


def scan_text(rel: str, text: str, report: Report, commit: str = "") -> None:
    """Examine one text blob and append every finding to the report."""
    for offset, provider, kind, source, revoke_key in _rule_hits(text):
        line = text.count("\n", 0, offset) + 1
        report.findings.append(
            _finding_from_hit(rel, line, provider, kind, source, revoke_key, commit)
        )


HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")


def _new_path(line: str) -> str:
    """Return the new-file path from one `+++` header, or '' for a deletion."""
    origin = line[4:].removeprefix("b/")
    return "" if origin == "/dev/null" else origin


def parse_diff(text: str) -> list[tuple[str, int, str]]:
    """Parse one unified diff into (path, new-file line, added line) rows.

    Only added lines are collected. A deletion changes nothing, and a
    context line advances the new-file line counter. The parser collects
    only after a hunk header for the current file, so header noise
    between files never produces a row.
    """
    added: list[tuple[str, int, str]] = []
    path = ""
    lineno = 0
    in_hunk = False
    for line in text.splitlines():
        if line.startswith("+++ "):
            path = _new_path(line)
            in_hunk = False
            continue
        if line.startswith("@@"):
            match = HUNK_RE.match(line)
            if match:
                lineno = int(match.group(1))
                in_hunk = True
            continue
        if not path or not in_hunk:
            continue
        if line.startswith("+"):
            added.append((path, lineno, line[1:]))
            lineno += 1
        elif line.startswith("-"):
            continue
        else:
            lineno += 1
    return added


def _env_literals(value: str | None) -> list[str]:
    """Return the non-empty operator literals from an environment value."""
    if not value:
        return []
    return [item for item in value.splitlines() if item.strip()]


class DiffScanError(RuntimeError):
    """The diff scan could not read the diff. The caller fails closed."""


def _default_git_runner(argv, cwd=None):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)


def scan_diff(root, ref, report, literals=None, runner=None):
    """Scan the added lines of one git diff. Fails closed on a git error."""
    run = runner or _default_git_runner
    result = run(["git", "diff", "--unified=0", ref], cwd=root)
    if result.returncode != 0:
        raise DiffScanError(result.stderr.strip() or "git exited with an error")
    for path, lineno, line in parse_diff(result.stdout):
        for offset, provider, kind, source, revoke_key in _rule_hits(line):
            report.findings.append(
                _finding_from_hit(path, lineno, provider, kind, source, revoke_key, "")
            )
        literals_here = literals if literals is not None else _env_literals(os.environ.get("SECRET_SCAN_LITERALS"))
        for literal in literals_here:
            if literal in line:
                digest = hashlib.sha256(literal.encode("utf-8")).hexdigest()[:12]
                report.findings.append(
                    Finding(
                        file=path,
                        line=lineno,
                        provider="operator literal",
                        kind=f"sha256:{digest}",
                        preview=digest + "…",
                        revoke_path="Rotate the literal at its source, then update the secret",
                        commit="",
                    )
                )


def scan_tree(root: Path, report: Report) -> None:
    """Walk the working tree, skipping vendored and dependency paths."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or skipped(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        scan_text(str(path.relative_to(root)), text, report)


def scan_history(root: Path, report: Report, runner=None) -> None:
    """Walk `git log -p` and scan every blob the history carries.

    A git failure returns silently, so the tree scan still decides the
    exit code. That fail-open posture predates the diff scan, which
    fails closed instead.
    """
    run = runner or _default_git_runner
    result = run(
        ["git", "log", "-p", "--all", "--format=commit %H"],
        cwd=root,
    )
    if result.returncode != 0:
        return
    _scan_log(result.stdout, report)


def _scan_log(log: str, report: Report) -> None:
    """Scan every blob one `git log -p` output carries."""
    commit = ""
    path = ""
    blob: list[str] = []
    for line in log.splitlines():
        if line.startswith("commit "):
            if blob:
                scan_text(path, "\n".join(blob), report, commit)
            commit, path, blob = line[7:], "", []
        elif line.startswith("+++ b/"):
            path = line[6:]
            blob = [line]
        elif path and blob is not None and not line.startswith("-"):
            blob.append(line)
    if blob:
        scan_text(path, "\n".join(blob), report, commit)


def disable_openrouter_key(key: str, provisioning_key: str) -> tuple[bool, str]:
    """Disable one OpenRouter key through the provisioning API. Returns
    (ok, reason)."""
    key_hash = key.split("-", 3)[-1] if key.count("-") >= 3 else key
    request = urllib.request.Request(
        f"https://openrouter.ai/api/v1/keys/{key_hash}",
        method="PATCH",
        data=json.dumps({"disabled": True}).encode(),
        headers={"Authorization": f"Bearer {provisioning_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as answer:
            return answer.status == 200, f"HTTP {answer.status}"
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except urllib.error.URLError as error:
        return False, str(error)


def revoke(report: Report, report_json: dict) -> int:
    """Run the gated revocation over the findings. Returns the process exit."""
    provisioning = os.environ.get("OPENROUTER_PROVISIONING_KEY", "")
    for finding in report.findings:
        label = f"{finding.file}:{finding.line} ({finding.provider})"
        if finding.provider.lower() == "openrouter" and provisioning:
            ok, reason = disable_openrouter_key(finding.key_hash, provisioning)
            if ok:
                report.revoked.append(label)
                report_json["revoked"].append(label)
            else:
                report.revoke_failures.append(f"{label}: {reason}")
                report_json["revoke_failures"].append(f"{label}: {reason}")
                report.manual.append(f"{label}: {finding.revoke_path}")
        else:
            report.manual.append(f"{label}: {finding.revoke_path}")
    for line in report.revoked:
        print(f"REVOKED {line}")
    for line in report.revoke_failures:
        print(f"REVOKE FAILED {line}")
    for line in report.manual:
        print(f"MANUAL REVOTE REQUIRED — see report: {line}")
    if report.revoke_failures:
        return 2
    return 0


def print_report(report: Report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.as_dict(), indent=2))
        return
    if not report.findings:
        print("No findings.")
        return
    for finding in report.findings:
        where = f"{finding.file}:{finding.line}"
        if finding.commit:
            where += f" (in {finding.commit[:12]})"
        print(f"{where} — {finding.provider}: {finding.kind} [{finding.preview}]")
        print(f"    revoke: {finding.revoke_path}")


def main(argv=None, runner=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="The repository root to scan")
    parser.add_argument("--json", action="store_true", help="Machine output")
    parser.add_argument("--history", action="store_true", help="Also scan git history")
    parser.add_argument(
        "--diff",
        metavar="REF",
        default=None,
        help="Scan only the lines the diff adds against REF",
    )
    parser.add_argument(
        "--revoke",
        action="store_true",
        help="Disable found OpenRouter keys through the provisioning API",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 2

    report = Report()
    if args.diff:
        literals = _env_literals(os.environ.get("SECRET_SCAN_LITERALS"))
        try:
            scan_diff(root, args.diff, report, literals=literals, runner=runner)
        except DiffScanError as error:
            print(f"diff scan failed: {error}", file=sys.stderr)
            return 2
    else:
        scan_tree(root, report)
        if args.history:
            scan_history(root, report)
    print_report(report, args.json)

    exit_code = 2 if report.findings else 0
    if args.revoke and report.findings:
        exit_code = max(exit_code, revoke(report, report.as_dict()))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
