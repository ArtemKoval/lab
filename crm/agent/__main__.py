"""Work one case with the CRM Agent: uv run -m agent CLM-1001"""

import argparse
import sys

from dotenv import load_dotenv

from agent import api
from agent.connection import Refused
from agent.console import show_reports
from agent.harness import case_graphs, checkpoint_pool, work_case


def main(args: list[str]) -> None:
    """Work the case named on the command line on the current version, with no
    run."""
    parser = argparse.ArgumentParser(
        prog="uv run -m agent", description="Work one case in the queue."
    )
    parser.add_argument("case_id", help="the case to work")
    options = parser.parse_args(args)
    with checkpoint_pool() as pool:
        graph = case_graphs(api.get_current_version(), pool)()
        try:
            work_case(options.case_id, None, graph)
        except Refused as refusal:
            parser.exit(1, f"{options.case_id}  not started: {refusal}\n")


if __name__ == "__main__":
    load_dotenv(override=True)
    show_reports()
    main(sys.argv[1:])
