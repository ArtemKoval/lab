"""Make the port_library_crm package importable from tools/, with the
mutation stand-in: under the mutator the mirror layout wins."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[2]

if "MUTANT_UNDER_TEST" not in os.environ:
    sys.path.insert(0, str(REPO_ROOT / "tools" / "port_library_crm"))
