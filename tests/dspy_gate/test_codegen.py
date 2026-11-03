"""Tests for the generated Tier-A conformance module: the GENERATED
header, the deterministic bytes, and the Tier-A case filter."""

from dspy_gate import codegen, manifest

from test_manifest import CHANGE, MODULES


def render():
    return codegen.generate(manifest.build(CHANGE, MODULES))


def test_the_module_starts_with_the_generated_marker():
    assert render().lstrip().startswith('"""GENERATED')


def test_the_module_names_every_tier_a_scenario():
    text = render()
    assert "outage-routes-to-on-call" in text
    assert "escalation-happens-before-reply" not in text


def test_the_render_is_deterministic():
    assert render() == render()


def test_the_render_carries_the_parametrize_contract():
    text = render()
    assert "parametrize" in text
    assert "run_tier_a" in text
    assert "edit the spec" in text


def test_write_lands_the_module_at_the_target_path(tmp_path):
    path = codegen.write(tmp_path, render())
    assert path == tmp_path / "test_spec_conformance.py"
    assert path.read_text(encoding="utf-8") == render()
