"""Scenarios (AO-03) endpoint tests (Phase 8)."""


def test_scenarios_returns_200(client):
    assert client.get("/api/scenarios").status_code == 200


def test_scenario_data_exists(client):
    body = client.get("/api/scenarios").json()
    assert body["count"] == 105
    assert len(body["data"]) == 105


def test_scenario_filter(client):
    body = client.get(
        "/api/scenarios",
        params={"scenario_status": "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"},
    ).json()
    assert body["count"] > 0
    assert all(
        r["scenario_status"] == "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"
        for r in body["data"]
    )


def test_scenario_metric_filter(client):
    body = client.get(
        "/api/scenarios", params={"metric_name": "variance_contribution_profit"}
    ).json()
    assert body["count"] > 0
    assert all(r["metric_name"] == "variance_contribution_profit" for r in body["data"])


def test_scenario_terminology_preserved(client):
    rows = client.get("/api/scenarios").json()["data"]
    statuses = {r["scenario_status"] for r in rows}
    assert statuses == {"OBSERVED BASELINE", "HYPOTHETICAL_ARITHMETIC_SENSITIVITY"}
