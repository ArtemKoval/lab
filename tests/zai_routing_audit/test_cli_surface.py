"""Pin the argparse surface as data, so help text, defaults, and required
flags die under mutation instead of drifting silently."""

from zai_routing_audit.cli import build_parser


def test_parser_surface_is_exact():
    parser = build_parser()
    assert _surface(parser) == {
        "json": ("print machine-readable JSON", False, False),
        "command": (None, None, True),
    }
    subs = _subcommands(parser)
    assert subs["config"] == {
        "settings": ("path to a settings.json file", None, False),
    }
    assert subs["transcripts"] == {
        "directory": ("directory with .jsonl files", None, True),
    }
    assert subs["echo"] == {
        "names": ("model names to test", None, True),
        "max_tokens": (None, 32, False),
        "settings": (None, None, False),
        "base_url": (None, None, False),
    }
    assert subs["usage"] == {
        "start": ("start YYYY-MM-DD HH:MM:SS, default today 00:00", None, False),
        "end": ("end YYYY-MM-DD HH:MM:SS, default today 23:59", None, False),
        "settings": (None, None, False),
        "base_url": (None, None, False),
    }
    assert subs["throughput"] == {
        "names": (None, None, True),
        "max_tokens": (None, 1024, False),
        "settings": (None, None, False),
        "base_url": (None, None, False),
    }
    assert subs["burn"] == {
        "names": (None, None, True),
        "pad_words": (None, 48000, False),
        "max_tokens": (None, 1, False),
        "spend_credits": (
            "required to send burn requests. Without it the tool prints the plan",
            False,
            False,
        ),
        "settings": (None, None, False),
        "base_url": (None, None, False),
    }


def _surface(parser):
    return {
        action.dest: (action.help, action.default, getattr(action, "required", False))
        for action in parser._actions
        if action.dest != "help"
    }


def _subcommands(parser):
    choices = None
    for action in parser._actions:
        if action.dest == "command":
            choices = action.choices
    return {name: _surface(sub) for name, sub in choices.items()}
