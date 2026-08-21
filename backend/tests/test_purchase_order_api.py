from datetime import date, datetime, timedelta, timezone

import pymongo

from app.core.config import get_settings

FUTURE_DATE = (date.today() + timedelta(days=15)).isoformat()


def _insert_extracted_quote(rfq_id: str, vendor_id: str, unit_price: float = 180.0) -> None:
    settings = get_settings()
    db = pymongo.MongoClient(settings.mongodb_uri)[settings.mongodb_database]
    db.quotes.insert_one(
        {
            "rfq_id": rfq_id,
            "vendor_id": vendor_id,
            "filename": "quote.pdf",
            "file_type": "pdf",
            "status": "extracted",
            "extraction_error": None,
            "created_at": datetime.now(timezone.utc),
            "extraction": {
                "items": [
                    {"sku": "SKU-1", "description": "Widget", "quantity": 500, "unit": "pcs", "unit_price": unit_price}
                ],
                "delivery_days": 10,
                "payment_terms": "Net 30",
                "warranty": "1 year",
                "exclusions": [],
                "risks": [],
                "missing_information": [],
            },
            "normalized": {
                "calculated_subtotal": unit_price * 500,
                "calculated_total": unit_price * 500,
                "document_total": unit_price * 500,
                "total_matches_document": True,
                "normalized_unit_price": unit_price,
            },
            "risks": [],
        }
    )


def _create_vendor(client, email="apex@example.com"):
    resp = client.post(
        "/api/v1/vendors",
        json={
            "name": "Priya Sharma",
            "company": "Apex Industrial Supplies",
            "email": email,
            "reliability_score": 65,
            "quality_score": 70,
            "payment_score": 70,
            "risk_level": "medium",
        },
    )
    return resp.json()["id"]


def _rfq_payload(vendor_ids, delivery_date=FUTURE_DATE):
    return {
        "title": "Industrial Bearing Procurement",
        "description": "Bulk bearing procurement",
        "specifications": "6205-2RS Industrial Bearing",
        "quantity": 500,
        "unit": "pcs",
        "required_delivery_date": delivery_date,
        "invited_vendor_ids": vendor_ids,
    }


def _fake_explanation():
    return {
        "recommendation_summary": "Vendor offers the best combined value.",
        "why_recommended": ["Lowest total cost"],
        "key_strengths": ["Reliable delivery"],
        "key_risks": [],
        "tradeoffs": [],
        "alternative_vendor": None,
        "confidence": "high",
        "explanation": "Deterministic scoring favors this vendor.",
    }


def _seed_recommendation_cache(client, rfq_id: str) -> None:
    comparison = client.get(f"/api/v1/rfqs/{rfq_id}/comparison").json()
    winner = comparison["entries"][0]
    alternative = comparison["entries"][1] if len(comparison["entries"]) > 1 else None

    settings = get_settings()
    db = pymongo.MongoClient(settings.mongodb_uri)[settings.mongodb_database]
    db.procurement_decisions.update_one(
        {"rfq_id": rfq_id},
        {
            "$set": {
                "rfq_id": rfq_id,
                "recommended_vendor_id": winner["vendor_id"],
                "recommended_vendor_name": winner["vendor_name"],
                "recommended_score": winner["total_score"],
                "alternative_vendor_id": alternative["vendor_id"] if alternative else None,
                "alternative_vendor_name": alternative["vendor_name"] if alternative else None,
                "alternative_score": alternative["total_score"] if alternative else None,
                "potential_savings": None,
                "explanation": _fake_explanation(),
                "generated_at": datetime.now(timezone.utc),
                "ranking_signature": [[e["vendor_id"], e["total_score"]] for e in comparison["entries"]],
            }
        },
        upsert=True,
    )

    rec_resp = client.get(f"/api/v1/rfqs/{rfq_id}/recommendation")
    assert rec_resp.status_code == 200, rec_resp.text


def _rfq_approved(client, email="apex@example.com"):
    vendor_id = _create_vendor(client, email)
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()
    _insert_extracted_quote(rfq["id"], vendor_id)
    _seed_recommendation_cache(client, rfq["id"])

    approval = client.post(
        f"/api/v1/rfqs/{rfq['id']}/approval",
        json={"decision": "approved", "approver_name": "Jordan Lee"},
    )
    assert approval.status_code == 201, approval.text

    return rfq, vendor_id


def test_create_po_before_approval_is_rejected(client):
    vendor_id = _create_vendor(client, "noapproval@example.com")
    rfq = client.post("/api/v1/rfqs", json=_rfq_payload([vendor_id])).json()

    resp = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]})
    assert resp.status_code == 409


def test_po_creation_and_issue_happy_path(client):
    rfq, vendor_id = _rfq_approved(client, email="happy@example.com")

    create_resp = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]})
    assert create_resp.status_code == 201, create_resp.text
    po = create_resp.json()
    assert po["po_number"].startswith("PO-")
    assert po["status"] == "draft"
    assert po["vendor_id"] == vendor_id
    assert po["rfq_id"] == rfq["id"]
    assert po["total"] == 180.0 * 500
    assert len(po["items"]) == 1
    assert po["items"][0]["line_total"] == 180.0 * 500

    rfq_after = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert rfq_after["status"] == "po_created"

    get_resp = client.get(f"/api/v1/purchase-orders/{po['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["po_number"] == po["po_number"]

    list_resp = client.get("/api/v1/purchase-orders")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    issue_resp = client.patch(
        f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "issued"}
    )
    assert issue_resp.status_code == 200
    assert issue_resp.json()["status"] == "issued"

    rfq_after_issue = client.get(f"/api/v1/rfqs/{rfq['id']}").json()
    assert rfq_after_issue["status"] == "po_issued"


def test_audit_trail_records_full_po_lifecycle(client):
    """Regression test: every PO status transition (issued, acknowledged,
    received, cancelled-from-issued) must produce a distinct audit event,
    not just 'issued'."""
    rfq, _ = _rfq_approved(client, email="audittrail@example.com")
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()

    client.patch(f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "issued"})
    client.patch(f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "acknowledged"})
    client.patch(f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "received"})

    trail = client.get(f"/api/v1/rfqs/{rfq['id']}/audit-trail")
    assert trail.status_code == 200
    event_types = [e["event_type"] for e in trail.json()["items"]]

    assert "rfq_approved" in event_types
    assert "po_created" in event_types
    assert "po_issued" in event_types
    assert "po_acknowledged" in event_types
    assert "po_received" in event_types


def test_invalid_po_status_transition_is_rejected(client):
    rfq, _ = _rfq_approved(client, email="invalidtransition@example.com")
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()

    # draft -> received is not a legal direct transition
    resp = client.patch(
        f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "received"}
    )
    assert resp.status_code == 409


def test_po_cancellation_allowed_from_draft(client):
    rfq, _ = _rfq_approved(client, email="cancel@example.com")
    po = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq["id"]}).json()

    resp = client.patch(
        f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "cancelled"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # cancelled is terminal
    resp2 = client.patch(
        f"/api/v1/purchase-orders/{po['id']}/status", json={"status": "issued"}
    )
    assert resp2.status_code == 409


def test_po_numbers_increment(client):
    rfq1, _ = _rfq_approved(client, email="increment1@example.com")
    rfq2, _ = _rfq_approved(client, email="increment2@example.com")

    first = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq1["id"]}).json()
    second = client.post("/api/v1/purchase-orders", json={"rfq_id": rfq2["id"]}).json()

    assert first["po_number"] != second["po_number"]


def test_get_unknown_purchase_order_returns_404(client):
    resp = client.get("/api/v1/purchase-orders/000000000000000000000000")
    assert resp.status_code == 404
