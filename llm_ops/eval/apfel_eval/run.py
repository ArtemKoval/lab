"""Ask a local apfel server four questions and score the answers with DeepEval.

Run it with `python -m apfel_eval.run`. The same apfel server is the judge.
"""

import argparse
import json
import os
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from pathlib import Path

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

from apfel_eval.judge import DEFAULT_MODEL, ApfelJudge

DEFAULT_BASE_URL = "http://host.docker.internal:11434/v1"
DEFAULT_THRESHOLD = 0.5
ANSWER_PROMPT = (
    "Answer the question with only the answer, in as few words as possible.\n\n"
    "Question: {question}"
)
# The steps are fixed. When the judge writes its own steps, they drift and a correct
# answer can get a score of 0.0 (measured on the apfel server, see the design).
EVALUATION_STEPS = (
    "Read the expected output and the actual output.",
    "If the actual output states the same fact as the expected output, give a score of 9 or 10. "
    "A shorter or longer wording of the same fact is the same fact.",
    "If the actual output states a different fact, give a score of 0 or 1.",
)


@dataclass(frozen=True)
class Case:
    question: str
    expected: str


@dataclass(frozen=True)
class Result:
    question: str
    expected: str
    actual: str | None
    score: float | None
    passed: bool
    reason: str | None
    error: str | None


def cases() -> tuple[Case, ...]:
    return (
        Case("What is the capital of France?", "Paris"),
        Case("How many days are in a leap year?", "366"),
        Case("What is the chemical symbol for water?", "H2O"),
        Case("Who wrote the play Romeo and Juliet?", "William Shakespeare"),
    )


def build_metric(judge: ApfelJudge, threshold: float) -> GEval:
    return GEval(
        name="Correctness",
        evaluation_steps=list(EVALUATION_STEPS),
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=threshold,
        async_mode=False,
    )


def run_case(judge: ApfelJudge, metric: GEval, case: Case) -> Result:
    try:
        actual = judge.generate(ANSWER_PROMPT.format(question=case.question)).strip()
        test_case = LLMTestCase(
            input=case.question, actual_output=actual, expected_output=case.expected
        )
        # DeepEval prints progress text. The standard output must hold only the report.
        with redirect_stdout(sys.stderr):
            metric.measure(test_case, _show_indicator=False)
        return Result(
            case.question,
            case.expected,
            actual,
            metric.score,
            bool(metric.is_successful()),
            metric.reason,
            None,
        )
    except Exception as error:  # noqa: BLE001  One bad question must not stop the others.
        message = f"{type(error).__name__}: {error}"
        return Result(case.question, case.expected, None, None, False, None, message)


def summarize(results: list[Result]) -> dict[str, int]:
    errors = sum(result.error is not None for result in results)
    passed = sum(result.passed for result in results)
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed - errors,
        "errors": errors,
    }


def exit_code(summary: dict[str, int]) -> int:
    if summary["errors"]:
        return 2
    return 1 if summary["failed"] else 0


def format_row(result: Result) -> str:
    if result.error is not None:
        verdict, score, last = "ERROR", "n/a", f"error: {result.error}"
    else:
        verdict = "PASS" if result.passed else "FAIL"
        score, last = f"{result.score:.2f}", f"answer: {result.actual}"
    row = f"{verdict} {score} | {result.question} | expected: {result.expected} | {last}"
    return " ".join(row.splitlines())


def format_summary(summary: dict[str, int]) -> str:
    return "total={total} passed={passed} failed={failed} errors={errors}".format(**summary)


def format_json(args: argparse.Namespace, results: list[Result]) -> str:
    report = {
        "base_url": args.base_url,
        "model": args.model,
        "threshold": args.threshold,
        "results": [asdict(result) for result in results],
        "summary": summarize(results),
    }
    return json.dumps(report, indent=2)


def _threshold(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError(f"{text!r} is not from 0 to 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m apfel_eval.run",
        description="Ask four questions and score the answers. The apfel server is the judge.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("APFEL_BASE_URL", DEFAULT_BASE_URL),
        help="the base URL of the apfel server (default: APFEL_BASE_URL or %(default)s)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="the model name (%(default)s)")
    parser.add_argument(
        "--threshold",
        type=_threshold,
        default=DEFAULT_THRESHOLD,
        help="the lowest score that passes, from 0 to 1 (%(default)s)",
    )
    parser.add_argument("--json", action="store_true", help="print one JSON document")
    return parser


def main(argv: list[str] | None = None) -> int:
    # The call is first: the parser reads APFEL_BASE_URL. The shell has priority over the file.
    try:
        load_dotenv(Path.cwd() / ".env")
    except (OSError, UnicodeError) as error:
        print(f"Cannot read the .env file: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    args = build_parser().parse_args(argv)
    try:
        judge = ApfelJudge(args.base_url, args.model, os.environ.get("APFEL_TOKEN"))
        judge.ping()
    except Exception as error:  # noqa: BLE001  Any failure here makes the server unusable.
        print(
            f"Cannot use the apfel server at {args.base_url}: {type(error).__name__}: {error}\n"
            "Start the server on the host with: apfel --serve",
            file=sys.stderr,
        )
        return 2
    # Each question gets a new metric. A metric keeps its error state between questions.
    results = [run_case(judge, build_metric(judge, args.threshold), case) for case in cases()]
    summary = summarize(results)
    if args.json:
        print(format_json(args, results))
    else:
        print("\n".join([*map(format_row, results), format_summary(summary)]))
    return exit_code(summary)


if __name__ == "__main__":
    raise SystemExit(main())
