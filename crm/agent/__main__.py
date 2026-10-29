"""Work the queue with the CRM Agent: uv run -m agent [--cap 5 | CLM-1001]"""

import argparse
import sys

from dotenv import load_dotenv

from agent import api
from agent.console import show_reports
from agent.harness import case_graph, checkpointer, model, run_queue, work_case


def positive(text: str) -> int:
    """Read a whole number of at least 1."""
    number = int(text)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(args: list[str]) -> None:
    """Work the case named on the command line, or the queue up to a cap."""
    parser = argparse.ArgumentParser(
        prog="uv run -m agent", description="Work the cases queue."
    )
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("case_id", nargs="?", help="work this one case")
    choice.add_argument("--cap", type=positive, help="the most cases the run works")
    options = parser.parse_args(args)
    with checkpointer() as saver:
        graph = case_graph(model(), saver)
        if not options.case_id:
            run_queue(options.cap, model(), graph)
            return
        try:
            work_case(options.case_id, graph)
        except api.Refused as refusal:
            parser.exit(1, f"{options.case_id}  not started: {refusal}\n")


if __name__ == "__main__":
    load_dotenv(override=True)
    show_reports()
    main(sys.argv[1:])
