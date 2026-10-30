"""The revoke gate: without --revoke no network path runs; with it, an
OpenRouter key is disabled through the provisioning API; without the
provisioning key the manual command is printed."""

import json
import urllib.error
from unittest import mock

import pytest

from tools.sec_scan import sec_scan
from tools.sec_scan.sec_scan import Finding, Report, revoke

OPENROUTER_KEY = "sk-or-v1-" + "a" * 64


def a_report() -> Report:
    report = Report()
    report.findings.append(
        Finding(
            file="crm/.env",
            line=3,
            provider="OpenRouter",
            kind="provider key",
            preview=OPENROUTER_KEY[:12] + "…",
            revoke_path="OpenRouter: revoke at openrouter.ai/keys",
            key_hash=OPENROUTER_KEY,
        )
    )
    return report


def test_revoke_without_the_flag_makes_no_network_call(capsys):
    report = a_report()
    with mock.patch.object(sec_scan, "disable_openrouter_key", side_effect=AssertionError):
        exit_code = revoke(report, report.as_dict())
    assert exit_code == 0
    assert report.manual and not report.revoked


def test_revoke_with_a_provisioning_key_disables(monkeypatch):
    report = a_report()
    calls = []

    def fake_disable(key, provisioning):
        calls.append((key, provisioning))
        return True, "HTTP 200"

    monkeypatch.setenv("OPENROUTER_PROVISIONING_KEY", "prov-key")
    monkeypatch.setattr(sec_scan, "disable_openrouter_key", fake_disable)
    exit_code = revoke(report, report.as_dict())
    assert exit_code == 0
    assert calls == [(OPENROUTER_KEY, "prov-key")]
    assert report.revoked


def test_a_failed_revoke_is_reported(monkeypatch):
    report = a_report()
    monkeypatch.setenv("OPENROUTER_PROVISIONING_KEY", "prov-key")
    monkeypatch.setattr(
        sec_scan,
        "disable_openrouter_key",
        lambda key, provisioning: (False, "HTTP 403"),
    )
    exit_code = revoke(report, report.as_dict())
    assert exit_code == 2
    assert report.revoke_failures


def test_disable_openrouter_key_parses_the_provider_answer():
    import urllib.error

    class Answer:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"{}"

        status = 200

    request = mock.patch.object(
        sec_scan.urllib.request,
        "urlopen",
        return_value=Answer(),
    )
    with request:
        ok, reason = sec_scan.disable_openrouter_key(OPENROUTER_KEY, "prov")
    assert ok is True and reason == "HTTP 200"


def test_disable_openrouter_key_reports_an_http_error():
    error = urllib.error.HTTPError("url", 403, "forbidden", {}, None)
    with mock.patch.object(sec_scan.urllib.request, "urlopen", side_effect=error):
        ok, reason = sec_scan.disable_openrouter_key(OPENROUTER_KEY, "prov")
    assert (ok, reason) == (False, "HTTP 403")
