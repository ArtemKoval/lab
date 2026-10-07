"""Evaluate answers with DeepEval and a local apfel server as the judge."""

import os


def _opt_out_of_telemetry() -> None:
    # DeepEval connects to a telemetry host unless this variable is set.
    # A value that the user set stays as it is.
    os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")


# This call runs before a submodule loads DeepEval.
_opt_out_of_telemetry()
