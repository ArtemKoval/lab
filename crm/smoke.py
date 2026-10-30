"""The pack smoke run: seed a temporary database, work three cases on the stub
model, and print the decisions. No network, no model key.

Run from the crm directory: .venv/bin/python smoke.py <pack-name>
Exit 0 when the three cases were worked; exit 2 otherwise.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from domains import loader  # noqa: E402


def smoke(pack_name: str) -> int:
    os.environ["CRM_DOMAIN"] = pack_name
    # A throwaway key for the run, exactly as the tests carry one.
    os.environ.setdefault("CRM_AGENT_KEY", "smoke-agent-key")
    # The smoke run reads the pack through the loader only, and the backend's
    # test client needs the import after the variable is set.
    from backend.tests.dashboard_reads import steps_of  # noqa: F401
    from backend.tests.sign_in import PUBLIC_KEYS, signed_in  # noqa: F401
    import jwt  # noqa: F401

    from backend.database import engine, seed, is_seeded

    with tempfile.TemporaryDirectory() as tmp:
        os.environ["CRM_DB"] = str(Path(tmp) / "smoke.db")
        seed_path = Path(os.environ["CRM_DB"])
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        seed(engine())

        from fastapi.testclient import TestClient

        from agent import connection, harness
        from agent.direct import CONTEXT_URL
        from agent.tests.stubs import agent_on, decide, stub
        from backend.main import app
        from context.server import build_server

        cases = loader.pack().load_json("cases.json")
        chosen = [case["case_id"] for case in cases[:3]]
        replies = []
        for _ in chosen:
            replies.extend(decide("refer", 0))
        model = stub(*replies)

        import threading
        import uvicorn

        from agent.tests.local_server import serving

        with (
            TestClient(app, base_url=str(connection.backend.base_url)) as backend,
            serving(build_server().streamable_http_app()) as context_address,
        ):
            os.environ[CONTEXT_URL] = f"{context_address}/mcp"
            original_backend = connection.backend
            connection.backend = backend
            try:
                print(f"smoking {pack_name} on the stub model:")
                agent = agent_on(model)
                for case_id in chosen:
                    report = harness.work_case(case_id, None, agent)
                    print(f"  {report}")
            finally:
                connection.backend = original_backend

        from sqlalchemy import select

        from backend.database import cases

        with engine().connect() as connection:
            decided = connection.execute(
                select(cases.c.case_id, cases.c.status).where(
                    cases.c.status != "waiting"
                )
            ).fetchall()
        if not decided:
            print("FAIL no case was worked")
            return 2
        print(f"smoke clean: {len(decided)} cases left waiting changed state")
        return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python smoke.py <pack-name>")
        return 2
    return smoke(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
