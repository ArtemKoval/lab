"""Render the Claude Code status line for the current session.

The tool reads one status line payload on standard input and prints
one summary line: the model, the thinking effort, the 5-hour and
weekly limit percentages, the session cache rate, the input and
output token totals in millions, and the time in UTC. The payload is
the first source for every field. The session transcript backs the
token totals and the cache rate. The `usage` command of
`zai_routing_audit` backs absent limit percentages behind a cache.
The tool fails open: every data fault renders n/a fields and exits 0.

Usage:
    python session_statusline.py [--json] [--cache-dir PATH]

Exit 0 on a rendered line and 2 on a wrong invocation.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CACHE_TTL_SECONDS = 300
CONSOLE_TIMEOUT_SECONDS = 10
MODEL_MAX_CHARS = 24
REPO_ROOT = Path(__file__).resolve().parents[2]


def load_payload(stream):
    """Parse the stdin payload, or raise ValueError on a bad payload."""
    data = json.loads(stream.read())
    if not isinstance(data, dict):
        raise ValueError("payload is no JSON object")
    return data


def fmt_pct(value):
    """Format one percentage payload value, or n/a."""
    if value is None:
        return "n/a"
    return f"{round(value)}%"


def fmt_millions(value):
    """Format one token count in millions with two decimals, or n/a."""
    if value is None:
        return "n/a"
    return f"{value / 1_000_000:.2f}M"


def fmt_cache_rate(value):
    """Format one cache ratio from 0 to 1, or n/a."""
    if value is None:
        return "n/a"
    return f"{round(value * 100)}%"


def payload_mapping(payload, key):
    """Return one payload key as a dict, or an empty dict."""
    value = payload.get(key) or {}
    return value if isinstance(value, dict) else {}


def payload_effort(payload):
    """Return the effort level from the payload, or None."""
    return payload_mapping(payload, "effort").get("level")


def payload_window(payload, window):
    """Return one payload rate-limit percentage, or None."""
    window_row = payload_mapping(payload, "rate_limits").get(window)
    if not isinstance(window_row, dict):
        return None
    return window_row.get("used_percentage")


def payload_cache_ratio(payload):
    """Return the payload prompt-cache hit ratio, or None."""
    return payload_mapping(payload, "prompt_cache").get("hit_ratio")


def read_json_cache(path):
    """Read one cache file, or None on any fault."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_json_cache(path, data):
    """Write one cache file atomically, and ignore write faults."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False, suffix=".tmp"
        )
        with handle:
            json.dump(data, handle)
        os.replace(handle.name, path)
    except OSError:
        pass


def transcript_sums(text):
    """Sum the usage fields over the assistant lines of a transcript.

    A line that does not parse, or carries no usage object, adds
    nothing. The keys follow the handover-telemetry rule.
    """
    total_in = 0
    total_out = 0
    cache_read = 0
    cache_creation = 0
    rows = 0
    for line in text.splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        rows += 1
        total_in += usage.get("input_tokens") or 0
        total_out += usage.get("output_tokens") or 0
        cache_read += usage.get("cache_read_input_tokens") or 0
        cache_creation += usage.get("cache_creation_input_tokens") or 0
    return {
        "rows": rows,
        "in": total_in,
        "out": total_out,
        "cache_read": cache_read,
        "cache_creation": cache_creation,
    }


def usable_offset(offset, size):
    """Return True when the cached offset re-reads a live transcript."""
    return isinstance(offset, int) and 0 < offset <= size


def cache_totals(cache, session_id, size):
    """Return (offset, rows, totals) from a valid session cache, or
    the empty start. A cached offset past the size resets the read."""
    empty = (0, 0, {"in": 0, "out": 0, "cache_read": 0, "cache_creation": 0})
    if not isinstance(cache, dict):
        return empty
    if cache.get("session_id") != session_id:
        return empty
    offset = cache.get("offset")
    if not usable_offset(offset, size):
        return empty
    totals = {
        "in": cache.get("in") or 0,
        "out": cache.get("out") or 0,
        "cache_read": cache.get("cache_read") or 0,
        "cache_creation": cache.get("cache_creation") or 0,
    }
    return offset, cache.get("rows") or 0, totals


def read_transcript_sums(transcript_path, cache_path, session_id):
    """Return the session usage sums, with the incremental cache.

    The cache keys on the session id. A new session resets the sums
    and drops the prior record. A cached offset past the transcript
    size triggers a full re-read. A missing or unreadable transcript
    returns None sums.
    """
    if not transcript_path:
        return None
    path = Path(transcript_path)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    size = len(raw)
    offset, rows, totals = cache_totals(
        read_json_cache(cache_path), session_id, size
    )
    chunk = raw[offset:]
    # Commit only up to the last newline, so a line that was mid-write
    # at refresh time is re-parsed on the next refresh.
    boundary = chunk.rfind(b"\n") + 1
    text = chunk[:boundary].decode("utf-8", errors="replace")
    sums = transcript_sums(text)
    keys = ("in", "out", "cache_read", "cache_creation")
    totals = {key: totals[key] + sums[key] for key in keys}
    rows += sums["rows"]
    sums.update(totals)
    sums["rows"] = rows
    record = {
        "session_id": session_id,
        "offset": offset + boundary,
        "rows": rows,
        "in": totals["in"],
        "out": totals["out"],
        "cache_read": totals["cache_read"],
        "cache_creation": totals["cache_creation"],
    }
    write_json_cache(cache_path, record)
    return sums


def default_transport(argv):
    """Run the console command, and return the completed result."""
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "tools" / "zai_routing_audit"),
    }
    try:
        done = subprocess.run(
            argv,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=CONSOLE_TIMEOUT_SECONDS,
            env=env,
        )
        return done.returncode, done.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def pool_percentages(stdout):
    """Return the two pool percentages in console order, or None rows.

    The tool reads the CREDIT_LIMIT rows only, and computes 100 times
    consumed divided by the sum of consumed and remaining. A zero
    total or a missing value renders n/a. A pool count that is not
    two renders both n/a.
    """
    try:
        payload = json.loads(stdout)
    except ValueError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    pools = [
        row
        for row in payload.get("pools", [])
        if isinstance(row, dict) and row.get("type") == "CREDIT_LIMIT"
    ]
    if len(pools) != 2:
        return None, None
    percents = []
    for row in pools:
        consumed = row.get("consumed")
        remaining = row.get("remaining")
        usable = isinstance(consumed, (int, float)) and isinstance(
            remaining, (int, float)
        )
        if not usable or consumed + remaining <= 0:
            percents.append(None)
        else:
            percents.append(round(100 * consumed / (consumed + remaining)))
    return tuple(percents)


def console_percentages(transport, cache_path, now):
    """Return (five, seven) percentages, payload-first in the caller.

    A fresh cache serves the percentages with no console call. A
    failed call serves the stale cache, and no cache renders n/a.
    """
    cache = read_json_cache(cache_path)
    if cache and isinstance(cache.get("updated"), (int, float)):
        if now - cache["updated"] < CACHE_TTL_SECONDS:
            return cache.get("five"), cache.get("seven")
    argv = [
        str(REPO_ROOT / "tools" / "zai_routing_audit" / ".venv" / "bin" / "python"),
        "-m",
        "zai_routing_audit",
        "--json",
        "usage",
    ]
    code, stdout = transport(argv)
    if code == 0:
        five, seven = pool_percentages(stdout)
        write_json_cache(cache_path, {"updated": now, "five": five, "seven": seven})
        return five, seven
    if cache:
        return cache.get("five"), cache.get("seven")
    return None, None


def resolve_windows(payload, now, transport, cache_dir):
    """Return the 5h and weekly percentages, payload first, console
    second."""
    five = payload_window(payload, "five_hour")
    seven = payload_window(payload, "seven_day")
    if five is not None and seven is not None:
        return five, seven
    console_five, console_seven = console_percentages(
        transport, Path(cache_dir) / "console.json", now
    )
    five = five if five is not None else console_five
    seven = seven if seven is not None else console_seven
    return five, seven


def resolve_cache_rate(payload, sums):
    """Return the cache rate field from the payload or the sums."""
    ratio = payload_cache_ratio(payload)
    if ratio is not None:
        return fmt_cache_rate(ratio)
    if sums and sums["rows"]:
        side = sums["in"] + sums["cache_read"] + sums["cache_creation"]
        return fmt_cache_rate(sums["cache_read"] / side) if side else "n/a"
    return "n/a"


def render(payload, now, transport, cache_dir):
    """Render the summary line, or the --json fields dict."""
    session_id = payload.get("session_id")
    transcript = payload.get("transcript_path")
    cache_dir = Path(cache_dir)
    sums = read_transcript_sums(
        transcript, cache_dir / "sums.json", session_id
    )
    five, seven = resolve_windows(payload, now, transport, cache_dir)
    cache = resolve_cache_rate(payload, sums)
    fields = {
        "model": (
            payload_mapping(payload, "model").get("display_name") or "n/a"
        )[:MODEL_MAX_CHARS],
        "effort": payload_effort(payload) or "n/a",
        "five": fmt_pct(five),
        "seven": fmt_pct(seven),
        "cache": cache,
        "in_millions": fmt_millions(sums["in"] if sums else None),
        "out_millions": fmt_millions(sums["out"] if sums else None),
        "time": datetime.fromtimestamp(now, timezone.utc).strftime("%H:%M"),
        "fault": None,
    }
    line = (
        f"{fields['model']} effort {fields['effort']} 5h {fields['five']} "
        f"wk {fields['seven']} cache {fields['cache']} in {fields['in_millions']} "
        f"out {fields['out_millions']} {fields['time']} UTC"
    )
    return line, fields


def degraded_line(now):
    """Return the fault line and fields for an unparsable payload."""
    time_text = datetime.fromtimestamp(now, timezone.utc).strftime("%H:%M")
    fields = {
        "model": "n/a",
        "effort": "n/a",
        "five": "n/a",
        "seven": "n/a",
        "cache": "n/a",
        "in_millions": "n/a",
        "out_millions": "n/a",
        "time": time_text,
        "fault": "unparsable payload",
    }
    line = (
        f"statusline: unparsable payload effort n/a 5h n/a wk n/a "
        f"cache n/a in n/a out n/a {time_text} UTC"
    )
    return line, fields


def main(argv=None):
    """Run the CLI. Render one line, or exit 2 on a wrong invocation."""
    parser = argparse.ArgumentParser(
        prog="session_statusline",
        description="Render the Claude Code status line for the session.",
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    parser.add_argument("--cache-dir", default=None, help="cache directory")
    args = parser.parse_args(argv)
    cache_dir = args.cache_dir or os.path.expanduser(
        "~/.cache/session_statusline"
    )
    now = datetime.now(timezone.utc).timestamp()
    try:
        payload = load_payload(sys.stdin)
        line, fields = render(payload, now, default_transport, cache_dir)
    except ValueError:
        line, fields = degraded_line(now)
    if args.json:
        print(json.dumps(fields))
    else:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
