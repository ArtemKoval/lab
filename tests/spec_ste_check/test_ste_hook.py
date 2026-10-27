"""Behavior tests for the PreToolUse STE hook glue."""

import json

import pytest

from spec_ste_check import hook


def _spec_root(tmp_path):
    (tmp_path / "openspec" / "specs" / "fde" / "chat").mkdir(parents=True)
    (tmp_path / "openspec" / "changes" / "active-dir").mkdir(parents=True)
    (tmp_path / "openspec" / "changes" / "archive").mkdir(parents=True)
    return tmp_path


class TestScope:
    @pytest.mark.parametrize(
        "rel",
        [
            "openspec/specs/fde/chat/spec.md",
            "openspec/specs/spec.md",
            "openspec/changes/active-dir/proposal.md",
            "openspec/changes/proposal.md",
        ],
    )
    def test_gate_paths_are_in_scope(self, rel):
        assert hook.in_gate_scope(rel) is True

    @pytest.mark.parametrize(
        "rel",
        [
            "openspec/changes/archive/old/spec.md",
            "tools/spec_ste_check/rules.py",
            "README.md",
            "openspec/other.md",
            "openspec",
        ],
    )
    def test_other_paths_are_out_of_scope(self, rel):
        assert hook.in_gate_scope(rel) is False


class TestEvaluate:
    def test_a_blockable_write_returns_2(self, tmp_path, capsys):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "Run it; stop it.\n",
            },
        }
        assert hook.evaluate(event, root) == 2
        assert "semicolon" in capsys.readouterr().err

    def test_a_clean_write_returns_0(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "Run it now.\n",
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_a_warning_only_write_returns_0(self, tmp_path, capsys):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "The job has finished.\n",
            },
        }
        assert hook.evaluate(event, root) == 0
        assert "perfect-tense" in capsys.readouterr().err

    def test_an_archive_write_passes(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/changes/archive/old/spec.md"),
                "content": "Run it; stop it.\n",
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_a_write_outside_the_repo_passes(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(tmp_path / "elsewhere/notes.md"),
                "content": "Run it; stop it.\n",
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_an_edit_reconstruction_finds_the_error(self, tmp_path, capsys):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "now",
                "new_string": "now; then stop",
            },
        }
        assert hook.evaluate(event, root) == 2
        assert "semicolon" in capsys.readouterr().err

    def test_a_missing_old_string_passes(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "absent text",
                "new_string": "whatever",
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_an_edit_to_a_missing_file_passes(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(root / "openspec/specs/ghost.md"),
                "old_string": "a",
                "new_string": "b",
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_an_unknown_tool_passes(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}
        assert hook.evaluate(event, root) == 0

    def test_a_crash_fails_open(self, tmp_path, capsys, monkeypatch):
        root = _spec_root(tmp_path)

        def boom(text, filename=""):
            raise RuntimeError("checker down")

        monkeypatch.setattr(hook.rules, "check_text", boom)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "Run it now.\n",
            },
        }
        assert hook.evaluate(event, root) == 0
        assert "fails open" in capsys.readouterr().err


class TestMain:
    def test_broken_json_fails_open(self, capsys, monkeypatch):
        monkeypatch.setattr(
            "sys.stdin", type("Stream", (), {"read": staticmethod(lambda: "{oops")})()
        )
        assert hook.main() == 0
        assert "fails open" in capsys.readouterr().err

    def test_a_valid_event_flows_through(self, tmp_path, monkeypatch):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "Run it now.\n",
            },
        }
        monkeypatch.setattr(
            "sys.stdin",
            type("Stream", (), {"read": staticmethod(lambda: json.dumps(event))})(),
        )
        assert hook.main() == 0
