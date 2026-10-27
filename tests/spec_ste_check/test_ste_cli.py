"""Behavior tests for the spec_ste_check CLI."""

import json

import pytest

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


_MIXED = "Run it; stop it.\nThe job has finished.\nThe job has failed.\n"


class TestHumanSummary:
    def test_the_summary_counts_errors_and_warnings_apart(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", _MIXED)
        assert cli.main([str(target)]) == 2
        captured = capsys.readouterr()
        assert captured.out.startswith(f"{target}:1: error: semicolon")
        assert captured.err == "1 errors, 2 warnings in 1 files\n"


class TestJsonMixedCounts:
    def test_the_json_report_counts_errors_and_warnings_apart(self, tmp_path, capsys):
        target = _write(tmp_path, "a.md", _MIXED)
        assert cli.main([str(target), "--json"]) == 2
        data = json.loads(capsys.readouterr().out)
        assert data["errors"] == 1
        assert data["warnings"] == 2
        assert len(data["violations"]) == 3


class TestUnreadableFileMessage:
    def test_an_unreadable_file_reports_the_path_on_stderr(self, tmp_path, capsys):
        ghost = tmp_path / "ghost.md"
        assert cli.main([str(ghost)]) == 2
        captured = capsys.readouterr()
        assert captured.err.startswith("spec_ste_check: cannot read ")
        assert str(ghost) in captured.err
        assert captured.out == ""


class TestDefaultRepoRoot:
    def test_a_bare_run_uses_the_working_directory_as_root(
        self, tmp_path, capsys, monkeypatch
    ):
        _write(tmp_path, "openspec/specs/only/spec.md", "Run it; stop it.\n")
        monkeypatch.chdir(tmp_path)
        assert cli.main([]) == 2
        captured = capsys.readouterr()
        assert "openspec/specs/only/spec.md" in captured.out
        assert captured.err == "1 errors, 0 warnings in 1 files\n"


class TestGateScopeCounts:
    def test_the_scope_summary_counts_specs_and_active_changes(
        self, tmp_path, capsys
    ):
        _write(tmp_path, "openspec/specs/bad/spec.md", "Run it; stop it.\n")
        _write(tmp_path, "openspec/changes/act/proposal.md", "The job has finished.\n")
        _write(tmp_path, "openspec/changes/archive/old/spec.md", "Run it; stop it.\n")
        assert cli.main(["--repo-root", str(tmp_path)]) == 2
        captured = capsys.readouterr()
        assert "openspec/specs/bad/spec.md" in captured.out
        assert "openspec/changes/act/proposal.md" in captured.out
        assert "archive" not in captured.out
        assert captured.err == "1 errors, 1 warnings in 2 files\n"


class TestHelpText:
    def test_help_names_the_program_the_description_and_every_option(self, capsys):
        with pytest.raises(SystemExit) as exit_info:
            cli.main(["--help"])
        assert exit_info.value.code == 0
        flat = " ".join(capsys.readouterr().out.split())
        assert "usage: spec_ste_check" in flat
        assert (
            "Report mechanical ASD-STE100 violations in spec text. positional arguments:"
            in flat
        )
        assert "paths files or trees to scan; default: the gate scope" in flat
        assert "--json print a JSON report on stdout" in flat
        assert "--repo-root REPO_ROOT repository root for the default gate scope" in flat
