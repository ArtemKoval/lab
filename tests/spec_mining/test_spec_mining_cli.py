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
    (archive / "specs" / "widget-maker").mkdir(parents=True)
    (archive / "specs" / "widget-maker" / "spec.md").write_text(
        "## ADDED Requirements\n#### Scenario: A lost scenario\n"
        "## REMOVED Requirements\n#### Scenario: A removed scenario\n"
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


def test_the_json_stdout_matches_the_stored_payload(tmp_path, capsys):
    root = _fabricate(tmp_path)
    cli.main(
        ["run", "--repo-root", str(root), "--json"],
        run=FakeRunner(out=GIT_LOG),
        today=TODAY,
    )
    stdout = capsys.readouterr().out
    stored = (
        root / "reports" / "spec_mining" / TODAY / "coverage.json"
    ).read_text()
    assert stdout == stored
    assert stdout == json.dumps(json.loads(stdout), indent=2, sort_keys=True) + "\n"


def test_a_seed_prints_zero_commits_for_an_unranked_unit():
    text = cli._seed_text("cap", [{"unit": "tools/a"}], {}, [])
    assert "- unit `tools/a` with 0 commits" in text


def test_the_seed_write_is_idempotent(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    payload = json.loads((run_dir / "coverage.json").read_text())
    cli._write_drafts(run_dir, payload)
    seed = run_dir / "drafts" / "widget-maker" / "proposal.md"
    assert seed.is_file()


def test_a_hook_counts_commits_through_its_extension(tmp_path):
    root = _fabricate(tmp_path)
    log = (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        ".claude/hooks/halt-gate.sh\n"
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        ".claude/hooks/halt-gate.sh\n"
        "cccccccccccccccccccccccccccccccccccccccc\n"
        "tools/widget_maker/wheel.py\n"
    )
    _main(root, FakeRunner(out=log))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    rows = {row["area"]: row["commits"] for row in payload["ranking"]}
    assert rows[".claude/hooks/halt-gate"] == 2
    assert rows["tools/widget_maker"] == 1


def test_a_nested_archived_delta_is_drift_scanned(tmp_path):
    root = _fabricate(tmp_path)
    nested = (
        root / "openspec" / "changes" / "archive" / "2026-01-02-add-nested"
        / "specs" / "fde" / "onboarding"
    )
    nested.mkdir(parents=True)
    (nested / "spec.md").write_text(
        "## ADDED Requirements\n#### Scenario: A nested scenario\n"
    )
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    row = next(
        r for r in payload["drift"] if r["capability"] == "fde/onboarding"
    )
    assert row["scenario"] == "A nested scenario"
    assert row["missing_spec"] is True


def test_a_change_with_no_delta_stays_off_the_drift_scan(tmp_path):
    root = _fabricate(tmp_path)
    (root / "openspec" / "changes" / "archive" / "2026-01-03-no-delta").mkdir(
        parents=True
    )
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    changes = {row["change"] for row in payload["drift"]}
    assert "2026-01-03-no-delta" not in changes


def test_the_drift_scans_a_deeply_nested_delta_only_once(tmp_path):
    root = _fabricate(tmp_path)
    nested = (
        root / "openspec" / "changes" / "archive" / "2026-01-02-add-nested"
        / "specs" / "fde" / "onboarding"
    )
    nested.mkdir(parents=True)
    (nested / "spec.md").write_text(
        "## ADDED Requirements\n#### Scenario: A nested scenario   \n"
    )
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    rows = [
        r for r in payload["drift"] if r["capability"] == "fde/onboarding"
    ]
    assert [r["scenario"] for r in rows] == ["A nested scenario"]


def test_the_fallback_git_message_names_the_code(tmp_path, capsys):
    root = _fabricate(tmp_path)
    code = _main(root, FakeRunner(code=1, err=""))
    captured = capsys.readouterr()
    assert code == 2
    assert "exited with code 1" in captured.err


def test_the_report_marks_missing_specs(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    report = (root / "reports" / "spec_mining" / TODAY / "report.md").read_text()
    assert "(missing spec)" in report


def test_a_dotted_unit_gets_a_kebab_candidate(tmp_path):
    root = _fabricate(tmp_path)
    (root / "tools" / "a.b").mkdir()
    _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    assert (run_dir / "drafts" / "a-b" / "proposal.md").is_file()


def test_an_empty_candidate_writes_no_collapsed_seed(tmp_path):
    root = _fabricate(tmp_path)
    (root / "tools" / ".hidden").mkdir()
    (root / "tools" / "-").mkdir()
    _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    assert not (run_dir / "drafts" / "proposal.md").exists()
    report = (run_dir / "report.md").read_text()
    assert "tools/-" in report


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


def test_a_missing_archive_root_exits_2(tmp_path, capsys):
    root = tmp_path / "half"
    (root / "openspec" / "specs").mkdir(parents=True)
    code = _main(root, FakeRunner(out=GIT_LOG))
    captured = capsys.readouterr()
    assert code == 2
    assert "archive" in captured.err


def test_the_git_call_pins_the_subprocess_contract(tmp_path, monkeypatch):
    root = _fabricate(tmp_path)
    seen = {}

    class FakeProc:
        returncode = 0
        stdout = GIT_LOG
        stderr = ""

    def fake_run(argv, **kwargs):
        seen.update(kwargs)
        if kwargs.get("check") is not False:
            raise AssertionError("check must stay False")
        if kwargs.get("capture_output") is not True:
            raise AssertionError("capture_output must stay True")
        if kwargs.get("text") is not True:
            raise AssertionError("text must stay True")
        return FakeProc()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    code = cli.main(["run", "--repo-root", str(root)])
    assert code == 0
    assert seen["check"] is False


def test_the_project_walk_skips_dot_dirs_and_loose_files(tmp_path):
    root = _fabricate(tmp_path)
    (root / ".custom").mkdir()
    (root / "loose.txt").write_text("not a unit\n")
    code = _main(root, FakeRunner(out=GIT_LOG))
    assert code == 0
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    units = [row["unit"] for row in payload["tree"]["uncovered"]]
    assert ".custom" not in units
    assert "loose.txt" not in units


def test_a_delta_whose_removed_section_comes_first(tmp_path):
    root = _fabricate(tmp_path)
    delta = (
        root / "openspec" / "changes" / "archive" / "2026-01-01-add-x"
        / "specs" / "widget-maker" / "spec.md"
    )
    delta.write_text(
        "## REMOVED Requirements\n#### Scenario: A gone scenario\n"
        "## ADDED Requirements\n#### Scenario: A kept scenario\n"
    )
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    names = [row["scenario"] for row in payload["drift"]]
    assert "A kept scenario" in names
    assert "A gone scenario" not in names


def test_the_seed_file_ends_with_a_newline(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    seed = (
        root / "reports" / "spec_mining" / TODAY / "drafts"
        / "widget-maker" / "proposal.md"
    ).read_text()
    assert seed.endswith("\n")
    assert seed.startswith("# Proposal: add-widget-maker (seed)\n")


def test_the_coverage_payload_file_ends_with_a_newline(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    text = (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    assert text.endswith("\n")


def test_the_drafts_hold_exactly_the_candidates(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    run_dir = root / "reports" / "spec_mining" / TODAY
    names = sorted(p.name for p in (run_dir / "drafts").iterdir())
    assert names == ["crm", "halt-gate", "widget-guide", "widget-maker"]
    report = (run_dir / "report.md").read_text()
    assert report.startswith("# Spec mining report\n")
    assert "Uncovered units: 4" in report


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


def test_the_default_dispatch_runs_git_through_subprocess(tmp_path, monkeypatch):
    root = _fabricate(tmp_path)
    calls = []

    class FakeProc:
        returncode = 0
        stdout = GIT_LOG
        stderr = ""

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return FakeProc()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    code = cli.main(["run", "--repo-root", str(root)])
    assert code == 0
    assert calls and calls[0][0] == "git"


def test_a_failed_git_program_exits_2(tmp_path, monkeypatch):
    root = _fabricate(tmp_path)

    def fake_run(*args, **kwargs):
        raise OSError("no git binary")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    assert cli.main(["run", "--repo-root", str(root)]) == 2


def test_a_removed_delta_section_stays_out_of_the_drift(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    names = [row["scenario"] for row in payload["drift"]]
    assert "A removed scenario" not in names


def test_a_seed_carries_the_drift_of_its_candidate(tmp_path):
    root = _fabricate(tmp_path)
    _main(root, FakeRunner(out=GIT_LOG))
    seed = (root / "reports" / "spec_mining" / TODAY / "drafts" / "widget-maker" / "proposal.md").read_text()
    assert "drift: `A lost scenario` from 2026-01-01-add-x" in seed


def test_the_repo_root_flows_through_the_argv(tmp_path):
    root = _fabricate(tmp_path)
    code = cli.main(
        ["run", "--repo-root", str(root)], run=FakeRunner(out=GIT_LOG), today=TODAY
    )
    assert code == 0


def test_the_git_parse_skips_blank_and_orphan_lines(tmp_path):
    root = _fabricate(tmp_path)
    messy = (
        "tools/widget_maker/orphan.py\n"
        "\n"
        "dddddddddddddddddddddddddddddddddddddddd\n"
        "\n"
        "tools/widget_maker/wheel.py\n"
        "\n"
    )
    code = _main(root, FakeRunner(out=messy))
    assert code == 0
    payload = json.loads(
        (root / "reports" / "spec_mining" / TODAY / "coverage.json").read_text()
    )
    rows = {row["area"]: row["commits"] for row in payload["ranking"]}
    assert rows["tools/widget_maker"] == 1
