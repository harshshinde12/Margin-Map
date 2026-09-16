"""Baseline (AO-01) endpoint tests (Phase 8)."""

EXPECTED_FIELDS = {
    "output_name",
    "scenario_status",
    "grain",
    "source_artifact",
    "metric_name",
    "metric_value",
    "unit",
    "definition_ref",
    "limitation",
}


def test_baseline_returns_200(client):
    r = client.get("/api/baseline")
    assert r.status_code == 200


def test_baseline_rows_exist(client):
    body = client.get("/api/baseline").json()
    assert body["count"] == 20
    assert len(body["data"]) == 20


def test_baseline_expected_fields(client):
    row = client.get("/api/baseline").json()["data"][0]
    assert EXPECTED_FIELDS <= set(row.keys())


def test_baseline_metric_filter(client):
    body = client.get("/api/baseline", params={"metric_name": "net_revenue"}).json()
    assert body["count"] == 1
    assert body["data"][0]["metric_name"] == "net_revenue"
    assert body["data"][0]["metric_value"] == "2297200.8603000003"
    assert body["data"][0]["unit"] == "CUR"


def test_baseline_unknown_metric_returns_empty(client):
    body = client.get("/api/baseline", params={"metric_name": "no_such_metric"}).json()
    assert body["count"] == 0
    assert body["data"] == []
