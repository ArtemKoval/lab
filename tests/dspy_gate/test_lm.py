"""Tests for the model factory: the pins from gates.yaml, the key
gate, and the one-constructor-site rule."""

import sys
import types

import pytest

from dspy_gate import gatepolicy, lm


@pytest.fixture()
def stub_dspy(monkeypatch):
    """A dspy stand-in whose LM records its constructor kwargs."""
    module = types.ModuleType("dspy")
    built = []

    class LM:
        def __init__(self, model, **kwargs):
            self.model = model
            self.kwargs = kwargs
            built.append(self)

    module.LM = LM
    monkeypatch.setitem(sys.modules, "dspy", module)
    monkeypatch.setattr(lm, "_built", built)
    return built


def test_lm_for_builds_the_pinned_role(stub_dspy, monkeypatch):
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    lm.lm_for("judge")
    instance = stub_dspy[-1]
    assert instance.model == "openai/glm-5.3-flash"
    assert instance.kwargs["temperature"] == 0.0
    assert instance.kwargs["max_tokens"] == 4096
    assert instance.kwargs["api_base"] == lm.ZAI_BASE
    thinking = instance.kwargs["model_kwargs"]["extra_body"]["thinking"]
    assert thinking == {"type": "disabled"}


def test_lm_for_without_a_key_names_the_variable(stub_dspy, monkeypatch):
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    with pytest.raises(lm.MissingKeyError) as exc:
        lm.lm_for("judge")
    assert "ZAI_API_KEY" in str(exc.value)


def test_every_role_pin_is_flash():
    policy = lm.load_policy()
    roles = gatepolicy.roles(policy)
    assert roles["runtime"]["model"] == "glm-5.3-flash"
    assert roles["runtime_hard"]["model"] == "glm-5.3-flash"
    assert roles["reflection"]["model"] == "glm-5.3-flash"
    assert roles["judge"]["model"] == "glm-5.3-flash"
    assert roles["vision_judge"]["model"] == "glm-5.3-flash"


def test_no_role_enables_thinking():
    policy = lm.load_policy()
    for role, spec in gatepolicy.roles(policy).items():
        assert spec["thinking"] == "disabled", role


def test_dspy_lm_is_constructed_in_one_site_only():
    """The one-factory rule: a second constructor site would silently
    opt a code path out of the pin governance."""
    from pathlib import Path

    package = Path(lm.__file__).parent
    offenders = []
    for source in package.glob("*.py"):
        if source.name == "lm.py":
            continue
        if "dspy.LM(" in source.read_text(encoding="utf-8"):
            offenders.append(source.name)
    assert offenders == []
