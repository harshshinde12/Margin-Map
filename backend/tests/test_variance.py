"""Variance (AO-04) endpoint tests (Phase 8)."""


def test_variance_returns_200(client):
    assert client.get("/api/variance").status_code == 200


def test_variance_data_exists(client):
    body = client.get("/api/variance").json()
    assert body["count"] == 560


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


def test_uniform020_bands_sum_to_total(client):
    body = client.get(
        "/api/variance", params={"scenario_id": "uniform_replace_0.20"}
    ).json()
    rows = [r for r in body["data"]
            if r["block"] == "variance" and r["metric_name"] == "variance_contribution"]
    by_band = {r["band"]: float(r["metric_value"]) for r in rows}
    detail = sum(v for b, v in by_band.items() if b != "TOTAL")
    assert abs(detail - by_band["TOTAL"]) < 0.05
