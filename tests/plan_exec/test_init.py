"""Pin the package metadata."""

import plan_exec


def test_version_is_pinned():
    assert plan_exec.__version__ == "1.0.0"
