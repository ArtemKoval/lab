"""Make the saturation_pass module importable from tools/.

absolute(), not resolve(): the mutator symlink overlay must keep this
path inside the worker tree, so the tests import the mutated copy.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "saturation_pass"))
