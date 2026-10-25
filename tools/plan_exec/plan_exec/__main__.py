"""Entry point for `python -m plan_exec`. The suite tests cli.main
directly, so this shim stays two lines."""
from plan_exec.cli import main

raise SystemExit(main())
