"""Entry point for `python -m handover_telemetry`. The suite tests
cli.main directly, so this shim stays two lines."""
from handover_telemetry.cli import main

raise SystemExit(main())
