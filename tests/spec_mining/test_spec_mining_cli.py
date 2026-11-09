"""Behavior tests for the spec_mining CLI over a fabricated tree."""

import json

from spec_mining import cli

TODAY = "2026-11-09"
GIT_LOG = (
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
    "tools/widget_maker/wheel.py\n"
    "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
    "tools/widget_maker/rim.py\n"
    "tools/widget_maker/README.md\n"
    "cccccccccccccccccccccccccccccccccccccccc\n"
    "openspec/specs/residue-scan/spec.md\n"
)


class FakeRunner:
    """Answer git calls by marker, with one fixed reply."""

    def __init__(self, code=0, out="", err=""):
        self.code, self.out, self.err = code, out, err
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        return self.code, self.out, self.err


def _fabricate(root):
    """Build one minimal repo shape with two uncovered units."""
    specs = root / "openspec" / "specs" / "residue-scan"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "#### Scenario: A merged branch reports\n- **THEN** the report names it\n"
    )
    archive = root / "openspec" / "changes" / "archive" / "2026-01-01-add-x"
    (archive / "specs" / "residue-scan").mkdir(parents=True)
    (archive / "specs" / "residue-scan" / "spec.md").write_text(
        "## ADDED Requirements\n#### Scenario: A merged branch reports\n"
        "#### Scenario: A lost scenario\n"
    )
    (root / "tools" / "widget_maker").mkdir(parents=True)
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".claude" / "hooks" / "halt-gate.sh").write_text("#!/bin/bash\n")
    (root / ".claude" / "skills" / "widget-guide").mkdir(parents=True)
    (root / "crm").mkdir()
    return root


def _main(root, runner, **kw):
    return cli.main(
        ["run", "--repo-root", str(root)],
        run=runner,
        today=TODAY,
        **kw,
    )


def test_a_run_writes_the_report_set(tmp_path):
    root = _fabricate(tmp_path)
    code = _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    assert code == 0
    assert (run_dir / "coverage.json").is_file()
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "drafts" / "widget-maker" / "proposal.md").is_file()
    assert (run_dir / "drafts" / "widget-guide" / "proposal.md").is_file()


def test_a_hook_reports_with_its_stem_name(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    units = [row["unit"] for row in payload["tree"]["uncovered"]]
    assert ".claude/hooks/halt-gate" in units


def test_a_project_needs_no_data_entry_to_surface(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    units = [row["unit"] for row in payload["tree"]["uncovered"]]
    assert "crm" in units


def test_the_seeds_stay_out_of_the_planning_home(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    names = sorted(p.name for p in (root / "openspec" / "changes").iterdir())
    assert names == ["archive"]


def test_the_json_payload_carries_the_three_sections(tmp_path, capsys):
    root = _fabricate(tmp_path)
    code = cli.main(
        ["run", "--repo-root", str(root), "--json"],
        run=FakeRunner(out=GIT_LOG),
        today=TODAY,
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert set(payload) == {"tree", "drift", "ranking"}


def test_the_ranking_counts_commits_per_uncovered_area(tmp_path):
    root = _fabricate(tmp_path)
    cli.main(
        ["run", "--repo-root", str(root), "--json"],
        run=FakeRunner(out=GIT_LOG),
        today=TODAY,
    )
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    rows = {row["area"]: row["commits"] for row in payload["ranking"]}
    assert rows["tools/widget_maker"] == 2


def test_a_failed_git_read_exits_2_with_empty_stdout(tmp_path, capsys):
    root = _fabricate(tmp_path)
    code = _main(root, FakeRunner(code=128, err="fatal: not a git repository"))
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "fatal" in captured.err


def test_a_missing_specs_root_exits_2(tmp_path, capsys):
    root = tmp_path / "bare"
    root.mkdir()
    code = _main(root, FakeRunner(out=GIT_LOG))
    captured = capsys.readouterr()
    assert code == 2
    assert "openspec/specs" in captured.err


def test_a_rerun_replaces_owned_files_and_keeps_the_rest(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    (run_dir / "note.txt").write_text("hand-written\n")
    stale = run_dir / "drafts" / "gone-maker" / "proposal.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale seed\n")
    code = _main(root, FakeRunner(out=GIT_LOG))
    assert code == 0
    assert (run_dir / "note.txt").read_text() == "hand-written\n"
    assert not (run_dir / "drafts" / "gone-maker").exists()
    assert (run_dir / "drafts" / "widget-maker" / "proposal.md").is_file()
