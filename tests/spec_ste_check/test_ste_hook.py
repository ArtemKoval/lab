"""Behavior tests for the PreToolUse STE hook glue."""

import json
import locale

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
        captured = capsys.readouterr()
        assert "openspec/specs/fde/chat/spec.md:1" in captured.err
        assert "semicolon" in captured.err
        assert (
            "SPEC-STE: fix the listed sentences, then write again. "
            "Run the checker for the full report."
        ) in captured.err
        assert captured.out == ""

    def test_a_blocked_violation_text_is_truncated_to_120_chars(
        self, tmp_path, capsys
    ):
        root = _spec_root(tmp_path)
        sentence = " ".join(["alpha"] * 30)
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": sentence + "\n",
            },
        }
        assert hook.evaluate(event, root) == 2
        err = capsys.readouterr().err
        assert sentence[:120] in err
        assert sentence[:121] not in err

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

    def test_an_edit_tool_without_a_file_path_fails_open(self, tmp_path):
        root = _spec_root(tmp_path)
        event = {
            "tool_name": "Edit",
            "tool_input": {"old_string": "a", "new_string": "b"},
        }
        assert hook.evaluate(event, root) == 0

    def test_an_edit_reads_the_file_as_utf8_in_a_c_locale(self, tmp_path, capsys):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Le café est prêt.\n", encoding="utf-8")
        previous = locale.setlocale(locale.LC_CTYPE)
        try:
            locale.setlocale(locale.LC_CTYPE, "C")
            event = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(target),
                    "old_string": "café",
                    "new_string": "café; très bien",
                },
            }
            assert hook.evaluate(event, root) == 2
            assert "semicolon" in capsys.readouterr().err
        finally:
            locale.setlocale(locale.LC_CTYPE, previous)

    def test_a_relative_path_resolves_against_the_root_not_the_cwd(
        self, tmp_path, monkeypatch
    ):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        monkeypatch.chdir(target.parent)
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "openspec/specs/fde/chat/spec.md",
                "old_string": "now",
                "new_string": "now; then stop",
            },
        }
        assert hook.evaluate(event, root) == 2

    def test_a_multiedit_reconstruction_is_checked(self, tmp_path, capsys):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(target),
                "edits": [
                    {"old_string": "now", "new_string": "now; then stop"},
                ],
            },
        }
        assert hook.evaluate(event, root) == 2
        assert "semicolon" in capsys.readouterr().err

    def test_an_edit_without_old_string_prepends_the_new_text(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "new_string": "Stop; halt. ",
            },
        }
        assert hook.evaluate(event, root) == 2

    def test_a_replace_all_edit_that_clears_every_semicolon_passes(
        self, tmp_path
    ):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it; stop it. Sit; wait a bit.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "; ",
                "new_string": ", ",
                "replace_all": True,
            },
        }
        assert hook.evaluate(event, root) == 0

    def test_a_replace_all_edit_that_adds_an_error_blocks(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now. Do it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "now",
                "new_string": "now; then stop",
                "replace_all": True,
            },
        }
        assert hook.evaluate(event, root) == 2

    def test_an_edit_without_replace_all_fixes_only_the_first_hit(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it; stop it. Sit; wait a bit.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "; ",
                "new_string": ", ",
            },
        }
        assert hook.evaluate(event, root) == 2


class TestPostEditText:
    def test_an_edit_applies_at_the_old_string(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "now",
                "new_string": "then stop",
            },
        }
        assert hook._post_edit_text(event, root) == "Run it then stop.\n"

    def test_an_edit_without_new_string_deletes_the_old_string(self, tmp_path):
        root = _spec_root(tmp_path)
        target = root / "openspec/specs/fde/chat/spec.md"
        target.write_text("Run it now.\n", encoding="utf-8")
        event = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "now",
            },
        }
        assert hook._post_edit_text(event, root) == "Run it .\n"


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


class TestPostEditTextDirect:
    def test_a_write_without_a_target_gives_none(self, tmp_path):
        event = {"tool_name": "Write", "tool_input": {}}
        assert hook._post_edit_text(event, tmp_path) is None

    def test_an_unknown_tool_gives_none(self, tmp_path):
        event = {
            "tool_name": "Bash",
            "tool_input": {"file_path": str(tmp_path / "x.md"), "command": "echo"},
        }
        assert hook._post_edit_text(event, tmp_path) is None

    def test_a_blocking_event_through_the_env_root_exits_2(
        self, tmp_path, capsys, monkeypatch
    ):
        root = _spec_root(tmp_path)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(root / "openspec/specs/fde/chat/spec.md"),
                "content": "Run it; stop it.\n",
            },
        }
        monkeypatch.setattr(
            "sys.stdin",
            type("Stream", (), {"read": staticmethod(lambda: json.dumps(event))})(),
        )
        assert hook.main() == 2
        assert "semicolon" in capsys.readouterr().err
