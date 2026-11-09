"""Behavior tests for the pure scans in spec_mining.core."""

from spec_mining import core

SPECS = ["process-issues", "residue-scan", "spec-ste-enforcement"]

DATA = {
    "aliases": {"tools/spec_ste_check": "spec-ste-enforcement"},
    "projects": {"crm": ["crm-*"]},
    "coverage": {".claude/skills/residue-scan": "residue-scan"},
}


def _units(**extra):
    units = {
        "tools": ["tools/residue_scan", "tools/widget_maker"],
        "hooks": [".claude/hooks/halt-gate"],
        "skills": [".claude/skills/residue-scan", ".claude/skills/widget-guide"],
        "projects": ["crm"],
    }
    units.update(extra)
    return units


def test_the_name_rule_normalizes_one_token():
    assert core.normalize("widget_maker.py") == "widget-maker"
    assert core.normalize("peak-hours-gate.sh") == "peak-hours-gate"
    assert core.normalize("a--b") == "a-b"


def test_a_tool_with_no_capability_reports_as_uncovered():
    report = core.scan_tree(_units(), SPECS, DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert "tools/widget_maker" in names


def test_an_alias_keeps_a_unit_off_the_uncovered_list():
    report = core.scan_tree(_units(), SPECS, DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert "tools/spec_ste_check" not in names


def test_a_name_match_keeps_a_tool_covered():
    report = core.scan_tree(_units(), SPECS, DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert "tools/residue_scan" not in names


def test_a_skill_with_no_coverage_entry_reports_as_uncovered():
    report = core.scan_tree(_units(), SPECS, DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert ".claude/skills/widget-guide" in names


def test_a_skill_with_a_name_match_stays_covered():
    data = {"aliases": {}, "projects": {}, "coverage": {}}
    units = _units(skills=[".claude/skills/process-issues"])
    report = core.scan_tree(units, SPECS, data)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert ".claude/skills/process-issues" not in names


def test_a_covered_skill_stays_off_the_uncovered_list():
    report = core.scan_tree(_units(), SPECS, DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert ".claude/skills/residue-scan" not in names


def test_a_project_glob_stays_covered():
    report = core.scan_tree(_units(), SPECS + ["crm-engine"], DATA)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert "crm" not in names


def test_a_project_without_a_matching_capability_is_uncovered():
    data = {"aliases": {}, "projects": {"crm": ["crm-*"]}, "coverage": {}}
    report = core.scan_tree(_units(), ["residue-scan"], data)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert "crm" in names


def test_a_coverage_entry_holds_a_glob_list():
    data = {
        "aliases": {},
        "projects": {},
        "coverage": {".claude/skills/widget-guide": ["widget-*"]},
    }
    units = _units(skills=[".claude/skills/widget-guide"])
    report = core.scan_tree(units, SPECS + ["widget-guide"], data)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert ".claude/skills/widget-guide" not in names


def test_a_string_coverage_entry_covers_a_renamed_skill():
    data = {
        "aliases": {},
        "projects": {},
        "coverage": {".claude/skills/gizmo-guide": "gizmo-capability"},
    }
    units = _units(skills=[".claude/skills/gizmo-guide"])
    report = core.scan_tree(units, SPECS + ["gizmo-capability"], data)
    names = [entry["unit"] for entry in report["uncovered"]]
    assert ".claude/skills/gizmo-guide" not in names


def test_a_data_file_entry_without_a_unit_is_stale():
    data = {
        "aliases": {"tools/gone_tool": "residue-scan"},
        "projects": {},
        "coverage": {},
    }
    report = core.scan_tree(_units(), SPECS, data)
    assert report["stale"] == ["tools/gone_tool"]


def _delta(body, capability="residue-scan", change="2026-01-01-add-x"):
    return {"change": change, "capability": capability, "scenarios": body}


def test_a_missing_spec_scenario_reports_as_drift():
    archive = [_delta(["Old run"])]
    specs = {"residue-scan": ["A merged branch reports"]}
    drift = core.scan_drift(archive, specs)
    assert drift == [
        {
            "change": "2026-01-01-add-x",
            "capability": "residue-scan",
            "scenario": "Old run",
            "missing_spec": False,
        }
    ]


def test_a_synced_capability_reports_no_drift():
    archive = [_delta(["Old run"])]
    specs = {"residue-scan": ["Old run"]}
    assert core.scan_drift(archive, specs) == []


def test_an_empty_delta_produces_no_drift():
    assert core.scan_drift([_delta([])], {"residue-scan": []}) == []


def test_a_missing_spec_directory_carries_the_mark():
    archive = [_delta(["Old run"], capability="old-cap")]
    drift = core.scan_drift(archive, {})
    assert drift[0]["missing_spec"] is True


def test_the_rank_orders_by_count_then_name():
    counts = {"tools/widget_maker": 10, "docs/widget_guide": 10, "crm": 30}
    ranked = core.rank(counts)
    assert [row["area"] for row in ranked] == ["crm", "docs/widget_guide", "tools/widget_maker"]
    assert ranked[0]["commits"] == 30
