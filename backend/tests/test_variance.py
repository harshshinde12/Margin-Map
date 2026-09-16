"""Variance (AO-04) endpoint tests (Phase 8)."""


def test_variance_returns_200(client):
    assert client.get("/api/variance").status_code == 200


def test_variance_data_exists(client):
    body = client.get("/api/variance").json()
    assert body["count"] == 420


def test_variance_band_filter(client):
    body = client.get("/api/variance", params={"band": "B5"}).json()
    assert body["count"] > 0
    assert all(r["band"] == "B5" for r in body["data"])


def test_variance_scenario_filter(client):
    body = client.get(
        "/api/variance", params={"scenario_id": "uniform_replace_0.10"}
    ).json()
    assert body["count"] > 0
    assert all(r["scenario_id"] == "uniform_replace_0.10" for r in body["data"])
