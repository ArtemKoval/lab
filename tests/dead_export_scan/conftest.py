"""Make the dead_export_scan module importable from tools/, with the
worker-relative path."""

import sys
from pathlib import Path

# absolute(), not resolve(): the mutator symlink overlay must keep this
# path inside the worker tree, so the tests import the mutated copy.
REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "dead_export_scan"))
