"""Health endpoint tests (Phase 8)."""


def test_health_returns_200(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_health_database_available(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_read_only(client):
    body = client.get("/api/health").json()
    assert body["read_only"] is True
