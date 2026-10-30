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


def scan_text(rel: str, text: str, report: Report, commit: str = "") -> None:
    """Examine one text blob and append every finding to the report."""
    for provider, pattern, revoke_key in PROVIDER_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            report.findings.append(
                Finding(
                    file=rel,
                    line=line,
                    provider=provider,
                    kind="provider key",
                    preview=match.group(0)[:12] + "…",
                    revoke_path=REVOKE_COMMANDS[revoke_key],
                    commit=commit,
                    key_hash=match.group(0),
                )
            )
    for match in ASSIGNMENT_PATTERN.finditer(text):
        name, value = match.group(1), match.group(2)
        if classify(value):
            continue
        if shannon_entropy(value) >= ENTROPY_THRESHOLD:
            line = text.count("\n", 0, match.start()) + 1
            report.findings.append(
                Finding(
                    file=rel,
                    line=line,
                    provider="unknown",
                    kind=f"high-entropy assignment to {name}",
                    preview=value[:12] + "…",
                    revoke_path=REVOKE_COMMANDS["private key"],
                    commit=commit,
                )
            )
    if PRIVATE_KEY.search(text):
        line = text.count("\n", 0, PRIVATE_KEY.search(text).start()) + 1
        report.findings.append(
            Finding(
                file=rel,
                line=line,
                provider="private key",
                kind="private key block",
                preview="-----BEGIN …",
                revoke_path=REVOKE_COMMANDS["private key"],
                commit=commit,
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


def scan_history(root: Path, report: Report) -> None:
    """Walk `git log -p` and scan every blob the history carries."""
    result = subprocess.run(
        ["git", "log", "-p", "--all", "--format=commit %H"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return
    commit = ""
    path = ""
    blob: list[str] = []
    for line in result.stdout.splitlines():
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="The repository root to scan")
    parser.add_argument("--json", action="store_true", help="Machine output")
    parser.add_argument("--history", action="store_true", help="Also scan git history")
    parser.add_argument(
        "--revoke",
        action="store_true",
        help="Disable found OpenRouter keys through the provisioning API",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 2

    report = Report()
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
