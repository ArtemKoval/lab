"""Tests of the database helpers."""

import threading

from backend.database import connect


def test_one_connection_serves_two_threads(database):
    """The connection opts out of SQLite's same-thread check."""
    connection = connect()
    seen = []

    def read():
        row = connection.execute("SELECT award_approval_limit FROM settings")
        seen.append(row.fetchone()[0])

    thread = threading.Thread(target=read)
    thread.start()
    thread.join()
    assert seen == [1000.0]
