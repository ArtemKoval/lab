"""Work the queue with the CRM Agent: uv run -m agent [CLM-1001]"""

import sys
import uuid

from agent.main import run, work_queue


def main(args: list[str]) -> None:
    """Work the case named on the command line, or every waiting case."""
    if args:
        print(run(args[0], str(uuid.uuid4())))
    else:
        work_queue()


if __name__ == "__main__":
    main(sys.argv[1:])
