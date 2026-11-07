"""Gate-integrity guard for protected gate paths in pull requests.

esf protects its gates from the tree that runs them. This guard is the
pull-request form of that idea: a pull request whose diff touches a
protected gate path fails CI unless the pull request body carries the
acknowledgment line. The operator merge is the acknowledgment.

The guard runs inside the hermetic suite and is active only on
pull_request events, where GitHub provides GITHUB_BASE_REF and
GITHUB_EVENT_PATH. Outside CI the test skips.
"""

import fnmatch
import json
import os
import subprocess

import pytest

MARKER_LINE = "gate-integrity: acknowledged"

PROTECTED_PATTERNS = (
    ".claude/hooks/*",
    ".claude/settings.json",
    "pytest.ini",
    "tests/conftest.py",
    "tests/*/conftest.py",
    "tools/crapper/*",
    "tools/dryer/*",
    "tools/mutator/*",
    ".github/workflows/*",
    # The guard protects itself, so its own weakening needs the marker.
    "tests/claude_infra/test_gate_integrity.py",
)

_FAILURE_MESSAGE = (
    "gate-integrity guard: the pull request touches protected gate "
    "paths without the acknowledgment. Protected paths hit: {hits}. "
    "When the operator accepts the gate change, add the line "
    "'{marker}' to the pull request body."
)


def protected_hits(changed_files, patterns=PROTECTED_PATTERNS):
    """Return the changed files that match one protected pattern."""
    return sorted(
        name for name in changed_files
        if any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
    )


def body_has_marker(body):
    """Return True when the body carries the acknowledgment line."""
    if not isinstance(body, str):
        return False
    return any(line.strip() == MARKER_LINE for line in body.splitlines())


def guard_decision(changed_files, body, patterns=PROTECTED_PATTERNS):
    """Return the protected hits when the body lacks the marker."""
    hits = protected_hits(changed_files, patterns)
    if not hits or body_has_marker(body):
        return []
    return hits


def collect_changed_files(base_ref, runner):
    """Return the pull request changed files through one git call."""
    argv = [
        "git", "diff", "--name-only", "--diff-filter=d",
        "origin/{}...HEAD".format(base_ref),
    ]
    output = runner(argv)
    return [line for line in output.splitlines() if line.strip()]


def _default_runner(argv):
    completed = subprocess.run(argv, capture_output=True, text=True, check=True)
    return completed.stdout


def _event_body(event_path):
    """Return the pull request body from the event payload file."""
    try:
        with open(event_path, encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, ValueError):
        return ""
    pull = payload.get("pull_request") if isinstance(payload, dict) else None
    body = pull.get("body") if isinstance(pull, dict) else None
    return body if isinstance(body, str) else ""


def _on_pull_request():
    return os.environ.get("GITHUB_EVENT_NAME") == "pull_request"


def test_protected_hits_match_each_pattern_class():
    assert protected_hits([]) == []
    assert protected_hits(["README.md", "reports/x.md"]) == []
    assert protected_hits([".claude/hooks/cc-logging.sh"]) == [".claude/hooks/cc-logging.sh"]
    assert protected_hits([".claude/settings.json"]) == [".claude/settings.json"]
    assert protected_hits(["pytest.ini"]) == ["pytest.ini"]
    assert protected_hits(["tests/conftest.py"]) == ["tests/conftest.py"]
    assert protected_hits(["tests/peak_hours_gate/conftest.py"]) == [
        "tests/peak_hours_gate/conftest.py",
    ]
    assert protected_hits(["tools/crapper/crapper/__init__.py"]) == [
        "tools/crapper/crapper/__init__.py",
    ]
    assert protected_hits([".github/workflows/tests.yml"]) == [".github/workflows/tests.yml"]
    assert protected_hits(["tests/claude_infra/test_gate_integrity.py"]) == [
        "tests/claude_infra/test_gate_integrity.py",
    ]


def test_protected_hits_come_back_sorted():
    hits = protected_hits([
        ".github/workflows/tests.yml",
        ".claude/settings.json",
    ])
    assert hits == [".claude/settings.json", ".github/workflows/tests.yml"]


def test_protected_hits_accept_custom_patterns():
    hits = protected_hits(["a/b.py", "c/d.py"], patterns=("a/*",))
    assert hits == ["a/b.py"]


def test_body_carries_the_marker_only_as_a_whole_line():
    assert body_has_marker("gate-integrity: acknowledged") is True
    assert body_has_marker("  gate-integrity: acknowledged  ") is True
    assert body_has_marker("text\ngate-integrity: acknowledged\ntail") is True
    assert body_has_marker("see gate-integrity: acknowledged below") is False
    assert body_has_marker("gate-integrity: denied") is False
    assert body_has_marker("") is False
    assert body_has_marker(None) is False


def test_guard_decision_fails_closed_without_the_marker():
    changed = [".github/workflows/tests.yml"]
    assert guard_decision(changed, "") == changed
    assert guard_decision(changed, None) == changed


def test_guard_decision_passes_with_the_marker():
    changed = [".github/workflows/tests.yml"]
    assert guard_decision(changed, "notes\n" + MARKER_LINE) == []


def test_guard_decision_passes_without_protected_hits():
    assert guard_decision(["README.md"], "") == []


def test_collect_changed_files_filters_blank_lines():
    def fake_runner(argv):
        assert argv[-1] == "origin/main...HEAD"
        return "a.py\n\nb.py\n"
    assert collect_changed_files("main", fake_runner) == ["a.py", "b.py"]


def test_event_body_reads_the_pull_request_body(tmp_path):
    event = tmp_path / "event.json"
    event.write_text('{"pull_request": {"body": "x\\ngate-integrity: acknowledged"}}', encoding="utf-8")
    assert _event_body(str(event)) == "x\ngate-integrity: acknowledged"


def test_event_body_stays_empty_on_a_broken_payload(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert _event_body(str(broken)) == ""
    missing = tmp_path / "missing.json"
    assert _event_body(str(missing)) == ""
    empty_pull = tmp_path / "empty.json"
    empty_pull.write_text('{"pull_request": {"body": null}}', encoding="utf-8")
    assert _event_body(str(empty_pull)) == ""


@pytest.mark.skipif(not _on_pull_request(), reason="runs only on pull_request events")
def test_pull_request_protects_the_gate_paths():
    changed = collect_changed_files(os.environ.get("GITHUB_BASE_REF", "main"), _default_runner)
    body = _event_body(os.environ.get("GITHUB_EVENT_PATH", ""))
    hits = guard_decision(changed, body)
    if hits:
        pytest.fail(_FAILURE_MESSAGE.format(hits=", ".join(hits), marker=MARKER_LINE))
