"""Pin the argparse surface as data, so the suite kills mutants of the
help text, the defaults, and the flag definitions."""

from devcontainer_init.cli import build_parser


def test_parser_surface_is_exact():
    parser = build_parser()
    assert parser.prog == "devcontainer-init"
    assert parser.description == (
        "Scaffold a devcontainer.json with Ubuntu LTS, git, node, "
        "and uv wired up for VS Code."
    )
    surface = {}
    for action in parser._actions:
        if action.dest == "help":
            continue
        surface[action.dest] = (
            tuple(action.option_strings),
            action.help,
            action.default,
            getattr(action, "required", False),
            action.metavar,
            getattr(action, "nargs", None),
        )
    assert surface == {
        "target": (
            (),
            "project directory that receives the .devcontainer directory",
            ".",
            False,
            None,
            "?",
        ),
        "os_version": (
            ("--os",),
            "Ubuntu version for the base image",
            "26.04",
            False,
            None,
            None,
        ),
        "extensions": (
            ("--extension",),
            "VS Code extension to add to the config; repeatable",
            [],
            False,
            "ID",
            None,
        ),
        "force": (
            ("--force",),
            "overwrite an existing devcontainer.json",
            False,
            False,
            None,
            0,
        ),
        "as_json": (
            ("--json",),
            "print machine-readable JSON output",
            False,
            False,
            None,
            0,
        ),
    }
