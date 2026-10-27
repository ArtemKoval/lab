"""Entry point for `python -m spec_ste_check`. The suite tests cli.main
directly, so this shim stays two lines."""
from spec_ste_check.cli import main

raise SystemExit(main())
