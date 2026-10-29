"""The redaction engine shared by the hook and the CLI.

Three layers live here. The pattern scrub marks secret shapes in every
emitted string and counts each hit per category. The home-path rule
rewrites host paths to a tilde form. The high-entropy pass catches
unshaped secrets, with a pure-hex exemption that keeps commit ids.
The omission layer lives in the callers: they only hand allowlisted
fields to this module.
"""

import math
import re
from collections import Counter

_MARK = "[REDACTED:{category}]"

_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
            r"|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}"
            r"|xox[baprs]-[A-Za-z0-9-]{10,}"
            r"|glpat-[A-Za-z0-9_-]{15,})\b"
        ),
        _MARK,
    ),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        _MARK,
    ),
    (
        "key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        _MARK,
    ),
    (
        "credential_pair",
        re.compile(
            r"(?i)\b(?:api[_-]?key|apikey|secret|password|passwd|pwd|auth[_-]?token"
            r"|access[_-]?token|token)\b[ \t]*[:=][ \t]*\S{8,}"
        ),
        "",
    ),
    (
        "url_cred",
        re.compile(r"([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^@\s]+@"),
        r"\1" + _MARK + "@",
    ),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), _MARK),
    ("ip", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), _MARK),
    ("home_path", re.compile(r"/(?:home|users)/[A-Za-z0-9._-]+", re.IGNORECASE), "~"),
    (
        "tz_name",
        re.compile(
            r"\b(?:UTC|Etc|Africa|America|Antarctica|Arctic|Asia|Atlantic"
            r"|Australia|Europe|Indian|Pacific)/[A-Za-z0-9_+-]+"
        ),
        _MARK,
    ),
]

_HIGH_ENTROPY = re.compile(r"[A-Za-z0-9_.+=/-]{32,}")
_HEX_ONLY = re.compile(r"[0-9a-f]+\Z")


def _entropy(text: str) -> float:
    total = len(text)
    counts = Counter(text)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def _looks_secretish(candidate: str) -> bool:
    if _HEX_ONLY.match(candidate):
        return False
    if _entropy(candidate) < 3.5:
        return False
    has_digit = any(c.isdigit() for c in candidate)
    has_upper = any(c.isupper() for c in candidate)
    return has_digit and has_upper


class Redactor:
    """Scrubs strings and counts every hit per category."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()

    def scrub(self, text: str) -> str:
        out = text
        for category, pattern, replacement in _PATTERNS:
            repl = self._replacement(replacement, category)
            out, hits = pattern.subn(repl, out)
            if hits:
                self.counts[category] += hits
        return self._scrub_high_entropy(out)

    @staticmethod
    def _replacement(replacement: str, category: str) -> str:
        if "{category}" in replacement:
            return replacement.format(category=category)
        return replacement

    def _scrub_high_entropy(self, text: str) -> str:
        parts: list[str] = []
        hits = 0
        last = 0  # pragma: no mutate: None slices like 0
        for match in _HIGH_ENTROPY.finditer(text):
            parts.append(text[last:match.start()])
            if _looks_secretish(match.group(0)):
                parts.append(_MARK.format(category="high_entropy"))
                hits += 1
            else:
                parts.append(match.group(0))
            last = match.end()
        parts.append(text[last:])
        if hits:
            self.counts["high_entropy"] += hits
        return "".join(parts)

    def scrub_value(self, value: object) -> object:
        if isinstance(value, str):
            return self.scrub(value)
        if isinstance(value, dict):
            return {key: self.scrub_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            fixed = [self.scrub_value(item) for item in value]
            return type(value)(fixed)
        return value


def default_redactor() -> Redactor:
    return Redactor()
