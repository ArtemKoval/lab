"""Make both session_statusline modules importable from tools/, with
the same pattern the other tool lanes use."""

import sys
from pathlib import Path

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree, so the tests import the mutated copy.
REPO_ROOT = Path(__file__).absolute().parents[2]

for _candidate in (
    REPO_ROOT / "tools" / "session_statusline",
    REPO_ROOT / "tools" / "session_statusline_setup",
):
    if _candidate.is_dir():
        sys.path.insert(0, str(_candidate))
