import pytest

from apfel_eval.judge import host_headers


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("http://host.docker.internal:11434/v1", {"Host": "localhost:11434"}),
        ("http://host.docker.internal:8080/v1", {"Host": "localhost:8080"}),
        ("http://host.docker.internal/v1", {"Host": "localhost"}),
        ("http://192.168.1.20:11434/v1", {"Host": "localhost:11434"}),
        ("http://[fe80::1]:11434/v1", {"Host": "localhost:11434"}),
        ("http://localhost:11434/v1", {}),
        ("http://LOCALHOST:11434/v1", {}),
        ("http://127.0.0.1:11434/v1", {}),
        ("http://[::1]:11434/v1", {}),
        ("http://localhost/v1", {}),
    ],
)
def test_host_headers(base_url, expected):
    assert host_headers(base_url) == expected
