import os
import subprocess
import sys
from pathlib import Path

import apfel_eval

ROOT = Path(__file__).resolve().parents[1]
PRINT_VARIABLE = "import os, apfel_eval; print(os.environ['DEEPEVAL_TELEMETRY_OPT_OUT'])"


def variable_after_import(**overrides):
    """Import the package in a new interpreter and return the telemetry variable."""
    env = {k: v for k, v in os.environ.items() if k != "DEEPEVAL_TELEMETRY_OPT_OUT"}
    env.update(overrides)
    done = subprocess.run(
        [sys.executable, "-c", PRINT_VARIABLE],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def test_import_turns_telemetry_off_by_default():
    assert variable_after_import() == "YES"


def test_import_keeps_a_value_that_the_user_set():
    assert variable_after_import(DEEPEVAL_TELEMETRY_OPT_OUT="NO") == "NO"


def test_function_sets_the_variable_when_it_is_missing():
    os.environ.pop("DEEPEVAL_TELEMETRY_OPT_OUT", None)
    apfel_eval._opt_out_of_telemetry()
    assert os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] == "YES"


def test_function_keeps_a_value_that_the_user_set():
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "NO"
    apfel_eval._opt_out_of_telemetry()
    assert os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] == "NO"
