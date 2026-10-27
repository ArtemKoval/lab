"""Behavior tests for the spec_ste_check CLI."""

import json

from spec_ste_check import cli


def _write(tmp_path, rel, text):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestExplicitPaths:
    def test_a_clean_file_exits_0(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", "Run it now.\n")
        assert cli.main([str(target)]) == 0
        assert capsys.readouterr().out == ""

    def test_a_violation_exits_2_and_names_the_spot(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", "Run it; stop it.\n")
        assert cli.main([str(target)]) == 2
        out = capsys.readouterr().out
        assert f"{target}:1" in out
        assert "semicolon" in out

    def test_a_tree_walks_only_markdown(self, tmp_path, capsys):
        _write(tmp_path, "docs/b.md", "It provides nothing.\n")
        _write(tmp_path, "docs/c.txt", "Run it; stop it.\n")
        assert cli.main([str(tmp_path)]) == 2
        out = capsys.readouterr().out
        assert "b.md" in out
        assert "c.txt" not in out

    def test_json_output_parses_and_carries_records(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", "Run it; stop it.\n")
        assert cli.main([str(target), "--json"]) == 2
        data = json.loads(capsys.readouterr().out)
        assert data["errors"] == 1
        record = data["violations"][0]
        assert record["file"] == str(target)
        assert record["line"] == 1
        assert record["rule"] == "semicolon"
        assert record["severity"] == "error"
        assert record["text"] == "Run it; stop it."

    def test_an_unreadable_file_exits_2(self, tmp_path):
        ghost = tmp_path / "ghost.md"
        assert cli.main([str(ghost)]) == 2


class TestGateScope:
    def test_bare_run_scans_specs_and_active_changes_but_not_archive(
        self, tmp_path, capsys
    ):
        _write(tmp_path, "openspec/specs/clean/spec.md", "Run it now.\n")
        _write(
            tmp_path,
            "openspec/changes/active-dir/proposal.md",
            "It provides nothing.\n",
        )
        _write(tmp_path, "openspec/changes/archive/old/spec.md", "Run it; stop it.\n")
        assert cli.main(["--repo-root", str(tmp_path)]) == 2
        out = capsys.readouterr().out
        assert "active-dir/proposal.md" in out
        assert "archive" not in out

    def test_bare_run_on_a_clean_scope_exits_0(self, tmp_path):
        _write(tmp_path, "openspec/specs/clean/spec.md", "Run it now.\n")
        _write(tmp_path, "openspec/changes/archive/old/spec.md", "Run it; stop it.\n")
        assert cli.main(["--repo-root", str(tmp_path)]) == 0

    def test_a_root_without_openspec_is_clean(self, tmp_path):
        assert cli.main(["--repo-root", str(tmp_path)]) == 0


class TestSeverities:
    def test_a_warning_only_file_exits_0(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", "The job has finished.\n")
        assert cli.main([str(target), "--json"]) == 0
        data = json.loads(capsys.readouterr().out)
        assert data["errors"] == 0
        assert data["warnings"] == 1
