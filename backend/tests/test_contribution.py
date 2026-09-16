"""Contribution (AO-02) endpoint tests (Phase 8)."""

EXPECTED_FIELDS = {
    "output_name",
    "scenario_status",
    "grain",
    "basis",
    "band",
    "source_artifact",
    "metric_name",
    "metric_value",
    "unit",
    "definition_ref",
    "limitation",
}


def test_contribution_returns_200(client):
    assert client.get("/api/contribution").status_code == 200


def test_contribution_expected_fields(client):
    row = client.get("/api/contribution").json()["data"][0]
    assert EXPECTED_FIELDS <= set(row.keys())


def test_contribution_row_count(client):
    body = client.get("/api/contribution").json()
    assert body["count"] == 238


def test_contribution_band_filter(client):
    body = client.get("/api/contribution", params={"band": "B2"}).json()
    assert body["count"] > 0
    assert all(r["band"] == "B2" for r in body["data"])


def test_contribution_metric_filter(client):
    body = client.get(
        "/api/contribution", params={"metric_name": "contribution_profit"}
    ).json()
    assert body["count"] > 0
    assert all(r["metric_name"] == "contribution_profit" for r in body["data"])
