"""Quality (AO-06) endpoint tests (Phase 8)."""


def test_quality_returns_200(client):
    assert client.get("/api/quality").status_code == 200


def test_quality_rows_exist(client):
    body = client.get("/api/quality").json()
    assert body["count"] == 125


def test_quality_status_filter(client):
    body = client.get("/api/quality", params={"status": "PASS"}).json()
    assert body["count"] == 125
    assert all(r["status"] == "PASS" for r in body["data"])


def test_quality_artifact_filter(client):
    body = client.get(
        "/api/quality", params={"artifact": "ALL_ARTIFACTS"}
    ).json()
    assert body["count"] == 3
    assert all(r["artifact"] == "ALL_ARTIFACTS" for r in body["data"])
