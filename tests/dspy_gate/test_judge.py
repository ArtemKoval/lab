"""Tests for the Tier-B judge: the pure ensemble, the threshold
contract, and the lazy dspy-backed vote functions under a stub."""

import sys
import types

import pytest

from dspy_gate import judge


def case(rubric="rubrics/escalation.md", ensemble=3):
    return {
        "scenario_id": "escalation-happens-before-reply",
        "rubric": rubric,
        "checks": [
            {"tier": "B", "kind": "judge", "rubric": rubric, "ensemble": ensemble}
        ],
    }


def votes(*scores):
    sequence = iter(scores)
    return lambda case: next(sequence)


def test_the_ensemble_mean_passes_at_the_threshold():
    result = judge.judge_case(case(), votes(1.0, 0.5, 1.0), threshold=0.80)
    assert result.passed
    assert "0.83" in result.detail


def test_the_ensemble_mean_fails_below_the_threshold():
    result = judge.judge_case(case(), votes(1.0, 0.5, 0.5), threshold=0.80)
    assert not result.passed
    assert "0.67" in result.detail
    assert "0.8" in result.detail


def test_the_detail_names_the_rubric():
    result = judge.judge_case(case(), votes(1.0, 1.0, 1.0), threshold=0.80)
    assert "rubrics/escalation.md" in result.detail


def test_ensemble_size_comes_from_the_case_checks():
    result = judge.judge_case(case(ensemble=2), votes(1.0, 0.0), threshold=0.80)
    assert "0.5" in result.detail


def test_a_missing_rubric_fails_the_judge():
    result = judge.judge_case(case(rubric=None), votes(1.0, 1.0, 1.0), threshold=0.80)
    assert not result.passed
    assert "no rubric" in result.detail


@pytest.fixture()
def stub_dspy(monkeypatch):
    """A minimal dspy stand-in: Predict returns a fixed score object."""
    module = types.ModuleType("dspy")

    class Image:
        pass

    class Signature:
        pass

    class InputField:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class OutputField:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Predict:
        def __init__(self, signature):
            self.signature = signature

        def load_lm(self, lm):
            self.lm = lm

        def __call__(self, **kwargs):
            result = types.SimpleNamespace(score=1.0, verdict="pass", reason="ok")
            return result

    class LM:
        def __init__(self, model, **kwargs):
            self.model = model
            self.kwargs = kwargs

    module.Image = Image
    module.Signature = Signature
    module.InputField = InputField
    module.OutputField = OutputField
    module.Predict = Predict
    module.LM = LM
    monkeypatch.setitem(sys.modules, "dspy", module)
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    return module


def test_the_text_vote_fn_builds_under_a_stub_dspy(stub_dspy):
    vote_fn = judge.build_vote_fn(role="judge")
    score = vote_fn(case())
    assert score == 1.0


def test_the_visual_vote_fn_builds_under_a_stub_dspy(stub_dspy):
    vote_fn = judge.build_visual_vote_fn(role="vision_judge")
    score = vote_fn({"assertion": "the banner is legible"})
    assert score == 1.0
