"""The module entry point: python -m slidecast."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
