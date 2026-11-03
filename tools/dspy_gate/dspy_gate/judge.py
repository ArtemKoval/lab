"""The Tier-B judge: rubric ensembles with lazy dspy imports.

The pure ensemble math runs anywhere; the dspy-backed vote functions
import dspy and the model factory only inside their bodies, so the
root suite never touches the model stack. A live run needs the
ZAI_API_KEY variable; a text vote returns a 0..1 rubric score, and a
visual vote returns 1.0 for pass and 0.0 for fail.
"""

from . import checks


def judge_case(case, vote_fn, threshold):
    """Vote ensemble-size times and compare the mean with the threshold.

    The detail carries the rubric, the mean, and the threshold, so a
    failure names its evidence.
    """
    rubric = case.get("rubric")
    if not rubric:
        return checks.Result(False, "judge: the case carries no rubric")
    size = _ensemble_size(case)
    votes = [float(vote_fn(case)) for _ in range(size)]
    mean = sum(votes) / size
    detail = (
        f"judge {rubric}: mean {mean:.2f} of {size} votes"
        f" against threshold {threshold}"
    )
    if mean < threshold:
        return checks.Result(False, detail)
    return checks.Result(True, detail)


def _ensemble_size(case):
    for assertion in case.get("checks", []):
        if assertion.get("tier") == "B":
            return int(assertion.get("ensemble", 3))
    return 3


def build_vote_fn(role="judge"):
    """Build the rubric-score vote function on the pinned judge role."""
    import dspy

    from . import lm

    class ConformanceJudge(dspy.Signature):
        """Score one scenario prediction against its rubric."""

        rubric: str = dspy.InputField(desc="the rubric text")
        prediction: str = dspy.InputField(desc="the prediction")
        trace: str = dspy.InputField(desc="the tool trace")
        score: float = dspy.OutputField(desc="0.0 to 1.0")

    predict = dspy.Predict(ConformanceJudge)
    predict.load_lm(lm.lm_for(role))

    def vote(case):
        result = predict(
            rubric=_rubric_text(case["rubric"]),
            prediction="",  # filled by the runner before the call
            trace="",
        )
        return max(0.0, min(1.0, float(result.score)))

    return vote


def build_visual_vote_fn(role="vision_judge"):
    """Build the majority-vote visual function on the vision role."""
    import dspy

    from . import lm

    class VisualCheck(dspy.Signature):
        """Judge whether a rendered page satisfies one spec assertion."""

        screenshot: dspy.Image = dspy.InputField(desc="full-page screenshot")
        a11y_snapshot: str = dspy.InputField(desc="accessibility tree")
        assertion: str = dspy.InputField(desc="THEN text from the manifest")
        verdict: str = dspy.OutputField(desc="pass or fail")

    predict = dspy.Predict(VisualCheck)
    predict.load_lm(lm.lm_for(role))

    def vote(case):
        result = predict(
            screenshot=case.get("screenshot"),
            a11y_snapshot=case.get("a11y_snapshot", ""),
            assertion=case.get("assertion", ""),
        )
        return 1.0 if result.verdict == "pass" else 0.0

    return vote


def visual_gate(case, vote_fn, votes=3):
    """Majority vote of the visual ensemble; a single vote is no gate."""
    results = [vote_fn(case) for _ in range(votes)]
    passed = sum(1 for score in results if score >= 0.5)
    return passed * 2 > votes


def _rubric_text(rubric):
    """Read the rubric text from its path, or return the path itself."""
    from pathlib import Path

    path = Path(rubric)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return rubric
