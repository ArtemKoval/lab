"""Keep a mutant from launching coverage against the project under test.

`run()` falls through into `run_coverage` when a mutant skips the help return.
That would delete `target/coverage` and recurse into this suite.
"""

import pytest


@pytest.fixture(autouse=True)
def do_not_launch_project_coverage(monkeypatch):
    monkeypatch.setattr("crapper.cli.run_coverage", lambda *_args, **_kwargs: None)


# Owned by this repository: the two upstream tests below shell out to tools
# this repository does not carry (Babashka for the crap4clj EDN reader, and
# the zsh-shebang `uml` launcher). Skip them with a written reason wherever
# those tools are absent, so the vendored suite stays green in CI and on
# plain hosts while it still runs everywhere the tools exist.

import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

_EXTERNAL_TOOLS = ("bb", "zsh")


def pytest_collection_modifyitems(config, items):
    missing = [name for name in _EXTERNAL_TOOLS if shutil.which(name) is None]
    if not missing:
        return
    reasons = {
        "test_project_snapshot_is_readable_as_crap4clj_edn",
        "test_uml_loader_rejects_a_missing_viewer",
    }
    skip = pytest.mark.skip(
        reason=f"upstream test shells out to a missing external tool: {', '.join(missing)}"
    )
    for item in items:
        if item.name in reasons:
            item.add_marker(skip)
