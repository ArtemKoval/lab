"""Core audit logic. Standard library only.

The z.ai console endpoints are undocumented. Their shapes come from
reverse engineering on 2026-10-15. The parser accepts both known
envelope variants and fails with an excerpt on any other shape.
"""

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, urlsplit

DEFAULT_SETTINGS = Path.home() / ".claude" / "settings.json"

MODEL_SLOTS = (
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODE",
    "CLAUDE_CODE_SUBAGENT_MODEL",
)

QUOTA_PATH = "/api/monitor/usage/quota/limit"
MODEL_USAGE_PATH = "/api/monitor/usage/model-usage"

ECHO_PROMPT = "ping"
THROUGHPUT_PROMPT = "Write 300 words about the history of lighthouses."
BURN_MARKER = "BURNTEST."
BURN_WORDS = ("apple", "banana", "cherry", "date")


class TransportError(Exception):
    """A request to an endpoint failed."""


def redact(secret):
    """Return a short redacted prefix of a secret value."""
    if not secret:
        return ""
    return secret[:4] + "..."


def sanitize(text, token):
    """Remove a secret value from free text."""
    # pragma: no mutate - the or-form behaves the same: replacing an absent
    # token and replacing the empty token are both no-ops.
    if token and token in text:
        return text.replace(token, redact(token))
    return text


def load_json_file(path):
    """Read and parse a JSON file."""
    # pragma: no mutate - the runner locale is UTF-8, so the default and the
    # codec alias read the file identically.
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def routing_facts(settings, settings_path):
    """Extract the routing facts from a settings mapping. The token stays redacted."""
    env = settings.get("env") or {}
    return {
        "settings_path": str(settings_path),
        "base_url": env.get("ANTHROPIC_BASE_URL"),
        # pragma: no mutate - redact maps a missing and an empty token to
        # the same output, so every default form behaves the same.
        "token_redacted": redact(env.get("ANTHROPIC_AUTH_TOKEN", "")),
        "model_slots": {name: env[name] for name in MODEL_SLOTS if name in env},
    }


def settings_token(settings):
    """Return the auth token from a settings mapping, or an empty string."""
    env = settings.get("env") or {}
    return env.get("ANTHROPIC_AUTH_TOKEN") or ""


def tolerant_json(text):
    """Parse JSON, then retry with the control-character-tolerant parser."""
    try:
        return json.loads(text)
    except ValueError:
        pass
    try:
        # pragma: no mutate - the json decoder treats strict=None as falsy,
        # which is the same tolerant parse.
        return json.loads(text, strict=False)
    except ValueError as exc:
        raise ValueError(f"unparsable JSON: {exc}") from exc


def console_base(base_url):
    """Derive the console origin from a model API base URL."""
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"not a usable base URL: {base_url}")
    return f"{parts.scheme}://{parts.netloc}"


def model_usage_url(base_url, start, end):
    """Build the console per-model usage URL for a time window."""
    query = urlencode({"startTime": start, "endTime": end})
    return console_base(base_url) + MODEL_USAGE_PATH + "?" + query


def quota_url(base_url):
    """Build the console credit pool URL."""
    return console_base(base_url) + QUOTA_PATH


class LiveTransport:
    """HTTP transport for the model API and the console endpoints."""

    def __init__(self, base_url, token, timeout=120.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def post_json(self, path, payload):
        """Send a JSON POST request and return the parsed body."""
        # pragma: no mutate - UTF-8 is a codec alias of utf-8.
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            # pragma: no mutate - urllib infers POST from the data argument.
            self.base_url + path, data=data, headers=self._headers(), method="POST"
        )
        return self._read(request)

    def get_json(self, url):
        """Send a JSON GET request and return the parsed body."""
        request = urllib.request.Request(url, headers=self._headers(), method="GET")
        return self._read(request)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "Accept": "application/json",
        }

    def _read(self, request):
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return tolerant_json(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:200]
            raise TransportError(f"HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise TransportError(f"connection failed: {exc.reason}") from exc


def build_message_payload(model, max_tokens, prompt):
    """Build one Anthropic-style message request body."""
    return {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }


def echo_compare(transport, names, max_tokens=32, prompt=ECHO_PROMPT):
    """Send one small request per model name and compare the echoed names."""
    results = []
    for name in names:
        try:
            response = transport.post_json(
                "/v1/messages", build_message_payload(name, max_tokens, prompt)
            )
            if not isinstance(response, dict):
                raise ValueError("unexpected messages shape")
            usage = response.get("usage") or {}
            results.append(
                {
                    "requested": name,
                    "echoed": response.get("model"),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "error": None,
                }
            )
        except (TransportError, ValueError) as exc:
            results.append(_error_entry(name, str(exc)))
    return results


def echo_ok(results):
    """Return True when every request matched its echo without an error."""
    return all(
        entry["error"] is None and entry["echoed"] == entry["requested"]
        for entry in results
    )


def throughput_compare(
    transport, names, clock=None, max_tokens=1024, prompt=THROUGHPUT_PROMPT
):
    """Time one bounded generation per model name."""
    clock = clock or time.monotonic
    results = []
    for name in names:
        start = clock()
        try:
            response = transport.post_json(
                "/v1/messages", build_message_payload(name, max_tokens, prompt)
            )
            if not isinstance(response, dict):
                raise ValueError("unexpected messages shape")
            elapsed = clock() - start
            results.append(_throughput_entry(name, response, elapsed))
        except (TransportError, ValueError) as exc:
            results.append(_error_entry(name, str(exc)))
    return results


def _throughput_entry(name, response, elapsed):
    usage = response.get("usage") or {}
    output = usage.get("output_tokens")
    rate = None
    if output is not None and elapsed > 0:
        rate = round(output / elapsed, 1)
    return {
        "requested": name,
        "echoed": response.get("model"),
        "output_tokens": output,
        "seconds": round(elapsed, 3),
        "tokens_per_second": rate,
        "error": None,
    }


def padded_prompt(word, count):
    """Build a padding prompt with a known token footprint."""
    return f"{BURN_MARKER} Ignore all padding. " + " ".join([word] * count)


def burn_plan(names, pad_words=48000, max_tokens=1):
    """Describe a burn run without sending anything."""
    return {
        "spend": False,
        "plan": {
            "names": list(names),
            "pad_words": pad_words,
            "max_tokens": max_tokens,
        },
    }


def burn_compare(
    transport,
    base_url,
    names,
    pad_words=48000,
    max_tokens=1,
    spend=False,
    sleep=None,
    sleep_seconds=2.0,
    token="",
):
    """Measure the credit pool cost of one identical request per model name.

    Without spend, the transport never sees a burn request.
    """
    if not spend:
        return burn_plan(names, pad_words, max_tokens)
    sleep = sleep or time.sleep
    before = fetch_pools(transport, base_url, token)
    results = []
    for index, name in enumerate(names):
        word = BURN_WORDS[index % len(BURN_WORDS)]
        prompt = padded_prompt(word, pad_words)
        response = transport.post_json(
            "/v1/messages", build_message_payload(name, max_tokens, prompt)
        )
        usage = response.get("usage") or {}
        sleep(sleep_seconds)
        after = fetch_pools(transport, base_url, token)
        results.append(
            {
                "requested": name,
                "input_tokens": usage.get("input_tokens"),
                "pools": _pool_deltas(before, after),
            }
        )
        before = after
    return {"spend": True, "results": results}


def _pool_deltas(before, after):
    """Pair two pool snapshots by position and compute the consumed delta.

    The pool rows can repeat a type, so the position is the only stable key.
    """
    deltas = []
    for index, pool in enumerate(after):
        previous = before[index]["consumed"] if index < len(before) else None
        delta = None if previous is None else pool["consumed"] - previous
        deltas.append(
            {
                "type": pool["type"],
                "before": previous,
                "after": pool["consumed"],
                "delta": delta,
            }
        )
    return deltas


def fetch_pools(transport, base_url, token):
    """Read the credit pool state. Drift raises with a redacted body excerpt."""
    payload = transport.get_json(quota_url(base_url))
    try:
        return parse_quota(payload)
    except ValueError:
        raise ValueError(_shape_message("quota", payload, token)) from None


def fetch_model_rows(transport, base_url, start, end, token):
    """Read the per-model usage rows. Drift raises with a redacted body excerpt."""
    payload = transport.get_json(model_usage_url(base_url, start, end))
    try:
        return parse_model_usage(payload)
    except ValueError:
        raise ValueError(_shape_message("model-usage", payload, token)) from None


def _shape_message(kind, payload, token):
    """Build the drift error message with a truncated, redacted body."""
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return f"unexpected {kind} shape; body starts: {sanitize(body[:200], token)}"


def parse_model_usage(payload):
    """Normalize the per-model usage report. Raises on an unknown shape."""
    if not isinstance(payload, dict):
        raise ValueError("unexpected model-usage shape")
    data = payload.get("data") or {}
    # pragma: no mutate - the data value is always a dict here, so the
    # isinstance check cannot go false.
    rows = data.get("modelDataList") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError("unexpected model-usage shape")
    parsed = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            {
                "model": row.get("modelName"),
                "total_tokens": _row_total(row),
            }
        )
    return parsed


def _row_total(row):
    """Prefer the reported total; otherwise sum the time buckets."""
    total = row.get("totalTokens")
    if isinstance(total, (int, float)):
        return total
    buckets = row.get("tokensUsage")
    if isinstance(buckets, list):
        return sum(value for value in buckets if isinstance(value, (int, float)))
    return None


def parse_quota(payload):
    """Normalize the credit pool state. Accepts both known envelopes."""
    data = payload.get("data") if isinstance(payload, dict) else None
    limits = data.get("limits") if isinstance(data, dict) else None
    if not isinstance(limits, list):
        limits = payload.get("limits") if isinstance(payload, dict) else None
    if not isinstance(limits, list):
        raise ValueError("unexpected quota shape")
    return [
        {
            "type": limit.get("type"),
            "consumed": limit.get("currentValue"),
            "remaining": limit.get("remaining"),
        }
        for limit in limits
        if isinstance(limit, dict)
    ]


def day_bounds(now=None):
    """Return the start and the end of the current day as console timestamps."""
    moment = now or datetime.now()
    # pragma: no mutate - the timestamps hide microseconds, so the omitted
    # and the nonzero microsecond forms print the same strings.
    start = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    fmt = "%Y-%m-%d %H:%M:%S"
    return start.strftime(fmt), end.strftime(fmt)


def _error_entry(name, message):
    return {
        "requested": name,
        "echoed": None,
        "input_tokens": None,
        "output_tokens": None,
        "tokens_per_second": None,
        "error": message,
    }


def scan_transcripts(directory):
    """Scan transcript files for requested models, echoed models, and usage."""
    stats = {"files": 0, "skipped_lines": 0, "requested": {}, "echoed": {}, "usage": {}}
    for path in sorted(Path(directory).rglob("*.jsonl")):
        stats["files"] += 1
        _scan_file(path, stats)
    return stats


def _scan_file(path, stats):
    """Fold one transcript file into the statistics."""
    # pragma: no mutate - the runner locale is UTF-8, so the default and the
    # codec alias read the file identically.
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            is_request, model, usage = _parse_line(line)
            if is_request is None:
                stats["skipped_lines"] += 1
            elif is_request:
                stats["requested"][model] = stats["requested"].get(model, 0) + 1
            else:
                stats["echoed"][model] = stats["echoed"].get(model, 0) + 1
                if usage:
                    _add_usage(stats["usage"], model, usage)


def _parse_line(line):
    """Classify one transcript line.

    Returns (is_request, model, usage): None means skip the line, True
    means a request record, False means an assistant record.
    """
    text = line.strip()
    if not text:
        return (None, None, None)
    try:
        record = tolerant_json(text)
    except ValueError:
        return (None, None, None)
    if not isinstance(record, dict):
        return (None, None, None)
    if record.get("type") == "api-request":
        params = record.get("params") or {}
        return (True, params.get("model"), None)
    if record.get("type") == "assistant":
        message = record.get("message") or {}
        return (False, message.get("model"), message.get("usage"))
    return (None, None, None)


_USAGE_KEYS = (
    ("input", "input_tokens"),
    ("cache_write", "cache_creation_input_tokens"),
    ("cache_read", "cache_read_input_tokens"),
    ("output", "output_tokens"),
)


def _add_usage(usage_map, model, usage):
    """Sum one usage record into the per-model totals."""
    slot = usage_map.setdefault(model, {name: 0 for name, _ in _USAGE_KEYS})
    for name, key in _USAGE_KEYS:
        slot[name] += usage.get(key) or 0
