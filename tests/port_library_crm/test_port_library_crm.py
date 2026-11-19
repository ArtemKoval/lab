"""Unit tests for the port_library_crm script: parsing, classification,
reporting, verification, and the git-driving flow with a fake runner."""

import json

import pytest

from port_library_crm import port_library_crm as plc


class TestParseMergeTreeOutput:
    def test_parse_returns_tree_oid_from_first_line(self):
        out = "abc123\n100644 aa11 1\tfile.txt\n"
        tree, _ = plc.parse_merge_tree_output(out)
        assert tree == "abc123"

    def test_parse_collects_conflicted_paths_once_across_stages(self):
        out = (
            "abc123\n"
            "100644 aa11 1\tCLAUDE.md\n"
            "100644 bb22 2\tCLAUDE.md\n"
            "100644 cc33 3\tCLAUDE.md\n"
            "100644 dd44 1\t.coveragerc\n"
            "\n"
            "Auto-merging CLAUDE.md\n"
            "CONFLICT (content): Merge conflict in CLAUDE.md\n"
        )
        _, conflicted = plc.parse_merge_tree_output(out)
        assert conflicted == ["CLAUDE.md", ".coveragerc"]

    def test_parse_returns_empty_conflicts_when_merge_is_clean(self):
        tree, conflicted = plc.parse_merge_tree_output("abc123\n")
        assert tree == "abc123"
        assert conflicted == []

    def test_parse_skips_lines_whose_stage_is_not_a_conflict_stage(self):
        out = (
            "abc123\n"
            "100644 aa11 1\tCLAUDE.md\n"
            "100644 bb22 2\tCLAUDE.md\n"
            "100644 cc33 3\tCLAUDE.md\n"
            "100644 dd44 9\tstray.txt\n"
        )
        _, conflicted = plc.parse_merge_tree_output(out)
        assert conflicted == ["CLAUDE.md"]

    def test_parse_treats_only_the_first_line_as_the_tree(self):
        out = (
            "100644 zz99 2\tCLAUDE.md\n"
            "abc123\n"
            "100644 aa11 1\t.coveragerc\n"
        )
        tree, conflicted = plc.parse_merge_tree_output(out)
        assert tree == "100644 zz99 2\tCLAUDE.md"
        assert conflicted == [".coveragerc"]


class TestClassifyChangedFiles:
    NAME_STATUS = (
        "A\tcrm/domains/library/rules.py\n"
        "M\tcrm/backend/main.py\n"
        "D\ttools/gone.py\n"
        "A\topenspec/specs/crm-library-domain/spec.md\n"
        "M\topenspec/specs/crm-engine/spec.md\n"
    )

    def test_added_files_land_in_the_copied_bucket(self):
        buckets = plc.classify_changed_files(self.NAME_STATUS, ("openspec/specs/",))
        assert buckets["copied"] == ["crm/domains/library/rules.py"]

    def test_modified_files_land_in_the_transferred_bucket(self):
        buckets = plc.classify_changed_files(self.NAME_STATUS, ("openspec/specs/",))
        assert buckets["transferred"] == ["crm/backend/main.py"]

    def test_deleted_files_land_in_the_deletions_bucket(self):
        buckets = plc.classify_changed_files(self.NAME_STATUS, ("openspec/specs/",))
        assert buckets["deletions"] == ["tools/gone.py"]

    def test_excluded_prefix_removes_paths_from_every_bucket(self):
        buckets = plc.classify_changed_files(self.NAME_STATUS, ("openspec/specs/",))
        assert buckets["excluded"] == [
            "openspec/specs/crm-library-domain/spec.md",
            "openspec/specs/crm-engine/spec.md",
        ]
        assert buckets["copied"] == ["crm/domains/library/rules.py"]

    def test_status_scores_are_stripped_from_rename_entries(self):
        buckets = plc.classify_changed_files("R100\told.py\tpath.py\n", ())
        assert buckets["renamed"] == [("old.py", "path.py")]


class TestBuildReport:
    def test_report_carries_the_deletions_row(self):
        report = plc.build_report(
            copied=["a.py"],
            transferred=["b.py"],
            deletions=[],
            conflicted=["c.py"],
            excluded=["d.py"],
            base="base",
            child_head="head",
        )
        assert report["deletions"] == []

    def test_report_counts_add_to_the_total(self):
        report = plc.build_report(
            copied=["a.py", "a2.py"],
            transferred=["b.py"],
            deletions=[],
            conflicted=["c.py"],
            excluded=["d.py"],
            base="base",
            child_head="head",
        )
        assert report["total"] == 4

    def test_markdown_renders_a_deletions_row_with_a_count(self):
        report = plc.build_report(
            copied=["a.py"],
            transferred=["b.py"],
            deletions=["gone.py"],
            conflicted=[],
            excluded=[],
            base="base",
            child_head="head",
        )
        text = plc.render_markdown(report)
        assert "deletions: 1" in text
        assert "gone.py" in text

    def test_total_counts_deletions_when_the_set_is_not_empty(self):
        report = plc.build_report(
            copied=["a.py", "a2.py"],
            transferred=["b.py"],
            deletions=["gone.py"],
            conflicted=[],
            excluded=[],
            base="base",
            child_head="head",
        )
        assert report["total"] == 4

    def test_markdown_names_the_conflict_files(self):
        report = plc.build_report(
            copied=[], transferred=[], deletions=[], conflicted=["CLAUDE.md"],
            excluded=[], base="base", child_head="head",
        )
        assert "CLAUDE.md" in plc.render_markdown(report)


class TestVerifyExpected:
    def test_no_violations_when_the_applied_set_matches(self):
        violations = plc.verify_expected(
            applied={"a.py", "b.py"},
            expected={"a.py", "b.py"},
            deletions=[],
        )
        assert violations == []

    def test_an_unexpected_applied_path_is_a_violation(self):
        violations = plc.verify_expected(
            applied={"a.py", "surprise.py"},
            expected={"a.py"},
            deletions=[],
        )
        assert any("surprise.py" in v for v in violations)

    def test_a_missing_expected_path_is_a_violation(self):
        violations = plc.verify_expected(
            applied={"a.py"},
            expected={"a.py", "missing.py"},
            deletions=[],
        )
        assert any("missing.py" in v for v in violations)

    def test_a_deletion_is_always_a_violation_for_this_port(self):
        violations = plc.verify_expected(applied=set(), expected=set(), deletions=["x.py"])
        assert len(violations) == 1


class FakeRunner:
    """Stands in for run_git with scripted outputs and a call log."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, args, cwd=None):
        self.calls.append(list(args))
        entry = self.outputs.pop(0)
        if isinstance(entry, Exception):
            raise entry
        out, code = entry
        if code != 0:
            raise plc.GitError(args, code, out)
        return out


def write_scripted_runner(monkeypatch, outputs):
    fake = FakeRunner(outputs)
    monkeypatch.setattr(plc, "run_git", fake)
    return fake


class TestApplyPort:
    def _outputs(self, tree):
        name_status = (
            "A\tcrm/domains/library/rules.py\n"
            "M\tcrm/backend/main.py\n"
            "M\tCLAUDE.md\n"
            "A\topenspec/specs/crm-library-domain/spec.md\n"
            "M\topenspec/specs/crm-engine/spec.md\n"
        )
        merge_out = (
            f"{tree}\n"
            "100644 aa11 1\tCLAUDE.md\n"
            "100644 bb22 2\tCLAUDE.md\n"
            "100644 cc33 3\tCLAUDE.md\n"
            "\n"
            "CONFLICT (content): Merge conflict in CLAUDE.md\n"
        )
        return [
            ("", 0),          # fetch
            ("fedcba9876543210fedcba9876543210fedcba98", 0),  # rev-parse FETCH_HEAD
            (merge_out, 0),   # merge-tree
            (name_status, 0),  # diff HEAD..tree
            ("", 0),          # checkout tree -- .
            ("", 0),          # checkout HEAD -- excluded modified path
            ("", 0),          # rm excluded added path
        ]

    def test_apply_writes_merged_files_and_restores_excluded_paths(
        self, tmp_path, monkeypatch
    ):
        fake = write_scripted_runner(monkeypatch, self._outputs("tree1"))
        report = plc.apply_port(
            runner=fake,
            repo_root=tmp_path,
            child_source="/tmp/child",
            child_ref="main",
            base="base",
            report_dir=tmp_path / "reports",
        )
        assert ["checkout", "tree1", "--", "."] in fake.calls
        assert ["checkout", "HEAD", "--", "openspec/specs/crm-engine/spec.md"] in fake.calls
        assert report["conflicted"] == ["CLAUDE.md"]
        assert report["deletions"] == []

    def test_apply_records_the_resolved_child_oid_in_the_report(
        self, tmp_path, monkeypatch
    ):
        fake = write_scripted_runner(monkeypatch, self._outputs("tree1"))
        report = plc.apply_port(
            runner=fake,
            repo_root=tmp_path,
            child_source="/tmp/child",
            child_ref="main",
            base="base",
            report_dir=tmp_path / "reports",
        )
        assert report["child_head"] == "fedcba9876543210fedcba9876543210fedcba98"
        assert ["rev-parse", "FETCH_HEAD"] in fake.calls

    def test_apply_writes_the_report_json_and_markdown(self, tmp_path, monkeypatch):
        report_dir = tmp_path / "reports"
        plc.apply_port(
            runner=FakeRunner(self._outputs("tree1")),
            repo_root=tmp_path,
            child_source="/tmp/child",
            child_ref="head",
            base="base",
            report_dir=report_dir,
        )
        assert (report_dir / "report.json").exists()
        assert (report_dir / "report.md").exists()

    def test_apply_creates_missing_report_parents_and_reruns_in_place(
        self, tmp_path, monkeypatch
    ):
        report_dir = tmp_path / "deeply" / "nested" / "reports"
        for _ in range(2):
            plc.apply_port(
                runner=FakeRunner(self._outputs("tree1")),
                repo_root=tmp_path,
                child_source="/tmp/child",
                child_ref="head",
                base="base",
                report_dir=report_dir,
            )
        assert (report_dir / "report.md").exists()

    def test_apply_exits_2_with_remediation_when_fetch_fails(
        self, tmp_path, monkeypatch
    ):
        outputs = [("fatal: bad source", 128)]
        fake = write_scripted_runner(monkeypatch, outputs)
        with pytest.raises(plc.OperationalFailure) as exc:
            plc.apply_port(
                runner=fake,
                repo_root=tmp_path,
                child_source="/tmp/child",
                child_ref="head",
                base="base",
                report_dir=tmp_path / "reports",
            )
        assert "fetch" in exc.value.remediation.lower()

    def test_apply_accepts_merge_tree_exit_1_with_conflicts(
        self, tmp_path, monkeypatch
    ):
        merge_out = (
            "tree9\n"
            "100644 aa11 1\tCLAUDE.md\n"
            "100644 bb22 2\tCLAUDE.md\n"
            "100644 cc33 3\tCLAUDE.md\n"
            "\n"
            "CONFLICT (content): Merge conflict in CLAUDE.md\n"
        )
        outputs = [
            ("", 0),
            ("fedcba9876543210fedcba9876543210fedcba98", 0),
            plc.GitError(["merge-tree"], 1, merge_out),
            ("A\tCLAUDE.md\n", 0),
            ("", 0),
            ("", 0),
            ("", 0),
        ]
        fake = write_scripted_runner(monkeypatch, outputs)
        report = plc.apply_port(
            runner=fake,
            repo_root=tmp_path,
            child_source="/tmp/child",
            child_ref="main",
            base="base",
            report_dir=tmp_path / "reports",
        )
        assert report["conflicted"] == ["CLAUDE.md"]
        assert report["total"] == 1

    def test_apply_refuses_a_nonempty_deletion_set(self, tmp_path, monkeypatch):
        outputs = [
            ("", 0),
            ("fedcba9876543210fedcba9876543210fedcba98", 0),
            ("tree1\n", 0),
            ("D\ttools/gone.py\n", 0),
        ]
        fake = write_scripted_runner(monkeypatch, outputs)
        with pytest.raises(plc.OperationalFailure) as exc:
            plc.apply_port(
                runner=fake,
                repo_root=tmp_path,
                child_source="/tmp/child",
                child_ref="head",
                base="base",
                report_dir=tmp_path / "reports",
            )
        assert "deletion" in exc.value.remediation.lower()


class TestCli:
    def test_cli_json_output_carries_the_counts(self, tmp_path, monkeypatch, capsys):
        outputs = [
            ("", 0),
            ("fedcba9876543210fedcba9876543210fedcba98", 0),
            ("tree1\n", 0),
            ("A\tcrm/domains/library/rules.py\n", 0),
            ("", 0),
        ]
        write_scripted_runner(monkeypatch, outputs)
        code = plc.main(
            [
                "--json",
                "--repo-root", str(tmp_path),
                "--child-source", "/tmp/child",
                "--report-dir", str(tmp_path / "reports"),
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert code == 0
        assert payload["copied"] == ["crm/domains/library/rules.py"]
        assert payload["ok"] is True

    def test_cli_failure_json_names_the_remediation(
        self, tmp_path, monkeypatch, capsys
    ):
        outputs = [("fatal: bad source", 128)]
        write_scripted_runner(monkeypatch, outputs)
        code = plc.main(
            [
                "--json",
                "--repo-root", str(tmp_path),
                "--child-source", "/tmp/child",
                "--report-dir", str(tmp_path / "reports"),
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert code == 2
        assert payload["ok"] is False
        assert "fetch" in payload["remediation"].lower()

    def test_cli_plain_output_names_the_report_path(
        self, tmp_path, monkeypatch, capsys
    ):
        outputs = [
            ("", 0),
            ("fedcba9876543210fedcba9876543210fedcba98", 0),
            ("tree1\n", 0),
            ("A\tcrm/domains/library/rules.py\n", 0),
            ("", 0),
        ]
        write_scripted_runner(monkeypatch, outputs)
        report_dir = tmp_path / "reports"
        code = plc.main(
            [
                "--repo-root", str(tmp_path),
                "--child-source", "/tmp/child",
                "--report-dir", str(report_dir),
            ]
        )
        out = capsys.readouterr().out
        assert code == 0
        assert f"report: {report_dir / 'report.md'}" in out
