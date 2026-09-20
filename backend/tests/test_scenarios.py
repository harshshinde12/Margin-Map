"""Scenarios (AO-03) endpoint tests (Phase 8)."""


def test_scenarios_returns_200(client):
    assert client.get("/api/scenarios").status_code == 200


def test_scenario_data_exists(client):
    body = client.get("/api/scenarios").json()
    assert body["count"] == 140
    assert len(body["data"]) == 140


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


def test_uniform020_scenario_present_with_values(client):
    body = client.get(
        "/api/scenarios", params={"scenario_id": "uniform_replace_0.20"}
    ).json()
    assert body["count"] == 35
    by_block_metric = {(r["block"], r["metric_name"]): r for r in body["data"]}
    hypo = float(by_block_metric[("hypothetical", "contribution_profit")]["metric_value"])
    var = float(by_block_metric[("variance", "variance_contribution_profit")]["metric_value"])
    assert abs(hypo - 560667.96) < 0.05
    assert abs(var - -4448.98) < 0.05


def test_baseline_identical_across_scenarios(client):
    base = {}
    for sid in ("uniform_replace_0.10", "uniform_replace_0.20",
                "discount_increase_pp_0.00", "discount_decrease_pp_0.00"):
        rows = client.get("/api/scenarios", params={"scenario_id": sid}).json()["data"]
        base[sid] = {(r["block"], r["metric_name"]): r["metric_value"] for r in rows
                     if r["block"] == "baseline"}
    ref = base["uniform_replace_0.10"]
    for sid, vals in base.items():
        assert vals == ref, f"baseline differs for {sid}"
