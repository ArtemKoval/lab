"""Tests of the database helpers."""

import threading

from backend.database import connect, seed


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


def test_a_seed_over_a_seeded_database_rebuilds_the_same_queue(database):
    """The seed rebuilds the pack queue, so a second run holds the same rows."""

    def queue_rows():
        rows = (
            connect()
            .execute("SELECT case_id, record, status FROM cases ORDER BY case_id")
            .fetchall()
        )
        return [(row["case_id"], row["record"], row["status"]) for row in rows]

    first = queue_rows()
    counts = seed(database)
    assert counts["cases"] == 25
    assert queue_rows() == first
