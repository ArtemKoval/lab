"""Shared path setup for the devcontainer_init tests. Hermetic by default."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The package sits under tools/ in the repository and directly under the
# root in a flat mutation mirror. Import whichever copy is present, so a
# moved tree still has tests for its own source. Under mutmut, the
# variable MUTANT_UNDER_TEST is set and mutmut must control the import
# path, so the manual insert stops and the mutants copy wins.
if "MUTANT_UNDER_TEST" not in os.environ:
    for _candidate in (REPO_ROOT / "tools" / "devcontainer_init", REPO_ROOT):
        if (_candidate / "devcontainer_init").is_dir():
            sys.path.insert(0, str(_candidate))
            break
