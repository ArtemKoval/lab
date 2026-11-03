"""The example bank (L2): the system's experiential memory.

One JSONL entry per validated trajectory. Writes are the sensitive
path: only trajectories whose gate verdicts are all green enter, and
an entry leaves when it fails a frozen suite. Retrieval scores token
overlap, so the runtime needs no model to recall a demonstration.
"""

import json
from pathlib import Path


def read_all(path):
    """Read every entry from the JSONL store."""
    store = Path(path)
    if not store.is_file():
        return []
    return [
        json.loads(line)
        for line in store.read_text(encoding="utf-8").splitlines()
        if line
    ]


def write(path, entry):
    """Append one entry when every gate verdict is green; else refuse."""
    verdicts = entry.get("gate_verdicts", {})
    if not verdicts or not all(verdicts.values()):
        return False
    store = Path(path)
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


def evict(path, scenario_id):
    """Remove every entry of one scenario; record nothing else."""
    store = Path(path)
    if not store.is_file():
        return 0
    kept = []
    removed = 0
    for line in store.read_text(encoding="utf-8").splitlines():
        if line and json.loads(line)["scenario_id"] == scenario_id:
            removed += 1
        elif line:
            kept.append(line)
    store.write_text(
        "".join(line + "\n" for line in kept), encoding="utf-8"
    )
    return removed


def retrieve(path, query, k=3):
    """Return the k most similar entries by token overlap."""
    query_tokens = set(query.lower().split())
    scored = []
    for entry in read_all(path):
        text = " ".join(
            [str(entry.get("inputs", "")), str(entry.get("prediction", ""))]
        ).lower()
        entry_tokens = set(text.split())
        union = max(1, len(query_tokens | entry_tokens))
        overlap = len(query_tokens & entry_tokens) / union
        scored.append((overlap, entry))
    scored.sort(key=lambda pair: -pair[0])
    return [entry for _, entry in scored[:k]]
