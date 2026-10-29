"""Tests for the redaction engine: one secret shape per behaviour,
the clean pass-through, the counts, and the deep value walk. Every
planted shape here is synthetic."""

import pytest
from handover_telemetry.redact import Redactor, default_redactor

MARK = "[REDACTED"


def test_token_shape_gets_marked_and_counted():
    r = default_redactor()
    out = r.scrub("auth gho_AAAABBBBCCCCDDDDEEEEFFFFGGGGHHH1 end")
    assert "gho_AAAABBBB" not in out
    assert MARK in out
    assert r.counts["token"] == 1


def test_sk_token_shape_gets_marked():
    r = default_redactor()
    out = r.scrub("key sk-live-abc123def456ghi789jkl012 end")
    assert "sk-live-abc123" not in out
    assert r.counts["token"] == 1


def test_aws_key_shape_gets_marked():
    r = default_redactor()
    out = r.scrub("id AKIAIOSFODNN7EXAMPLE end")
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert r.counts["token"] == 1


def test_slack_token_shape_gets_marked():
    r = default_redactor()
    out = r.scrub("hook xoxb-123456789012-abcdef end")
    assert "xoxb-123456789012" not in out
    assert r.counts["token"] == 1


def test_gitlab_token_shape_gets_marked():
    # the literal splits so the push scanner sees no full token shape
    token = "glpat-" + "Ab12Cd34Ef56Gh78Ij90"
    r = default_redactor()
    out = r.scrub(f"pat {token} end")
    assert token not in out
    assert r.counts["token"] == 1


def test_github_pat_shape_gets_marked():
    r = default_redactor()
    out = r.scrub("pat github_pat_11AAAAAAA0aaaaaaaaaaaaaa end")
    assert "github_pat_11AAAAAAA0" not in out
    assert r.counts["token"] == 1


def test_jwt_gets_marked():
    r = default_redactor()
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3OH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJVadQssw5c"
    out = r.scrub(f"bearer {jwt} end")
    assert "eyJhbGciOiJ" not in out
    assert r.counts["jwt"] == 1


def test_private_key_block_gets_marked():
    r = default_redactor()
    block = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA7n\n-----END RSA PRIVATE KEY-----"
    out = r.scrub(f"pem {block} end")
    assert "MIIEpAIBAAKCAQEA7n" not in out
    assert r.counts["key_block"] == 1


def test_credential_pair_gets_marked():
    r = default_redactor()
    out = r.scrub("api_key = hunter2secret end")
    assert "hunter2secret" not in out
    assert r.counts["credential_pair"] == 1


def test_email_gets_marked():
    r = default_redactor()
    out = r.scrub("mail jane.doe@example.org end")
    assert "jane.doe@example.org" not in out
    assert r.counts["email"] == 1


def test_ipv4_gets_marked():
    r = default_redactor()
    out = r.scrub("addr 192.168.13.5 end")
    assert "192.168.13.5" not in out
    assert r.counts["ip"] == 1


def test_url_credentials_gets_marked():
    r = default_redactor()
    out = r.scrub("at https://bob:hunter2@example.com/repo end")
    assert "bob:hunter2@" not in out
    assert r.counts["url_cred"] == 1


def test_home_path_becomes_tilde():
    r = default_redactor()
    out = r.scrub("run at /home/alice/repo/main.py end")
    assert "/home/alice" not in out
    assert "~/repo/main.py" in out
    assert r.counts["home_path"] == 1


def test_macos_home_path_becomes_tilde():
    r = default_redactor()
    out = r.scrub("run at /Users/alice/repo end")
    assert "/Users/alice" not in out
    assert "~/repo" in out


def test_timezone_name_gets_marked():
    r = default_redactor()
    out = r.scrub("zone Europe/Paris offset end")
    assert "Europe/Paris" not in out
    assert r.counts["tz_name"] == 1


def test_high_entropy_secret_gets_marked():
    r = default_redactor()
    secret = "0123456789abcdef0123456789abcdef.xSyntheticTest0Key"
    out = r.scrub(f"env {secret} end")
    assert secret not in out
    assert r.counts["high_entropy"] == 1


def test_commit_sha_survives():
    r = default_redactor()
    sha = "47ed7c8baaa291b11112222333344445555666677"
    assert sha in r.scrub(f"merge {sha} end")
    assert "high_entropy" not in r.counts


def test_low_entropy_mixed_candidate_survives():
    r = default_redactor()
    candidate = "A1a" * 16
    assert candidate in r.scrub(f"word {candidate} end")
    assert "high_entropy" not in r.counts


def test_clean_text_passes_with_no_counts():
    r = default_redactor()
    text = "The suite runs three gates. 12 tool calls, 4 models."
    assert r.scrub(text) == text
    assert sum(r.counts.values()) == 0


def test_counts_accumulate_across_calls():
    r = default_redactor()
    r.scrub("mail a@example.org end")
    r.scrub("mail b@example.org end")
    assert r.counts["email"] == 2


def test_scrub_value_walks_containers():
    r = default_redactor()
    value = {"cmd": "mail a@example.org", "n": 3, "deep": ["at /home/alice/x"]}
    out = r.scrub_value(value)
    assert out["cmd"] != value["cmd"]
    assert out["n"] == 3
    assert "/home/alice" not in out["deep"][0]


def test_scrub_value_keeps_tuple_type():
    r = default_redactor()
    out = r.scrub_value(("mail a@example.org", "clean"))
    assert isinstance(out, tuple)
    assert out[1] == "clean"


def test_mark_carries_the_category():
    r = default_redactor()
    out = r.scrub("mail jane.doe@example.org end")
    assert "[REDACTED:email]" in out


def test_new_redactor_starts_empty():
    r = Redactor()
    assert r.counts == {}


@pytest.mark.parametrize(
    "text",
    [
        "tools/spec_ste_check rules",
        "see adr/0004-enforce-ste-in-specs.md",
        "run at ~/repo/main.py",
        "gap 42 ms",
    ],
)
def test_common_repo_text_survives(text):
    r = default_redactor()
    assert r.scrub(text) == text
