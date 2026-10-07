import threading

import pytest
from fake_apfel import FakeApfel, completion, error

from apfel_eval import run
from apfel_eval.run import ANSWER_PROMPT, EVALUATION_STEPS, Case

PARIS = Case("What is the capital of France?", "Paris")


def run_one(make_judge, handler, threshold=0.5, case=PARIS):
    judge = make_judge(handler)
    return run.run_case(judge, run.build_metric(judge, threshold), case)


def test_cases_are_the_four_fixed_questions_in_order():
    assert run.cases() == (
        Case("What is the capital of France?", "Paris"),
        Case("How many days are in a leap year?", "366"),
        Case("What is the chemical symbol for water?", "H2O"),
        Case("Who wrote the play Romeo and Juliet?", "William Shakespeare"),
    )


# --- the score


def test_score_above_the_threshold_passes(make_judge):
    result = run_one(make_judge, FakeApfel(score=8))
    assert result == run.Result(
        question=PARIS.question,
        expected="Paris",
        actual="Paris",
        score=0.8,
        passed=True,
        reason="fake reason",
        error=None,
    )


def test_score_equal_to_the_threshold_passes(make_judge):
    result = run_one(make_judge, FakeApfel(score=5), threshold=0.5)
    assert (result.score, result.passed, result.error) == (0.5, True, None)


def test_score_below_the_threshold_fails(make_judge):
    result = run_one(make_judge, FakeApfel(score=0), threshold=0.5)
    assert (result.score, result.passed, result.error) == (0.0, False, None)


def test_the_threshold_of_the_user_decides(make_judge):
    assert run_one(make_judge, FakeApfel(score=8), threshold=0.9).passed is False
    assert run_one(make_judge, FakeApfel(score=8), threshold=0.8).passed is True


# --- the calls


def test_answer_prompt_asks_for_the_answer_only_with_temperature_zero(make_judge):
    fake = FakeApfel()
    run_one(make_judge, fake)
    assert fake.prompts() == [ANSWER_PROMPT.format(question=PARIS.question)]
    assert "only the answer" in fake.prompts()[0]
    assert fake.bodies[0]["temperature"] == 0


def test_answer_is_stripped(make_judge):
    fake = FakeApfel(answers={PARIS.question: "  Paris\n"})
    assert run_one(make_judge, fake).actual == "Paris"


def test_score_prompt_has_the_fixed_steps_and_both_outputs(make_judge):
    fake = FakeApfel(answers={PARIS.question: "Lyon"})
    run_one(make_judge, fake)
    (score_prompt,) = fake.prompts("ReasonScore")
    for number, step in enumerate(EVALUATION_STEPS, start=1):
        assert f"{number}. {step}\n" in score_prompt
    assert "Actual Output:\nLyon" in score_prompt
    assert "Expected Output:\nParis" in score_prompt


def test_metric_is_named_correctness_and_runs_in_sync_mode(make_judge):
    metric = run.build_metric(make_judge(FakeApfel()), 0.5)
    assert metric.__name__ == "Correctness [GEval]"
    # None and False both mean sync mode in DeepEval, so the test names the value.
    assert metric.async_mode is False


def test_metric_makes_every_call_from_the_calling_thread(make_judge):
    fake = FakeApfel()
    run_one(make_judge, fake)
    assert fake.thread_ids == {threading.get_ident()}


def test_metric_never_asks_the_judge_to_write_steps(make_judge):
    fake = FakeApfel()
    judge = make_judge(fake)
    metric = run.build_metric(judge, 0.5)
    for case in run.cases():
        run.run_case(judge, metric, case)
    assert len(fake.prompts()) == 4
    assert len(fake.prompts("Steps")) == 0
    assert len(fake.prompts("ReasonScore")) == 4


def test_run_case_gives_the_test_case_to_the_metric(make_judge):
    class Spy:
        score = 1.0
        reason = "spy reason"

        def measure(self, test_case, _show_indicator=True):
            self.arguments = (test_case, _show_indicator)

        def is_successful(self):
            return True

    spy = Spy()
    run.run_case(make_judge(FakeApfel()), spy, PARIS)
    test_case, show_indicator = spy.arguments
    assert show_indicator is False
    assert test_case.input == PARIS.question
    assert test_case.actual_output == "Paris"
    assert test_case.expected_output == "Paris"


def test_text_from_the_metric_goes_to_the_error_stream(make_judge, capsys):
    class Noisy:
        score = 1.0
        reason = "r"

        def measure(self, test_case, _show_indicator=True):
            print("noise from the metric")

        def is_successful(self):
            return True

    run.run_case(make_judge(FakeApfel()), Noisy(), PARIS)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "noise from the metric" in captured.err


# --- errors


def test_error_in_the_answer_call_is_recorded(make_judge):
    result = run_one(make_judge, FakeApfel(fail_questions=(PARIS.question,)))
    assert result.error.startswith("BadRequestError: ")
    assert "context window is full" in result.error
    assert (result.actual, result.score, result.reason, result.passed) == (None, None, None, False)


def test_error_in_the_score_call_is_recorded(make_judge):
    fake = FakeApfel()

    def handler(request):
        if b"ReasonScore" in request.content:
            return error(500, "score call failed")
        return fake(request)

    result = run_one(make_judge, handler)
    assert result.error.startswith("InternalServerError: ")
    assert (result.actual, result.score, result.passed) == (None, None, False)


def test_error_that_is_not_from_the_server_is_recorded(make_judge):
    result = run_one(make_judge, lambda request: completion(None))
    assert result.error == "ValueError: The reply from the apfel server has no text."


def test_interrupt_is_not_caught(make_judge):
    def interrupt(request):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_one(make_judge, interrupt)
