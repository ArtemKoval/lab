"""Make the negative_instruction_audit module importable from tools/,
with the same pattern the other tool lanes use."""

import sys
from pathlib import Path

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree, so the tests import the mutated copy.
REPO_ROOT = Path(__file__).absolute().parents[2]

for _candidate in (REPO_ROOT / "tools" / "negative_instruction_audit", REPO_ROOT):
    if (_candidate / "negative_instruction_audit.py").is_file():
        sys.path.insert(0, str(_candidate))
        break
