"""Tests for the Tier-A assertion runner: eq, in, and schema checks
with self-describing failures."""

from dspy_gate import checks


def test_an_eq_pass_holds():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}],
        {"severity": "P0"},
        [],
    )
    assert result.passed
    assert result.detail == ""


def test_an_eq_failure_names_the_field_and_both_sides():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "eq", "field": "severity", "value": "P0"}],
        {"severity": "P2"},
        [],
    )
    assert not result.passed
    assert "severity" in result.detail
    assert "P0" in result.detail and "P2" in result.detail


def test_an_in_pass_holds():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "in", "field": "severity", "values": ["P1", "P2"]}],
        {"severity": "P2"},
        [],
    )
    assert result.passed


def test_an_in_failure_names_the_values():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "in", "field": "severity", "values": ["P1", "P2"]}],
        {"severity": "P0"},
        [],
    )
    assert not result.passed
    assert "P1" in result.detail


def test_a_schema_pass_holds():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "schema", "fields": ["severity", "team"]}],
        {"severity": "P1", "team": "billing"},
        [],
    )
    assert result.passed


def test_a_schema_failure_names_the_missing_field():
    result = checks.run_tier_a(
        [{"tier": "A", "kind": "schema", "fields": ["severity", "team"]}],
        {"severity": "P1"},
        [],
    )
    assert not result.passed
    assert "team" in result.detail


def test_the_worst_failure_wins():
    result = checks.run_tier_a(
        [
            {"tier": "A", "kind": "eq", "field": "severity", "value": "P0"},
            {"tier": "A", "kind": "eq", "field": "team", "value": "on-call"},
        ],
        {"severity": "P2", "team": "general"},
        [],
    )
    assert not result.passed
    assert "severity" in result.detail
