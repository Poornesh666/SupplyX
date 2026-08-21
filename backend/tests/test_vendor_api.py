def _vendor_payload(email="apex@example.com"):
    return {
        "name": "Priya Sharma",
        "company": "Apex Industrial Supplies",
        "email": email,
        "reliability_score": 65,
        "quality_score": 70,
        "payment_score": 70,
        "risk_level": "medium",
    }


def test_create_and_get_vendor(client):
    create_resp = client.post("/api/v1/vendors", json=_vendor_payload())
    assert create_resp.status_code == 201
    vendor = create_resp.json()
    assert vendor["company"] == "Apex Industrial Supplies"
    assert vendor["vendor_id"].startswith("VND-")

    get_resp = client.get(f"/api/v1/vendors/{vendor['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "apex@example.com"


def test_list_vendors(client):
    client.post("/api/v1/vendors", json=_vendor_payload("a@example.com"))
    client.post("/api/v1/vendors", json=_vendor_payload("b@example.com"))

    resp = client.get("/api/v1/vendors")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_duplicate_email_rejected(client):
    client.post("/api/v1/vendors", json=_vendor_payload("dup@example.com"))
    resp = client.post("/api/v1/vendors", json=_vendor_payload("dup@example.com"))
    assert resp.status_code == 409


def test_invalid_email_rejected(client):
    payload = _vendor_payload()
    payload["email"] = "not-an-email"
    resp = client.post("/api/v1/vendors", json=payload)
    assert resp.status_code == 422


def test_get_unknown_vendor_returns_404(client):
    resp = client.get("/api/v1/vendors/000000000000000000000000")
    assert resp.status_code == 404


def test_get_vendor_with_malformed_id_returns_400(client):
    resp = client.get("/api/v1/vendors/not-a-valid-id")
    assert resp.status_code == 400
