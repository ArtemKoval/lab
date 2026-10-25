"""Make the plan_exec package importable from tools/, with the mutation
stand-down: under mutmut the mirror layout wins."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

if "MUTANT_UNDER_TEST" not in os.environ:
    for _candidate in (REPO_ROOT / "tools" / "plan_exec", REPO_ROOT):
        if (_candidate / "plan_exec").is_dir():
            sys.path.insert(0, str(_candidate))
            break
