"""Orders (AO-05) endpoint tests (Phase 8)."""


def test_orders_returns_200(client):
    assert client.get("/api/orders").status_code == 200


def test_orders_default_pagination(client):
    body = client.get("/api/orders").json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["count"] == 50
    assert len(body["data"]) == 50


def test_orders_limit_enforced(client):
    r = client.get("/api/orders", params={"limit": 501})
    assert r.status_code == 400
    r = client.get("/api/orders", params={"limit": 0})
    assert r.status_code == 400


def test_orders_offset(client):
    first = client.get("/api/orders", params={"limit": 5, "offset": 0}).json()
    second = client.get("/api/orders", params={"limit": 5, "offset": 5}).json()
    assert second["offset"] == 5
    assert first["data"] != second["data"]


def test_orders_band_filter(client):
    body = client.get(
        "/api/orders", params={"discount_band": "B0", "limit": 10}
    ).json()
    assert body["count"] > 0
    assert all(r["discount_band"] == "B0" for r in body["data"])


def test_orders_neg_flag_filter(client):
    body = client.get("/api/orders", params={"neg_flag": "True", "limit": 10}).json()
    assert body["count"] > 0
    assert all(r["neg_flag"] == "True" for r in body["data"])


def test_orders_grain_preserved(client):
    body = client.get("/api/orders", params={"limit": 50}).json()
    for row in body["data"]:
        assert row["order_id"]
        assert row["metric_name"]
        assert row["grain"] == "Order"
