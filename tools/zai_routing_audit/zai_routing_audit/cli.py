"""Command line interface. Argparse wiring and output only; logic lives in core."""

import argparse
import json
import sys

from . import core
from .core import LiveTransport, TransportError


def namespace(**overrides):
    """Build an argparse Namespace with CLI defaults for programmatic callers."""
    values = {
        "func": None,
        "json": False,
        "settings": None,
        "base_url": None,
        "directory": None,
        "names": None,
        "max_tokens": None,
        "pad_words": None,
        "spend_credits": False,
        "start": None,
        "end": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def build_parser():
    """Build the argument parser with one subcommand per audit step."""
    parser = argparse.ArgumentParser(
        prog="zai_routing_audit",
        description="Audit the z.ai GLM model routing behind Claude Code.",
    )
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable JSON"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    config = sub.add_parser("config", help="read back the routing settings")
    config.add_argument("--settings", default=None, help="path to a settings.json file")
    config.set_defaults(func=run_config)

    transcripts = sub.add_parser("transcripts", help="scan Claude Code transcripts")
    transcripts.add_argument(
        "--directory", required=True, help="directory with .jsonl files"
    )
    transcripts.set_defaults(func=run_transcripts)

    echo = sub.add_parser("echo", help="compare requested and echoed model names")
    echo.add_argument("names", nargs="+", help="model names to test")
    echo.add_argument("--max-tokens", type=int, default=32)
    echo.add_argument("--settings", default=None)
    echo.add_argument("--base-url", dest="base_url", default=None)
    echo.set_defaults(func=run_echo)

    usage = sub.add_parser("usage", help="read per-model usage rows and credit pools")
    usage.add_argument(
        "--start", default=None, help="start YYYY-MM-DD HH:MM:SS, default today 00:00"
    )
    usage.add_argument(
        "--end", default=None, help="end YYYY-MM-DD HH:MM:SS, default today 23:59"
    )
    usage.add_argument("--settings", default=None)
    usage.add_argument("--base-url", dest="base_url", default=None)
    usage.set_defaults(func=run_usage)

    speed = sub.add_parser("throughput", help="time one generation per model name")
    speed.add_argument("names", nargs="+")
    speed.add_argument("--max-tokens", type=int, default=1024)
    speed.add_argument("--settings", default=None)
    speed.add_argument("--base-url", dest="base_url", default=None)
    speed.set_defaults(func=run_throughput)

    burn = sub.add_parser("burn", help="measure the credit cost per model name")
    burn.add_argument("names", nargs="+")
    burn.add_argument("--pad-words", dest="pad_words", type=int, default=48000)
    burn.add_argument("--max-tokens", type=int, default=1)
    burn.add_argument(
        "--spend-credits",
        dest="spend_credits",
        action="store_true",
        help="required to send burn requests. Without it the tool prints the plan",
    )
    burn.add_argument("--settings", default=None)
    burn.add_argument("--base-url", dest="base_url", default=None)
    burn.set_defaults(func=run_burn)
    return parser


def _resolve(args):
    """Load settings and build a live transport for the network commands."""
    settings_path = args.settings or core.DEFAULT_SETTINGS
    settings = core.load_json_file(settings_path)
    token = core.settings_token(settings)
    if not token:
        raise ValueError(f"no ANTHROPIC_AUTH_TOKEN in {settings_path}")
    # pragma: no mutate - the facts dictionary only feeds the base URL here,
    # so the settings_path argument cannot change the outcome.
    facts = core.routing_facts(settings, settings_path)
    base_url = args.base_url or facts["base_url"]
    if not base_url:
        raise ValueError(f"no ANTHROPIC_BASE_URL in {settings_path}")
    return LiveTransport(base_url, token), token


def run_config(args):
    """Read back the routing settings."""
    settings_path = args.settings or core.DEFAULT_SETTINGS
    return core.routing_facts(core.load_json_file(settings_path), settings_path)


def run_transcripts(args):
    """Scan a transcript directory."""
    return core.scan_transcripts(args.directory)


def run_echo(args):
    """Compare requested and echoed model names."""
    transport, _ = _resolve(args)
    results = core.echo_compare(transport, args.names, max_tokens=args.max_tokens)
    return {"ok": core.echo_ok(results), "results": results}


def run_usage(args):
    """Read per-model usage rows and credit pools."""
    transport, token = _resolve(args)
    start, end = _window(args)
    base_url = transport.base_url
    rows = core.fetch_model_rows(transport, base_url, start, end, token)
    pools = core.fetch_pools(transport, base_url, token)
    return {"window": {"start": start, "end": end}, "models": rows, "pools": pools}


def run_throughput(args):
    """Time one generation per model name."""
    transport, _ = _resolve(args)
    results = core.throughput_compare(
        transport, args.names, max_tokens=args.max_tokens
    )
    return {"results": results}


def run_burn(args):
    """Measure the credit cost per model name, behind the explicit flag."""
    if not args.spend_credits:
        return core.burn_plan(
            args.names, pad_words=args.pad_words, max_tokens=args.max_tokens
        )
    transport, token = _resolve(args)
    return core.burn_compare(
        transport,
        transport.base_url,
        args.names,
        pad_words=args.pad_words,
        max_tokens=args.max_tokens,
        spend=True,
        token=token,
    )


def _window(args):
    """Resolve the usage time window from arguments or the day bounds."""
    start, end = core.day_bounds()
    return args.start or start, args.end or end


def _print_text(payload, indent=0):
    """Print a payload as nested key and value lines."""
    pad = "  " * indent
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                print(f"{pad}{key}:")
                _print_text(value, indent + 1)
            else:
                print(f"{pad}{key}: {value}")
    elif isinstance(payload, list):
        for item in payload:
            _print_text(item, indent)
    else:
        print(f"{pad}{payload}")


def main(argv=None):
    """Run one command. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = args.func(args)
    except (ValueError, OSError, TransportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)
    if args.func is run_echo and not payload["ok"]:
        return 2
    return 0
