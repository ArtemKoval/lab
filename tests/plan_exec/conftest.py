"""Make the plan_exec package importable from tools/, with the mutation
stand-down: under mutmut the mirror layout wins."""

import os
import sys
from pathlib import Path

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree, so the tests import the mutated copy.
REPO_ROOT = Path(__file__).absolute().parents[2]

if "MUTANT_UNDER_TEST" not in os.environ:
    for _candidate in (REPO_ROOT / "tools" / "plan_exec", REPO_ROOT):
        if (_candidate / "plan_exec").is_dir():
            sys.path.insert(0, str(_candidate))
            break
