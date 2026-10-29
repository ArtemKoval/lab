"""What the test backend has recorded on cases and runs."""


def case_of(client, case_id):
    return client.get(f"/api/cases/{case_id}").json()


def steps_of(client, case_id):
    return client.get(f"/api/cases/{case_id}/steps").json()


def latest(client):
    return client.get("/api/runs/latest").json()
