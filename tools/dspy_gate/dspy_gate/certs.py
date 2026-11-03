"""The Gate 5 certification ledger.

One JSONL row per green certification beside the tool, keyed by
capability. The row carries the pins digest of the policy it
certified. Drift compares the current digest with the last row: a pin
change without a fresh green record fails the gate. Before the first
certification the ledger is absent and the gate passes with a note.
"""

import hashlib
import json
from pathlib import Path

CERTS_DIR = Path("tools/dspy_gate/certs")


def pins_digest(policy_text):
    """The short digest of the model role pins of one policy text."""
    import yaml

    roles = yaml.safe_load(policy_text).get("models", {}).get("roles", {})
    canonical = json.dumps(roles, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def read_rows(path):
    """Read every ledger row."""
    store = Path(path)
    if not store.is_file():
        return []
    return [
        json.loads(line)
        for line in store.read_text(encoding="utf-8").splitlines()
        if line
    ]


def record(path, pins, source, green=True):
    """Append one certification row."""
    store = Path(path)
    store.parent.mkdir(parents=True, exist_ok=True)
    row = {"pins": pins, "source": source, "green": green}
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def drift(path, current_pins):
    """Return the drift violations of one capability ledger."""
    rows = read_rows(path)
    if not rows:
        return []
    last = rows[-1]
    if not last.get("green"):
        return [f"{Path(path).parent.name}: the last certification is red"]
    if last.get("pins") != current_pins:
        return [
            f"{Path(path).parent.name}: pins stale; the ledger holds "
            f"{last.get('pins')} against current {current_pins}"
        ]
    return []


def ledger_path(root, capability):
    """The ledger path of one capability."""
    return Path(root) / CERTS_DIR / f"{capability}.jsonl"
